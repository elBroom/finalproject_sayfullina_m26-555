import hashlib
import json
from datetime import datetime


class User:
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
        return self._user_id

    @property
    def username(self) -> str:
        return self._username

    @username.setter
    def username(self, value: str):
        if not value or not value.strip():
            raise ValueError("Имя пользователя не может быть пустым.")
        self._username = value.strip()

    @property
    def registration_date(self) -> datetime:
        return self._registration_date

    @property
    def salt(self) -> str:
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
        return self._currency_code

    @property
    def balance(self) -> float:
        return self._balance

    @balance.setter
    def balance(self, value: float):
        """
        Сеттер для баланса.
        Запрещает отрицательные значения и некорректные типы.
        """
        if not isinstance(value, (int, float)):
            raise TypeError("Баланс должен быть числом (int или float).")

        if value < 0:
            raise ValueError("Баланс не может быть отрицательным.")

        self._balance = float(value)

    def deposit(self, amount: float) -> None:
        """
        Пополнение баланса.
        Проверяет, что сумма положительная.
        """
        if not isinstance(amount, (int, float)):
            raise TypeError("Сумма пополнения должна быть числом.")

        if amount <= 0:
            raise ValueError("Сумма пополнения должна быть положительной.")

        self._balance += amount

    def withdraw(self, amount: float) -> float:
        """
        Снятие средств.
        Проверяет, что сумма положительная и не превышает текущий баланс.
        Возвращает фактическую сумму снятия (или raises ошибку, если нельзя снять).
        """
        if not isinstance(amount, (int, float)):
            raise TypeError("Сумма снятия должна быть числом.")

        if amount <= 0:
            raise ValueError("Сумма снятия должна быть положительной.")

        if amount > self._balance:
            raise ValueError(f"Недостаточно средств. "
                             f"Текущий баланс: {self._balance}, запрошено: {amount}")

        self._balance -= amount
        return amount

    def get_balance_info(self) -> dict:
        """
        Возвращает информацию о балансе в виде словаря.
        """
        return {
            "currency_code": self._currency_code,
            "balance": self._balance
        }

    def to_json(self) -> str:
        """
        Конвертирует объект в JSON-строку для сохранения в портфеле.
        """
        return json.dumps({
            "currency_code": self._currency_code,
            "balance": self._balance
        }, indent=2)

    @classmethod
    def from_json(cls, json_str: str) -> 'Wallet':
        """
        Создает объект Wallet из JSON-строки.
        """
        data = json.loads(json_str)
        return cls(
            currency_code=data["currency_code"],
            balance=data["balance"]
        )
