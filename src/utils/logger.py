import logging
import os
import sys
from logging.handlers import RotatingFileHandler

# Tạo thư mục logs
if not os.path.exists("logs"):
    os.makedirs("logs")

# --- CẤU HÌNH FORMAT ---
# Thay vì %(name)s, ta dùng %(filename)s:%(lineno)d
# Để biết chính xác log đến từ file nào, dòng bao nhiêu
LOG_FORMAT = "%(asctime)s | %(levelname)-8s | %(filename)s:%(lineno)d | %(message)s"
DATE_FORMAT = "%H:%M:%S"


class ColoredFormatter(logging.Formatter):
    """Class tô màu log"""

    GREY = "\x1b[38;20m"
    GREEN = "\x1b[32;20m"
    YELLOW = "\x1b[33;20m"
    RED = "\x1b[31;20m"
    BOLD_RED = "\x1b[31;1m"
    RESET = "\x1b[0m"

    FORMATS = {
        logging.DEBUG: GREY + LOG_FORMAT + RESET,
        logging.INFO: GREEN + LOG_FORMAT + RESET,
        logging.WARNING: YELLOW + LOG_FORMAT + RESET,
        logging.ERROR: RED + LOG_FORMAT + RESET,
        logging.CRITICAL: BOLD_RED + LOG_FORMAT + RESET,
    }

    def format(self, record):
        log_fmt = self.FORMATS.get(record.levelno)
        formatter = logging.Formatter(log_fmt, DATE_FORMAT)
        return formatter.format(record)


def _initialize_logger():
    """Hàm nội bộ để khởi tạo logger duy nhất"""
    logger = logging.getLogger("OMNI_APP")  # Tên chung cho toàn app
    logger.setLevel(logging.DEBUG)

    if logger.hasHandlers():
        return logger

    # 1. File Handler
    file_handler = RotatingFileHandler(
        "logs/app.log", maxBytes=5 * 1024 * 1024, backupCount=3, encoding="utf-8"
    )
    file_handler.setFormatter(logging.Formatter(LOG_FORMAT, DATE_FORMAT))
    file_handler.setLevel(logging.DEBUG)

    # 2. Console Handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(ColoredFormatter())
    console_handler.setLevel(logging.INFO)

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger


# --- KHỞI TẠO SẴN Ở ĐÂY ---
# Các file khác chỉ cần import biến 'logger' này là dùng được ngay
logger = _initialize_logger()
