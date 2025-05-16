#!/bin/bash

# Check if prefix is provided
if [ $# -eq 0 ]; then
    echo "Usage: $0 <prefix>"
    echo "Example: $0 '[Socket] '"
    exit 1
fi

PREFIX="$1"
DIR="/home/ming/E2E-network-measurement/Measure/result"

# List of files to rename
FILES=(
    "nfapi-VNF_vs_nfapi-PNF_box_plot.png"
    "nfapi-VNF_vs_nfapi-PNF_filtered_plot.png"
    "nfapi-VNF_vs_nfapi-PNF_plot.png"
    "nfapi-VNF_vs_nfapi-PNF_report.txt"
)

# Rename files
for file in "${FILES[@]}"; do
    if [ -f "$DIR/$file" ]; then
        mv "$DIR/$file" "$DIR/$PREFIX$file"
        echo "Renamed: $file → $PREFIX$file"
    else
        echo "Warning: $file not found"
    fi
done

echo "Renaming complete!"
