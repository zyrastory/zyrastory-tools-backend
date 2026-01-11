import logging
import os
from logging.handlers import TimedRotatingFileHandler

LOG_DIR = "logs"
LOG_FILE = os.path.join(LOG_DIR, "app.log")

def setup_logger():
    # 確保日誌目錄存在
    os.makedirs(LOG_DIR, exist_ok=True)

    logger = logging.getLogger("zyrastory")
    logger.setLevel(logging.INFO)

    # 防止重複添加 handler
    if not logger.handlers:
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )

        # 1. Console Handler (Docker logs)
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

        # 2. File Handler (實體日誌)
        # 'when="D"' 表示按天滾動，'interval=1' 表示每天滾動一次，'backupCount=7' 保留 7 天
        file_handler = TimedRotatingFileHandler(
            LOG_FILE, when="D", interval=1, backupCount=7, encoding="utf-8"
        )
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger

# 預先建立一個實例供其他模組使用
logger = setup_logger()
