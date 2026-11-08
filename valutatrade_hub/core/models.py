import hashlib
import json
from datetime import datetime
from typing import Dict, Optional

from valutatrade_hub.core.exceptions import InsufficientFundsError
from valutatrade_hub.core.utils import get_rate_val


class User:
    """
        Модель пользователя системы.

    Атрибуты:
        user_id (int): Уникальный идентификатор пользователя.
        username (str): Имя пользователя.
        registration_date (datetime): Дата регистрации.
        salt (str): Криптографическая соль для хеширования пароля.

    Управляет хранением и верификацией учетных данных.
    """
    def __init__(self, user_id: int, username: str, password: str, salt: str):
        """
        Инициализация пользователя.
        :param user_id: Уникальный идентификатор.
        :param username: Имя пользователя.
        :param password: Пароль в открытом виде (будет зашифрован).
        :param salt: Соль.
        """
        self._user_id = user_id
        self._username = username
        self._salt = salt
        self._hashed_password = self._hash_password(password)
        self._registration_date = datetime.now()

    def _hash_password(self, password: str) -> str:
        """
        Создает односторонний хеш пароля.
        """
        return hashlib.sha256((password + self._salt).encode('utf-8')).hexdigest()


    @property
    def user_id(self) -> int:
        """Возвращает уникальный идентификатор пользователя."""
        return self._user_id

    @property
    def username(self) -> str:
        """Возвращает имя пользователя."""
        return self._username

    @username.setter
    def username(self, value: str):
        """
        Устанавливает имя пользователя.

        Args:
            value: Новое имя пользователя.

        Raises:
            ValueError: Если имя пользователя пустое или содержит только пробелы.
        """
        if not value or not value.strip():
            raise ValueError("Имя пользователя не может быть пустым.")
        self._username = value.strip()

    @property
    def registration_date(self) -> datetime:
        """Возвращает дату регистрации пользователя."""
        return self._registration_date

    @property
    def salt(self) -> str:
        """Возвращает криптографическую соль."""
        return self._salt

    def verify_password(self, password: str) -> bool:
        """
        Проверяет введенный пароль на совпадение с сохраненным хешем.
        """
        calculated_hash = self._hash_password(password)
        return calculated_hash == self._hashed_password

    def change_password(self, new_password: str):
        """
        Изменяет пароль пользователя.
        Проверяет длину пароля и обновляет хеш.
        """
        if len(new_password) < 4:
            raise ValueError("Пароль должен быть не короче 4 символов.")

        self._hashed_password = self._hash_password(new_password)

    def get_user_info(self) -> dict:
        """
        Возвращает информацию о пользователе (без пароля).
        """
        return {
            "user_id": self._user_id,
            "username": self._username,
            "registration_date": self._registration_date.isoformat(),
            "salt": self._salt,
        }

    def to_json(self) -> str:
        """
        Конвертирует объект в JSON-строку для сохранения в файл.
        """
        return json.dumps({
            "user_id": self._user_id,
            "username": self._username,
            "hashed_password": self._hashed_password,
            "salt": self._salt,
            "registration_date": self._registration_date.isoformat()
        }, indent=2)

    @classmethod
    def from_json(cls, json_str: str) -> 'User':
        """
        Создает объект User из JSON-строки.
        """
        data = json.loads(json_str)
        user = cls(
            user_id=data["user_id"],
            username=data["username"],
            password="",
            salt=data["salt"]
        )
        user._hashed_password = data["hashed_password"]
        return user


class Wallet:
    """
    Модель кошелька для хранения конкретной валюты.

    Атрибуты:
        currency_code (str): Код валюты (например, "USD", "BTC").
        balance (float): Текущий баланс.

    Обеспечивает проверку целостности операций пополнения и снятия.
    """
    def __init__(self, currency_code: str, balance: float = 0.0):
        """
        Инициализация кошелька.
        :param currency_code: Код валюты (например, "USD", "BTC").
        :param balance: Начальный баланс (по умолчанию 0.0).
        """
        self._currency_code = currency_code
        self._balance = balance


    @property
    def currency_code(self) -> str:
        """Возвращает код валюты кошелька."""
        return self._currency_code

    @property
    def balance(self) -> float:
        """Возвращает текущий баланс."""
        return self._balance

    @balance.setter
    def balance(self, value: float):
        """
        Устанавливает баланс кошелька.

        Args:
            value: Новое значение баланса.

        Raises:
            TypeError: Если значение не число (int или float).
            ValueError: Если баланс становится отрицательным.
        """
        if not isinstance(value, (int, float)):
            raise TypeError("Баланс должен быть числом (int или float).")

        if value < 0:
            raise ValueError("Баланс не может быть отрицательным.")

        self._balance = float(value)

    def deposit(self, amount: float) -> None:
        """
        Пополняет баланс кошелька.

        Args:
            amount: Сумма для пополнения.

        Raises:
            ValueError: Если сумма для пополнения неположительная.
        """
        if amount <= 0:
            raise ValueError("Сумма пополнения должна быть положительной.")

        self._balance += amount

    def withdraw(self, amount: float) -> float:
        """
        Снимает средства с кошелька.

        Args:
            amount: Сумма для снятия.

        Returns:
            float: Фактическая сумма снятия (подтвержденная).

        Raises:
            ValueError: Если сумма для снятия неположительная или
            превышает текущий баланс.
        """
        if amount <= 0:
            raise ValueError("Сумма снятия должна быть положительной.")

        if amount > self._balance:
            raise InsufficientFundsError(
                code=self._currency_code,
                required=amount,
                available=self._balance,
            )

        self._balance -= amount
        return amount


class Portfolio:
    """
    Модель портфеля пользователя, содержащая коллекцию кошельков.

    Атрибуты:
        user (int): ID владельца портфеля.
        wallets (Dict[str, Wallet]): Словарь кошельков {currency_code: Wallet}.

    Управляет балансами по разным валютам и рассчитывает общую стоимость.
    """
    def __init__(self, user_id: int, wallets: Optional[Dict[str, Wallet]]):
        """
        Инициализация портфеля.
        :param user_id: ID пользователя.
        :param wallets: Словарь существующих кошельков.
        """
        self._user_id = user_id
        self._wallets = wallets


    @property
    def user(self) -> int:
        """Возвращает ID владельца портфеля."""
        return self._user_id

    @property
    def wallets(self) -> Dict[str, Wallet]:
        """
        Возвращает копию словаря кошельков.

        Returns:
            dict: Копия словаря кошельков.

        Примечание: Возвращаемая копия предотвращает прямую модификацию
        внутреннего состояния объекта извне.
        """
        return self._wallets.copy()

    def add_currency(self, currency_code: str) -> Wallet:
        """
        Добавляет новый кошелёк в портфель с начальной нулевой суммой.

        Args:
            currency_code: Код валюты для нового кошелька.

        Returns:
            Wallet: Новый объект кошелька.

        Raises:
            ValueError: Если кошелёк с указанным кодом валюты уже существует.
        """
        if currency_code in self._wallets:
            raise ValueError(f"Кошелёк с валютой {currency_code} уже существует.")

        new_wallet = Wallet(currency_code=currency_code, balance=0.0)
        self._wallets[currency_code] = new_wallet
        return new_wallet

    def get_wallet(self, currency_code: str) -> Optional[Wallet|None]:
        """
        Возвращает объект кошелька по коду валюты.

        Args:
            currency_code: Код валюты.

        Returns:
            Wallet|None: Объект кошелька или None, если валюта отсутствует в портфеле.
        """
        return self._wallets.get(currency_code)

    def get_total_value(self, base_currency: str = 'USD') -> float:
        """
        Рассчитывает общую стоимость портфеля в указанной базовой валюте.

        Args:
           base_currency: Базовая валюта для конвертации (по умолчанию 'USD').

        Returns:
           float: Общая стоимость всех кошельков в базовой валюте.
        """

        total_value = 0.0
        for currency_code, wallet in self._wallets.items():
            if currency_code != base_currency:
                rate = get_rate_val(currency_code, base_currency)
                value_in_base = wallet.balance * rate
            else:
                value_in_base = wallet.balance

            total_value += value_in_base

        return total_value

    def to_json(self) -> str:
        """
        Конвертирует портфель в JSON-строку для сохранения.
        """
        return json.dumps({
            "user_id": self._user_id,
            "wallets": {
                code: wallet.balance
                for code, wallet in self._wallets.items()
            }
        }, indent=2)

    @classmethod
    def from_json(cls, json_str: str) -> 'Portfolio':
        """
        Создает объект Portfolio из JSON-строки.
        """
        data = json.loads(json_str)

        return cls(user_id=data["user_id"], wallets={
            code: Wallet(code, balance)
            for code, balance in data["wallets"].items()
        })
