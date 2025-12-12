import time

from utils.constants import RATE_TIME_SECONDS


def rate_limit():
    """Prevent exceeding API rate limits (15 RPM)"""
    time.sleep(RATE_TIME_SECONDS)
