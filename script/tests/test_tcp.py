"""Transport TCP réel sur boucle locale, sans Nucleo ni interface graphique."""

import socket
import sys
import time
import unittest
from pathlib import Path
from unittest.mock import Mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from connecteur import TcpConnection
from controller import Controller
from model import Model


class TcpTest(unittest.TestCase):
    def setUp(self):
        self.listener = socket.socket()
        self.listener.bind(('127.0.0.1', 0))
        self.listener.listen(1)
        self.listener.settimeout(2)
        self.addCleanup(self.listener.close)
        self.endpoint = f'tcp://127.0.0.1:{self.listener.getsockname()[1]}'

    def test_timeout_and_eof(self):
        connection = TcpConnection(self.endpoint, 0.01)
        self.addCleanup(connection.close)
        peer, _ = self.listener.accept()
        self.addCleanup(peer.close)
        self.assertEqual(connection.read(1), b'')
        peer.sendall(b'abc')
        self.assertEqual(connection.read(3), b'abc')
        peer.close()
        with self.assertRaises(OSError):
            connection.read(1)

    def test_controller_fragmentation_disconnect_and_reconnect(self):
        model, view = Model(), Mock()
        controller = Controller(model, view)
        self.addCleanup(controller.close)
        for _ in range(2):
            self.assertTrue(controller.connect(self.endpoint))
            self.assertIsNone(model.firmware_version)
            peer, _ = self.listener.accept()
            self.addCleanup(peer.close)
            peer.sendall(b'Firmware STM')
            peer.sendall(b'32 : 1.0.0\r\nTemperature STM32 : 28 C')
            peer.sendall(b' | VDDA : 3300 mV\r\n')
            deadline = time.monotonic() + 2
            while model.firmware_version is None:
                controller._consume_events()
                self.assertLess(time.monotonic(), deadline)
                time.sleep(0.01)
            peer.close()
            while controller._serial is not None:
                controller._consume_events()
                self.assertLess(time.monotonic(), deadline)
                time.sleep(0.01)
            self.assertEqual(model.latest_measurement.temperature_c, 28)
            self.assertIn('interrompue', view.show_error.call_args.args[0])

    def test_invalid_endpoints(self):
        for endpoint in ('tcp://localhost', 'tcp://localhost:99999',
                         'tcp://localhost:8081/path'):
            with self.subTest(endpoint=endpoint), self.assertRaises(ValueError):
                TcpConnection(endpoint, 0.1)


if __name__ == '__main__':
    unittest.main()
