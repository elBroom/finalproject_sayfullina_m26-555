import argparse
import shlex

import prompt

from valutatrade_hub.core.usecases import (
    CURRENCY_BASE,
    buy_currency,
    get_rate_currency,
    login_user,
    register_user,
    sell_currency,
    show_portfolio,
)


def run_cli():
    parser = get_parser()
    current_user = None

    while True:
        try:
            user_input = prompt.string('\n>>>Введите команду: ')
            args = parse_args(parser, user_input)

            match args.command:
                case "register":
                    # register --username test --password 1234
                    user = register_user(args.username, args.password)

                    print(
                        f"Войдите: login --username {user.username} --password ****"
                    )
                case "login":
                    # login --username test --password 1234
                    current_user = login_user(args.username, args.password)

                    print(f"Вы вошли как '{current_user.username}'")
                case "show-portfolio":
                    # show-portfolio
                    show_portfolio(current_user, args.base)
                case "buy":
                    # buy --currency BTC --amount 0.05
                    buy_currency(current_user, args.currency, args.amount)
                case "sell":
                    # sell --currency USD --amount 100
                    sell_currency(current_user, args.currency, args.amount)
                case "get-rate":
                    # get-rate --from USD --to BTC
                    get_rate_currency(args.from_currency, args.to_currency)
                case 'exit':
                    break
                case 'help':
                    parser.print_help()
        except (Exception, SystemExit) as e:
            print(f"Ошибка: {e}")


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
        default=CURRENCY_BASE,
        help=f"Базовая валюта (по умолчанию {CURRENCY_BASE})",
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

    return parser


def parse_args(parser, command_line):
    return parser.parse_args(shlex.split(command_line))
