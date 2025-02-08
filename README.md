# GameLink

> Connects players via different networks

GameLink allows you to play games with an LAN modus over a virtual private network.  
You will see hosted games and players in the game lobby, like you would see in the same local area network.

## Supported Platforms

- Windows 11

### Requirements

> [!NOTE]
> In case you have Wireshark installed, you don´t need this library, it ships per default.

This program needs a third-party library to get access to the network interface.

- [Npcap](https://npcap.com/) ([latest version](https://nmap.org/npcap/#download))

## Usage

> [!NOTE]
> All players have to configure and run **gamelink**, in order to play together.

1. Copy `config.json.example` to `config.json` and define the following values:

    - `interface`: your VPN network interface name
    - `player_ips`: your friends VPN IP addresses
    - `path`: the path of your partylan installation to automatically determine the settings [OPTIONAL, NOT RELIABLE]

    ```json
    {
        "vpn": {
            "interface": "PartyLAN Tunnel",
            "player_ips": [
                "100.99.128.189",
                "100.78.131.99"
            ]
        },
        "partylan": {
            "path": "D:\\partylan"
        }
    }
    ```

2. Run `gamelink.exe vpn`

    ```cmd
    2025-01-25 16:12:10 INFO: Start sniffing on 'PartyLAN Tunnel'
    2025-01-25 16:12:10 INFO: Listen to packets with destination: '255.255.255.255' UDP ports: [8086]
    2025-01-25 16:12:10 INFO: Send modified packets to ['100.99.128.189', '100.78.131.99']
    2025-01-25 16:12:10 INFO: Waiting for packets to modify and send
    ```

3. Host a lan game and play with you friends

    > [!IMPORTANT]
    > Make sure your game is using the VPN network interface

### Useful commands

- `gamelink.exe show interface` - list of you network interfaces  
- `gamelink.exe show game` - list of verified games

### Configuration Files

| Filename        | Description                                                                              |
| --------------- | ---------------------------------------------------------------------------------------- |
| `config.json`   | general network settings                                                                 |
| `lan-games.csv` | List of lan games <br/> Needs a value in column *Verified* & *UdpPorts* to use this game |

### Verified Games

If a game is not yet verified in `lan-games.csv`, you have to determine the ports once.  

In this example you see how to get the UDP ports for the game *The Lord of the Rings: Battle for Middle-earth*.  
The game process is named: `lotrbfme.exe` (take a look in the task manager to determine the process name of the game)

1. Start the game
2. Go to the lan multiplayer
3. Execute the following command

```cmd
> gamelink.exe show ports lotrbfme.exe
2025-02-02 21:48:48 INFO: Successfully scanned UDP sockets for process 'lotrbfme.exe' (PID 29148).
2025-02-02 21:48:48 INFO: Monitoring of UDP broadcasts on ports: {8086}
Enter 'exit' or press Ctrl+C to close this program.
2025-02-02 21:48:49 INFO: Broadcast packet detected: Ether / IP / UDP 10.10.1.15:8086 > 255.255.255.255:8086 / Raw
2025-02-02 21:48:49 INFO: Broadcast packet detected: Ether / IP / UDP 10.10.1.15:8086 > 255.255.255.255:8087 / Raw
2025-02-02 21:48:49 INFO: Broadcast packet detected: Ether / IP / UDP 10.10.1.15:8086 > 255.255.255.255:8088 / Raw
2025-02-02 21:48:49 INFO: Broadcast packet detected: Ether / IP / UDP 10.10.1.15:8086 > 255.255.255.255:8089 / Raw
2025-02-02 21:48:49 INFO: Broadcast packet detected: Ether / IP / UDP 10.10.1.15:8086 > 255.255.255.255:8090 / Raw
2025-02-02 21:48:49 INFO: Broadcast packet detected: Ether / IP / UDP 10.10.1.15:8086 > 255.255.255.255:8091 / Raw
2025-02-02 21:48:49 INFO: Broadcast packet detected: Ether / IP / UDP 10.10.1.15:8086 > 255.255.255.255:8092 / Raw
2025-02-02 21:48:49 INFO: Broadcast packet detected: Ether / IP / UDP 10.10.1.15:8086 > 255.255.255.255:8093 / Raw
```

The process `lotrbfme.exe` sends broadcast packets to the ports 8086-8093, but only listen on port 8086.  
The listen port **8086** is the port we are interested, this packets need to reach our friends over VPN.  

Open `resources/lan-games-db/lan-games.csv`:

1. Search for *The Lord of the Rings: Battle for Middle-earth*
2. Set **8086** in column *UdpPorts*
3. Set **Yes** in column *Verified*

## Development

Requirements:

- Python >=3.13
- Python Package Manager ([uv](https://docs.astral.sh/uv/))

### Building executable

```cmd
pyinstaller .\main.py -n gamelink
```

## Recommended "VPN"

[partylan](https://github.com/gyf304/partylan) makes the steam network accessible for older games.  
It creates a windows network adapter for the steam network, this adapter can be used by any game.

## Credits

Ìnspired by other projects:

- [partylan](https://github.com/gyf304/partylan)
- [py-udp-broadcast-forward](https://github.com/nozberkaryaindonesia/py-udp-broadcast-forward)
- [VPNubt](https://github.com/KingKeule/VPNubt)
- [ubrs](https://github.com/lyon-esport/ubrs)
