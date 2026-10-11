"""Point d'entrée du moniteur graphique de la Nucleo.

Lancer avec : python3 script/monitor.py
Tkinter est nécessaire à l'affichage ; pyserial à la connexion série.
La connexion TCP à la Raspberry est proposée par défaut.
Aucun port n’est ouvert avant une action sur le bouton Connecter.
"""

import tkinter as tk

from controller import Controller
from model import Model
from view import View


def main() -> None:
    """Assemble les composants MVC et lance la boucle graphique."""
    model = Model()
    view = View()
    controller = None
    try:
        controller = Controller(model, view)
        view.bind_controller(controller)
        view.render(model)
        view.mainloop()
    except KeyboardInterrupt:
        # Permet aussi l'arrêt depuis le terminal avec Ctrl+C.
        pass
    finally:
        try:
            if controller is not None:
                controller.close()
        finally:
            try:
                view.destroy()
            except tk.TclError:
                # La fermeture par la croix a déjà détruit la fenêtre.
                pass


if __name__ == "__main__":
    main()
