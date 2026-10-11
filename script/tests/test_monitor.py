"""Tests MVC avec Tkinter et bouchon série, sans accès à la Nucleo.

Exécution : python3 -m unittest discover -s script/tests -v
Une session graphique est nécessaire pour Tkinter.
"""

import os
import subprocess
import sys
import time
import types
import unittest
from functools import wraps
from pathlib import Path
from queue import Empty, Queue
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import monitor
from view import View


def isolated_window(test_method):
    """Une application Tk par processus pour le backend natif macOS."""
    @wraps(test_method)
    def run(self):
        """Exécute le test dans un processus dédié ou dans le processus enfant."""
        if os.environ.get("NUCLEO_GUI_TEST_CHILD") == "1":
            return test_method(self)
        environment = dict(os.environ, NUCLEO_GUI_TEST_CHILD="1")
        result = subprocess.run(
            [sys.executable, "-B", str(Path(__file__).resolve()),
             f"MonitorTest.{test_method.__name__}"],
            env=environment, capture_output=True, text=True, timeout=15,
        )
        self.assertEqual(
            result.returncode, 0, result.stdout + result.stderr
        )
    return run


class SerialStub:
    """Remplace intégralement le port physique par une file en mémoire."""

    instances = []

    def __init__(self, port, baudrate, timeout):
        """Mémorise les paramètres du port simulé et crée sa file de réception."""
        self.port = port
        self.baudrate = baudrate
        self.timeout = timeout
        self.closed = False
        self.data = Queue()
        self.instances.append(self)

    def read(self, size):
        """Lit un octet simulé ou renvoie une chaîne vide à expiration.

        Le paramètre size est ignoré : le lecteur du moniteur demande un octet.
        """
        try:
            return self.data.get(timeout=self.timeout)
        except Empty:
            return b""

    def feed(self, message):
        """Injecte les octets d’un message dans la file de réception."""
        for byte in message:
            self.data.put(bytes([byte]))

    def close(self):
        """Marque le port simulé comme fermé."""
        self.closed = True


class MonitorTest(unittest.TestCase):
    def setUp(self):
        """Prépare les doublures série et l’inventaire USB pour chaque test."""
        SerialStub.instances = []
        self.serial = types.SimpleNamespace(
            Serial=SerialStub, SerialException=OSError
        )
        port = types.SimpleNamespace(
            device="NUCLEO_STUB", vid=0x0483, pid=0x374B,
            description="ST-LINK", product="STM32 STLink"
        )
        self.serial_tools = types.SimpleNamespace(
            list_ports=types.SimpleNamespace(comports=lambda: [port])
        )

    @isolated_window
    def test_reception_and_window_close(self):
        """Vérifie l’affichage des messages et le nettoyage à la fermeture."""
        failures = []
        windows = []
        test = self

        class TestView(View):
            def __init__(self):
                """Crée et mémorise la fenêtre dont le nettoyage sera vérifié."""
                super().__init__()
                windows.append(self)

            def mainloop(self):
                # Exercer les vrais widgets avec un port fictif.
                """Injecte des mesures, vérifie les widgets puis ferme la fenêtre."""
                try:
                    test.assertEqual(SerialStub.instances, [])
                    test.assertEqual(self._temperature.get(), "— °C")
                    test.assertEqual(self._port.get(), "tcp://192.168.1.14:8081")
                    self._port.set("NUCLEO_STUB")
                    test.assertEqual(self._port.get(), "NUCLEO_STUB")
                    self._on_connection()
                    port = SerialStub.instances[0]
                    test.assertEqual(port.baudrate, 115200)
                    port.feed(
                        b"Firmware STM32 : 1.0.0\r\n"
                        b"Temperature STM32 : 28 C | VDDA : 3300 mV\r\n"
                        b"Mesures en pause\r\n"
                    )
                    deadline = time.monotonic() + 3
                    while self._controller.model.message_count < 3:
                        if time.monotonic() >= deadline:
                            test.fail(
                                "Les messages simulés ne sont pas reçus."
                            )
                        self.update()
                        time.sleep(0.01)
                    test.assertEqual(
                        self._firmware.get(), "Firmware : 1.0.0"
                    )
                    test.assertEqual(self._temperature.get(), "28 °C")
                    test.assertEqual(self._supply.get(), "3300 mV")
                    test.assertEqual(
                        self._measurement_state.get(), "En pause"
                    )
                    test.assertIn(
                        "Mesures en pause", self._messages.get("1.0", "end")
                    )
                except Exception as error:
                    failures.append(error)
                finally:
                    self._on_close()

        with patch.dict(sys.modules, {
            "serial": self.serial, "serial.tools": self.serial_tools
        }):
            with patch.object(monitor, "View", TestView):
                monitor.main()
        if failures:
            raise failures[0]
        self.assertTrue(SerialStub.instances[0].closed)
        self.assertIsNone(windows[0]._controller._reader)
        self.assertIsNone(windows[0]._controller._after_id)

    @isolated_window
    def test_keyboard_interrupt_cleanup(self):
        """Vérifie la libération du lecteur et des rappels après Ctrl+C."""
        windows = []

        class InterruptedView(View):
            def __init__(self):
                """Crée et mémorise la fenêtre interrompue pendant le test."""
                super().__init__()
                windows.append(self)

            def mainloop(self):
                """Ouvre le port simulé puis déclenche une interruption clavier."""
                self._port.set("NUCLEO_STUB")
                self._on_connection()
                raise KeyboardInterrupt

        with patch.dict(sys.modules, {
            "serial": self.serial, "serial.tools": self.serial_tools
        }):
            with patch.object(monitor, "View", InterruptedView):
                monitor.main()
        self.assertTrue(SerialStub.instances[0].closed)
        self.assertIsNone(windows[0]._controller._reader)
        self.assertIsNone(windows[0]._controller._after_id)


if __name__ == "__main__":
    unittest.main()
