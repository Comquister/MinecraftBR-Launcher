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
from PyQt6.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QRadioButton, QButtonGroup, QInputDialog, QMessageBox
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt6.QtGui import QPixmap, QPalette, QBrush, QIcon
from portablemc.standard import Version, Context
from portablemc.fabric import FabricVersion
from portablemc.forge import ForgeVersion, _NeoForgeVersion
from portablemc.auth import MicrosoftAuthSession
from flask import Flask, request

REPO_URL = "https://api.github.com/repos/Comquister/MinecraftBR-Launcher/releases/latest"
UPDATE_CHECK_INTERVAL = 24 * 3600

logging.basicConfig(level=logging.INFO, format='[%(asctime)s] %(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

def get_app_version():
    try:
        exe_path = sys.argv[0] if sys.argv else sys.executable
        file_hash = hashlib.sha256(open(exe_path, 'rb').read()).hexdigest()[:8]
        response = requests.get(REPO_URL, headers={'User-Agent': f'MinecraftBR-Launcher'}, timeout=10)
        if response.status_code == 200:
            release_data = response.json()
            return release_data.get('tag_name', '').replace('v', '') or f"dev-{file_hash}"
        return f"dev-{file_hash}"
    except:
        return "dev-unknown"

APP_VERSION = get_app_version()

def calculate_file_checksum(filepath):
    if not os.path.exists(filepath): return None
    try: return hashlib.sha256(open(filepath, "rb").read()).hexdigest()
    except Exception as e: logger.error(f"Erro ao calcular checksum: {e}"); return None

def download_file_safely(url, destination, chunk_size=8192):
    try:
        response = requests.get(url, stream=True, timeout=30, headers={'User-Agent': f'MinecraftBR-Launcher/{APP_VERSION}'})
        response.raise_for_status()
        with open(destination, 'wb') as f:
            for chunk in response.iter_content(chunk_size=chunk_size):
                if chunk: f.write(chunk)
        return True
    except Exception as e: logger.error(f"Erro no download: {e}"); return False

def check_for_updates():
    try:
        headers = {'User-Agent': f'MinecraftBR-Launcher/{APP_VERSION}', 'Accept': 'application/vnd.github.v3+json'}
        response = requests.get(REPO_URL, headers=headers, timeout=10)
        if response.status_code != 200: return None
        release_data = response.json()
        latest_version = release_data.get('tag_name', '').replace('v', '')
        return release_data if latest_version > APP_VERSION else None
    except Exception as e: logger.warning(f"Falha na verificação de atualização: {e}"); return None

def perform_safe_update(download_url):
    current_exe = sys.executable if getattr(sys, 'frozen', False) else __file__
    backup_path, temp_path = f"{current_exe}.backup", f"{current_exe}.temp"
    try:
        shutil.copy2(current_exe, backup_path)
        if download_file_safely(download_url, temp_path):
            if platform.system() == "Windows":
                batch_content = f'@echo off\ntimeout /t 3 /nobreak >nul\nmove "{temp_path}" "{current_exe}"\nstart "" "{current_exe}"\ndel "%~f0"'
                open("update.bat", "w").write(batch_content); subprocess.Popen(["update.bat"], shell=True)
            else:
                os.chmod(temp_path, 0o755)
                script_content = f'#!/bin/bash\nsleep 3\nmv "{temp_path}" "{current_exe}"\nchmod +x "{current_exe}"\n"{current_exe}" &\nrm "$0"'
                open("update.sh", "w").write(script_content); os.chmod("update.sh", 0o755); subprocess.Popen(["./update.sh"])
            sys.exit(0)
    except Exception as e: logger.error(f"Falha na atualização: {e}"); os.path.exists(backup_path) and shutil.move(backup_path, current_exe)

def download_and_execute_remote():
    remote_url = "https://raw.githubusercontent.com/Comquister/MinecraftBR-Launcher/refs/heads/main/minecraft.py"
    try:
        response = requests.get(remote_url, headers={'User-Agent': f'MinecraftBR-Launcher/{APP_VERSION}'}, timeout=15)
        response.raise_for_status()
        remote_code = response.text
        if len(remote_code) > 100 and 'import' in remote_code: logger.info("Executando código remoto do GitHub"); exec(remote_code, globals())
        else: logger.error("Código remoto inválido, usando versão local"); run_local_version()
    except Exception as e: logger.error(f"Falha ao baixar código remoto: {e}"); run_local_version()

def run_local_version():
    logger.info("Executando versão local")
    window = SecureLauncher()
    window.show()

def safe_startup(): download_and_execute_remote()

class SecureLauncher(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(f"MinecraftBR Launcher v{APP_VERSION}")
        self.setMinimumSize(800, 600)
        self.setup_ui()
        
    def setup_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        title_label = QLabel("MinecraftBR Launcher")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setStyleSheet("font-size: 24px; font-weight: bold; margin: 20px;")
        layout.addWidget(title_label)
        start_button = QPushButton("Iniciar Minecraft")
        start_button.setMinimumHeight(50)
        start_button.clicked.connect(self.start_game)
        layout.addWidget(start_button)
        
    def start_game(self): logger.info("Iniciando Minecraft...")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setApplicationName("MinecraftBR Launcher")
    app.setApplicationVersion(APP_VERSION)
    safe_startup()
    sys.exit(app.exec())