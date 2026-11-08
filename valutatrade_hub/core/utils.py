import json
import os
from typing import Any, Optional

from valutatrade_hub.infra.settings import settings

USERS_FILE = os.path.join(settings.get("data_dir"), "users.json")
PORTFOLIOS_FILE = os.path.join(settings.get("data_dir"), "portfolios.json")
RATES_FILE = os.path.join(settings.get("data_dir"), "rates.json")


def load_json_file(filepath: str, default=None):
    """
    Загружает JSON-файл по указанному пути.

    Если файл не существует или встречается ошибка чтения/парсинга,
    возвращается значение по умолчанию. Если default не указано,
    возвращается пустой список (для файлов пользователей) или пустой
    словарь (для файлов курсов), в зависимости от контекста вызова.

    Args:
        filepath: Полный путь к JSON-файлу.
        default: Значение для возврата в случае ошибки или отсутствия файла.
                 Если None, возвращается пустой список [].

    Returns:
        Any: Данные, распарсенные из JSON-файла, или значение default.
    """
    if not os.path.exists(filepath):
        return default if default is not None else []
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return default if default is not None else []


def save_json_file(filepath: str, data: Any):
    """
    Сохраняет объект данных в JSON-файл по указанному пути.

    Автоматически создает директорию, если она не существует.
    Данные форматируются с отступами для удобства чтения.

    Args:
        filepath: Полный путь к файлу для сохранения.
        data: Любая Python-структура, поддерживаемая модулем json.
    """
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def get_rate_val(from_currency: str, to_currency: str) -> Optional[float|None]:
    """
    Получает текущий курс конвертации одной валюты
    в другую из локального кэша.
    """
    if from_currency == to_currency:
        return 1.0

    rates = load_json_file(RATES_FILE, {})
    key = f"{from_currency}_{to_currency}"

    if key in rates:
        return rates[key]["rate"]

    # Если нет прямого курса, пытаемся найти обратный
    key = f"{to_currency}_{from_currency}"
    if key in rates:
        return 1.0 / rates[key]["rate"]

    return None
