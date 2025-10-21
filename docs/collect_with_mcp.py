#!/usr/bin/env python3
"""
Collect baseline measurements using MCP Puppeteer tools.

This script coordinates with Claude Code's MCP Puppeteer integration
to measure real browser page load times.

Usage:
    This script should be run within the Claude Code environment
    where MCP tools are available.
"""

import json
import sys

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

# Output the measurement plan for Claude to execute
print(json.dumps({
    "pages": TEST_PAGES,
    "runs_per_page": RUNS_PER_PAGE,
    "total_measurements": len(TEST_PAGES) * RUNS_PER_PAGE,
    "instructions": [
        "For each page and run:",
        "1. Call mcp__puppeteer__puppeteer_navigate with the URL",
        "2. Call mcp__puppeteer__puppeteer_evaluate with script: 'performance.timing.loadEventEnd - performance.timing.navigationStart'",
        "3. Record the result to CSV with: timestamp, page_type, url, run, load_time_ms"
    ]
}, indent=2))
