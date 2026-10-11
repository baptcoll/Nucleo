"""Vue Tkinter du moniteur série, sans accès direct au port série.

Assemblage prévu dans monitor.py : créer Model et View, puis Controller,
appeler view.bind_controller(controller), view.render(model) et mainloop().
Toutes les méthodes de la vue doivent être appelées dans le thread principal.
"""

import tkinter as tk
from tkinter import ttk
from tkinter.scrolledtext import ScrolledText
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from controller import Controller
    from model import Model


class View(tk.Tk):
    """Affiche les données et transmet les actions au contrôleur."""

    def __init__(self) -> None:
        super().__init__()
        self.title("Moniteur Nucleo")
        self.geometry("900x620")
        self.minsize(700, 480)
        self._controller: Optional["Controller"] = None
        self._connected = False
        self._closing = False
        self._port = tk.StringVar(self)
        self._baudrate = tk.StringVar(self, value="115200")
        self._refresh_ms = tk.StringVar(self, value="100")
        self._connection = tk.StringVar(self, value="Déconnecté")
        self._temperature = tk.StringVar(self, value="— °C")
        self._supply = tk.StringVar(self, value="— mV")
        self._measurement_state = tk.StringVar(self, value="État inconnu")
        self._last_update = tk.StringVar(self, value="Aucune mesure reçue")
        self._message_count = tk.StringVar(self, value="0 message reçu")
        self._error = tk.StringVar(self)
        self._follow = tk.BooleanVar(self, value=True)
        self._build_widgets()
        self.protocol("WM_DELETE_WINDOW", self._on_close)
        self.set_connected(False)

    def _build_widgets(self) -> None:
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)
        content = ttk.Frame(self, padding=16)
        content.grid(sticky="nsew")
        content.columnconfigure(0, weight=1)
        content.rowconfigure(3, weight=1)

        connection = ttk.LabelFrame(
            content, text="Connexion série", padding=10
        )
        connection.grid(row=0, column=0, sticky="ew", pady=(0, 12))
        connection.columnconfigure(1, weight=1)
        ttk.Label(connection, text="Port").grid(row=0, column=0, padx=(0, 8))
        self._port_entry = ttk.Entry(connection, textvariable=self._port)
        self._port_entry.grid(row=0, column=1, sticky="ew", padx=(0, 12))
        ttk.Label(connection, text="Bauds").grid(row=0, column=2)
        self._baud_entry = ttk.Entry(
            connection, textvariable=self._baudrate, width=9
        )
        self._baud_entry.grid(row=0, column=3, padx=8)
        self._connect_button = ttk.Button(
            connection, text="Connecter", command=self._on_connection
        )
        self._connect_button.grid(row=0, column=4)
        ttk.Label(connection, textvariable=self._connection).grid(
            row=1, column=0, columnspan=2, sticky="w", pady=(8, 0)
        )
        ttk.Label(
            connection, text="Port : /dev/cu.usbmodem… ou COM3"
        ).grid(row=2, column=0, columnspan=5, sticky="w", pady=(4, 0))

        settings = ttk.Frame(content)
        settings.grid(row=1, column=0, sticky="ew", pady=(0, 12))
        ttk.Label(settings, text="Rafraîchissement (ms)").pack(side="left")
        ttk.Entry(settings, textvariable=self._refresh_ms, width=8).pack(
            side="left", padx=8
        )
        self._apply_button = ttk.Button(
            settings, text="Appliquer", command=self._on_refresh
        )
        self._apply_button.pack(side="left")
        ttk.Checkbutton(
            settings, text="Suivre les messages", variable=self._follow
        ).pack(side="right")

        measurements = ttk.LabelFrame(
            content, text="Dernière mesure reçue", padding=10
        )
        measurements.grid(row=2, column=0, sticky="ew", pady=(0, 12))
        for column, (label, variable) in enumerate(
            (("Température", self._temperature), ("VDDA", self._supply))
        ):
            measurements.columnconfigure(column, weight=1)
            ttk.Label(measurements, text=label).grid(row=0, column=column)
            ttk.Label(
                measurements, textvariable=variable, font=("TkDefaultFont", 20)
            ).grid(row=1, column=column, pady=6)
        ttk.Label(measurements, textvariable=self._measurement_state).grid(
            row=2, column=0, sticky="w"
        )
        ttk.Label(measurements, textvariable=self._last_update).grid(
            row=2, column=1, sticky="e"
        )

        self._messages = ScrolledText(
            content, wrap="word", state="disabled", height=12,
            font="TkFixedFont", takefocus=True
        )
        self._messages.grid(row=3, column=0, sticky="nsew")
        ttk.Label(content, textvariable=self._message_count).grid(
            row=4, column=0, sticky="w", pady=(8, 0)
        )
        ttk.Label(
            content, textvariable=self._error, foreground="#b3261e",
            wraplength=650
        ).grid(row=5, column=0, sticky="ew", pady=(4, 0))

    def bind_controller(self, controller: "Controller") -> None:
        """Relie les actions après la construction du contrôleur."""
        self._controller = controller
        self.set_connected(self._connected)
        self._apply_button.configure(state="normal")
        self._on_refresh()

    def set_connected(self, connected: bool) -> None:
        """Actualise la connexion sans effacer la dernière mesure connue."""
        self._connected = connected
        self._connection.set("Connecté" if connected else "Déconnecté")
        state = "disabled" if connected else "normal"
        self._port_entry.configure(state=state)
        self._baud_entry.configure(state=state)
        self._connect_button.configure(
            text="Déconnecter" if connected else "Connecter",
            state="normal" if self._controller is not None else "disabled",
        )
        self._apply_button.configure(
            state="normal" if self._controller is not None else "disabled"
        )
        if connected:
            self._error.set("")

    def show_error(self, message: str) -> None:
        """Affiche une erreur sans boîte modale ni blocage du contrôleur."""
        self._error.set(message)

    def render(self, model: "Model") -> None:
        """Affiche un instantané des données ; ne modifie jamais le modèle."""
        measurement = model.latest_measurement
        if measurement is None:
            self._temperature.set("— °C")
            self._supply.set("— mV")
            self._last_update.set("Aucune mesure reçue")
        else:
            self._temperature.set(f"{measurement.temperature_c} °C")
            self._supply.set(f"{measurement.supply_mv} mV")
            self._last_update.set(
                measurement.timestamp.strftime("Reçue le %d/%m à %H:%M:%S")
            )
        self._measurement_state.set(
            {None: "État inconnu", True: "En pause", False: "Mesures actives"}[
                model.paused
            ]
        )
        messages = model.messages
        self._message_count.set(
            f"{model.message_count} messages reçus · {len(messages)} affichés"
        )
        position = self._messages.yview()[0]
        self._messages.configure(state="normal")
        self._messages.delete("1.0", "end")
        self._messages.insert(
            "end", "".join(
                f"[{message.timestamp:%H:%M:%S}] {message.text}\n"
                for message in messages
            )
        )
        self._messages.configure(state="disabled")
        if self._follow.get():
            self._messages.see("end")
        else:
            self._messages.yview_moveto(position)

    def _on_connection(self) -> None:
        if self._controller is None:
            return
        if self._connected:
            self._controller.disconnect()
            return
        try:
            baudrate = int(self._baudrate.get())
            if baudrate <= 0:
                raise ValueError
        except ValueError:
            self.show_error("Le débit doit être un entier positif.")
            return
        port = self._port.get().strip()
        if not port:
            self.show_error("Renseigner le port série de la Nucleo.")
            return
        self._error.set("")
        self._controller.connect(port, baudrate)

    def _on_refresh(self) -> None:
        if self._controller is None:
            return
        try:
            refresh_ms = int(self._refresh_ms.get())
            self._controller.set_refresh_interval(refresh_ms)
        except ValueError:
            self.show_error("Le rafraîchissement doit être un entier positif.")
            return
        self._error.set("")

    def _on_close(self) -> None:
        if self._closing:
            return
        self._closing = True
        if self._controller is not None:
            self._controller.close()
        self.destroy()
