import functools
from typing import Any, Callable

# Импортируем логгер из config
from valutatrade_hub.logging_config import logger


def log_action(action_name: str, verbose: bool = False):
    """
    Декоратор для логирования доменных операций.

    :param action_name: Название действия (BUY, SELL, REGISTER, LOGIN).
    :param verbose: Если True, добавляет контекст (было/стало).
    """

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            data = {
                "action": action_name,
                "user": '',
            }

            if 'username' in kwargs:
                data['user'] = kwargs['username']
            elif 'user' in kwargs:
                if hasattr(kwargs['user'], "username"):
                    data['user'] = kwargs['user'].username

            if 'currency' in kwargs:
                data['currency'] = kwargs['currency']
            elif 'currency_code' in kwargs:
                data['currency'] = kwargs['currency_code']

            if 'from_code' in kwargs:
                data['from_code'] = kwargs['from_code']
            if 'to_code' in kwargs:
                data['to_code'] = kwargs['to_code']

            if 'amount' in kwargs:
                data['amount'] = kwargs['amount']

            if 'rate' in kwargs:
                data['rate'] = kwargs['rate']

            if 'base' in kwargs:
                data['base'] = kwargs['base']

            try:
                # Выполняем функцию
                result = func(*args, **kwargs)
                data["result"] = "OK"

                # Логирование успеха
                logger.info("", extra=data)
                return result

            except Exception as e:
                data["result"] = "ERROR"
                data["error_type"] = type(e).__name__,
                data["error_message"] = str(e)
                # Логирование ошибки
                logger.error("", extra=data)

                # Пробрасываем исключение дальше
                raise

        return wrapper

    return decorator
