#!/usr/bin/env python3
"""
Collect all baseline performance measurements using real browser timing.

This script uses Selenium WebDriver to measure actual page load times
in a real browser environment.

Requirements:
    pip install selenium webdriver-manager

Usage:
    python3 collect_all_baselines.py
"""

import csv
import time
from datetime import datetime
from pathlib import Path

try:
    from selenium import webdriver
    from selenium.webdriver.chrome.service import Service
    from selenium.webdriver.chrome.options import Options
    from webdriver_manager.chrome import ChromeDriverManager
except ImportError:
    print("ERROR: Required packages not installed")
    print("Please run: pip install selenium webdriver-manager")
    exit(1)

# Test pages configuration
TEST_PAGES = [
    ("Front", "http://localhost:5000/"),
    ("Player_Main", "http://localhost:5000/players/"),
    ("Player_Letter", "http://localhost:5000/players/letter/R"),
    ("Player_Detail", "http://localhost:5000/players/15"),
    ("Coach_Main", "http://localhost:5000/coaches/"),
    ("Coach_Detail", "http://localhost:5000/coaches/1"),
    ("Team_Main", "http://localhost:5000/teams/"),
    ("Team_Detail", "http://localhost:5000/teams/1"),
    ("Team_Year", "http://localhost:5000/teams/1/1997"),
]

RUNS_PER_PAGE = 7
CSV_FILE = Path(__file__).parent / "performance_baseline.csv"

def setup_driver():
    """Setup Chrome WebDriver with appropriate options."""
    chrome_options = Options()
    chrome_options.add_argument("--headless")  # Run in background
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")

    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)
    return driver

def measure_page_load(driver, url):
    """
    Measure page load time using Navigation Timing API.

    Returns:
        int: Load time in milliseconds
    """
    driver.get(url)

    # Wait for page to fully load
    time.sleep(0.5)

    # Get load time from Navigation Timing API
    load_time = driver.execute_script(
        "return performance.timing.loadEventEnd - performance.timing.navigationStart;"
    )

    return load_time

def main():
    print("=" * 80)
    print("BASELINE PERFORMANCE MEASUREMENT COLLECTION")
    print("=" * 80)
    print(f"Pages to test: {len(TEST_PAGES)}")
    print(f"Runs per page: {RUNS_PER_PAGE}")
    print(f"Total measurements: {len(TEST_PAGES) * RUNS_PER_PAGE}")
    print(f"Output file: {CSV_FILE}")
    print("=" * 80)
    print()

    # Check if CSV exists, if not create it
    if not CSV_FILE.exists():
        with open(CSV_FILE, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['timestamp', 'page_type', 'url', 'run', 'load_time_ms'])
        print("✓ Created new CSV file")

    # Read existing measurements
    existing = set()
    with open(CSV_FILE, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row['load_time_ms'] and row['load_time_ms'] != 'PLACEHOLDER':
                key = (row['page_type'], row['run'])
                existing.add(key)

    print(f"✓ Found {len(existing)} existing valid measurements\n")

    # Setup browser
    print("Setting up Chrome WebDriver...")
    driver = setup_driver()
    print("✓ Browser ready\n")

    try:
        results = []
        total_collected = 0

        for page_type, url in TEST_PAGES:
            print(f"Testing: {page_type}")
            print(f"URL: {url}")

            page_times = []

            for run in range(1, RUNS_PER_PAGE + 1):
                key = (page_type, str(run))

                # Skip if already collected
                if key in existing:
                    print(f"  Run {run}: Already collected ✓")
                    continue

                # Measure page load
                try:
                    load_time = measure_page_load(driver, url)

                    if load_time > 0:
                        page_times.append(load_time)
                        print(f"  Run {run}: {load_time}ms")

                        # Record to CSV immediately
                        with open(CSV_FILE, 'a', newline='') as f:
                            writer = csv.writer(f)
                            writer.writerow([
                                datetime.now().isoformat(),
                                page_type,
                                url,
                                run,
                                load_time
                            ])

                        total_collected += 1
                    else:
                        print(f"  Run {run}: ERROR (invalid timing)")

                except Exception as e:
                    print(f"  Run {run}: ERROR ({str(e)})")

                # Small delay between runs
                time.sleep(0.3)

            # Show statistics for this page
            if page_times:
                avg = sum(page_times) / len(page_times)
                min_time = min(page_times)
                max_time = max(page_times)
                print(f"  Stats: Avg={avg:.0f}ms, Min={min_time}ms, Max={max_time}ms")

            print()

    finally:
        driver.quit()
        print("✓ Browser closed")

    print("=" * 80)
    print(f"COLLECTION COMPLETE")
    print(f"New measurements collected: {total_collected}")
    print(f"Results saved to: {CSV_FILE}")
    print("=" * 80)

if __name__ == "__main__":
    main()
