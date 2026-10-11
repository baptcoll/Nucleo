# Nucleo — mesures et moniteur série

Le projet STM32 utilise PlatformIO et la HAL STM32. Le moniteur Python du
dossier `script` affiche les messages reçus de la Nucleo, la température,
la tension VDDA et l'état de pause des mesures.

## Prérequis du moniteur Python

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
3. Renseigner le port dans la fenêtre et conserver **115200 bauds**.
4. Cliquer sur **Connecter**.

Sur macOS, lister les ports disponibles avec :

```bash
ls /dev/cu.*
```

Le port de la carte ressemble à `/dev/cu.usbmodem11103`, mais son nom peut
changer. Pour l'identifier, comparer la liste avant et après branchement.

Le rafraîchissement de l'affichage est réglé sur **100 ms** par défaut.
Modifier la valeur puis cliquer sur **Appliquer** pour changer ce délai.
Ce réglage ne modifie pas la fréquence des mesures envoyées par la Nucleo.

## Tests sans Nucleo

```bash
.venv/bin/python -B -m unittest discover -s script/tests -v
```

Les tests utilisent un bouchon série en mémoire : aucun port physique n'est
ouvert. Ils ouvrent temporairement des fenêtres Tkinter et nécessitent donc
une session graphique. Chaque test graphique s'exécute dans un processus séparé.
