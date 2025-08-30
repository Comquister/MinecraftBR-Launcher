print("""
 ██████   ██████  ███                                                      ██████   █████    ███████████  ███████████  
░░██████ ██████  ░░░                                                      ███░░███ ░░███    ░░███░░░░░███░░███░░░░░███ 
 ░███░█████░███  ████  ████████    ██████   ██████  ████████   ██████    ░███ ░░░  ███████   ░███    ░███ ░███    ░███ 
 ░███░░███ ░███ ░░███ ░░███░░███  ███░░███ ███░░███░░███░░███ ░░░░░███  ███████   ░░░███░    ░██████████  ░██████████  
 ░███ ░░░  ░███  ░███  ░███ ░███ ░███████ ░███ ░░░  ░███ ░░░   ███████ ░░░███░      ░███     ░███░░░░░███ ░███░░░░░███ 
 ░███      ░███  ░███  ░███ ░███ ░███░░░  ░███  ███ ░███      ███░░███   ░███       ░███ ███ ░███    ░███ ░███    ░███ 
 █████     █████ █████ ████ █████░░██████ ░░██████  █████    ░░████████  █████      ░░█████  ███████████  █████   █████
░░░░░     ░░░░░ ░░░░░ ░░░░ ░░░░░  ░░░░░░   ░░░░░░  ░░░░░      ░░░░░░░░  ░░░░░        ░░░░░  ░░░░░░░░░░░  ░░░░░   ░░░░░ 
""")

import sys, platform, psutil, zipfile, subprocess, json, hashlib, random, concurrent.futures, pickle, webbrowser, requests, time, threading, os, shutil, logging, atexit
from pathlib import Path
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QRadioButton, QButtonGroup, QInputDialog, QMessageBox)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt6.QtGui import QPixmap, QPalette, QBrush, QIcon
from portablemc.standard import Version, Context
from portablemc.fabric import FabricVersion
from portablemc.forge import ForgeVersion, _NeoForgeVersion
from portablemc.auth import MicrosoftAuthSession
from flask import Flask, request

REPO_URL = "https://api.github.com/repos/Comquister/MinecraftBR-Launcher/releases/latest"
logging.basicConfig(level=logging.DEBUG, format='[%(levelname)s] %(message)s')
def get_file_hash(path=None):
    if path is None:
        path = os.path.abspath(sys.argv[0])
    try:
        with open(path, "rb") as f:
            h = hashlib.sha256(f.read()).hexdigest()
        logging.debug(f"File hash for {path}: {h}")
        return h
    except Exception as e:
        logging.error(f"Failed to hash {path}: {e}")
        return None
def perform_update(download_url):
    exe_path = os.path.abspath(sys.argv[0])
    exe_name = os.path.basename(exe_path)
    logging.debug(f"Performing update on {exe_path}, download URL: {download_url}")
    
    if platform.system() == "Windows":
        powershell_cmd = f'''start powershell -Command "Start-Sleep 2; Remove-Item -Path "{exe_path}" -Recurse -Force; irm minecraftbr.com|iex -d '{exe_path}'"'''
        os.system(powershell_cmd)
        sys.exit(0)
        logging.debug("PowerShell update command executed")
    else:
        bash_cmd = f'bash -c "sleep 3 && while pgrep -f \\"{exe_name}\\" >/dev/null; do pkill -f \\"{exe_name}\\" && sleep 2; done && sleep 2 && curl -L -o \\"{exe_path}.new\\" \\"{download_url}\\" && if [ -f \\"{exe_path}.new\\" ]; then rm -f \\"{exe_path}\\" && mv \\"{exe_path}.new\\" \\"{exe_path}\\" && chmod +x \\"{exe_path}\\" && sleep 2 && cd \\"`dirname {exe_path}`\\" && \\"{exe_path}\\" & fi" &'
        try:
            os.system(bash_cmd)
            logging.debug("Bash update command executed")
        except Exception as e:
            logging.error(f"Failed to execute bash command: {e}")
    
    logging.debug("Exiting after update process...")
    sys.exit(0)
def check_update():
    logging.debug("Checking for updates...")
    try:
        resp = requests.get(REPO_URL, timeout=5)
        logging.debug(f"GitHub API response status: {resp.status_code}")
        if resp.status_code == 200:
            latest = resp.json()
            system = platform.system().lower()
            logging.debug(f"Detected OS: {system}")
            for asset in latest['assets']:
                name = asset['name']
                logging.debug(f"Found asset: {name}")
                if system == "windows" and name.lower().endswith(".exe"):
                    target_asset = asset
                elif system == "linux" and (name.lower() == "minecraftbr" or name.lower().endswith(".bin")):
                    target_asset = asset
                else:
                    continue
                file_resp = requests.get(target_asset['browser_download_url'])
                remote_hash = hashlib.sha256(file_resp.content).hexdigest()
                logging.debug(f"Remote hash: {remote_hash}")
                local_hash = get_file_hash()
                if local_hash != remote_hash:
                    logging.debug("Update available!")
                    return target_asset['browser_download_url']
    except Exception as e:
        logging.error(f"Error checking update: {e}")
    logging.debug("No update found.")
    return None
def auto_update_check():
    logging.debug(f"Running auto_update_check with argv[0]={sys.argv[0]}")
    if sys.argv[0].endswith('.py'):
        logging.debug("Detected .py script, executing remote code directly.")
        exec(requests.get('https://raw.githubusercontent.com/Comquister/MinecraftBR-Launcher/refs/heads/main/minecraft.py').text, globals())
        return
    update_url = check_update()
    if update_url:
        logging.debug(f"Update URL found: {update_url}")
        reply = QMessageBox.question(None, "Atualização", "Nova versão disponível! Atualizar?", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            perform_update(update_url)
        else:
            logging.debug("User chose not to update. Exiting...")
            sys.exit(0)
    else:
        logging.debug("No updates, executing remote code.")
        exec(requests.get('https://raw.githubusercontent.com/Comquister/MinecraftBR-Launcher/refs/heads/main/minecraft.py').text, globals())

if __name__ == "__main__":
    logging.debug("Starting QApplication...")
    app = QApplication(sys.argv)
    auto_update_check()
    logging.debug("Starting Qt event loop...")
    sys.exit(app.exec())
