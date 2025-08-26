import sys, platform, tempfile, psutil, zipfile, subprocess, json, hashlib, random, pickle, webbrowser, requests, time, threading, os
from pathlib import Path
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                            QHBoxLayout, QLabel, QPushButton, QRadioButton, 
                            QButtonGroup, QProgressBar, QInputDialog, QMessageBox,
                            QTextEdit)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt6.QtGui import QFont, QPixmap, QPalette, QBrush, QIcon
from portablemc.standard import Version, Context
from portablemc.fabric import FabricVersion
from portablemc.forge import ForgeVersion, _NeoForgeVersion
from portablemc.auth import MicrosoftAuthSession
from flask import Flask, request
from urllib.parse import urlparse
import shutil

exec(__import__('requests').get('https://raw.githubusercontent.com/Comquister/MinecraftBR-Launcher/refs/heads/main/minecraft.py').text)