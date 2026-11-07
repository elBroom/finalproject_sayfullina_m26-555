import re
from abc import ABC, abstractmethod

from valutatrade_hub.core.exceptions import CurrencyNotFoundError


class Currency(ABC):
    """
    Абстрактный базовый класс для всех типов валют.
    Определяет общий интерфейс и валидацию.
    """

    def __init__(self, code: str, name: str):
        self._code = self._validate_code(code)
        self._name = self._validate_name(name)

        # Сохраняем исходные значения для доступа (если нужно)
        self._original_code = code
        self._original_name = name

    @property
    def code(self) -> str:
        return self._code

    @property
    def name(self) -> str:
        return self._name

    @staticmethod
    def _validate_code(code: str) -> str:
        """
        Валидация кода:
        - Верхний регистр
        - Длина 2-5 символов
        - Без пробелов и спецсимволов (только буквы и цифры)
        """
        if not isinstance(code, str):
            raise TypeError("Код валюты должен быть строкой.")

        code_upper = code.upper()

        if len(code_upper) < 2 or len(code_upper) > 5:
            raise ValueError(
                f"Код валюты должен содержать от 2 до 5 символов. "
                f"Получено: {code}")

        if not re.match(r"^[A-Z0-9]+$", code_upper):
            raise ValueError(
                f"Код валюты должен содержать только буквы и цифры (A-Z, 0-9). "
                f"Получено: {code}")

        return code_upper

    @staticmethod
    def _validate_name(name: str) -> str:
        """Валидация имени: не пустая строка."""
        if not isinstance(name, str) or not name.strip():
            raise ValueError("Имя валюты не может быть пустым.")
        return name.strip()

    @abstractmethod
    def get_display_info(self) -> str:
        """
        Возвращает строковое представление для UI/логов.
        Должен быть переопределен в наследниках.
        """
        pass

    def __str__(self) -> str:
        return self.get_display_info()


class FiatCurrency(Currency):
    """
    Класс для фиатных валют ( fiat = законное платежное средство).
    """

    def __init__(self, code: str, name: str, issuing_country: str):
        super().__init__(code, name)
        self._issuing_country = issuing_country

    @property
    def issuing_country(self) -> str:
        return self._issuing_country

    def get_display_info(self) -> str:
        """
        Формат: "[FIAT] USD — US Dollar (Issuing: United States)"
        """
        return (f"[FIAT] {self.code} — {self.name} "
                f"(Issuing: {self._issuing_country})")


class CryptoCurrency(Currency):
    """
    Класс для криптовалют.
    """

    def __init__(self, code: str, name: str, algorithm: str, market_cap: float):
        super().__init__(code, name)
        self._algorithm = algorithm
        self._market_cap = market_cap

    @property
    def algorithm(self) -> str:
        return self._algorithm

    @property
    def market_cap(self) -> float:
        return self._market_cap

    def get_display_info(self) -> str:
        """
        Формат: "[CRYPTO] BTC — Bitcoin (Algo: SHA-256, MCAP: 1.12e12)"
        """
        # Форматируем капитализацию в научной нотации для больших чисел
        mcap_str = f"{self._market_cap:.2e}"
        return (f"[CRYPTO] {self.code} — {self.name} "
                f"(Algo: {self._algorithm}, MCAP: {mcap_str})")


_currencies_registry = {
    "USD": FiatCurrency(
        name="US Dollar", code="USD", issuing_country="United States",
    ),
    "EUR": FiatCurrency(
        name="Euro", code="EUR", issuing_country="Eurozone",
    ),
    "BTC": CryptoCurrency(
        name="Bitcoin", code="BTC", algorithm="SHA-256", market_cap=1.12e12,
    ),
    "ETH": CryptoCurrency(
        name="Ethereum", code="ETH", algorithm="Ethash", market_cap=3.5e11,
    ),
}


def get_currency(code: str) -> Currency:
    """
    Получает объект валюты по коду.
    """
    # Приводим код к верхнему регистру для поиска
    code_upper = code.strip().upper()

    if code_upper in _currencies_registry:
        return _currencies_registry[code_upper]

    raise CurrencyNotFoundError(code=code)
