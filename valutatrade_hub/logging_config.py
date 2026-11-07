import json
import logging
import os
from datetime import datetime

# Путь к директории логов
from valutatrade_hub.infra.settings import settings

BACKUP_COUNT = settings.get("log_backup_count", 5)
MAX_BYTES = settings.get("log_max_bytes", 1024*1024*5)
LOG_DIR = settings.get("log_path", "logs")
LOG_FILE = os.path.join(LOG_DIR, "actions.log")

# Создаем директорию, если нет
os.makedirs(LOG_DIR, exist_ok=True)


def setup_logging(level=logging.INFO):
    """
    Настройка логирования.
    Использует ротацию файлов (по размеру и времени).
    """
    # Создаем root logger
    logger = logging.getLogger()
    logger.setLevel(level)

    # Очистка старых handlers (если вызывается повторно)
    logger.handlers = []

    # Форматирование
    # Используем JSON формат для структурированных логов,
    # но выводим в консоль в читаемом виде
    class JSONFormatter(logging.Formatter):
        def format(self, record):
            log_data = {
                "timestamp": datetime.fromtimestamp(record.created).isoformat(),
                "level": record.levelname,
                "action": getattr(record, "action", "UNKNOWN"),
                "user": getattr(record, "user", "UNKNOWN"),
                "result": getattr(record, "result", "UNKNOWN"),
            }
            if hasattr(record, "currency"):
                log_data["currency"] = record.currency

            if hasattr(record, "amount"):
                log_data["amount"] = record.amount

            if hasattr(record, "error_message"):
                log_data["error_message"] = record.error_message

            if hasattr(record, "error_type"):
                log_data["error_type"] = record.error_type

            if hasattr(record, "extra"):
                log_data["extra"] = record.extra

            return json.dumps(log_data, ensure_ascii=False)

    # Файловый handler (JSON формат, ротация)
    file_handler = logging.FileHandler(LOG_FILE, encoding='utf-8')
    file_handler.setLevel(level)
    file_handler.setFormatter(JSONFormatter())

    from logging.handlers import RotatingFileHandler
    file_handler = RotatingFileHandler(
        LOG_FILE, maxBytes=MAX_BYTES, backupCount=BACKUP_COUNT)
    file_handler.setFormatter(JSONFormatter())
    logger.addHandler(file_handler)

    return logger


# Инициализация логгера (можно вызвать в main.py или при импорте)
logger = setup_logging()
