import logging

logger = logging.getLogger("process_monitor")
logger.setLevel(logging.INFO)

formatter = logging.Formatter("[%(asctime)s] %(levelname)s: %(message)s")

console_handler = logging.StreamHandler()
console_handler.setFormatter(formatter)

# Prevent duplicate handlers
if not logger.hasHandlers():
    logger.addHandler(console_handler)
