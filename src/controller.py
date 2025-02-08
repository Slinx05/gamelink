"""Use argparse arguments to control the app."""

import sys
from argparse import Namespace
from itertools import chain
from typing import TypedDict
from pathlib import Path

from pydantic import Field, ValidationError
from pydantic.dataclasses import dataclass

from .filehandler import FileHandler
from .helper import print_header
from .interfacehandler import get_interfaces
from .loghandler import setup_logger
from .packethandler import PacketHandler
from .partylan import PartyLan, PartylanLogStatus
from .porthandler import run_monitor_broadcasts

logger = setup_logger(__name__)

file_abs_path = Path(__file__).absolute()
parent_dir = file_abs_path.parents[1].parts[-1]
base_dir = file_abs_path.parents[2] if parent_dir == "_internal" else file_abs_path.parents[1]

DEFAULT_GAMES = base_dir.joinpath("resources/lan-games-db/lan-games.csv")
DEFAULT_CONFIG = base_dir.joinpath("./config.json")
OLD_DESTINATION = "255.255.255.255"


class ConfigVPN(TypedDict):
    """config.json description."""

    interface: str
    player_ips: list[str]


class ConfigPartylan(TypedDict):
    """config.json description."""

    path: str


class Config(TypedDict):
    """config.json description."""

    vpn: ConfigVPN
    partylan: ConfigPartylan


class Games(TypedDict):
    """lan-games.csv description."""

    Verified: str
    Name: str
    Series: str
    Developer: str
    Publisher: str
    DatePublished: str
    UdpPorts: str


@dataclass
class Controller:
    """Initilize app config."""

    games: list[Games] = Field(init=False)
    config: Config = Field(init=False)

    def init_games(self, file: str) -> None:
        """Load game database.

        Args:
            file (str): games database file name

        """
        self.games = FileHandler(file).read()

    def init_config(self, file: str) -> None:
        """Load config file.

        Args:
            file (str): config file name

        """
        self.config = FileHandler(file).read()

    def _verified_games(self) -> list[Games]:
        """Get only games with verified status.

        Returns:
            list[Games]: verified games

        """
        return [game for game in self.games if game.get("Verified") == "Yes"]

    def get_udp_ports(self, verified: bool = True) -> set[int]:
        """Get UDP ports from game database.

        Args:
            verified (bool, optional): get only ports of verified games or all games. Defaults to True.

        Returns:
            set[int]: set of UDP ports

        """
        games_verified = self._verified_games() if verified else self.games
        ports_raw = {game.get("UdpPorts") for game in games_verified}
        ports = [port.split(",") for port in ports_raw]
        try:
            ports = {int(port) for port in set(chain(*ports))}
        except ValueError:
            logger.critical("Unsupported value found in '%s' %s", DEFAULT_GAMES, "column: 'UdpPorts'")
            sys.exit(1)
        else:
            return ports

    def get_games(self, verified: bool = True) -> list[Games]:
        """Get a list of games from game database.

        Args:
            verified (bool, optional): get only ports of verified games or all games. Defaults to True.

        Returns:
            list[Games]: list of Games-

        """
        return self._verified_games() if verified else self.games

    def run_packethandler(self, config: dict) -> None:
        """Run packethandler and modify ip packets.

        Args:
            config (dict): config parameter fpr packethandler

        """
        try:
            PacketHandler(**config).start()
        except ValidationError as err:
            error_messages = [e["msg"] for e in err.errors()]
            for msg in error_messages:
                logger.error(msg)  # noqa: TRY400
            sys.exit(1)


def cli_run_adhoc(args: Namespace) -> None:
    """Run program with user input."""
    ctrl = Controller()
    config = {
        "interface": args.interface,
        "old_dest": args.old_dest,
        "new_dests": args.new_dests,
        "ports": args.ports,
    }
    ctrl.run_packethandler(config)


def cli_run_config(args: Namespace) -> None:
    """Run program with config file."""
    ctrl = Controller()
    ctrl.init_games(DEFAULT_GAMES)
    if args.file:
        ctrl.init_config(args.file)
    else:
        ctrl.init_config(DEFAULT_CONFIG)
    config = {
        "interface": ctrl.config["vpn"]["interface"],
        "old_dest": OLD_DESTINATION,
        "new_dests": ctrl.config["vpn"]["player_ips"],
        "ports": ctrl.get_udp_ports(),
    }
    ctrl.run_packethandler(config)


def cli_run_partylan(args: Namespace) -> None:
    """Run program with parameters from partylan log file."""
    ctrl = Controller()
    ctrl.init_games(DEFAULT_GAMES)
    ctrl.init_config(DEFAULT_CONFIG)
    partylan = PartyLan(args.path) if args.path else PartyLan(ctrl.config["partylan"]["path"])
    config = {
        "interface": partylan.get_interface(),
        "old_dest": OLD_DESTINATION,
        "new_dests": partylan.get_addresses(PartylanLogStatus.ALL)
        if args.all
        else partylan.get_addresses(PartylanLogStatus.ACCEPTED),
        "ports": ctrl.get_udp_ports(),
    }
    ctrl.run_packethandler(config)


def cli_sh_intf() -> None:
    """Print a header and the network interfaces."""
    print_header("Available network interfaces")
    for intf in get_interfaces():
        print(intf)


def cli_sh_games() -> None:
    """Show verified games."""
    ctrl = Controller()
    ctrl.init_games(DEFAULT_GAMES)
    games = [game.get("Name") for game in ctrl.get_games()]
    print_header("Verified Games")
    [print(game) for game in games]


def cli_sh_ports(args: Namespace):
    run_monitor_broadcasts(args.process)


if __name__ == "__main__":
    print(base_dir)
