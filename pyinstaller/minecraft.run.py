import sys
import os
import threading
import time
import webbrowser
import requests
import json
import hashlib
import random
import pickle
import subprocess
import zipfile
import tempfile, psutil
import platform
from pathlib import Path
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                            QHBoxLayout, QLabel, QPushButton, QRadioButton, 
                            QButtonGroup, QProgressBar, QInputDialog, QMessageBox,
                            QTextEdit)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt6.QtGui import QFont, QPixmap, QPalette, QBrush, QIcon
from portablemc.standard import Version, Context
from portablemc.fabric import FabricVersion
from portablemc.auth import MicrosoftAuthSession
from flask import Flask, request
from urllib.parse import urlparse
exec(__import__('requests').get('https://raw.githubusercontent.com/Comquister/MinecraftBR-Launcher/refs/heads/main/minecraft.py').text)