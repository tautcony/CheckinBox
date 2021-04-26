import logging
import os
import sys

log_level = os.environ.get("LOG_LEVEL")

# init logger
app_logger = logging.getLogger()
fmt = "%(asctime)s %(levelname)-8s %(message)s"
log_formatter = logging.Formatter(fmt)
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setFormatter(log_formatter)
app_logger.addHandler(console_handler)
if log_level:
    app_logger.setLevel(log_level)
else:
    app_logger.setLevel(logging.INFO)
