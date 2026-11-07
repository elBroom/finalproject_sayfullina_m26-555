class InsufficientFundsError(Exception):
    """Ошибка недостатка средств для операции вывода или продажи."""
    def __init__(self, code, required, available):
        super().__init__(code)
        self.code = code
        self.required = required
        self.available = available

    def __str__(self):
        return (f"Недостаточно средств: доступно {self.available} {self.code},"
                f" требуется {self.required} {self.code}")

class CurrencyNotFoundError(Exception):
    """Ошибка: запрошенная валюта не найдена в базе данных."""

    def __init__(self, code):
        super().__init__(code)
        self.code = code

    def __str__(self):
        return f"Неизвестная валюта: {self.code}"

class ApiRequestError(Exception):
    """Базовое исключение для ошибок API."""
    def __init__(self, reason):
        super().__init__(reason)
        self.reason = reason

    def __str__(self):
        return f"Ошибка при обращении к внешнему API: {self.reason}"
