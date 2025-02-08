"""Packethandler sniff, modify and send packets."""

import sys
from ipaddress import IPv4Address

from pydantic import Field
from pydantic.dataclasses import dataclass
from scapy.all import UDP, AsyncSniffer, Packet, Raw, send
from scapy.layers.inet import IP

from .loghandler import modify_scapy_log, setup_logger

modify_scapy_log()
logger = setup_logger(__name__)


# done: debug flag in debug logging umbauen und dann löschen
# done: in start() den while-Teil in eigene Funktion auslagern


@dataclass
class PacketHandler:
    """Sniff, modify and send packets."""

    interface: str
    old_dest: IPv4Address
    ports: list[int]
    new_dests: list[IPv4Address]
    _sniff_init: bool = Field(init=False)
    _filter: str = Field(init=False)

    def __post_init__(self) -> None:
        """Set attributes after initilization."""
        self._filter = f"udp and host {self.old_dest}"
        self._sniff_init = False

    def _send_packets(self, pkts: list[IP]) -> None:
        """Send the packets."""
        # send() only layer3 packets, not layer2 frame with encapsulated IP packets
        try:
            send(pkts, verbose=False)
        except Exception:
            logger.error("An unexpected error occurred while sending the packages.")  # noqa: TRY400
            sys.exit(1)
        else:
            logger.info(f"Sent {len(pkts)} packets.")
            logger.debug(
                f"Captured original packet src: {pkts[0][IP].src}:{pkts[0][UDP].sport} -> dst: {self.old_dest}:{pkts[0][UDP].dport}",
            )
            for pkt in pkts:
                logger.debug(
                    f"Sent modified packet {'src':>7}: {pkt[IP].src}:{pkt[UDP].sport} -> dst: {pkt[IP].dst}:{pkt[UDP].dport}",
                )

    def _build_packet(self, pkt: Packet, newdest: str) -> IP:
        """Build a new/modified packet and only use some information.

        Args:
            pkt (Packet): scapy network packet
            newdest (str): new destination IP address

        Returns:
            IP: new scapy network packet

        """
        return IP(src=pkt[IP].src, dst=newdest) / UDP(sport=pkt[UDP].sport, dport=pkt[UDP].dport) / Raw(load=pkt[Raw].load)

    def _modify_packet(self, pkt: Packet | IP) -> None:
        """If packet matches upd port, modify it and send to new destination."""
        # filter packet for UDP port
        if pkt[UDP].dport in self.ports:
            # create empty list for modified packets
            modified_pkts = []
            for newdest in self.new_dests:
                # build packet with same payload but new destination ip
                modified_pkt = self._build_packet(pkt, str(newdest))
                # collect modified IP packet
                modified_pkts.append(modified_pkt)
            # send all modified packets
            self._send_packets(modified_pkts)

    def _set_sniffer_init(self) -> None:
        """Get the status from the sniffer thread."""
        self._sniff_init = True

    def _exit(self) -> None:
        logger.info("Program terminated by user.")
        sys.exit(0)

    def _init_log(self) -> None:
        """Init log about the configuration."""
        logger.info(f"Start sniffing on '{self.interface}'")
        logger.info(f"Listen to packets with destination: '{self.old_dest}' UDP ports: {self.ports}")
        logger.info(f"Send modified packets to {[str(ip) for ip in self.new_dests]}")
        logger.info("Waiting for packets to modify and send")

    def _intercept_sniff_exception(self, sniff: AsyncSniffer) -> None:
        """Intercept exception from sniffer thread.

        i.e. config.json has wrong network interface defined and sniffer cant initialize.
        """
        while sniff.exception is None and self._sniff_init is False:
            if sniff.exception is not None:
                logger.error(sniff.exception)
                sys.exit(1)

    def _wait_user_input(self, sniff: AsyncSniffer) -> None:
        """Wait for user input to stop sniff and exit the program."""
        user_input = None
        try:
            while user_input != "exit":
                self._intercept_sniff_exception(sniff)
                user_input = input("")
                if user_input == "exit":
                    sniff.stop()
                    self._exit()
                else:
                    print("Enter 'exit' or press Ctrl+C to close this program.")
        except KeyboardInterrupt:
            sniff.stop()
            self._exit()

    def start(self) -> None:
        """Start the sniffer to copy, modify and send the packets."""
        # thread (async) to keep the cli responseable
        sniff = AsyncSniffer(
            iface=self.interface,
            prn=self._modify_packet,
            filter=self._filter,
            store=0,
            started_callback=self._set_sniffer_init,
        )
        sniff.start()
        self._init_log()
        self._wait_user_input(sniff)


if __name__ == "__main__":
    ph = PacketHandler(
        interface="Realtek Gaming 2.5GbE Family Controller",
        old_dest=IPv4Address("255.255.255.255"),
        ports=[8086],
        new_dests=[IPv4Address("10.0.10.1")],
        debug=False,
    )
    ph.start()
