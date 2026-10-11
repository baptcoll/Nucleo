"""Relais TCP/série transparent, réservé à un client sur le réseau local."""

import argparse
import logging
import selectors
import socket

import serial
from serial.tools import list_ports


LOGGER = logging.getLogger(__name__)


def detect_port():
    """Exige une unique interface ST-LINK si aucun port n'est indiqué."""
    candidates = []
    for port in list_ports.comports():
        description = f"{port.description} {port.product}".upper()
        if "STLINK" in description.replace("-", "").replace(" ", ""):
            candidates.append(port.device)
    if len(candidates) != 1:
        raise ValueError(
            f"{len(candidates)} ports ST-LINK détectés ; préciser --serial-port"
        )
    return candidates[0]


def serve(listener, device):
    """Transmet les octets et refuse les clients supplémentaires.

    La série est vidée même sans client : aucun historique ne s'accumule.
    Les délais d'écriture bornés libèrent un client qui ne lit plus.
    """
    client = None
    with selectors.DefaultSelector() as selector:
        selector.register(listener, selectors.EVENT_READ)
        selector.register(device, selectors.EVENT_READ)
        try:
            while True:
                for key, _ in selector.select():
                    if key.fileobj is listener:
                        incoming, address = listener.accept()
                        if client is not None:
                            incoming.close()
                            LOGGER.info("Client supplémentaire refusé : %s", address)
                        else:
                            client = incoming
                            client.settimeout(1.0)
                            selector.register(client, selectors.EVENT_READ)
                            LOGGER.info("Client connecté : %s", address)
                    elif key.fileobj is device:
                        data = device.read(max(1, min(device.in_waiting, 4096)))
                        if not data:
                            raise serial.SerialException("Port série déconnecté")
                        if client is not None:
                            try:
                                client.sendall(data)
                            except OSError:
                                selector.unregister(client)
                                client.close()
                                client = None
                                LOGGER.info("Client déconnecté")
                    elif key.fileobj is client:
                        try:
                            data = client.recv(4096)
                        except OSError:
                            data = b""
                        if data:
                            device.write(data)
                        else:
                            selector.unregister(client)
                            client.close()
                            client = None
                            LOGGER.info("Client déconnecté")
        finally:
            if client is not None:
                client.close()


def main():
    """Ouvre le ST-LINK à 115200 bauds et écoute sur le port 8081."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--host", default="0.0.0.0")
    parser.add_argument("--port", type=int, default=8081)
    parser.add_argument("--serial-port")
    parser.add_argument("--baudrate", type=int, default=115200)
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")
    try:
        port = args.serial_port or detect_port()
        with serial.Serial(port, args.baudrate, timeout=0.1,
                           write_timeout=1.0, exclusive=True) as device:
            with socket.socket() as listener:
                listener.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                listener.bind((args.host, args.port))
                listener.listen(1)
                LOGGER.info("Relais %s:%s -> %s (%s bauds)",
                            args.host, args.port, port, args.baudrate)
                serve(listener, device)
    except (OSError, ValueError, serial.SerialException):
        LOGGER.exception("Arrêt du relais")
        raise SystemExit(1)
    except KeyboardInterrupt:
        LOGGER.info("Arrêt demandé")


if __name__ == "__main__":
    main()
