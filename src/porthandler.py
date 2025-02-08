import asyncio
import sys
from collections.abc import Callable

import psutil
from scapy.all import AsyncSniffer, Packet

from .loghandler import modify_scapy_log, setup_logger

modify_scapy_log()
logger = setup_logger(__name__)


def get_udp_ports(process_name: str) -> set[int]:
    """Return the local UDP ports of the specified process."""
    udp_ports = set()
    for proc in psutil.process_iter(attrs=["pid", "name"]):
        if proc.info["name"] and process_name.lower() in proc.info["name"].lower():
            try:
                pid = proc.info["pid"]
                process = psutil.Process(pid)
                connections = process.net_connections(kind="udp")
                udp_ports.update(conn.laddr.port for conn in connections if conn.laddr)
            except (psutil.AccessDenied, psutil.NoSuchProcess):
                logger.warning(f"Access denied or process no longer available: {process_name}")
            else:
                logger.info(f"Successfully scanned UDP sockets for process '{process_name}' (PID {pid}).")
    return udp_ports


def _packet_callback_factory(udp_ports: set[int]) -> Callable:
    """Create a callback function that is only executed for certain UDP ports."""

    def _packet_callback(packet: Packet) -> None:
        if packet.haslayer("IP") and packet.haslayer("UDP"):  # noqa: SIM102
            if packet["IP"].dst == "255.255.255.255" and packet["UDP"].sport in udp_ports:
                logger.info(f"Broadcast packet detected: {packet.summary()}")

    return _packet_callback


async def monitor_broadcasts(process_name: str) -> None:
    udp_ports = get_udp_ports(process_name)
    if not udp_ports:
        logger.warning(f"No open UDP sockets found for '{process_name}'.")
        return

    logger.info(f"Monitoring of UDP broadcasts on ports: {udp_ports}")

    sniffer = AsyncSniffer(filter="udp and dst host 255.255.255.255", prn=_packet_callback_factory(udp_ports), store=False)
    sniffer.start()

    try:
        while True:
            user_input = await asyncio.to_thread(input, "Enter 'exit' or press Ctrl+C to close this program.\n")
            if user_input.strip().lower() == "exit":
                break
    except (KeyboardInterrupt, asyncio.exceptions.CancelledError):
        logger.info("Program terminated by user.")
    finally:
        sniffer.stop()
        logger.info("Sniffer stopped.")
        sys.exit(0)


def run_monitor_broadcasts(process_name: str) -> None:
    asyncio.run(monitor_broadcasts(process_name))


if __name__ == "__main__":
    process_name = "UT2004.exe"  # Ersetze mit deinem Prozessnamen
    asyncio.run(monitor_broadcasts(process_name))
