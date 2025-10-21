#!/usr/bin/env python3
"""
Script to coordinate baseline measurements.
This will output commands that Claude Code can execute via MCP.
"""

import json

# Test configuration
TEST_PAGES = [
    ("Front", "http://localhost:5000/", "Home page with standings"),
    ("Player Main", "http://localhost:5000/players/", "Player list page"),
    ("Player Letter", "http://localhost:5000/players/letter/R", "Players with last name R"),
    ("Player Detail", "http://localhost:5000/players/15", "Ricardo Reyes detail page"),
    ("Coach Main", "http://localhost:5000/coaches/", "Coach list page"),
    ("Coach Detail", "http://localhost:5000/coaches/1", "Jesse Touchstone detail page"),
    ("Team Main", "http://localhost:5000/teams/", "Team list page"),
    ("Team Detail", "http://localhost:5000/teams/1", "Cleveland team detail page"),
    ("Team Year", "http://localhost:5000/teams/1/1997", "Cleveland 1997 season page"),
]

RUNS_PER_PAGE = 7

# Generate measurement plan
measurements = []
for page_type, url, desc in TEST_PAGES:
    for run in range(1, RUNS_PER_PAGE + 1):
        measurements.append({
            "page_type": page_type,
            "url": url,
            "description": desc,
            "run": run
        })

print(json.dumps(measurements, indent=2))
print(f"\nTotal measurements to collect: {len(measurements)}")
