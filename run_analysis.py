"""
Network Measurement Orchestrator (Python-only)
- Collects data (ping + iperf) via SSH/ADB
- Samples CPU (CN/gNB/VNF/PNF) with mpstat and fetches logs
- Saves results into ./data/<date>-<mode>(...)/...
- Runs existing analysis scripts with a centralized output dir
"""

import os
import sys
import time
import json
import shlex
import argparse
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Tuple, List

# ---------------------------
# Configuration data classes
# ---------------------------
@dataclass
class ServerConfig:
    # Required: export these in your shell or a .env before running
    server_password: str = os.environ.get("SERVER_PASSWORD", "")
    # CN server where iperf3 server and ping run
    cn_user: str = os.environ.get("CN_SERVER_USER", "")
    cn_host: str = os.environ.get("CN_SERVER_HOST", "")
    # gNB PNF/Monolithic server
    gnb_user: str = os.environ.get("GNB_SERVER_USER", "")
    gnb_host: str = os.environ.get("GNB_SERVER_HOST", "")
    # gNB VNF (NFAPI split) server (optional; use when split mode)
    vnf_user: str = os.environ.get("VNF_GNB_SERVER_USER", "")
    vnf_host: str = os.environ.get("VNF_GNB_SERVER_HOST", "")
    # Control PC ADB device id
    adb_device: str = os.environ.get("ADB_DEVICE", "")
    # Control PC (for remote ADB; optional)
    control_pc_user: str = os.environ.get("CONTROL_PC_USER", "")
    control_pc_ip: str = os.environ.get("CONTROL_PC_IP", "")
    # CN side egress interface for ping
    interface: str = os.environ.get("INTERFACE", "ogstun")
    # CN IP (server that iperf client connects to)
    test_server_ip: str = os.environ.get("TEST_SERVER_IP", "")
    # Optional SSH options
    ssh_options: str = os.environ.get("SSH_OPTIONS", "-o StrictHostKeyChecking=no")

@dataclass
class TestMatrix:
    # Ranges; set via CLI or env
    dl_start: int = int(os.environ.get("DL_START", "100"))
    dl_end: int = int(os.environ.get("DL_END", "500"))
    dl_step: int = int(os.environ.get("DL_STEP", "100"))
    enable_ul: bool = os.environ.get("ENABLE_UL", "false").lower() == "true"
    ul_start: int = int(os.environ.get("UL_START", "100"))
    ul_end: int = int(os.environ.get("UL_END", "500"))
    ul_step: int = int(os.environ.get("UL_STEP", "100"))
    test_udp: bool = os.environ.get("TEST_UDP", "true").lower() == "true"
    test_tcp: bool = os.environ.get("TEST_TCP", "false").lower() == "true"
    duration: int = int(os.environ.get("TEST_DURATION", "15"))
    sleep_window: int = int(os.environ.get("SLEEP_WINDOW", "3"))

@dataclass
class ModeConfig:
    # "Monolithic" or "NFAPI"
    mode: str = os.environ.get("CURRENT_MODE", "Monolithic")
    single_machine: bool = os.environ.get("SINGLE_MACHINE_MODE", "false").lower() == "true"

# ---------------------------
# Utility helpers
# ---------------------------
def which(cmd: str) -> bool:
    return subprocess.call(["bash", "-lc", f"command -v {shlex.quote(cmd)} >/dev/null 2>&1"]) == 0

def prefer_remote_adb(server: ServerConfig) -> bool:
    return bool(server.control_pc_user and server.control_pc_ip)

def ensure_tools():
    missing = []
    # Always need these on the orchestrator machine
    for tool in ["sshpass", "screen", "iperf3"]:
        if not which(tool):
            missing.append(tool)
    # Require local adb only when not using remote ADB via Control PC
    server = ServerConfig()
    if not prefer_remote_adb(server):
        if not which("adb"):
            missing.append("adb")
    if missing:
        print(f"Missing tools: {', '.join(missing)}. Please install them before running.")
        sys.exit(1)

def ssh(server: ServerConfig, user: str, host: str, command: str) -> int:
    cmd = f"sshpass -p {shlex.quote(server.server_password)} ssh {server.ssh_options} {shlex.quote(user)}@{shlex.quote(host)} {shlex.quote(command)}"
    return subprocess.call(["bash", "-lc", cmd])

def scp_from(server: ServerConfig, user: str, host: str, remote_path: str, local_path: str) -> int:
    cmd = f"sshpass -p {shlex.quote(server.server_password)} scp {server.ssh_options} {shlex.quote(user)}@{shlex.quote(host)}:{shlex.quote(remote_path)} {shlex.quote(local_path)}"
    return subprocess.call(["bash", "-lc", cmd])

def scp_to(server: ServerConfig, user: str, host: str, local_path: str, remote_path: str) -> int:
    cmd = f"sshpass -p {shlex.quote(server.server_password)} scp {server.ssh_options} {shlex.quote(local_path)} {shlex.quote(user)}@{shlex.quote(host)}:{shlex.quote(remote_path)}"
    return subprocess.call(["bash", "-lc", cmd])

def adb_shell(server: ServerConfig, shell_cmd: str, capture_to: Optional[Path] = None) -> int:
    """
    Run 'adb shell <cmd>' either locally (if adb exists) or remotely via Control PC over SSH.
    """
    if prefer_remote_adb(server):
        # Execute adb on Control PC via SSH and stream stdout back
        remote_cmd = f"adb -s {shlex.quote(server.adb_device)} shell {shlex.quote(shell_cmd)}"
        full = f"sshpass -p {shlex.quote(server.server_password)} ssh {server.ssh_options} {shlex.quote(server.control_pc_user)}@{shlex.quote(server.control_pc_ip)} {shlex.quote(remote_cmd)}"
        if capture_to:
            with open(capture_to, "wb") as f:
                return subprocess.call(["bash", "-lc", full], stdout=f)
        return subprocess.call(["bash", "-lc", full])
    else:
        base = ["adb"]
        if server.adb_device:
            base += ["-s", server.adb_device]
        base += ["shell", shell_cmd]
        if capture_to:
            with open(capture_to, "wb") as f:
                return subprocess.call(base, stdout=f)
        return subprocess.call(base)

def adb_shell_capture(server: ServerConfig, shell_cmd: str) -> str:
    """
    Capture 'adb shell <cmd>' output either locally or via remote Control PC.
    Robust to non-UTF8 bytes (ignores undecodable sequences).
    """
    if prefer_remote_adb(server):
        # Force C locale to minimize localized output noise
        remote_inner = f"LC_ALL=C LANG=C adb -s {server.adb_device} shell {shell_cmd}"
        remote_cmd = (
            f"sshpass -p {shlex.quote(server.server_password)} ssh {server.ssh_options} "
            f"{shlex.quote(server.control_pc_user)}@{shlex.quote(server.control_pc_ip)} "
            f"{shlex.quote(remote_inner)}"
        )
        proc = subprocess.run(["bash", "-lc", remote_cmd], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        try:
            return proc.stdout.decode("utf-8", errors="ignore").strip()
        except Exception:
            return ""
    else:
        base = ["adb"]
        if server.adb_device:
            base += ["-s", server.adb_device]
        base += ["shell", shell_cmd]
        proc = subprocess.run(base, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        try:
            return proc.stdout.decode("utf-8", errors="ignore").strip()
        except Exception:
            return ""

# ---------------------------
# Collection modules
# ---------------------------
def detect_ue_ip(server: ServerConfig) -> Optional[str]:
    """
    Try to detect UE IP. Attempts multiple passes and checks common interfaces.
    """
    probe_cmd = (
        r"(ip -f inet addr show ccmni0 2>/dev/null || true; "
        r"ip -f inet addr show ccmni1 2>/dev/null || true; "
        r"ip -f inet addr show rmnet_data0 2>/dev/null || true; "
        r"ip -f inet addr show || true) | "
        r"awk '/inet / && $2 !~ /^127\./ {print $2}' | cut -d/ -f1 | head -n1"
    )
    out = adb_shell_capture(server, probe_cmd)
    return out if out else None

def start_ping(server: ServerConfig, target_ip: str) -> int:
    # ping from CN interface to UE, timestamped
    cmd = (
        f"screen -dmS ping-session bash -lc "
        f"'ping -I {shlex.quote(server.interface)} {shlex.quote(target_ip)} | "
        f"awk '{{print strftime(\"%s\"),$0}}' > ~/ping_value.log'"
    )
    return ssh(server, server.cn_user, server.cn_host, cmd)

def stop_ping_and_fetch(server: ServerConfig, local_path: Path) -> int:
    ssh(server, server.cn_user, server.cn_host, "screen -X -S ping-session quit 2>/dev/null || true")
    return scp_from(server, server.cn_user, server.cn_host, "~/ping_value.log", str(local_path))

def start_iperf_server(server: ServerConfig) -> int:
    # Start iperf3 server JSON in screen with preface start timestamp
    cmd = (
        "cat > ~/process_iperf.sh <<'EOF'\n"
        "#!/bin/bash\n"
        "ts=$(date +\"%s\")\n"
        "echo \"{\\\"start_timestamp\\\": $ts,\" > ~/iperf-server.json\n"
        "tail -n +2 <(iperf3 -s -J) >> ~/iperf-server.json\n"
        "EOF\n"
        "chmod +x ~/process_iperf.sh && screen -dmS iperf-server ~/process_iperf.sh"
    )
    return ssh(server, server.cn_user, server.cn_host, cmd)

def stop_iperf_server_and_fetch(server: ServerConfig, local_path: Path) -> int:
    # Graceful stop and fetch JSON
    ssh(server, server.cn_user, server.cn_host, "pkill -TERM iperf3 || true")
    time.sleep(3)
    ssh(server, server.cn_user, server.cn_host, "screen -X -S iperf-server quit 2>/dev/null || true")
    return scp_from(server, server.cn_user, server.cn_host, "~/iperf-server.json", str(local_path))

def run_iperf_client_on_ue(server: ServerConfig, params: str, local_path: Path) -> int:
    # Run iperf3 client on UE and capture stdout JSON locally
    shell_cmd = f"/data/local/tmp/iperf3 {params}"
    return adb_shell(server, shell_cmd, capture_to=local_path)

def start_cpu_sampling(server: ServerConfig, user: str, host: str, label: str, duration: int, interval: int = 1) -> int:
    # mpstat sampling in screen to user home
    cmd = (
        f"screen -dmS cpu-{shlex.quote(label)} bash -lc "
        f"'mpstat {interval} {duration} > ~/cpu_{label}.log 2>/dev/null || top -b -d {interval} -n {max(1, duration//interval)} > ~/cpu_{label}.log'"
    )
    return ssh(server, user, host, cmd)

def fetch_cpu_sampling(server: ServerConfig, user: str, host: str, label: str, local_path: Path) -> int:
    ssh(server, user, host, f"screen -X -S cpu-{shlex.quote(label)} quit 2>/dev/null || true")
    return scp_from(server, user, host, f"~/cpu_{label}.log", str(local_path))

# ---------------------------
# Orchestration
# ---------------------------
def build_dir_name(mode_cfg: ModeConfig, tm: TestMatrix) -> str:
    current_date = time.strftime("%Y%m%d")
    hour = time.strftime("%H")
    dl_span = f"({tm.dl_start}-{tm.dl_end}M)"
    if tm.enable_ul:
        ul_span = f"-UL({tm.ul_start}-{tm.ul_end}M)"
    else:
        ul_span = ""
    dur = f"-{tm.duration}sec" if tm.duration < 60 else f"-{tm.duration//60}min"
    return f"{current_date}-{mode_cfg.mode}{dl_span}{ul_span}{dur}-{hour}"

def run_collection(server: ServerConfig, mode_cfg: ModeConfig, tm: TestMatrix, data_dir: Path, ue_ip_override: Optional[str] = None):
    ensure_tools()

    # Resolve UE IP (with optional manual override and retries)
    if ue_ip_override:
        ue_ip = ue_ip_override
        print(f"Using provided UE IP: {ue_ip}")
    else:
        print("Detecting UE IP via ADB...")
        ue_ip = None
        for attempt in range(1, 6):
            ue_ip = detect_ue_ip(server)
            if ue_ip:
                break
            print(f"  Attempt {attempt}/5: UE IP not found, retrying...")
            time.sleep(2)
        if not ue_ip:
            print("❌ UE IP not detected after retries. Provide manually with --ue-ip or verify ADB connectivity.")
            sys.exit(1)
        print(f"UE IP: {ue_ip}")

    protocols: List[str] = []
    if tm.test_udp:
        protocols.append("udp")
    if tm.test_tcp:
        protocols.append("tcp")

    directions = ["dl"] + (["ul"] if tm.enable_ul else [])
    data_dir.mkdir(parents=True, exist_ok=True)

    # Idle ping capture
    for direction in directions:
        for proto in protocols:
            print(f"Collecting idle ping for {direction}-{proto}...")
            start_ping(server, ue_ip)
            time.sleep(tm.sleep_window)
            idle_log = data_dir / f"ping-{direction}-{proto}-idle.log"
            stop_ping_and_fetch(server, idle_log)

    for direction in directions:
        start, end, step = (tm.dl_start, tm.dl_end, tm.dl_step) if direction == "dl" else (tm.ul_start, tm.ul_end, tm.ul_step)
        reverse = "-R" if direction == "dl" else ""
        for bw in range(start, end + 1, step):
            for proto in protocols:
                file_base = f"{direction}-{proto}-{bw}M"
                print(f"▶ Running {file_base} ...")

                # Build iperf client params
                base_params = f"-c {server.test_server_ip} -b {bw}M -t {tm.duration} -p 5201 {reverse} -J"
                if proto == "udp":
                    base_params = f"-u {base_params}"

                # Start iperf server on CN
                start_iperf_server(server)
                time.sleep(1)

                # Start CPU sampling on CN + gNB side
                cpu_labels = []
                # CN CPU
                cn_label = f"cn-{file_base}"
                start_cpu_sampling(server, server.cn_user, server.cn_host, cn_label, tm.duration + 8)
                cpu_labels.append(("cn", server.cn_user, server.cn_host, cn_label))
                # gNB CPU (Monolithic) or PNF/VNF
                if mode_cfg.mode == "Monolithic":
                    gnb_label = f"gnb-{file_base}"
                    start_cpu_sampling(server, server.gnb_user, server.gnb_host, gnb_label, tm.duration + 8)
                    cpu_labels.append(("gnb", server.gnb_user, server.gnb_host, gnb_label))
                else:
                    if mode_cfg.single_machine:
                        vnf_label = f"vnf-{file_base}"
                        pnf_label = f"pnf-{file_base}"
                        start_cpu_sampling(server, server.gnb_user, server.gnb_host, vnf_label, tm.duration + 8)
                        start_cpu_sampling(server, server.gnb_user, server.gnb_host, pnf_label, tm.duration + 8)
                        cpu_labels.append(("vnf", server.gnb_user, server.gnb_host, vnf_label))
                        cpu_labels.append(("pnf", server.gnb_user, server.gnb_host, pnf_label))
                    else:
                        vnf_label = f"vnf-{file_base}"
                        pnf_label = f"pnf-{file_base}"
                        start_cpu_sampling(server, server.vnf_user, server.vnf_host, vnf_label, tm.duration + 8)
                        start_cpu_sampling(server, server.gnb_user, server.gnb_host, pnf_label, tm.duration + 8)
                        cpu_labels.append(("vnf", server.vnf_user, server.vnf_host, vnf_label))
                        cpu_labels.append(("pnf", server.gnb_user, server.gnb_host, pnf_label))

                # Start ping (timestamped)
                start_ping(server, ue_ip)
                time.sleep(tm.sleep_window)

                # Run UE iperf3 client and capture JSON locally
                ue_json = data_dir / f"iperf-{file_base}-UE.json"
                ret = run_iperf_client_on_ue(server, base_params, ue_json)
                if ret != 0:
                    print(f"⚠️ UE iperf client returned {ret}")

                # Stop CN iperf server and fetch JSON
                cn_json = data_dir / f"iperf-{file_base}-CN.json"
                stop_iperf_server_and_fetch(server, cn_json)

                # Stop ping and fetch
                time.sleep(tm.sleep_window)
                ping_log = data_dir / f"ping-{file_base}.log"
                stop_ping_and_fetch(server, ping_log)

                # Fetch CPU logs
                for role, user, host, label in cpu_labels:
                    local_cpu = data_dir / f"cpu-{role}-{file_base}.log"
                    fetch_cpu_sampling(server, user, host, label, local_cpu)

                print(f"✓ Completed {file_base}")

# ---------------------------
# Analysis runner
# ---------------------------
def run_all_analyses(central_out: Path, data_dir: Path):
    os.environ["CENTRALIZED_OUTPUT_DIR"] = str(central_out)
    script_dir = Path(__file__).parent / "scripts"
    scripts = [
        script_dir / "analyze_throughput.py",
        script_dir / "analyze_packet_count.py",
        script_dir / "analyze_loss_rate.py",
        script_dir / "analyze_ping_latency.py",
        script_dir / "analyze_cpu_utilization.py",
    ]
    for script in scripts:
        if script.exists():
            print(f"Running {script.name}...")
            try:
                subprocess.run([sys.executable, str(script), str(data_dir)], check=True)
                print(f"✓ {script.name} OK")
            except subprocess.CalledProcessError as e:
                print(f"✗ {script.name} failed: {e}")
        else:
            print(f"✗ Script not found: {script}")

# ---------------------------
# CLI
# ---------------------------
def main():
    parser = argparse.ArgumentParser(description="Python E2E Orchestrator")
    parser.add_argument("--collect", action="store_true", help="Run data collection before analysis")
    parser.add_argument("--mode", choices=["Monolithic", "NFAPI"], default=os.environ.get("CURRENT_MODE", "Monolithic"))
    parser.add_argument("--single-machine", action="store_true", help="NFAPI on single machine")
    parser.add_argument("--out", type=str, default="", help="Centralized output directory for analyses")
    parser.add_argument("--data", type=str, default="", help="Use existing data directory (skip auto-naming)")
    parser.add_argument("--ue-ip", type=str, default="", help="Manually supply UE IP (skip auto-detect)")
    # Optional overrides for ranges
    parser.add_argument("--dl", type=str, default="", help="DL range like start:end:step (e.g., 100:500:100)")
    parser.add_argument("--ul", type=str, default="", help="UL range like start:end:step")
    parser.add_argument("--duration", type=int, default=int(os.environ.get("TEST_DURATION", "15")))
    args = parser.parse_args()

    server = ServerConfig()
    tm = TestMatrix(duration=args.duration)
    mode_cfg = ModeConfig(mode=args.mode, single_machine=args.single_machine)

    # Range overrides
    if args.dl:
        s, e, st = [int(x) for x in args.dl.split(":")]
        tm.dl_start, tm.dl_end, tm.dl_step = s, e, st
    if args.ul:
        s, e, st = [int(x) for x in args.ul.split(":")]
        tm.enable_ul = True
        tm.ul_start, tm.ul_end, tm.ul_step = s, e, st

    # Data directory
    if args.data:
        data_dir = Path(args.data)
    else:
        data_dir = Path("./data") / build_dir_name(mode_cfg, tm)
    data_dir.mkdir(parents=True, exist_ok=True)

    # Optional centralized analysis output directory
    if args.out:
        central_out = Path(args.out)
    else:
        central_out = Path("./Analysis") / f"analysis-{data_dir.name}"
    central_out.mkdir(parents=True, exist_ok=True)

    if args.collect:
        run_collection(server, mode_cfg, tm, data_dir, ue_ip_override=args.ue_ip or None)

    print(f"Analyzing data from: {data_dir}")
    run_all_analyses(central_out, data_dir)
    print(f"✅ All analyses saved in: {central_out}")

if __name__ == "__main__":
    main()
