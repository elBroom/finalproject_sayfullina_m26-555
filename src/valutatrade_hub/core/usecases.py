import json
import os
import secrets
from datetime import datetime
from typing import Dict, Optional

from valutatrade_hub.core.models import Portfolio, User
from valutatrade_hub.core.utils import load_json_file, save_json_file

DATA_DIR = "data"
USERS_FILE = os.path.join(DATA_DIR, "users.json")
PORTFOLIOS_FILE = os.path.join(DATA_DIR, "portfolios.json")
RATES_FILE = os.path.join(DATA_DIR, "rates.json")

CURRENCY_BASE = "USD"



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
    portfolios = [p for p in portfolios if p["user_id"] != portfolio.user]
    portfolios.append(json.loads(portfolio.to_json()))
    save_json_file(PORTFOLIOS_FILE, portfolios)

def get_rates() -> Dict[str, float]:
    rates = load_json_file(RATES_FILE, {})

    return {key: val['rate'] for key, val in rates.items() if 'rate' in val}


def get_rate(from_currency: str, to_currency: str) -> Optional[float|None]:
    if from_currency == to_currency:
        return 1.0

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


def register_user(username: str, password: str):
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

    print(
        f"Пользователь '{user.username}' "
        f"зарегистрирован (id={user.user_id}).\n",
    )


def login_user(username: str, password: str) -> User:
    user = get_user_by_username(username)
    if not user:
        raise ValueError(f"Пользователь '{username}' не найден")

    if not user.verify_password(password):
        raise ValueError("Неверный пароль")

    return user

def get_user_portfolio(user: User) -> Portfolio:
    """Получает портфель пользователя."""
    portfolio = get_portfolio_by_user_id(user.user_id)
    if not portfolio:
        portfolio = Portfolio(user_id=user.user_id, wallets={})
        save_portfolio(portfolio)
    return portfolio


def show_portfolio(user: User|None, base: str):
    """Отображает портфель пользователя."""
    if user is None:
        raise ValueError("Сначала выполните login")

    portfolio = get_user_portfolio(user)
    if not len(portfolio.wallets):
        raise ValueError(f"У пользователя {user.username} нет кошельков")

    try:
        total_value = 0.0
        print(
            f"Портфель пользователя '{user.username}' (база: {base}):",
        )
        for code, wallet in portfolio.wallets.items():
            # Получаем курс конвертации
            if code == base:
                rate = 1
            else:
                rate = get_rate(code, base)

            value_in_base = wallet.balance * rate
            total_value += value_in_base

            print(
                f"- {code}: {wallet.balance:.2f}  →  {value_in_base:.2f} {base}",
            )
        print(
            "-" * 30,
            f"\nИТОГО: {total_value:,.2f} {base}",
        )
    except KeyError:
        raise ValueError(f"Неизвестная базовая валюта '{base}'")


def buy_currency(user: User|None, currency: str, amount: float):
    if user is None:
        raise ValueError("Сначала выполните login")

    if amount <= 0:
        raise ValueError("'amount' должен быть положительным числом")

    rate = get_rate(currency, CURRENCY_BASE)
    if rate is None:
        raise ValueError(
            f'Не удалось получить курс для {currency}->{CURRENCY_BASE}',
        )

    portfolio = get_user_portfolio(user)
    wallet = portfolio.get_wallet(currency)
    if wallet is None:
        wallet = portfolio.add_currency(currency)

    prev_amount = wallet.balance
    cost_usd = amount * rate
    wallet.deposit(amount)
    curr_amount = wallet.balance

    save_portfolio(portfolio)

    print(
        f"Покупка выполнена: {amount:.4f} {currency} "
        f"по курсу {rate:.2f} {CURRENCY_BASE}/{currency}",
        "\nИзменения в портфеле:",
        f"\n- {currency}: было {prev_amount:.4f} → стало {curr_amount:.4f}"
        f"\nОценочная стоимость покупки: {cost_usd:.2f} {CURRENCY_BASE}"
    )

def sell_currency(user: User|None, currency: str, amount: float):
    if user is None:
        raise ValueError("Сначала выполните login")

    if amount <= 0:
        raise ValueError("'amount' должен быть положительным числом")

    rate = get_rate(currency, CURRENCY_BASE)
    if rate is None:
        raise ValueError(
            f'Не удалось получить курс для {currency}->{CURRENCY_BASE}',
        )

    portfolio = get_user_portfolio(user)
    wallet = portfolio.get_wallet(currency)
    if wallet is None:
        raise ValueError(
            f"У вас нет кошелька '{currency}'. "
            f"Добавьте валюту: она создаётся автоматически при первой покупке.",
        )

    if wallet.balance < amount:
        raise ValueError(
            f"Недостаточно средств: доступно {wallet.balance} {currency},"
            f" требуется {amount} {currency}",
        )

    prev_amount = wallet.balance
    cost_usd = amount * rate
    wallet.withdraw(amount)
    curr_amount = wallet.balance

    save_portfolio(portfolio)

    print(
        f"Продажа выполнена: {amount:.4f} {currency} "
        f"по курсу {rate:.2f} {CURRENCY_BASE}/{currency}",
        "\nИзменения в портфеле:",
        f"\n- {currency}: было {prev_amount:.4f} → стало {curr_amount:.4f}"
        f"\nОценочная выручка: {cost_usd:.2f} {CURRENCY_BASE}"
    )

