import os
import glob
import json

DATA_DIR = "/home/ming/E2E-network-measurement/data/20250418"

def is_error_block(obj):
    return (
        isinstance(obj, dict)
        and obj.get("error") == "interrupt - the server has terminated"
        and obj.get("intervals", []) == []
    )

def clean_json_file(filepath):
    with open(filepath, "r") as f:
        content = f.read().strip()
    # 嘗試處理多個 JSON 物件的情況
    json_objs = []
    decoder = json.JSONDecoder()
    idx = 0
    while idx < len(content):
        content = content.lstrip()
        try:
            obj, end = decoder.raw_decode(content)
            json_objs.append(obj)
            content = content[end:]
            idx = 0
        except json.JSONDecodeError:
            break
    # 過濾掉 error block
    cleaned_objs = [obj for obj in json_objs if not is_error_block(obj)]
    # 只保留第一個合法物件（通常只需要一個）
    if cleaned_objs:
        with open(filepath, "w") as f:
            json.dump(cleaned_objs[0], f, indent=4)
        print(f"Cleaned: {filepath}")
    else:
        print(f"Warning: No valid JSON object found in {filepath}")

def main():
    files = glob.glob(os.path.join(DATA_DIR, "*.json"))
    for filepath in files:
        clean_json_file(filepath)

if __name__ == "__main__":
    main()
