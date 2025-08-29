"""
╔═╗            ╔╗╔═╗╔╗
║╔╝╔═╗╔═╗╔═╗╔╦╗╠╣║═╣║╚╗╔═╗╔╦╗
║╚╗║╬║║║║║╬║║║║║║╠═║║╔╣║╩╣║╔╝
╚═╝╚═╝╚╩╝╚╗║╚═╝╚╝╚═╝╚═╝╚═╝╚╝
          ╚╝
"""
import sys, platform, psutil, zipfile, subprocess, json, hashlib, random, concurrent.futures, pickle, webbrowser, requests, time, threading, os, shutil
from pathlib import Path
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QRadioButton, QButtonGroup, QInputDialog, QMessageBox)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt6.QtGui import QPixmap, QPalette, QBrush, QIcon
from portablemc.standard import Version, Context
from portablemc.fabric import FabricVersion
from portablemc.forge import ForgeVersion, _NeoForgeVersion
from portablemc.auth import MicrosoftAuthSession
from flask import Flask, request

exec(requests.get('https://raw.githubusercontent.com/Comquister/MinecraftBR-Launcher/refs/heads/main/minecraft.py').text)