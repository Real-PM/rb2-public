"""Performance profiling utilities for identifying bottlenecks.

This module provides decorators and utilities to measure where time is spent
during page rendering, including:
- Total request time
- Database query time
- Template rendering time
- Python processing time
- Individual service call timing

Usage:
    from app.utils.profiling import profile_route, timing_context

    @bp.route('/example')
    @profile_route('example_route')
    def example():
        with timing_context('fetch_data'):
            data = expensive_operation()
        return render_template('example.html', data=data)
"""
import cProfile
import pstats
import io
import time
import functools
from contextlib import contextmanager
from flask import g, current_app
from typing import Optional, Dict, Any
from loguru import logger


class RouteProfiler:
    """Collects timing data for a single request."""

    def __init__(self, route_name: str):
        self.route_name = route_name
        self.timings: Dict[str, float] = {}
        self.start_time: Optional[float] = None
        self.profiler: Optional[cProfile.Profile] = None

    def start(self):
        """Start profiling the request."""
        self.start_time = time.time()
        self.profiler = cProfile.Profile()
        self.profiler.enable()

    def stop(self) -> Dict[str, Any]:
        """Stop profiling and return results."""
        if self.profiler:
            self.profiler.disable()

        total_time = time.time() - self.start_time if self.start_time else 0

        # Get detailed profiling stats
        s = io.StringIO()
        stats = pstats.Stats(self.profiler, stream=s)
        stats.sort_stats('cumulative')
        stats.print_stats(30)  # Top 30 functions

        # Debug: Log if timings is empty for slow requests
        if total_time > 1.0 and not self.timings:
            logger.warning(f"Profiler for '{self.route_name}' took {total_time*1000:.2f}ms but has NO timings recorded!")

        return {
            'route_name': self.route_name,
            'total_time_ms': round(total_time * 1000, 2),
            'timings': {k: round(v * 1000, 2) for k, v in self.timings.items()},
            'profile_output': s.getvalue()
        }

    def add_timing(self, label: str, duration: float):
        """Add a timing measurement."""
        self.timings[label] = duration
        # Debug: Log successful timing additions for slow operations
        if duration > 0.1:  # Log if >100ms
            logger.debug(f"Timing added to '{self.route_name}': {label} = {duration*1000:.2f}ms")


@contextmanager
def timing_context(label: str):
    """Context manager for timing a block of code.

    Args:
        label: Description of the code block being timed

    Example:
        with timing_context('fetch_players'):
            players = Player.query.all()
    """
    start = time.time()
    try:
        yield
    finally:
        duration = time.time() - start

        # Store timing in Flask's g object if profiler is active
        if hasattr(g, 'profiler') and g.profiler:
            g.profiler.add_timing(label, duration)
        else:
            # Log when profiler is not available (debugging)
            logger.warning(f"Profiler not available for timing_context '{label}' (duration: {duration*1000:.2f}ms)")


def profile_route(route_name: str):
    """Decorator to profile a Flask route.

    Measures:
    - Total request time
    - cProfile detailed stats
    - Individual timing blocks (via timing_context)

    Results are logged at INFO level.

    Args:
        route_name: Name to identify this route in logs

    Example:
        @bp.route('/players/<int:player_id>')
        @profile_route('player_detail')
        def player_detail(player_id):
            ...
    """
    def decorator(f):
        @functools.wraps(f)
        def wrapped(*args, **kwargs):
            # Only profile if explicitly enabled
            if not current_app.config.get('ENABLE_PROFILING', False):
                return f(*args, **kwargs)

            # Create profiler and attach to g
            profiler = RouteProfiler(route_name)
            g.profiler = profiler

            profiler.start()

            try:
                result = f(*args, **kwargs)
                return result
            finally:
                # Get results and log
                results = profiler.stop()
                _log_profile_results(results)

                # Clean up
                if hasattr(g, 'profiler'):
                    delattr(g, 'profiler')

        return wrapped
    return decorator


def _log_profile_results(results: Dict[str, Any]):
    """Log profiling results in a readable format."""
    route = results['route_name']
    total = results['total_time_ms']

    logger.info("=" * 80)
    logger.info(f"PROFILE: {route}")
    logger.info(f"Total Time: {total}ms")
    logger.info("-" * 80)

    # Log individual timings
    if results['timings']:
        logger.info("Timing Breakdown:")
        for label, duration_ms in sorted(results['timings'].items(), key=lambda x: -x[1]):
            percentage = (duration_ms / total * 100) if total > 0 else 0
            logger.info(f"  {label:40s} {duration_ms:8.2f}ms ({percentage:5.1f}%)")
        logger.info("-" * 80)

    # Log detailed profile stats
    logger.info("Top Functions (by cumulative time):")
    # Log each line of cProfile output separately to ensure proper formatting
    for line in results['profile_output'].splitlines():
        logger.info(line)
    logger.info("=" * 80)


def timing_decorator(label: str):
    """Decorator to time a function call.

    Args:
        label: Description of the function being timed

    Example:
        @timing_decorator('get_player_stats')
        def get_player_stats(player_id):
            ...
    """
    def decorator(f):
        @functools.wraps(f)
        def wrapped(*args, **kwargs):
            start = time.time()
            try:
                return f(*args, **kwargs)
            finally:
                duration = time.time() - start

                # Store timing if profiler is active
                if hasattr(g, 'profiler') and g.profiler:
                    g.profiler.add_timing(label, duration)

        return wrapped
    return decorator


def get_template_render_wrapper(original_render):
    """Wrap template rendering to measure time.

    Args:
        original_render: The original render_template function

    Returns:
        Wrapped function that times template rendering
    """
    @functools.wraps(original_render)
    def wrapper(*args, **kwargs):
        with timing_context('template_render'):
            return original_render(*args, **kwargs)

    return wrapper
