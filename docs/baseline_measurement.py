#!/usr/bin/env python3
"""
Baseline Performance Measurement Script

Measures page load times for various page types using Puppeteer via MCP.
Results are logged to CSV for comparison after optimization.

Page Types Tested:
- Front: Home page with standings
- Player Main: Player list page
- Player Letter: Player list filtered by letter
- Player Detail: Individual player page
- Coach Main: Coach list page
- Coach Detail: Individual coach page
- Team Main: Team list page
- Team Year: Team season page

Usage:
    python baseline_measurement.py
"""

import csv
import json
import subprocess
import time
from datetime import datetime
from pathlib import Path


# Base URL
BASE_URL = "http://localhost:5000"

# Test URLs with descriptions
TEST_PAGES = [
    {
        "type": "Front",
        "url": f"{BASE_URL}/",
        "description": "Home page with standings"
    },
    {
        "type": "Player Main",
        "url": f"{BASE_URL}/players/",
        "description": "Player list page"
    },
    {
        "type": "Player Letter",
        "url": f"{BASE_URL}/players/letter/R",
        "description": "Players with last name starting with R"
    },
    {
        "type": "Player Detail",
        "url": f"{BASE_URL}/players/15",
        "description": "Ricardo Reyes detail page"
    },
    {
        "type": "Coach Main",
        "url": f"{BASE_URL}/coaches/",
        "description": "Coach list page"
    },
    {
        "type": "Coach Detail",
        "url": f"{BASE_URL}/coaches/1",
        "description": "Jesse Touchstone detail page"
    },
    {
        "type": "Team Main",
        "url": f"{BASE_URL}/teams/",
        "description": "Team list page"
    },
    {
        "type": "Team Detail",
        "url": f"{BASE_URL}/teams/1",
        "description": "Cleveland team detail page"
    },
    {
        "type": "Team Year",
        "url": f"{BASE_URL}/teams/1/1997",
        "description": "Cleveland 1997 season page"
    }
]

# Number of runs per page
RUNS_PER_PAGE = 7

# Output file
OUTPUT_FILE = Path(__file__).parent / "performance_baseline.csv"


def measure_page_load(url):
    """
    Measure page load time using Puppeteer via MCP.

    Returns:
        float: Load time in milliseconds, or None if failed
    """
    start_time = time.time()

    try:
        # Use claude CLI to invoke MCP Puppeteer navigate
        result = subprocess.run(
            ["claude", "mcp", "call", "puppeteer", "puppeteer_navigate",
             json.dumps({"url": url})],
            capture_output=True,
            text=True,
            timeout=30
        )

        end_time = time.time()
        load_time_ms = (end_time - start_time) * 1000

        if result.returncode == 0:
            return load_time_ms
        else:
            print(f"Error navigating to {url}: {result.stderr}")
            return None

    except subprocess.TimeoutExpired:
        print(f"Timeout loading {url}")
        return None
    except Exception as e:
        print(f"Error measuring {url}: {e}")
        return None


def run_measurements():
    """Run all measurements and save to CSV."""

    print("=" * 80)
    print("BASELINE PERFORMANCE MEASUREMENT")
    print("=" * 80)
    print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Runs per page: {RUNS_PER_PAGE}")
    print(f"Total pages: {len(TEST_PAGES)}")
    print(f"Output file: {OUTPUT_FILE}")
    print("=" * 80)
    print()

    results = []

    for page in TEST_PAGES:
        print(f"Testing: {page['type']} - {page['description']}")
        print(f"URL: {page['url']}")

        page_results = []

        for run in range(1, RUNS_PER_PAGE + 1):
            print(f"  Run {run}/{RUNS_PER_PAGE}...", end=" ", flush=True)

            load_time = measure_page_load(page['url'])

            if load_time is not None:
                print(f"{load_time:.1f}ms")
                page_results.append(load_time)

                results.append({
                    "timestamp": datetime.now().isoformat(),
                    "page_type": page['type'],
                    "url": page['url'],
                    "run": run,
                    "load_time_ms": round(load_time, 1)
                })
            else:
                print("FAILED")

            # Small delay between runs
            time.sleep(0.5)

        # Calculate statistics
        if page_results:
            avg = sum(page_results) / len(page_results)
            min_time = min(page_results)
            max_time = max(page_results)
            print(f"  Stats: Avg={avg:.1f}ms, Min={min_time:.1f}ms, Max={max_time:.1f}ms")

        print()

    # Write results to CSV
    if results:
        with open(OUTPUT_FILE, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=[
                'timestamp', 'page_type', 'url', 'run', 'load_time_ms'
            ])
            writer.writeheader()
            writer.writerows(results)

        print("=" * 80)
        print(f"Results saved to: {OUTPUT_FILE}")
        print(f"Total measurements: {len(results)}")
        print("=" * 80)
    else:
        print("No results to save!")


if __name__ == "__main__":
    run_measurements()
