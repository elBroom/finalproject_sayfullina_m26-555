import json
import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional

from valutatrade_hub.core.currencies import get_currency
from valutatrade_hub.core.exceptions import ApiRequestError, InsufficientFundsError
from valutatrade_hub.core.models import Portfolio, User
from valutatrade_hub.core.utils import (
    PORTFOLIOS_FILE,
    RATES_FILE,
    USERS_FILE,
    get_rate_val,
    load_json_file,
    save_json_file,
)
from valutatrade_hub.decorators import log_action
from valutatrade_hub.infra.settings import settings
from valutatrade_hub.parser_service.config import ParserConfig
from valutatrade_hub.parser_service.updater import RatesUpdater

# Пути к файлам данных
CURRENCY_BASE = settings.get("default_base_currency")


def get_next_user_id() -> int:
    """
    Генерирует следующий уникальный ID для нового пользователя.

    Reads:
        USERS_FILE: Файл с массивом пользователей.

    Returns:
        int: Следующий доступный ID (максимальный ID + 1).
             Если файл пуст или не найден, возвращает 1.
    """
    users = load_json_file(USERS_FILE, [])
    if not users:
        return 1
    return max(u["user_id"] for u in users) + 1


def get_user_by_username(username: str) -> Optional[User]:
    """
    Поиск пользователя в базе по имени.

    Args:
        username: Имя пользователя для поиска.

    Returns:
        User|None: Объект User, если найден, иначе None.
    """
    users = load_json_file(USERS_FILE, [])
    for u_data in users:
        if u_data["username"] == username:
            return User.from_json(json.dumps(u_data))
    return None


def save_user(user: User):
    """
    Сохраняет или обновляет данные пользователя в файле.

    Args:
        user: Объект User для сохранения.
    """
    users = load_json_file(USERS_FILE, [])
    users = [u for u in users if u["username"] != user.username]
    users.append(json.loads(user.to_json()))
    save_json_file(USERS_FILE, users)


def get_portfolio_by_user_id(user_id: int) -> Optional[Portfolio]:
    """
    Поиск портфеля пользователя по ID.

    Args:
        user_id: ID владельца портфеля.

    Returns:
        Portfolio|None: Объект портфеля, если найден, иначе None.
    """
    portfolios = load_json_file(PORTFOLIOS_FILE, [])
    for p_data in portfolios:
        if p_data["user_id"] == user_id:
            return Portfolio.from_json(json.dumps(p_data))
    return None


def save_portfolio(portfolio: Portfolio):
    """
    Сохраняет или обновляет данные портфеля в файле.

    Args:
        portfolio: Объект Portfolio для сохранения.
    """
    portfolios = load_json_file(PORTFOLIOS_FILE, [])
    # Обновляем или добавляем
    portfolios = [p for p in portfolios if p["user_id"] != portfolio.user]
    portfolios.append(json.loads(portfolio.to_json()))
    save_json_file(PORTFOLIOS_FILE, portfolios)

def get_rate_fresh(from_currency: str, to_currency: str) -> dict:
    """
    Получает курс конвертации, проверяя актуальность кэша.
    Если данные устарели (большее 5 минут) или отсутствуют,
    получает новый курс по api.

    Args:
        from_currency: Код валюты для конвертации (из).
        to_currency: Код валюты целевой (в).

    Returns:
        dict: Словарь с курсом {'rate': float, 'updated_at': str}.

    Raises:
        ValueError: Если курс валюты не поддерживается.
        ApiRequestError: Если не получилось получить курс валюты.
    """
    update_rate_iscall = False
    while True:
        rates = load_json_file(RATES_FILE, {})
        if f"{from_currency}_{to_currency}" in rates:
            key = f"{from_currency}_{to_currency}"
        else:
            key = f"{to_currency}_{from_currency}"
        try:
            rate_data = rates[key]

            updated_at = datetime.fromisoformat(rate_data["updated_at"])
            delta = timedelta(seconds=settings.get('rates_ttl_seconds'))

            if datetime.now(timezone.utc) - updated_at < delta:
                return rate_data
        except KeyError:
            raise ValueError(f'Курс {to_currency}→{from_currency} не поддерживается.')
        if not update_rate_iscall:
            update_rate_iscall = True
            parser_srv = RatesUpdater(ParserConfig())
            parser_srv.run_update()
        else:
            raise ApiRequestError(
                f'Курс {to_currency}→{from_currency} недоступен. '
                f'Повторите попытку позже.'
            )

@log_action(action_name='REGISTER')
def register_user(username: str, password: str):
    """
    Регистрирует нового пользователя, создавая его запись и пустой портфель.

    Args:
        username: Имя пользователя.
        password: Пароль (должен быть >= 4 символов).

    Returns:
        User: Новый объект пользователя.

    Raises:
        ValueError: Если имя пользователя уже существует или пароль слишком короткий.
    """
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
    return user

@log_action(action_name='LOGIN')
def login_user(username: str, password: str) -> User:
    """
    Осуществляет вход пользователя в систему.

    Args:
        username: Имя пользователя.
        password: Пароль.

    Returns:
        User: Объект пользователя после успешной аутентификации.

    Raises:
        ValueError: Если пользователь не найден или пароль неверен.
    """
    user = get_user_by_username(username)
    if not user:
        raise ValueError(f"Пользователь '{username}' не найден")

    if not user.verify_password(password):
        raise ValueError("Неверный пароль")

    return user

def get_user_portfolio(user: User) -> Portfolio:
    """
    Получает портфель пользователя, создавая его при отсутствии.

    Args:
       user: Объект пользователя.

    Returns:
       Portfolio: Портфель пользователя.
   """
    portfolio = get_portfolio_by_user_id(user.user_id)
    if not portfolio:
        portfolio = Portfolio(user_id=user.user_id, wallets={})
        save_portfolio(portfolio)
    return portfolio


def show_portfolio(user: User|None, base: str):
    """
    Отображает текущее состояние портфеля пользователя с конвертацией
    всех валют в указанную базовую валюту.

    Args:
        user: Объект пользователя (или None, если не авторизован).
        base: Код базовой валюты для отображения (например, "USD").

    Raises:
        ValueError: Если пользователь не авторизован или портфель пуст.
    """
    if user is None:
        raise ValueError("Сначала выполните login")

    portfolio = get_user_portfolio(user)
    if not len(portfolio.wallets):
        raise ValueError(f"У пользователя {user.username} нет кошельков")

    total_value = 0.0
    print(
        f"Портфель пользователя '{user.username}' (база: {base}):",
    )
    base = base.upper()
    try:
        for code, wallet in portfolio.wallets.items():
            # Получаем курс конвертации
            if code == base:
                rate = 1
            else:
                rate = get_rate_val(code, base)

            value_in_base = wallet.balance * rate
            total_value += value_in_base

            print(
                f"- {code}: {wallet.balance:.2f}  →  {value_in_base:.2f} {base}",
            )
    except KeyError:
        raise ValueError(f"Неизвестная базовая валюта '{base}'")
    print(
        "-" * 30,
        f"\nИТОГО: {total_value:,.2f} {base}",
    )



@log_action(action_name='BUY')
def buy_currency(user: User|None, currency: str, amount: float):
    """
    Покупает указанную валюту у пользователя, учитывая текущий курс.

    Args:
        user: Объект пользователя (или None).
        currency: Код_currency для покупки.
        amount: Количество покупаемой валюты.

    Raises:
        ValueError: Если пользователь не авторизован, валюта не поддерживается
                    или insufficient funds (для продажи, но здесь только покупка).
    """
    if user is None:
        raise ValueError("Сначала выполните login")

    if amount <= 0:
        raise ValueError("'amount' должен быть положительным числом")

    get_currency(currency)

    rate = get_rate_val(currency, CURRENCY_BASE)
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

@log_action(action_name='SELL')
def sell_currency(user: User|None, currency: str, amount: float):
    """
    Продает указанную валюту пользователя, учитывая текущий курс.

    Args:
        user: Объект пользователя (или None).
        currency: Код валюты для продажи.
        amount: Количество продаваемой валюты.

    Raises:
        ValueError: Если пользователь не авторизован, валюта не найдена
                    или недостаточно средств.
    """
    if user is None:
        raise ValueError("Сначала выполните login")

    if amount <= 0:
        raise ValueError("'amount' должен быть положительным числом")

    get_currency(currency)

    rate = get_rate_val(currency, CURRENCY_BASE)
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
        raise InsufficientFundsError(
            code=currency,
            required=amount,
            available=wallet.balance,
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

@log_action(action_name='GET-RATE')
def get_rate(from_code: str, to_code: str):
    """
    Получает и отображает текущий курс конвертации между двумя валютами.

    Проверяет актуальность данных (kache) и генерирует новый курс, если он устарел.

    Args:
        from_currency: Код исходной валюты.
        to_currency: Код целевой валюты.

    Raises:
        ValueError: Если одна из валют не поддерживается системой.
    """
    get_currency(from_code)
    get_currency(to_code)

    rate_data = get_rate_fresh(from_code, to_code)

    rate = f'{rate_data["rate"]:.8f}'.rstrip('0')
    revert_rate = f'{1.0/rate_data["rate"]:.8f}'.rstrip('0')
    updated_at = rate_data["updated_at"]
    print(
        f"Курс {from_code}→{to_code}: {rate} (обновлено: {updated_at})"
        f"\nОбратный курс {to_code}→{from_code}: {revert_rate}",
    )

def update_rate(source: str = None):
    """
    Загружает курс валюты по апи.

    Args:
        source: Источник загрузки.
        'coingecko', 'exchangerate' или None (все)

    Raises:
        ApiRequestError: Если не получилось получить курс валюты.
    """
    parser_srv = RatesUpdater(ParserConfig())
    cnt = parser_srv.run_update(source)
    print(f'Обновлено: {cnt} валют')

def show_rate(currency: str, top: int, base: str):
    print('Команда не реализована')
