#!/usr/bin/env python3
"""Run profiling tests on all major routes and collect results.

This script:
1. Ensures the Flask app is running with profiling enabled
2. Makes requests to key routes with cache cleared
3. Collects profiling data from application logs
4. Generates a summary report

Usage:
    python scripts/run_profiling_tests.py [--env development|staging]
"""
import argparse
import requests
import time
import subprocess
from pathlib import Path
import json
from datetime import datetime

# Test routes with sample IDs
TEST_ROUTES = [
    {
        'name': 'Home Page',
        'url': '/',
        'cache_clear_pattern': 'home_standings'
    },
    {
        'name': 'Player Detail',
        'url': '/players/1010',  # Sample player ID
        'cache_clear_pattern': 'player_detail:1010'
    },
    {
        'name': 'Player Detail (Different)',
        'url': '/players/3000',  # Different player
        'cache_clear_pattern': 'player_detail:3000'
    },
    {
        'name': 'Player List',
        'url': '/players/',
        'cache_clear_pattern': 'players_list'
    },
    {
        'name': 'Team Detail',
        'url': '/teams/1',  # Sample team ID
        'cache_clear_pattern': None  # Team routes use default caching
    },
    {
        'name': 'Team Year',
        'url': '/teams/1/1945',  # Sample team ID and year (1945 = latest year with data)
        'cache_clear_pattern': None
    },
    {
        'name': 'Teams List',
        'url': '/teams/',
        'cache_clear_pattern': 'teams_list'
    },
]


def clear_redis_cache(env='development'):
    """Clear Redis cache for the environment."""
    redis_db = {'development': 0, 'staging': 1, 'production': 2}.get(env, 0)

    try:
        # Try docker exec first (for staging/production with containerized Redis)
        try:
            subprocess.run(
                ['docker', 'exec', 'redis-rb2', 'redis-cli', '-n', str(redis_db), 'FLUSHDB'],
                capture_output=True,
                check=True
            )
            print(f"✓ Cleared Redis cache via Docker (DB {redis_db})")
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            # Fallback to direct redis-cli (for development)
            redis_host = 'localhost' if env == 'development' else '192.168.10.94'
            subprocess.run(
                ['redis-cli', '-h', redis_host, '-n', str(redis_db), 'FLUSHDB'],
                capture_output=True,
                check=True
            )
            print(f"✓ Cleared Redis cache (DB {redis_db})")
            return True
    except subprocess.CalledProcessError as e:
        print(f"✗ Failed to clear Redis cache: {e}")
        return False
    except FileNotFoundError:
        print(f"⚠ Could not find redis-cli or docker, skipping cache clear")
        print(f"  To manually clear cache: docker exec redis-rb2 redis-cli -n {redis_db} FLUSHDB")
        return False


def make_request(base_url, route_info, iteration=1):
    """Make a request to a route and time the response."""
    url = f"{base_url}{route_info['url']}"

    print(f"\n[{iteration}] Testing: {route_info['name']}")
    print(f"    URL: {url}")

    start_time = time.time()
    try:
        response = requests.get(url, timeout=120)  # 2 minute timeout
        duration = (time.time() - start_time) * 1000  # Convert to ms

        print(f"    Status: {response.status_code}")
        print(f"    Time: {duration:.2f}ms")

        return {
            'route': route_info['name'],
            'url': route_info['url'],
            'status_code': response.status_code,
            'duration_ms': round(duration, 2),
            'iteration': iteration,
            'success': response.status_code == 200
        }
    except requests.exceptions.Timeout:
        duration = (time.time() - start_time) * 1000
        print(f"    Status: TIMEOUT after {duration:.2f}ms")
        return {
            'route': route_info['name'],
            'url': route_info['url'],
            'status_code': 0,
            'duration_ms': round(duration, 2),
            'iteration': iteration,
            'success': False,
            'error': 'timeout'
        }
    except Exception as e:
        duration = (time.time() - start_time) * 1000
        print(f"    Status: ERROR - {e}")
        return {
            'route': route_info['name'],
            'url': route_info['url'],
            'status_code': 0,
            'duration_ms': round(duration, 2),
            'iteration': iteration,
            'success': False,
            'error': str(e)
        }


def run_profiling_tests(base_url, env='development', iterations=3, clear_cache=True):
    """Run profiling tests on all routes."""
    print("=" * 80)
    print("PROFILING TEST RUN")
    print("=" * 80)
    print(f"Environment: {env}")
    print(f"Base URL: {base_url}")
    print(f"Iterations: {iterations}")
    print(f"Clear cache: {clear_cache}")
    print(f"Timestamp: {datetime.now().isoformat()}")

    all_results = []

    for iteration in range(1, iterations + 1):
        print(f"\n{'=' * 80}")
        print(f"ITERATION {iteration}/{iterations}")
        print(f"{'=' * 80}")

        if clear_cache and iteration == 1:
            # Only clear cache on first iteration to test cold vs warm loads
            clear_redis_cache(env)
            time.sleep(1)  # Give Redis a moment

        for route_info in TEST_ROUTES:
            result = make_request(base_url, route_info, iteration)
            all_results.append(result)

            # Small delay between requests
            time.sleep(0.5)

    return all_results


def generate_report(results, output_file=None):
    """Generate a summary report from profiling results."""
    print("\n" + "=" * 80)
    print("PROFILING RESULTS SUMMARY")
    print("=" * 80)

    # Group results by route
    routes = {}
    for result in results:
        route_name = result['route']
        if route_name not in routes:
            routes[route_name] = []
        routes[route_name].append(result)

    # Print summary for each route
    print(f"\n{'Route':<30} {'Iteration':<12} {'Time (ms)':<15} {'Status'}")
    print("-" * 80)

    for route_name in sorted(routes.keys()):
        route_results = routes[route_name]
        for result in route_results:
            iteration = f"#{result['iteration']}"
            duration = f"{result['duration_ms']:.2f}ms"
            status = "✓" if result['success'] else "✗"
            if 'error' in result:
                status += f" ({result['error']})"

            print(f"{route_name:<30} {iteration:<12} {duration:<15} {status}")

        # Calculate statistics
        durations = [r['duration_ms'] for r in route_results if r['success']]
        if durations:
            avg = sum(durations) / len(durations)
            min_time = min(durations)
            max_time = max(durations)
            print(f"  → Stats: avg={avg:.2f}ms, min={min_time:.2f}ms, max={max_time:.2f}ms")
        print()

    # Save detailed results to file
    if output_file:
        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, 'w') as f:
            json.dump({
                'timestamp': datetime.now().isoformat(),
                'results': results
            }, f, indent=2)

        print(f"\n✓ Detailed results saved to: {output_file}")

    return routes


def extract_profiling_logs(env='development', since_minutes=5):
    """Extract profiling logs from application logs.

    For development: Read from Flask's stdout
    For staging: Use journalctl to read from systemd service
    """
    if env == 'staging':
        # Extract from systemd logs
        try:
            cmd = [
                'journalctl',
                '-u', 'rb2-staging.service',
                '--since', f'{since_minutes} minutes ago',
                '--no-pager'
            ]
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            logs = result.stdout

            # Filter for profiling output
            profiling_lines = [line for line in logs.split('\n') if 'PROFILE:' in line or 'Timing Breakdown' in line]

            if profiling_lines:
                print("\n" + "=" * 80)
                print("PROFILING LOGS (from journalctl)")
                print("=" * 80)
                for line in profiling_lines[:50]:  # Limit to 50 lines
                    print(line)
            else:
                print("\n⚠ No profiling logs found in journalctl output")

        except subprocess.CalledProcessError as e:
            print(f"\n✗ Failed to extract logs from journalctl: {e}")
    else:
        print("\n⚠ Log extraction only supported for staging environment")
        print("   For development, check your Flask console output for profiling data")


def main():
    parser = argparse.ArgumentParser(description='Run profiling tests on Flask application')
    parser.add_argument('--env', choices=['development', 'staging'], default='development',
                       help='Environment to test (default: development)')
    parser.add_argument('--url', help='Base URL (auto-detected if not provided)')
    parser.add_argument('--iterations', type=int, default=3,
                       help='Number of iterations per route (default: 3)')
    parser.add_argument('--no-clear-cache', action='store_true',
                       help='Do not clear cache before first test')
    parser.add_argument('--output', help='Output file for detailed results (default: profiling_results.json)')

    args = parser.parse_args()

    # Auto-detect base URL based on environment
    if args.url:
        base_url = args.url
    elif args.env == 'staging':
        base_url = 'http://localhost:5002'
    else:
        base_url = 'http://localhost:5000'

    # Set default output file
    if not args.output:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        args.output = f'profiling_results_{args.env}_{timestamp}.json'

    # Run tests
    results = run_profiling_tests(
        base_url=base_url,
        env=args.env,
        iterations=args.iterations,
        clear_cache=not args.no_clear_cache
    )

    # Generate report
    generate_report(results, args.output)

    # Extract profiling logs (staging only)
    if args.env == 'staging':
        extract_profiling_logs(env=args.env, since_minutes=10)

    print("\n" + "=" * 80)
    print("✓ Profiling test run complete!")
    print("=" * 80)
    print("\nNext steps:")
    print("1. Review the summary above")
    print(f"2. Check detailed results in: {args.output}")
    if args.env == 'staging':
        print("3. Review profiling logs shown above")
        print("4. For full logs: journalctl -u rb2-staging.service -n 200 --no-pager")
    else:
        print("3. Check Flask console output for detailed profiling data")
    print("\nTo analyze results:")
    print(f"  python scripts/analyze_profiling_results.py {args.output}")


if __name__ == '__main__':
    main()
