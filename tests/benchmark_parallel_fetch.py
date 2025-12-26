#!/usr/bin/env python3
"""
Benchmark script to demonstrate parallel fetching performance improvement

This script compares sequential vs parallel provider fetching.
"""

import time
from freerouter.core.fetcher import FreeRouterFetcher
from freerouter.providers.base import BaseProvider


class MockSlowProvider(BaseProvider):
    """Mock provider that simulates slow API calls"""
    
    def __init__(self, name: str, delay: float = 0.5, num_models: int = 10):
        super().__init__()
        self._name = name
        self._delay = delay
        self._num_models = num_models
    
    @property
    def provider_name(self) -> str:
        return self._name
    
    def fetch_models(self):
        """Simulate slow API call"""
        time.sleep(self._delay)
        return [{"id": f"{self._name}-model-{i}"} for i in range(self._num_models)]


def benchmark_parallel_fetch():
    """Benchmark parallel fetching"""
    print("=" * 60)
    print("FreeRouter - Parallel Fetching Benchmark")
    print("=" * 60)
    
    # Create fetcher with 5 providers, each taking 0.5s
    num_providers = 5
    delay_per_provider = 0.5
    
    fetcher = FreeRouterFetcher()
    
    print(f"\nSetup:")
    print(f"  Providers: {num_providers}")
    print(f"  Delay per provider: {delay_per_provider}s")
    print(f"  Expected sequential time: {num_providers * delay_per_provider}s")
    print(f"  Expected parallel time: ~{delay_per_provider}s")
    
    for i in range(num_providers):
        provider = MockSlowProvider(f"provider-{i}", delay=delay_per_provider)
        fetcher.add_provider(provider)
    
    # Benchmark
    print("\nFetching models...")
    start_time = time.time()
    services = fetcher.fetch_all()
    elapsed_time = time.time() - start_time
    
    # Results
    print("\n" + "=" * 60)
    print("Results:")
    print("=" * 60)
    print(f"  Total services fetched: {len(services)}")
    print(f"  Time elapsed: {elapsed_time:.2f}s")
    
    # Calculate speedup
    sequential_time = num_providers * delay_per_provider
    speedup = sequential_time / elapsed_time
    
    print(f"\n  Sequential time (estimated): {sequential_time:.2f}s")
    print(f"  Parallel time (actual): {elapsed_time:.2f}s")
    print(f"  Speedup: {speedup:.2f}x")
    
    if speedup > 3.0:
        print("\n  ✓ Excellent! Parallel fetching is working efficiently")
    elif speedup > 2.0:
        print("\n  ✓ Good! Parallel fetching provides significant speedup")
    else:
        print("\n  ⚠ Warning: Speedup is lower than expected")
    
    print("=" * 60)


if __name__ == "__main__":
    benchmark_parallel_fetch()
