"""Show Network Interfaces."""

from scapy.all import get_working_ifaces

# import socket  # noqa: ERA001
# print(socket.if_nameindex())  # noqa: ERA001


def get_interfaces() -> list[str]:
    """Get a list of your network interfaces."""
    intfs = get_working_ifaces()
    return [intf.description for intf in intfs]


if __name__ == "__main__":
    print(get_interfaces())
