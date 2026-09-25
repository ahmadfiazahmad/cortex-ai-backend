import time
from collections.abc import Callable


def with_retry(
    function: Callable,
    max_retries: int = 3,
    base_delay_seconds: float = 0.5,
):
    last_error = None

    for attempt in range(max_retries + 1):
        try:
            return function()
        except Exception as exc:
            last_error = exc
            if attempt == max_retries:
                break

            delay = base_delay_seconds * (2**attempt)
            print(
                f"Retry attempt {attempt + 1}/{max_retries} failed: {exc}. "
                f"Retrying in {delay:.1f}s..."
            )
            time.sleep(delay)

    raise last_error
