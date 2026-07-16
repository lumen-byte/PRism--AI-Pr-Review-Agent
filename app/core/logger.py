import json
import logging
import sys


class JSONFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        log_data = {
            "timestamp": self.formatTime(record, self.datefmt or "%Y-%m-%d %H:%M:%S"),
            "logger": record.name,
            "level": record.levelname,
        }

        # If the log message itself is a dictionary, merge it in
        if isinstance(record.msg, dict):
            log_data.update(record.msg)
            if "message" not in record.msg:
                log_data["message"] = str(record.msg)
        else:
            log_data["message"] = record.getMessage()

        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_data)


def setup_logger(name: str = "reviewsense") -> logging.Logger:
    logger = logging.getLogger(name)

    if logger.hasHandlers():
        return logger

    logger.setLevel(logging.INFO)

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(JSONFormatter())

    logger.addHandler(console_handler)
    return logger


logger = setup_logger()


# Root logging configuration to capture uvicorn logs in JSON as well
def configure_root_logging():
    root = logging.getLogger()
    for handler in root.handlers:
        handler.setFormatter(JSONFormatter())
