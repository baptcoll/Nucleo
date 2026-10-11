"""Données du moniteur, indépendantes du port série et de l'interface.

Le contrôleur appelle add_message() depuis le thread de l'interface.
La future vue peut lire messages, measurements, latest_measurement et paused.
Les historiques sont bornés ; leurs propriétés renvoient des copies immuables.
"""

import re
from collections import deque
from dataclasses import dataclass
from datetime import datetime
from typing import Deque, Optional, Tuple


DEFAULT_HISTORY_LIMIT = 1000
MEASUREMENT_PATTERN = re.compile(
    r"Temperature STM32 : (?P<temperature>-?\d+) C"
    r" \| VDDA : (?P<supply>\d+) mV"
)
FIRMWARE_PATTERN = re.compile(r"Firmware STM32 : ([0-9]+\.[0-9]+\.[0-9]+)")
PAUSE_MESSAGE = "Mesures en pause"
RESUME_MESSAGE = "Reprise des mesures"


@dataclass(frozen=True)
class Message:
    """Ligne reçue, horodatée à son ajout dans le modèle."""

    timestamp: datetime
    text: str


@dataclass(frozen=True)
class Measurement:
    """Mesure décodée, avec les unités utilisées par le firmware."""

    timestamp: datetime
    temperature_c: int
    supply_mv: int


class Model:
    """Conserve les messages bruts et les dernières données de la Nucleo."""

    def __init__(self, history_limit: int = DEFAULT_HISTORY_LIMIT) -> None:
        if (
            isinstance(history_limit, bool)
            or not isinstance(history_limit, int)
        ):
            raise ValueError("La taille de l'historique doit être un entier.")
        if history_limit <= 0:
            raise ValueError("La taille de l'historique doit être positive.")

        self._messages: Deque[Message] = deque(maxlen=history_limit)
        self._measurements: Deque[Measurement] = deque(maxlen=history_limit)
        self._paused: Optional[bool] = None
        self._message_count = 0
        self._firmware_version: Optional[str] = None

    @property
    def firmware_version(self) -> Optional[str]:
        """Version annoncée par la carte, inconnue avant réception."""
        return self._firmware_version

    def reset_firmware_version(self) -> None:
        """Oublie la version précédente au début d'une nouvelle connexion."""
        self._firmware_version = None

    @property
    def messages(self) -> Tuple[Message, ...]:
        """Messages conservés, du plus ancien au plus récent."""
        return tuple(self._messages)

    @property
    def measurements(self) -> Tuple[Measurement, ...]:
        """Mesures conservées, de la plus ancienne à la plus récente."""
        return tuple(self._measurements)

    @property
    def latest_measurement(self) -> Optional[Measurement]:
        """Dernière mesure valide, ou None avant la première réception."""
        return self._measurements[-1] if self._measurements else None

    @property
    def paused(self) -> Optional[bool]:
        """Dernier état connu des mesures ; None signifie encore inconnu."""
        return self._paused

    @property
    def message_count(self) -> int:
        """Nombre de messages ajoutés depuis la dernière remise à zéro."""
        return self._message_count

    def add_message(self, message: str) -> None:
        """Ajoute une ligne et décode les formats émis par le firmware.

        Les messages inconnus ou malformés restent dans l'historique brut,
        sans remplacer la dernière mesure valide. L'horodatage correspond
        au traitement par le contrôleur, pas à l'instant de mesure embarqué.
        """
        if not isinstance(message, str):
            raise TypeError("Un message doit être une chaîne de caractères.")

        text = message.rstrip("\r\n")
        timestamp = datetime.now().astimezone()
        self._messages.append(Message(timestamp=timestamp, text=text))
        self._message_count += 1

        firmware = FIRMWARE_PATTERN.fullmatch(text)
        if firmware is not None:
            self._firmware_version = firmware.group(1)
            return

        match = MEASUREMENT_PATTERN.fullmatch(text)
        if match is not None:
            try:
                temperature = int(match.group("temperature"))
                supply = int(match.group("supply"))
            except ValueError:
                # Une valeur excessive reste consultable comme texte brut.
                return
            self._measurements.append(
                Measurement(
                    timestamp=timestamp,
                    temperature_c=temperature,
                    supply_mv=supply,
                )
            )
            self._paused = False
        elif text == PAUSE_MESSAGE:
            self._paused = True
        elif text == RESUME_MESSAGE:
            self._paused = False

    def clear(self) -> None:
        """Vide les historiques, le compteur et l'état des mesures."""
        self.reset_firmware_version()
        self._messages.clear()
        self._measurements.clear()
        self._paused = None
        self._message_count = 0
