"""Relais bidirectionnel avec une interface série simulée par socket."""

import socket
import sys
import threading
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import serial
from serial_bridge import serve


class SerialSocket:
    def __init__(self, stream):
        self.stream = stream
        self.in_waiting = 1

    def fileno(self):
        return self.stream.fileno()

    def read(self, size):
        return self.stream.recv(size)

    def write(self, data):
        self.stream.sendall(data)


class BridgeTest(unittest.TestCase):
    def test_bidirectional_and_single_client(self):
        with socket.socket() as listener:
            listener.bind(('127.0.0.1', 0))
            listener.listen(1)
            device, hardware = socket.socketpair()
            self.addCleanup(device.close)
            self.addCleanup(hardware.close)
            hardware.settimeout(2)
            failures = []

            def run():
                try:
                    serve(listener, SerialSocket(device))
                except serial.SerialException:
                    pass  # Fermeture du matériel simulé en fin de test.
                except Exception as error:
                    failures.append(error)

            worker = threading.Thread(target=run, daemon=True)
            worker.start()
            try:
                for _ in range(2):
                    with socket.create_connection(listener.getsockname()) as client:
                        client.settimeout(2)
                        client.sendall(b'commande\n')
                        self.assertEqual(hardware.recv(64), b'commande\n')
                        hardware.sendall(b'mesure\n')
                        received = bytearray()
                        while not received.endswith(b'\n'):
                            chunk = client.recv(64)
                            self.assertTrue(chunk)
                            received.extend(chunk)
                        self.assertEqual(received, b'mesure\n')
                        with socket.create_connection(listener.getsockname()) as other:
                            other.settimeout(2)
                            self.assertEqual(other.recv(1), b'')
                    # Attendre que le relais traite la fermeture du client.
                    import time
                    time.sleep(0.05)
            finally:
                hardware.close()
                worker.join(2)
            self.assertFalse(worker.is_alive())
            self.assertEqual(failures, [])
