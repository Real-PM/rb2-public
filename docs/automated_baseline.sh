#!/bin/bash
# Automated baseline measurement collection
# This script will be run manually to collect all 63 measurements (9 pages × 7 runs)

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CSV_FILE="$SCRIPT_DIR/performance_baseline.csv"

# Declare test pages
declare -a PAGES=(
    "Front|http://localhost:5000/"
    "Player_Main|http://localhost:5000/players/"
    "Player_Letter|http://localhost:5000/players/letter/R"
    "Player_Detail|http://localhost:5000/players/15"
    "Coach_Main|http://localhost:5000/coaches/"
    "Coach_Detail|http://localhost:5000/coaches/1"
    "Team_Main|http://localhost:5000/teams/"
    "Team_Detail|http://localhost:5000/teams/1"
    "Team_Year|http://localhost:5000/teams/1/1997"
)

RUNS=7

echo "=========================================="
echo "BASELINE MEASUREMENT COLLECTION"
echo "=========================================="
echo "Pages to test: ${#PAGES[@]}"
echo "Runs per page: $RUNS"
echo "Total measurements: $((${#PAGES[@]} * $RUNS))"
echo "Output: $CSV_FILE"
echo "=========================================="
echo ""

# For each page
for page_info in "${PAGES[@]}"; do
    IFS='|' read -r page_type url <<< "$page_info"

    echo "Testing: $page_type"
    echo "URL: $url"

    # Collect statistics for this page
    declare -a times=()

    # Run 7 measurements
    for run in $(seq 1 $RUNS); do
        # Use curl to measure (simpler than Puppeteer for scripting)
        start=$(date +%s%3N)
        response=$(curl -s -o /dev/null -w "%{http_code}|%{time_total}" "$url")
        end=$(date +%s%3N)

        http_code=$(echo "$response" | cut -d'|' -f1)
        time_total=$(echo "$response" | cut -d'|' -f2)

        # Convert to milliseconds
        load_time_ms=$(echo "$time_total * 1000" | bc)
        load_time_ms=${load_time_ms%.*}

        times+=($load_time_ms)

        # Record to CSV
        timestamp=$(date -Iseconds)
        echo "$timestamp,$page_type,$url,$run,$load_time_ms" >> "$CSV_FILE"

        echo "  Run $run: ${load_time_ms}ms (HTTP $http_code)"

        # Small delay between runs
        sleep 0.5
    done

    # Calculate stats
    sum=0
    min=${times[0]}
    max=${times[0]}

    for time in "${times[@]}"; do
        sum=$((sum + time))
        if [ "$time" -lt "$min" ]; then min=$time; fi
        if [ "$time" -gt "$max" ]; then max=$time; fi
    done

    avg=$((sum / ${#times[@]}))

    echo "  Stats: Avg=${avg}ms, Min=${min}ms, Max=${max}ms"
    echo ""
done

echo "=========================================="
echo "MEASUREMENT COMPLETE"
echo "Results saved to: $CSV_FILE"
echo "=========================================="
