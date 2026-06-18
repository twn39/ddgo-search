"""Rate-limiting mechanism for ddgo-search CLI using cross-process locking."""

import json
import os
import random
import tempfile
import time
from typing import Optional


def ensure_rate_limit(proxy: Optional[str] = None) -> None:
    """Enforce rate limits across processes using proxy-specific file-locking."""
    import hashlib

    temp_dir = tempfile.gettempdir()

    # Generate a unique key for the proxy to isolate rate limits per outbound IP
    if proxy:
        proxy_hash = hashlib.md5(proxy.encode("utf-8")).hexdigest()[:12]
        key = f"proxy_{proxy_hash}"
    else:
        key = "local"

    lock_file = os.path.join(temp_dir, f"ddgo_search_rate_{key}.lock")
    rate_file = os.path.join(temp_dir, f"ddgo_search_rate_{key}.json")

    # Generate a random gap between 1.0 and 2.5 seconds
    required_gap = random.uniform(1.0, 2.5)

    lock_fd = None
    try:
        lock_fd = open(lock_file, "w")

        # Try fcntl (Unix/macOS)
        try:
            import fcntl

            fcntl.flock(lock_fd, fcntl.LOCK_EX)
        except (ImportError, AttributeError):
            # Try msvcrt (Windows)
            try:
                import msvcrt

                msvcrt.locking(lock_fd.fileno(), msvcrt.LK_LOCK, 1)
            except (ImportError, AttributeError):
                pass  # Fallback to lock-free sleep

        # Read last request timestamp
        last_time = 0.0
        if os.path.exists(rate_file):
            try:
                with open(rate_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    last_time = data.get("last_time", 0.0)
            except Exception:
                pass

        elapsed = time.time() - last_time
        if elapsed < required_gap:
            sleep_time = required_gap - elapsed
            time.sleep(sleep_time)

        # Update last request time
        try:
            with open(rate_file, "w", encoding="utf-8") as f:
                json.dump({"last_time": time.time()}, f)
            # Make sure it writes to disk immediately
            lock_fd.flush()
            os.fsync(lock_fd.fileno())
        except Exception:
            pass

    except Exception:
        # Fallback lock-free rate limiter in case of permission errors or other failures
        try:
            if os.path.exists(rate_file):
                with open(rate_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    last_time = data.get("last_time", 0.0)
                elapsed = time.time() - last_time
                if elapsed < required_gap:
                    time.sleep(required_gap - elapsed)
            with open(rate_file, "w", encoding="utf-8") as f:
                json.dump({"last_time": time.time()}, f)
        except Exception:
            pass
    finally:
        if lock_fd:
            try:
                lock_fd.close()
            except Exception:
                pass
