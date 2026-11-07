import argparse
import shlex

import prompt

from valutatrade_hub.core.exceptions import (
    ApiRequestError,
    CurrencyNotFoundError,
    InsufficientFundsError,
)
from valutatrade_hub.core.usecases import (
    buy_currency,
    get_rate,
    login_user,
    register_user,
    sell_currency,
    show_portfolio,
    update_rate,
    show_rate,
)
from valutatrade_hub.infra.settings import settings


def run_cli():
    current_user = None
    parser = get_parser()

    while True:
        try:
            user_input = prompt.string('\n>>>Введите команду: ')
            args = parse_args(parser, user_input)

            match args.command:
                case "register":
                    # register --username test --password 1234
                    user = register_user(
                        username=args.username,
                        password=args.password,
                    )

                    print(
                        f"Войдите: login --username {user.username} --password ****"
                    )
                case "login":
                    # login --username test --password 1234
                    current_user = login_user(
                        username=args.username,
                        password=args.password,
                    )

                    print(f"Вы вошли как '{current_user.username}'")
                case "show-portfolio":
                    # show-portfolio
                    show_portfolio(
                        user=current_user, base=args.base,
                    )
                case "buy":
                    # buy --currency BTC --amount 0.05
                    buy_currency(
                        user=current_user,
                        currency=args.currency,
                        amount=args.amount,
                    )
                case "sell":
                    # sell --currency USD --amount 100
                    sell_currency(
                        user=current_user,
                        currency=args.currency,
                        amount=args.amount,
                    )
                case "get-rate":
                    # get-rate --from USD --to BTC
                    get_rate(
                        from_code=args.from_currency,
                        to_code=args.to_currency,
                    )
                case "update-rates":
                    # update-rates
                    update_rate(source=args.source)
                case "show-rates":
                    # show-rates
                    show_rate(
                        currency=args.currency,
                        top=args.top,
                        base=args.base,
                    )
                case 'exit':
                    break
                case 'help':
                    parser.print_help()
        except (
                InsufficientFundsError,
                CurrencyNotFoundError,
                ApiRequestError
        ) as e:
            print(e)
        except (ValueError, TypeError, Exception) as e:
            print(f"Ошибка: {e}")
        except SystemExit as e:
            print(f"Системная ошибка: {e}")


def get_parser():
    """
    Парсит строку командной строки.
    """
    parser = argparse.ArgumentParser(
        usage='',
        add_help=False,
        exit_on_error=False,
        description="Платформа для отслеживания и симуляции торговли валютами",
    )
    subparsers = parser.add_subparsers(dest="command", help="Доступные команды")

    # help
    subparsers.add_parser("help", help="Справочная информация")

    # exit
    subparsers.add_parser("exit", help="Выход из программы")

    # register
    p_register = subparsers.add_parser(
    "register",
        help="Создать нового пользователя",
        exit_on_error=False,
    )
    p_register.add_argument(
        "--username",
        required=True,
        help="Имя пользователя",
        type=str,
    )
    p_register.add_argument(
        "--password",
        required=True,
        help="Пароль (мин. 4 символа)",
        type=str,
    )

    # login
    p_login = subparsers.add_parser(
        "login", help="Войти в систему", exit_on_error=False)
    p_login.add_argument(
    "--username",
        required=True,
        help="Имя пользователя",
        type=str,
    )
    p_login.add_argument(
        "--password", required=True, help="Пароль",
        type=str,
    )

    # show-portfolio
    p_portfolio = subparsers.add_parser(
        "show-portfolio",
        help="Показать портфель",
        exit_on_error=False,
    )
    p_portfolio.add_argument(
        "--base",
        default=settings.get('default_base_currency'),
        help=f"Базовая валюта "
             f"(по умолчанию {settings.get('default_base_currency')})",
        type=str,
    )

    # buy
    p_buy = subparsers.add_parser(
        "buy",
        help="Купить валюту",
        exit_on_error=False,
    )
    p_buy.add_argument(
        "--currency",
        help="Код валюты",
        type=str,
    )
    p_buy.add_argument(
        "--amount",
        help="Количество покупаемой валюты",
        type=float,
    )

    # sell
    p_sell = subparsers.add_parser(
        "sell",
        help="Купить валюту",
        exit_on_error=False,
    )
    p_sell.add_argument(
        "--currency",
        help="Код валюты",
        type=str,
    )
    p_sell.add_argument(
        "--amount",
        help="Количество продаваемой валюты",
        type=float,
    )

    # get-rate
    p_get_rate = subparsers.add_parser(
        "get-rate",
        help="Получить текущий курс одной валюты к другой",
        exit_on_error=False,
    )
    p_get_rate.add_argument(
        "--from", dest="from_currency",
        required=True, help="Исходная валюта",
    )
    p_get_rate.add_argument(
        "--to", dest="to_currency",
        required=True, help="Целевая валюта",
    )

    # update-rates
    p_update_rates = subparsers.add_parser(
        "update-rates",
        help="Обновление курсов валют",
        exit_on_error=False,
    )
    p_update_rates.add_argument(
        "--source",
         help="Обновить данные только из указанного источника",
         type=str,
    )

    # show-rates
    p_show_rates = subparsers.add_parser(
        "show-rates",
        help="Обновление курсов валют",
        exit_on_error=False,
    )
    p_show_rates.add_argument(
        "--currency",
        required=True,
        help="Показать курс только для указанной валюты",
        type=str,
    )
    p_show_rates.add_argument(
        "--top",
        required=True,
        help="Показать N самых дорогих криптовалют",
        type=int,
    )
    p_show_rates.add_argument(
        "--base",
        help="Показать все курсы относительно указанной базы ",
        type=int,
    )
    return parser


def parse_args(parser, command_line):
    return parser.parse_args(shlex.split(command_line))
