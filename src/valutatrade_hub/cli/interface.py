import argparse
import shlex

import prompt

from valutatrade_hub.core.usecases import (
    register_user, login_user, show_portfolio
)

def run_cli():
    parser = get_parser()
    current_user = None
    # from valutatrade_hub.core.usecases import get_user_by_username
    # current_user = get_user_by_username('test')

    while True:
        try:
            user_input = prompt.string('\n>>>Введите команду: ')
            args = parse_args(parser, user_input)

            match args.command:
                case "register":
                    # register --username test --password 1234
                    user = register_user(args.username, args.password)

                    print(
                        f"Пользователь '{user.username}' "
                        f"зарегистрирован (id={user.user_id}).\n",
                        f"Войдите: login --username {user.username} --password ****"
                    )
                case "login":
                    # login --username test --password 1234
                    current_user = login_user(args.username, args.password)

                    print(f"Вы вошли как '{current_user.username}'")
                case "show-portfolio":
                    # show-portfolio
                    protfolio, rows = show_portfolio(current_user, args.base)
                    total = protfolio.get_total_value(args.base)
                    print(
                        f"Портфель пользователя '{current_user.username}'"
                        f" (база: {args.base}):",
                    )
                    [print(r) for r in rows]
                    print(
                        "-" * 30,
                        f"\nИТОГО: {total:,.2f} {args.base}",
                    )
                case 'exit':
                    break
                case 'help':
                    parser.print_help()
        except (Exception, SystemExit) as e:
            print(f"Ошибка: {e}")
            raise


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
    subparsers.add_parser("help", help="справочная информация")

    # exit
    subparsers.add_parser("exit", help="выход из программы")

    # register
    p_register = subparsers.add_parser(
    "register",
        help="создать нового пользователя",
        exit_on_error=False,
    )
    p_register.add_argument(
        "--username",
        required=True,
        help="Имя пользователя",
    )
    p_register.add_argument(
        "--password",
        required=True,
        help="Пароль (мин. 4 символа)",
    )

    # login
    p_login = subparsers.add_parser(
        "login", help="Войти в систему", exit_on_error=False)
    p_login.add_argument(
        "--username", required=True, help="Имя пользователя")
    p_login.add_argument(
        "--password", required=True, help="Пароль")

    # show-portfolio
    p_portfolio = subparsers.add_parser(
        "show-portfolio",
        help="Показать портфель",
        exit_on_error=False,
    )
    p_portfolio.add_argument(
        "--base",
        default="USD",
        help="Базовая валюта (по умолчанию USD)",
    )

    return parser


def parse_args(parser, command_line):
    return parser.parse_args(shlex.split(command_line))
