"""Détection avec inventaires USB simulés ; aucun accès au matériel."""

import sys
import types
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from controller import Controller


def port(device="COM3", vid=0x0483, pid=0x374B, description="", product=None):
    return types.SimpleNamespace(
        device=device, vid=vid, pid=pid,
        description=description, product=product,
    )


class DetectionTest(unittest.TestCase):
    def setUp(self):
        self.view = Mock()
        self.controller = Controller(Mock(), self.view)
        self.list_ports = Mock()
        self.tools = types.SimpleNamespace(list_ports=self.list_ports)
        self.patcher = patch.dict(sys.modules, {"serial.tools": self.tools})
        self.patcher.start()
        self.addCleanup(self.patcher.stop)
        self.addCleanup(self.controller.close)

    def test_stlink_among_unrelated_devices(self):
        self.list_ports.comports.return_value = [
            port("COM1", None, None), port(), port("COM4", 0x0483, 0x5740)
        ]
        self.assertEqual(self.controller.detect_port(), "COM3")
        self.view.set_port.assert_called_once_with("COM3")
        self.assertIsNone(self.controller._serial)

    def test_description_without_identifiers(self):
        self.list_ports.comports.return_value = [
            port("/dev/cu.usbmodem1", None, None, "STM32 ST-Link")
        ]
        self.assertEqual(
            self.controller.detect_port(), "/dev/cu.usbmodem1"
        )

    def test_no_card_preserves_manual_port(self):
        self.list_ports.comports.return_value = [port("COM1", None, None)]
        self.assertIsNone(self.controller.detect_port())
        self.view.set_port.assert_not_called()
        self.assertIn("non détectée", self.view.show_error.call_args.args[0])

    def test_multiple_candidates(self):
        self.list_ports.comports.return_value = [port(), port("COM4")]
        self.assertIsNone(self.controller.detect_port())
        self.view.set_port.assert_not_called()
        self.assertIn("Plusieurs", self.view.show_error.call_args.args[0])

    def test_enumeration_failure(self):
        self.list_ports.comports.side_effect = OSError("USB indisponible")
        self.assertIsNone(self.controller.detect_port())
        self.assertIn("impossible", self.view.show_error.call_args.args[0])

    def test_missing_pyserial(self):
        with patch.dict(sys.modules, {"serial.tools": None}):
            self.assertIsNone(self.controller.detect_port())
        self.assertIn("pyserial", self.view.show_error.call_args.args[0])

    def test_connected_skips_detection(self):
        self.controller._serial = Mock()
        self.assertIsNone(self.controller.detect_port())
        self.list_ports.comports.assert_not_called()


if __name__ == "__main__":
    unittest.main()
