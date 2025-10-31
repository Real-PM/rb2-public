#!/usr/bin/env python3
"""Analyze profiling results and identify bottlenecks.

This script reads profiling results JSON and generates:
1. Performance comparison across routes
2. Identification of slowest operations
3. Recommendations for optimization

Usage:
    python scripts/analyze_profiling_results.py profiling_results.json
"""
import argparse
import json
from pathlib import Path
from collections import defaultdict


def load_results(filepath):
    """Load profiling results from JSON file."""
    with open(filepath, 'r') as f:
        data = json.load(f)
    return data


def analyze_results(data):
    """Analyze profiling results and identify bottlenecks."""
    results = data['results']

    # Group by route
    routes = defaultdict(list)
    for result in results:
        routes[result['route']].append(result)

    print("=" * 80)
    print("PERFORMANCE ANALYSIS")
    print("=" * 80)
    print(f"Timestamp: {data.get('timestamp', 'Unknown')}")
    print(f"Total tests: {len(results)}")
    print(f"Routes tested: {len(routes)}")

    # Calculate statistics for each route
    route_stats = {}
    for route_name, route_results in routes.items():
        successful = [r for r in route_results if r['success']]
        if not successful:
            continue

        durations = [r['duration_ms'] for r in successful]
        route_stats[route_name] = {
            'count': len(successful),
            'avg': sum(durations) / len(durations),
            'min': min(durations),
            'max': max(durations),
            'first': durations[0] if durations else 0,  # Cold load
            'subsequent_avg': sum(durations[1:]) / len(durations[1:]) if len(durations) > 1 else 0  # Warm loads
        }

    # Sort by average duration (slowest first)
    sorted_routes = sorted(route_stats.items(), key=lambda x: x[1]['avg'], reverse=True)

    print("\n" + "=" * 80)
    print("ROUTE PERFORMANCE RANKING (Slowest to Fastest)")
    print("=" * 80)
    print(f"{'Route':<30} {'Cold Load':<12} {'Warm Avg':<12} {'Overall Avg':<12} {'Status'}")
    print("-" * 80)

    for route_name, stats in sorted_routes:
        cold_load = f"{stats['first']:.2f}ms"
        warm_avg = f"{stats['subsequent_avg']:.2f}ms" if stats['subsequent_avg'] > 0 else "N/A"
        overall_avg = f"{stats['avg']:.2f}ms"

        # Determine status based on performance
        if stats['avg'] < 100:
            status = "✓ Excellent"
        elif stats['avg'] < 500:
            status = "○ Good"
        elif stats['avg'] < 2000:
            status = "△ Acceptable"
        elif stats['avg'] < 5000:
            status = "⚠ Slow"
        else:
            status = "✗ CRITICAL"

        print(f"{route_name:<30} {cold_load:<12} {warm_avg:<12} {overall_avg:<12} {status}")

    # Identify routes needing optimization
    print("\n" + "=" * 80)
    print("OPTIMIZATION PRIORITIES")
    print("=" * 80)

    critical_routes = [(name, stats) for name, stats in sorted_routes if stats['avg'] >= 5000]
    slow_routes = [(name, stats) for name, stats in sorted_routes if 2000 <= stats['avg'] < 5000]
    acceptable_routes = [(name, stats) for name, stats in sorted_routes if 500 <= stats['avg'] < 2000]

    if critical_routes:
        print("\n🔴 CRITICAL (>5s average):")
        for route_name, stats in critical_routes:
            print(f"   • {route_name}: {stats['avg']:.2f}ms avg")
            print(f"     - Cold load: {stats['first']:.2f}ms")
            if stats['subsequent_avg'] > 0:
                improvement = ((stats['first'] - stats['subsequent_avg']) / stats['first'] * 100)
                print(f"     - Warm loads: {stats['subsequent_avg']:.2f}ms ({improvement:.1f}% faster)")
                if improvement < 10:
                    print(f"     ⚠ WARNING: Cache not effective! Only {improvement:.1f}% improvement")

    if slow_routes:
        print("\n🟡 SLOW (2-5s average):")
        for route_name, stats in slow_routes:
            print(f"   • {route_name}: {stats['avg']:.2f}ms avg")

    if acceptable_routes:
        print("\n🟢 ACCEPTABLE BUT IMPROVABLE (0.5-2s average):")
        for route_name, stats in acceptable_routes:
            print(f"   • {route_name}: {stats['avg']:.2f}ms avg")

    fast_routes = [(name, stats) for name, stats in sorted_routes if stats['avg'] < 500]
    if fast_routes:
        print(f"\n✅ PERFORMANT (<500ms average): {len(fast_routes)} routes")

    # Cache effectiveness analysis
    print("\n" + "=" * 80)
    print("CACHE EFFECTIVENESS ANALYSIS")
    print("=" * 80)
    print(f"{'Route':<30} {'Cold→Warm Improvement':<25} {'Effectiveness'}")
    print("-" * 80)

    for route_name, stats in sorted_routes:
        if stats['subsequent_avg'] > 0:
            improvement = ((stats['first'] - stats['subsequent_avg']) / stats['first'] * 100)
            improvement_str = f"{stats['first']:.0f}ms → {stats['subsequent_avg']:.0f}ms ({improvement:.1f}%)"

            if improvement >= 90:
                effectiveness = "✓ Excellent"
            elif improvement >= 50:
                effectiveness = "○ Good"
            elif improvement >= 10:
                effectiveness = "△ Marginal"
            else:
                effectiveness = "✗ Poor/Broken"

            print(f"{route_name:<30} {improvement_str:<25} {effectiveness}")

    # Recommendations
    print("\n" + "=" * 80)
    print("OPTIMIZATION RECOMMENDATIONS")
    print("=" * 80)

    if critical_routes:
        print("\n1. IMMEDIATE ACTION REQUIRED:")
        for route_name, stats in critical_routes:
            print(f"\n   {route_name}:")
            print(f"   • Current: {stats['avg']:.0f}ms average ({stats['first']:.0f}ms cold)")

            # Check if caching helps
            if stats['subsequent_avg'] > 0:
                improvement = ((stats['first'] - stats['subsequent_avg']) / stats['first'] * 100)
                if improvement < 10:
                    print(f"   • Problem: Cache not effective ({improvement:.1f}% improvement)")
                    print(f"   • Action: Profile to find non-cacheable bottleneck")
                    print(f"   • Likely cause: Database queries, template rendering, or Python processing")
                else:
                    print(f"   • Good news: Cache works ({improvement:.1f}% improvement)")
                    print(f"   • Action: Focus on optimizing cold load")
            else:
                print(f"   • Action: Test cache hit scenario")

            print(f"   • Next steps:")
            print(f"     1. Review profiling logs for this route")
            print(f"     2. Identify which operation takes >80% of time")
            print(f"     3. Target that specific bottleneck")

    if slow_routes and not critical_routes:
        print("\n1. OPTIMIZATION RECOMMENDED:")
        for route_name, stats in slow_routes:
            print(f"   • {route_name}: Target <2s ({stats['avg']:.0f}ms current)")

    print("\n2. GENERAL RECOMMENDATIONS:")
    print("   • Run cProfile on slow routes to identify Python bottlenecks")
    print("   • Check SQLAlchemy logs for slow queries (>100ms)")
    print("   • Review template rendering time")
    print("   • Consider async loading for secondary data")
    print("   • Ensure indexes exist on frequently queried columns")

    return route_stats


def compare_results(file1, file2):
    """Compare two profiling result files."""
    data1 = load_results(file1)
    data2 = load_results(file2)

    print("=" * 80)
    print("PERFORMANCE COMPARISON")
    print("=" * 80)
    print(f"Baseline:  {data1.get('timestamp', 'Unknown')}")
    print(f"Current:   {data2.get('timestamp', 'Unknown')}")

    # Build route stats for both
    def get_route_stats(data):
        routes = defaultdict(list)
        for result in data['results']:
            if result['success']:
                routes[result['route']].append(result['duration_ms'])
        return {name: sum(durations) / len(durations) for name, durations in routes.items()}

    stats1 = get_route_stats(data1)
    stats2 = get_route_stats(data2)

    all_routes = set(stats1.keys()) | set(stats2.keys())

    print(f"\n{'Route':<30} {'Baseline':<12} {'Current':<12} {'Change':<15} {'Status'}")
    print("-" * 80)

    for route in sorted(all_routes):
        baseline = stats1.get(route, 0)
        current = stats2.get(route, 0)

        if baseline > 0 and current > 0:
            change = ((current - baseline) / baseline * 100)
            change_str = f"{change:+.1f}%"

            if change < -10:
                status = "✓ Improved"
            elif change > 10:
                status = "✗ Regressed"
            else:
                status = "○ Stable"

            print(f"{route:<30} {baseline:>10.2f}ms {current:>10.2f}ms {change_str:<15} {status}")
        elif baseline > 0:
            print(f"{route:<30} {baseline:>10.2f}ms {'MISSING':<12} {'N/A':<15} ⚠ Not tested")
        else:
            print(f"{route:<30} {'NEW':<12} {current:>10.2f}ms {'N/A':<15} ○ New route")


def main():
    parser = argparse.ArgumentParser(description='Analyze profiling results')
    parser.add_argument('results_file', help='Profiling results JSON file')
    parser.add_argument('--compare', help='Compare with another results file (baseline)')
    parser.add_argument('--threshold', type=int, default=2000,
                       help='Threshold for slow routes in ms (default: 2000)')

    args = parser.parse_args()

    results_path = Path(args.results_file)
    if not results_path.exists():
        print(f"Error: File not found: {args.results_file}")
        return 1

    if args.compare:
        compare_path = Path(args.compare)
        if not compare_path.exists():
            print(f"Error: Comparison file not found: {args.compare}")
            return 1
        compare_results(args.compare, args.results_file)
    else:
        data = load_results(results_path)
        analyze_results(data)

    return 0


if __name__ == '__main__':
    exit(main())
