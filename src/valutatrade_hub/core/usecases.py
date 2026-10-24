import json
import os
import secrets
from datetime import datetime, timedelta
from typing import Optional

from valutatrade_hub.core.models import Portfolio, User
from valutatrade_hub.core.utils import load_json_file, save_json_file

DATA_DIR = "data"
USERS_FILE = os.path.join(DATA_DIR, "users.json")
PORTFOLIOS_FILE = os.path.join(DATA_DIR, "portfolios.json")
RATES_FILE = os.path.join(DATA_DIR, "rates.json")



def get_next_user_id() -> int:
    users = load_json_file(USERS_FILE, [])
    if not users:
        return 1
    return max(u["user_id"] for u in users) + 1


def get_user_by_username(username: str) -> Optional[User]:
    users = load_json_file(USERS_FILE, [])
    for u_data in users:
        if u_data["username"] == username:
            return User.from_json(json.dumps(u_data))
    return None


def save_user(user: User):
    users = load_json_file(USERS_FILE, [])
    users = [u for u in users if u["username"] != user.username]
    users.append(json.loads(user.to_json()))
    save_json_file(USERS_FILE, users)


def get_portfolio_by_user_id(user_id: int) -> Optional[Portfolio]:
    portfolios = load_json_file(PORTFOLIOS_FILE, [])
    for p_data in portfolios:
        if p_data["user_id"] == user_id:
            return Portfolio.from_json(json.dumps(p_data))
    return None


def save_portfolio(portfolio: Portfolio):
    portfolios = load_json_file(PORTFOLIOS_FILE, [])
    # Обновляем или добавляем
    portfolios = [p for p in portfolios if p["user_id"] != portfolio.user_id]
    portfolios.append(json.loads(portfolio.to_json()))
    save_json_file(PORTFOLIOS_FILE, portfolios)


def get_rate(from_currency: str, to_currency: str) -> Optional[float]:
    rates = load_json_file(RATES_FILE, {})
    key = f"{from_currency}_{to_currency}"

    if key in rates:
        return rates[key]["rate"]

    return None


def save_rate(from_currency: str, to_currency: str, rate: float):
    rates = load_json_file(RATES_FILE, {})
    key = f"{from_currency}_{to_currency}"
    rates[key] = {
        "rate": rate,
        "updated_at": datetime.now().isoformat(),
        "source": "CLI_Cache"
    }
    rates["last_refresh"] = datetime.now().isoformat()
    save_json_file(RATES_FILE, rates)


def register_user(username: str, password: str) -> User:
    if not username or not username.strip():
        raise ValueError("Имя пользователя не может быть пустым.")

    if len(password) < 4:
        raise ValueError("Пароль должен быть не короче 4 символов.")

    if get_user_by_username(username):
        raise ValueError(f"Имя пользователя '{username}' уже занято.")

    user_id = get_next_user_id()
    user = User(user_id=user_id, username=username, password=password,
                salt=secrets.token_urlsafe(16))
    save_user(user)

    portfolio = Portfolio(user_id=user_id, wallets={})
    save_portfolio(portfolio)

    return user


def login_user(username: str, password: str) -> User:
    user = get_user_by_username(username)
    if not user:
        raise ValueError(f"Пользователь '{username}' не найден")

    if not user.verify_password(password):
        raise ValueError("Неверный пароль")

    return user
