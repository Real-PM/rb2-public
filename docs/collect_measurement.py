#!/usr/bin/env python3
"""
Helper script to append a single measurement to the CSV.
Usage: python collect_measurement.py <page_type> <url> <run> <load_time_ms>
"""

import csv
import sys
from datetime import datetime
from pathlib import Path

if len(sys.argv) != 5:
    print("Usage: python collect_measurement.py <page_type> <url> <run> <load_time_ms>")
    sys.exit(1)

page_type = sys.argv[1]
url = sys.argv[2]
run = sys.argv[3]
load_time_ms = sys.argv[4]

csv_file = Path(__file__).parent / 'performance_baseline.csv'

with open(csv_file, 'a', newline='') as f:
    writer = csv.writer(f)
    writer.writerow([
        datetime.now().isoformat(),
        page_type,
        url,
        run,
        load_time_ms
    ])

print(f"✓ Recorded: {page_type} Run {run} = {load_time_ms}ms")
