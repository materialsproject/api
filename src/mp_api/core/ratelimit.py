from ratelimit import sleep_and_retry, limits
from mp_api.core.settings import MAPISettings


@sleep_and_retry
@limits(calls=MAPISettings().requests_per_min, period=60)
def check_limit():
    """
    Empty function for enabling global rate limiting.
    """
    return
