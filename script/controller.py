"""Coordination MVC du moniteur série de la Nucleo.

Dépendance pour la connexion : pyserial.
La vue fournit after()/after_cancel() (comme Tkinter), render(model),
set_connected(bool) et show_error(message). Le modèle fournit
add_message(message). Les méthodes publiques sont appelées depuis le thread
principal de l'interface ; seul le lecteur série s'exécute en arrière-plan.
"""

from queue import Empty, Full, Queue
from threading import Event, Thread
from typing import Any, Optional, Protocol


DEFAULT_BAUDRATE = 115200
DEFAULT_REFRESH_MS = 100
SERIAL_TIMEOUT_SECONDS = 0.1
QUEUE_CAPACITY = 1000
MAX_EVENTS_PER_REFRESH = 200
MAX_LINE_BYTES = 65536
STLINK_VENDOR_ID = 0x0483
STLINK_PRODUCT_IDS = {0x374B, 0x374E, 0x374F, 0x3752, 0x3753, 0x3754}


class Model(Protocol):
    """Interface attendue du futur modèle."""

    def add_message(self, message: str) -> None:
        ...

    def reset_firmware_version(self) -> None:
        ...


class View(Protocol):
    """Interface attendue de la future vue."""

    def after(self, delay_ms: int, callback: Any) -> Any:
        ...

    def after_cancel(self, callback_id: Any) -> None:
        ...

    def render(self, model: Model) -> None:
        ...

    def set_connected(self, connected: bool) -> None:
        ...

    def show_error(self, message: str) -> None:
        ...

    def set_port(self, port: str) -> None:
        ...


class Controller:
    """Lit les lignes série et actualise la vue à intervalle configurable."""

    def __init__(
        self,
        model: Model,
        view: View,
        refresh_ms: int = DEFAULT_REFRESH_MS,
    ) -> None:
        self._validate_refresh(refresh_ms)
        self.model = model
        self.view = view
        self._refresh_ms = refresh_ms
        self._events = Queue(maxsize=QUEUE_CAPACITY)
        self._stop = Event()
        self._serial = None
        self._reader: Optional[Thread] = None
        self._closed = False
        self._after_id = None
        self.view.set_connected(False)
        self._schedule_refresh()

    @staticmethod
    def _validate_refresh(refresh_ms: int) -> None:
        if isinstance(refresh_ms, bool) or not isinstance(refresh_ms, int):
            raise ValueError(
                "Le délai de rafraîchissement doit être un entier."
            )
        if refresh_ms <= 0:
            raise ValueError("Le délai de rafraîchissement doit être positif.")

    def set_refresh_interval(self, refresh_ms: int) -> None:
        """Change le délai entre deux actualisations, en millisecondes."""
        self._validate_refresh(refresh_ms)
        self._refresh_ms = refresh_ms
        if not self._closed:
            if self._after_id is not None:
                self.view.after_cancel(self._after_id)
            self._schedule_refresh()

    def detect_port(self) -> Optional[str]:
        """Identifie le ST-LINK sans ouvrir de port ni connecter la carte."""
        if self._closed or self._serial is not None:
            return None
        try:
            from serial.tools import list_ports
        except ImportError:
            self.view.show_error("Installer pyserial pour détecter la Nucleo.")
            return None
        try:
            ports = list_ports.comports()
        except OSError as error:
            self.view.show_error(f"Détection des ports impossible : {error}")
            return None

        candidates = set()
        for port in ports:
            description = " ".join(
                value or "" for value in (port.description, port.product)
            ).upper().replace("-", "").replace(" ", "")
            identified = (
                port.vid == STLINK_VENDOR_ID
                and port.pid in STLINK_PRODUCT_IDS
            )
            if identified or "STLINK" in description:
                candidates.add(port.device)

        if len(candidates) == 1:
            device = candidates.pop()
            self.view.set_port(device)
            self.view.show_error("")
            return device
        if not candidates:
            self.view.show_error(
                "Nucleo non détectée : brancher la carte puis cliquer sur "
                "Détecter, ou saisir le port manuellement."
            )
        else:
            self.view.show_error(
                "Plusieurs ports ST-LINK détectés : saisir le port souhaité."
            )
        return None

    def connect(self, port: str, baudrate: int = DEFAULT_BAUDRATE) -> bool:
        """Ouvre un port explicite, par exemple /dev/cu.usbmodem… ou COM3."""
        if self._closed:
            raise RuntimeError("Le contrôleur est fermé.")
        if self._serial is not None:
            self.view.show_error(
                "Déconnecter le port actuel avant de changer."
            )
            return False
        if not port.strip() or baudrate <= 0:
            self.view.show_error(
                "Le port et le débit série doivent être valides."
            )
            return False

        # Import différé : le module reste importable sans pyserial installé.
        try:
            import serial
        except ImportError:
            self.view.show_error(
                "Installer pyserial pour ouvrir le port série."
            )
            return False

        try:
            self._serial = serial.Serial(
                port=port,
                baudrate=baudrate,
                timeout=SERIAL_TIMEOUT_SECONDS,
            )
        except (serial.SerialException, OSError, ValueError) as error:
            self.view.show_error(
                f"Impossible d'ouvrir le port série : {error}"
            )
            return False

        self.model.reset_firmware_version()
        self.view.render(self.model)
        self._stop.clear()
        self._reader = Thread(target=self._read_serial, daemon=True)
        self._reader.start()
        self.view.set_connected(True)
        return True

    def _enqueue(self, kind: str, message: str) -> None:
        # Une file bornée évite une croissance mémoire illimitée.
        while not self._stop.is_set():
            try:
                self._events.put(
                    (kind, message), timeout=SERIAL_TIMEOUT_SECONDS
                )
                return
            except Full:
                continue

    def _read_serial(self) -> None:
        """Ne touche jamais au modèle ni aux widgets depuis ce thread."""
        import serial

        pending = bytearray()
        try:
            while not self._stop.is_set():
                chunk = self._serial.read(1)
                if not chunk:
                    continue
                if chunk == b"\n":
                    message = pending.rstrip(b"\r").decode(
                        "utf-8", errors="replace"
                    )
                    self._enqueue("message", message)
                    pending.clear()
                else:
                    pending.extend(chunk)
                    if len(pending) > MAX_LINE_BYTES:
                        self._enqueue("error", "Ligne série trop longue.")
                        return
        except (serial.SerialException, OSError) as error:
            self._enqueue("error", f"Connexion série interrompue : {error}")

    def _schedule_refresh(self) -> None:
        self._after_id = self.view.after(self._refresh_ms, self._refresh)

    def _refresh(self) -> None:
        self._after_id = None
        if self._closed:
            return
        changed = self._consume_events()
        if changed:
            self.view.render(self.model)
        self._schedule_refresh()

    def _consume_events(self) -> bool:
        changed = False
        # Limiter le travail d'un rafraîchissement pour garder la vue réactive.
        for _ in range(MAX_EVENTS_PER_REFRESH):
            try:
                kind, message = self._events.get_nowait()
            except Empty:
                break
            if kind == "message":
                self.model.add_message(message)
                changed = True
            else:
                self.disconnect()
                self.view.show_error(message)
                break
        return changed

    def disconnect(self) -> None:
        """Arrête le lecteur avant de fermer le port (attente <= timeout)."""
        self._stop.set()
        if self._reader is not None:
            self._reader.join()
            self._reader = None
        if self._serial is not None:
            try:
                self._serial.close()
            except OSError as error:
                self.view.show_error(f"Erreur de fermeture du port : {error}")
            finally:
                self._serial = None
        # Conserver les lignes complètes reçues avant la déconnexion.
        changed = False
        while True:
            try:
                kind, message = self._events.get_nowait()
            except Empty:
                break
            if kind == "message":
                self.model.add_message(message)
                changed = True
        if changed and not self._closed:
            self.view.render(self.model)
        self.view.set_connected(False)

    def close(self) -> None:
        """À appeler avant de détruire la fenêtre graphique."""
        if self._closed:
            return
        self._closed = True
        if self._after_id is not None:
            self.view.after_cancel(self._after_id)
            self._after_id = None
        self.disconnect()
