"""Décodage de version et reconnexion, sans matériel."""

import sys
import types
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from controller import Controller
from model import Model


class FirmwareVersionTest(unittest.TestCase):
    def test_version_preserves_measurement_state(self):
        model = Model()
        model.add_message('Mesures en pause')
        model.add_message('Firmware STM32 : 1.2.3\r\n')
        self.assertEqual(model.firmware_version, '1.2.3')
        self.assertTrue(model.paused)
        self.assertIsNone(model.latest_measurement)
        model.add_message('Firmware STM32 : invalide')
        self.assertEqual(model.firmware_version, '1.2.3')
        self.assertIn('invalide', model.messages[-1].text)
        model.add_message('Firmware STM32 : 2.0.0')
        self.assertEqual(model.firmware_version, '2.0.0')
        model.clear()
        self.assertIsNone(model.firmware_version)

    def test_old_firmware_remains_supported(self):
        model = Model()
        model.add_message('Temperature STM32 : 28 C | VDDA : 3300 mV')
        self.assertIsNone(model.firmware_version)
        self.assertEqual(model.latest_measurement.temperature_c, 28)

    def test_reconnect_discards_previous_version(self):
        model = Model()
        model.add_message('Firmware STM32 : 1.0.0')
        controller = Controller(model, Mock())
        serial = types.SimpleNamespace(Serial=Mock(), SerialException=OSError)
        with patch.dict(sys.modules, {'serial': serial}):
            with patch('controller.Thread'):
                self.assertTrue(controller.connect('STUB'))
                self.assertIsNone(model.firmware_version)
                controller.close()


if __name__ == '__main__':
    unittest.main()
