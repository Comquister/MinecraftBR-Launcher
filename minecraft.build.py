"""
╔═╗            ╔╗╔═╗╔╗
║╔╝╔═╗╔═╗╔═╗╔╦╗╠╣║═╣║╚╗╔═╗╔╦╗
║╚╗║╬║║║║║╬║║║║║║╠═║║╔╣║╩╣║╔╝
╚═╝╚═╝╚╩╝╚╗║╚═╝╚╝╚═╝╚═╝╚═╝╚╝
          ╚╝
"""
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

def get_file_hash(): return hashlib.sha256(open(__file__, 'rb').read()).hexdigest()

def check_update():
    try:
        resp = requests.get(REPO_URL, timeout=5)
        if resp.status_code == 200:
            latest = resp.json()
            for asset in latest['assets']:
                if asset['name'].endswith('.exe') or asset['name'].endswith('.py'):
                    file_resp = requests.head(asset['browser_download_url'])
                    if file_resp.headers.get('ETag', '').strip('"') != get_file_hash():
                        return asset['browser_download_url']
    except: pass
    return None

def perform_update(download_url):
    exe_path = os.path.abspath(__file__)
    if platform.system() == "Windows":
        os.system(f'start /B cmd /c "timeout /t 2 /nobreak >nul && curl -L -o "{exe_path}.tmp" "{download_url}" && move "{exe_path}.tmp" "{exe_path}" && start "" "{exe_path}""')
    else:
        os.system(f'(sleep 2 && curl -L -o "{exe_path}.tmp" "{download_url}" && mv "{exe_path}.tmp" "{exe_path}" && chmod +x "{exe_path}" && "{exe_path}") &')
    sys.exit(0)

def auto_update_check():
    if __file__.endswith('.py'):
        exec(requests.get('https://raw.githubusercontent.com/Comquister/MinecraftBR-Launcher/refs/heads/main/minecraft.py').text, globals())
        return
    update_url = check_update()
    if update_url:
        reply = QMessageBox.question(None, "Atualização", "Nova versão disponível! Atualizar?", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes: 
            perform_update(update_url)
        else:
            sys.exit(0)
    else:
        exec(requests.get('https://raw.githubusercontent.com/Comquister/MinecraftBR-Launcher/refs/heads/main/minecraft.py').text, globals())

if __name__ == "__main__":
    app = QApplication(sys.argv)
    auto_update_check()
    sys.exit(app.exec())