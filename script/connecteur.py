"""Connexion du moniteur au relais TCP de la Raspberry ou à un port local."""

import socket
from urllib.parse import urlsplit


DEFAULT_ENDPOINT = "tcp://192.168.1.14:8081"


class TcpConnection:
    """Adapte le flux TCP à l'interface read/close du lecteur existant."""

    def __init__(self, endpoint, timeout):
        address = urlsplit(endpoint)
        if (address.scheme != "tcp" or not address.hostname
                or address.port is None or address.path
                or address.query or address.fragment or address.username):
            raise ValueError("Adresse attendue : tcp://hôte:port")
        self.socket = socket.create_connection(
            (address.hostname, address.port), timeout=2.0
        )
        self.socket.settimeout(timeout)

    def read(self, size):
        """Un délai expiré est normal ; une fermeture TCP est une erreur."""
        try:
            data = self.socket.recv(size)
        except socket.timeout:
            return b""
        if not data:
            raise OSError("Le serveur TCP a fermé la connexion.")
        return data

    def close(self):
        self.socket.close()


def open_connection(endpoint, baudrate=115200, timeout=0.1):
    """Le débit ne s'applique qu'aux connexions série locales."""
    endpoint = endpoint.strip()
    if endpoint.startswith("tcp://"):
        return TcpConnection(endpoint, timeout)
    if "://" in endpoint:
        raise ValueError("Protocole attendu : tcp://")
    import serial

    return serial.Serial(port=endpoint, baudrate=baudrate, timeout=timeout)
