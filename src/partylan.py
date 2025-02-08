"""Works with partylan log to get informatios."""

import datetime
import re
from enum import Enum
from ipaddress import IPv4Address, IPv4Network
from pathlib import Path
from typing import TypedDict

from pydantic import Field
from pydantic.dataclasses import dataclass

from src.filehandler import FileHandler

# Partylan default settings
PARTYLAN_LOG_FILENAME = "lpvpn.log.txt"
PARTYLAN_NETWORK_IP = "100.64.0.0"
PARTYLAN_NETWORK_MASK = 10
PARTYLAN_COMPUTE_IP_ERROR = "No available address"
PARTYLAN_INTERFACE = "PartyLAN Tunnel"


TESTLOG = """
[2025-01-27T21:19:58] v0.1.3(015cadd) partylan\\src\\steam.cpp:269 Session with 76561197783410123 failed
[2025-01-27T21:20:09] v0.1.3(015cadd) partylan\\src\\steam.cpp:261 Accepted session with 76561197279154321
[2025-01-27T21:20:19] v0.1.3(015cadd) partylan\\src\\steam.cpp:269 Session with 76561197279154321 failed
[2025-01-27T21:20:36] v0.1.3(015cadd) partylan\\src\\steam.cpp:261 Accepted session with 76561196841456789
[2025-01-27T21:20:36] v0.1.3(015cadd) partylan\\src\\steam.cpp:269 Session with 76561196841456789 failed
[2025-01-27T21:20:36] v0.1.3(015cadd) partylan\\src\\steam.cpp:261 Accepted session with 76561196841456789
"""


class PartylanLogStatus(Enum):
    """Status type of log entries."""

    ALL = "all"
    ACCEPTED = "accepted"
    FAILED = "failed"


@dataclass
class SteamNetworkManager:
    """Uses partylans logic to compute ip address from SteamID64."""

    steam_id_to_addr: dict = Field(init=False, default={})
    addr_to_steam_id: dict = Field(init=False, default={})
    range = IPv4Network((PARTYLAN_NETWORK_IP, PARTYLAN_NETWORK_MASK), strict=False)

    def compute_addr(self, steam_id: int, offset: int = 0) -> IPv4Address:
        """Compute IP address from SteamID64.

        Partylan uses the CG-NAT ip range '100.64.0.0/10' to map SteamID64 with an IP address.

        Args:
            steam_id (int): SteamID64
            offset (int, optional): if different ids result in the same ip, use offset. Defaults to 0.

        Returns:
            IPv4Address: computed ip address from given SteamID64.

        """
        size = self.range.num_addresses
        mod = (steam_id + offset) % size
        if mod == 0:
            mod = 1
        elif mod == size - 1:
            mod = size - 2
        canonical_addr = int(self.range.network_address) + mod
        return IPv4Address(canonical_addr)

    def assign_addr(self, steam_id: int) -> IPv4Address:
        """Map SteamID64 with computed IP address.

        Args:
            steam_id (int): SteamID64

        Raises:
            RuntimeError: if all addresses are mapped and none are left

        Returns:
            IPv4Address: computed ip address

        """
        if steam_id in self.steam_id_to_addr:
            return self.steam_id_to_addr[steam_id]

        for offset in range(4):
            addr = self.compute_addr(steam_id, offset)
            if addr not in self.addr_to_steam_id:
                self.steam_id_to_addr[steam_id] = addr
                self.addr_to_steam_id[addr] = steam_id
                return addr

        raise RuntimeError(PARTYLAN_COMPUTE_IP_ERROR)


@dataclass
class PartyLan:
    """The class is used to get all ip addresses from partylan logfile."""

    path: str
    logfile: str = Field(init=False)
    addresses: list[IPv4Address] = Field(init=False, default=[])
    steam: SteamNetworkManager = Field(init=False)

    def __post_init__(self) -> None:
        """Load log file after class init."""
        logfile = Path(self.path, PARTYLAN_LOG_FILENAME)
        self.logfile = FileHandler(logfile).read()

    def get_addresses(self, status: PartylanLogStatus) -> list[IPv4Address]:
        """Get all computed ip address from partylan log file.

        Returns:
            list[IPv4Address]: computed ip address from Steam64ID

        """
        parsed_log = CustomParsers.partylan(log_content=self.logfile, status=status)
        steam = SteamNetworkManager()
        addresses = {steam.assign_addr(data.get("steamId")) for data in parsed_log}
        self.addresses = addresses
        self.steam = steam
        return addresses

    def get_interface(self) -> str:
        """Get partylan network interface name.

        Returns:
            str: partylan network interface name

        """
        return PARTYLAN_INTERFACE


class PartyLanLog(TypedDict):
    """Custom parsed dict of partylan log file."""

    build: str
    line: int
    path: Path
    steamId: int
    timestamp: datetime
    version: str


class CustomParsers:
    """Contains custom parser functions for different type of data."""

    @classmethod
    def partylan(cls, log_content: str, status: PartylanLogStatus) -> list[PartyLanLog]:
        """Parse partylan log file to get steamIds.

        Args:
            log_content (str): raw log file data
            status (PartylanLogStatus): the log status which get parsed

        Returns:
            self.parsed_data (dict): parsed log file data

        """
        log = log_content
        cls.parsed_data = []

        patterns: list[re.Pattern] = []
        # [2025-01-27T21:20:09] v0.1.3(015cadd) partylan\src\steam.cpp:261 Accepted session with 76561198068000001
        pat1 = re.compile(
            r"\[(?P<timestamp>\d+-\d+-\d+T\d+:\d+:\d+)\]\sv(?P<version>\d+.\d+.\d)\((?P<build>\S+)\)\s(?P<path>(.*)):(?P<line>\d*)\s(Accepted).+(?P<steamId>\d{17})",
        )

        # [2025-01-29T21:21:53] v0.1.3(015cadd) partylan\src\steam.cpp:269 Session with 76561197983431324 failed
        pat2 = re.compile(
            r"\[(?P<timestamp>\d+-\d+-\d+T\d+:\d+:\d+)\]\sv(?P<version>\d+.\d+.\d)\((?P<build>\S+)\)\s(?P<path>(.*)):(?P<line>\d*)\s(Session).+(?P<steamId>\d{17})",
        )
        if status.value == "all":
            patterns.append(pat1)
            patterns.append(pat2)
        elif status.value == "accepted":
            patterns.append(pat1)
        elif status.value == "failed":
            patterns.append(pat2)

        for line in log.splitlines():
            if line:
                line_strip = line.strip()
            else:
                continue

            matches = [pattern.match(line_strip) for pattern in patterns]

            for match in matches:
                if match:
                    group = match.groupdict()
                    temp_dict = cls._temp_dict(group)
                    cls.parsed_data.append(temp_dict)

        return cls.parsed_data

    @staticmethod
    def _temp_dict(group: dict) -> dict:
        """Get a temporary dict from given values."""
        return {
            "timestamp": datetime.datetime.strptime(group["timestamp"], "%Y-%m-%dT%H:%M:%S").astimezone(datetime.UTC),
            "version": group["version"],
            "build": group["build"],
            "path": Path(group["path"]),
            "line": int(group["line"]),
            "steamId": int(group["steamId"]),
        }


if __name__ == "__main__":
    partylan = PartyLan("D:\\partylan")
    partylan.get_addresses()
    print(partylan.addresses)
