# Nucleo — mesures et moniteur série

Le projet STM32 utilise PlatformIO et la HAL STM32. Le moniteur Python du
dossier `script` affiche les messages reçus de la Nucleo, la température,
la tension VDDA et l'état de pause des mesures.

## Prérequis du moniteur Python

### Exécutable autonome macOS

Le fichier `script/nucleo-monitor` embarque Python, Tkinter et pyserial.
Il fonctionne sans installation de Python ni activation de `.venv` :

```bash
./script/nucleo-monitor
```

Ce binaire est construit pour **macOS sur Apple Silicon (arm64)** et testé
sur le Mac de développement. Il ne convient pas à Windows, Linux ou aux Mac
Intel. Sa compatibilité avec des versions plus anciennes de macOS n'est pas
validée. Il porte une signature locale, sans notarisation Apple.

Les instructions suivantes concernent l'exécution depuis les sources.

- Python 3 avec Tkinter pour l'interface graphique.
- **pyserial** pour accéder au port série USB du ST-LINK.

Le paquet s'installe sous le nom `pyserial` et s'importe en Python avec
`import serial`. Sans cette dépendance, la connexion affiche le message
« Installer pyserial pour ouvrir le port série ».

## Installation dans un environnement virtuel

Exemple sur macOS ou Linux, depuis la racine du dépôt :

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r script/requirements.txt
```

Le dossier `.venv` contient un environnement Python propre au projet et est
ignoré par Git. Le fichier `script/requirements.txt` déclare `pyserial`.
L'installation directe équivalente utilisée lors de la mise en place était :

```bash
.venv/bin/python -m pip install pyserial
```

Vérifier que les dépendances sont accessibles :

```bash
.venv/bin/python -c "import serial, tkinter; print(serial.__version__)"
```

Si l'import de `tkinter` échoue, installer le support Tkinter adapté à la
distribution Python utilisée, puis recréer l'environnement virtuel si nécessaire.

## Lancer le moniteur

Depuis la racine du dépôt :

```bash
.venv/bin/python script/monitor.py
```

Cette commande utilise explicitement le Python dans lequel `pyserial` est
installé. Aucune activation préalable de l'environnement n'est nécessaire.
Il est aussi possible de l'activer dans le terminal :

```bash
source .venv/bin/activate
python script/monitor.py
# Après avoir fermé le moniteur :
deactivate
```

## Connecter la Nucleo

1. Brancher la Nucleo via le connecteur USB du ST-LINK.
2. Fermer le Monitor de PlatformIO pour libérer le port série.
3. Le port ST-LINK est détecté au démarrage et prérempli. Conserver
   **115200 bauds**.
4. Cliquer sur **Connecter**.

Si la carte est branchée après le lancement, cliquer sur **Détecter**.
La détection ne se connecte pas à la carte et ne lance aucune recherche
périodique. Elle utilise les identifiants USB ST-LINK ou sa description,
via [pyserial](https://pyserial.readthedocs.io/en/latest/tools.html).
Une seule Nucleo est attendue. Si aucun port ST-LINK n'est reconnu (ou si
plusieurs correspondent), un message apparaît et la saisie manuelle reste
possible. Le bouton Détecter est désactivé tant que la connexion est ouverte.

Sur macOS, lister les ports disponibles avec :

```bash
ls /dev/cu.*
```

Le port de la carte ressemble à `/dev/cu.usbmodem11103`, mais son nom peut
changer. Pour l'identifier, comparer la liste avant et après branchement.

Le rafraîchissement de l'affichage est réglé sur **100 ms** par défaut.
Modifier la valeur puis cliquer sur **Appliquer** pour changer ce délai.
Ce réglage ne modifie pas la fréquence des mesures envoyées par la Nucleo.

## Version du firmware

La fenêtre affiche la version annoncée par la Nucleo, indépendamment de la
version du logiciel Python. Elle est définie par `FIRMWARE_VERSION` dans
`src/measurement.c` (initialement `1.0.0`) et envoyée sous la forme :

```text
Firmware STM32 : 1.0.0
```

Cette ligne est envoyée au démarrage, avec chaque mesure et lors des changements
de pause. Une connexion tardive reçoit donc la version à la prochaine mesure.
Si la carte est déjà en pause, reprendre les mesures pour recevoir la version.
Le moniteur affiche « Firmware : inconnu » avant réception, y compris après
reconnexion. Les anciens firmwares restent compatibles, sans version affichée.
Compiler et téléverser le nouveau firmware pour activer cette information.

## Tests sans Nucleo

```bash
.venv/bin/python -B -m unittest discover -s script/tests -v
```

Les tests utilisent un bouchon série en mémoire : aucun port physique n'est
ouvert. Ils ouvrent temporairement des fenêtres Tkinter et nécessitent donc
une session graphique. Chaque test graphique s'exécute dans un processus séparé.

## Reconstruire le binaire macOS

Après modification du code Python, reconstruire l'exécutable depuis la racine
du dépôt (le venv sert uniquement à la fabrication) :

```bash
.venv/bin/python -m pip install -r script/requirements.txt pyinstaller==6.22.3
PYINSTALLER_CONFIG_DIR=/tmp/nucleo-pyinstaller-cache \
  .venv/bin/python -m PyInstaller --noconfirm --onefile \
  --name nucleo-monitor --distpath script \
  --workpath /tmp/nucleo-monitor-build --specpath /tmp \
  --hidden-import serial script/monitor.py
```

Le résultat remplace `script/nucleo-monitor`. PyInstaller doit être exécuté
sur le système cible ; voir sa [documentation](https://pyinstaller.org/en/stable/usage.html).
