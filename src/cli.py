"""Build the cli of this app."""

import argparse
from ipaddress import IPv4Address

from .controller import cli_run_adhoc, cli_run_config, cli_run_partylan, cli_sh_games, cli_sh_intf, cli_sh_ports
from .interfacehandler import get_interfaces


def init_argparse() -> argparse.ArgumentParser:
    """Initilize the cli."""
    parser = argparse.ArgumentParser(
        prog="GameLink",
        # usage="%(prog)s [OPTIONS]",  # noqa: ERA001
        description=" Connects players via different networks",
    )
    parser.add_argument("-v", "--version", action="version", version=f"{parser.prog} version 0.1.0")
    parser.add_argument(
        "-d",
        "--debug",
        action="store_true",
        help="print more informations",
    )
    subparsers = parser.add_subparsers(title="subcommands", help="available commands")

    # main -> show submenu
    show_parser = subparsers.add_parser("show", help="show more informations")
    show_subparsers = show_parser.add_subparsers(title="show menu", dest="subcommand", required=True, help="available commands")
    # show -> interface submenu
    show_interface_parser = show_subparsers.add_parser(
        "interface",
        help="show network interfaces to use",
    )
    show_interface_parser.set_defaults(func=cli_sh_intf)

    # show -> games submenu
    show_games_parser = show_subparsers.add_parser("game", help="show verified games")
    show_games_parser.set_defaults(func=cli_sh_games)

    # show -> ports submenu
    show_ports_parser = show_subparsers.add_parser("ports", help="show udp ports of your process (game)")
    show_ports_parser.set_defaults(func=cli_sh_ports)
    show_ports_parser.add_argument(
        "process",
        type=str,
        help="define the process name to monitor udp ports (ex. 'UT2004.exe').",
        nargs="?",
        metavar="process",
    )

    # main -> adhoc submenu
    adhoc_subparsers = subparsers.add_parser("adhoc", help="run with cli entered values")
    # main -> adhoc submenu run packethandler
    adhoc_subparsers.set_defaults(func=cli_run_adhoc)

    adhoc_subparsers.add_argument(
        "-o",
        dest="old_dest",
        type=IPv4Address,
        help="specify the (old) IP address to catch the packets to forward [DEFAULT: 255.255.255.255]",
        default=IPv4Address("255.255.255.255"),
        metavar="IP",
    )
    adhoc_subparsers.add_argument(
        "interface",
        type=str,
        help="specify the network interface you want to catch and forward the packets (available values run 'show interfaces')",
        choices=get_interfaces(),
        metavar="interface",
    )
    adhoc_subparsers.add_argument(
        "-p",
        type=int,
        dest="ports",
        nargs="+",
        help="specify multiple ports to catch the packets to forward",
        metavar="Port",
        required=True,
    )
    adhoc_subparsers.add_argument(
        "-n",
        type=IPv4Address,
        dest="new_dests",
        nargs="+",
        help="specify multiple IP addresses to forward the packets to new destinations",
        metavar="IP",
        required=True,
    )
    # main -> vpn submenu
    vpn_subparsers = subparsers.add_parser("vpn", help="run with custom vpn settings")
    # main -> vpn submenu run packethandler
    vpn_subparsers.set_defaults(func=cli_run_config)

    vpn_subparsers.add_argument(
        "file",
        help="OPTIONAL: specify a custom config file [DEFAULT: config.json]",
        type=str,
        default="config.json",
        nargs="?",
    )
    # main -> partylan submenu
    partylan_subparsers = subparsers.add_parser("partylan", help="run with partylan settings [NOT RELIABLE]")
    # main -> partylan submenu run packethandler with partylan informations
    partylan_subparsers.set_defaults(func=cli_run_partylan)
    partylan_subparsers.add_argument(
        "path",
        help="OPTIONAL: specify the partylan path [DEFAULT: path in config.json]",
        type=str,
        nargs="?",
    )
    partylan_subparsers.add_argument(
        "-a",
        "--all",
        action="store_true",
        help="""
        The partylan log is not consistent with it entries for 'accepted sessions' to determine the IP addresses.
        You can use this argument to use all log entries to determine the IP address.
        So you get IP addresses, even if this friend is offline.
        But sometimes it writes no log entry and this program cant determine your steam friends ip.
        """,
    )

    return parser


if __name__ == "__main__":
    parser = init_argparse()
    args = parser.parse_args()
    if hasattr(args, "func"):
        args.func()
