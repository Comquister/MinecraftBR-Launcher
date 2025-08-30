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
    exe_dir = os.path.dirname(exe_path)
    temp_exe = os.path.join(exe_dir, f"{exe_name}.new")
   
    if platform.system() == "Windows":
        try:
            resp = requests.get(download_url, timeout=30)
            with open(temp_exe, 'wb') as f: f.write(resp.content)
            cmd = f'Start-Sleep 2; Remove-Item -Force \\"{exe_path}\\"; Move-Item \\"{temp_exe}\\" \\"{exe_path}\\"; Add-Type -AssemblyName System.Windows.Forms; [System.Windows.Forms.MessageBox]::Show(\\"Atualização concluída! Você pode iniciar o aplicativo.\\", \\"Atualização\\", [System.Windows.Forms.MessageBoxButtons]::OK, [System.Windows.Forms.MessageBoxIcon]::Information)'
            os.system(f'start powershell -WindowStyle Hidden -Command "{cmd}"')
        except: pass
    else:
        try:
            resp = requests.get(download_url, timeout=30)
            with open(temp_exe, 'wb') as f: f.write(resp.content)
            os.system(f'sleep 3 & rm -f "{exe_path}" & mv "{temp_exe}" "{exe_path}" & chmod +x "{exe_path}" & "{exe_path}" &')
        except: pass
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
