from tenacity import retry, wait_fixed, stop_after_attempt, before_log
import logging

# Configure logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Retry wrapper with logging
def retry_on_failure(wait_seconds=2, max_attempts=5):
    return retry(
        wait=wait_fixed(wait_seconds),
        stop=stop_after_attempt(max_attempts),
        before=before_log(logger, logging.INFO) 
    )