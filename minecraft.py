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

# FUNÇÕES GLOBAIS (fora das classes)
def calculate_optimal_ram():
    """Calcula a quantidade ótima de RAM baseada no sistema"""
    total_ram_gb = psutil.virtual_memory().total / (1024**3)
    
    # Deixa pelo menos 2GB para o sistema
    available_ram_gb = max(1, total_ram_gb - 2)
    
    # Limita baseado no sistema
    if platform.machine().endswith('64'):
        # Sistema 64-bit
        optimal_ram_gb = min(available_ram_gb * 0.7, 8)  # Máximo 8GB
    else:
        # Sistema 32-bit
        optimal_ram_gb = min(available_ram_gb * 0.5, 3)  # Máximo 3GB
    
    return max(1, int(optimal_ram_gb * 1024))  # Retorna em MB

def diagnose_jvm_issues():
    """Função para diagnosticar problemas JVM"""
    print("=== DIAGNÓSTICO JVM ===")
    
    # Sistema
    print(f"SO: {platform.system()} {platform.release()}")
    print(f"Arquitetura: {platform.machine()}")
    print(f"RAM Total: {psutil.virtual_memory().total / (1024**3):.1f} GB")
    
    # RAM configurada
    ram_config = calculate_optimal_ram()
    print(f"RAM configurada: {ram_config}M")
    
    # Verificações específicas
    if platform.machine().endswith('64'):
        print("✓ Sistema 64-bit - sem limitações de RAM")
    else:
        print("⚠ Sistema 32-bit - RAM limitada a 3GB")
    
    print("=" * 25)

# Configurações
CONFIG = {
    'Title': 'MinecraftBr Launcher',
    'MINECRAFT_VERSION': "1.21.8",
    'SERVER_HOST': "max.cnq.wtf",
    'SERVER_PORT': 10069,
    'RAM_SIZE': f"{calculate_optimal_ram()}M",  # Usando função otimizada
    'CLIENT_ID': "708e91b5-99f8-4a1d-80ec-e746cbb24771",
    'EXTRAS_JSON_URL': "https://minecraftbr.com/extra/index.php",
    'EXTRAS_DOWNLOAD_URL': "https://minecraftbr.com/extra/download.php",
    'IGNORE_FILE': "?ignorar=!mods",
    'PORTWEB': random.randint(49152, 65535)
}
CONFIG['REDIRECT_URI'] = f"http://localhost:{CONFIG['PORTWEB']}/code"

auth_data = {'success': None, 'code': None, 'id_token': None}

# Funções utilitárias
def calculate_sha256(file_path):
    sha256_hash = hashlib.sha256()
    try:
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    except Exception:
        return None

def save_login_data(game_dir, login_type, data):
    login_file = game_dir / "last_login.dat"
    try:
        login_info = {'type': login_type, 'data': data}
        with open(login_file, 'wb') as f:
            pickle.dump(login_info, f)
    except Exception as e:
        print(f"Erro ao salvar login: {e}")

def load_login_data(game_dir):
    login_file = game_dir / "last_login.dat"
    try:
        if login_file.exists():
            with open(login_file, 'rb') as f:
                return pickle.load(f)
    except Exception as e:
        print(f"Erro ao carregar login: {e}")
    return None

def check_last(game_dir):
    return (game_dir / "options.txt").exists()

def download_background(game_dir):
    bg_path = game_dir / "background.png"
    if not bg_path.exists():
        try:
            response = requests.get("https://github.com/Comquister/MinecraftBR-Launcher/blob/main/image/background.png?raw=true", timeout=10)
            if response.status_code == 200:
                with open(bg_path, 'wb') as f:
                    f.write(response.content)
        except Exception as e:
            print(f"Erro ao baixar background: {e}")
            return None
    return bg_path if bg_path.exists() else None

def create_auth_app():
    app = Flask(__name__)
    app.logger.disabled = True
    
    # Adicione estas linhas para suprimir completamente os logs
    import logging
    log = logging.getLogger('werkzeug')
    log.setLevel(logging.ERROR)
    
    @app.route('/code', methods=['GET', 'POST'])
    def handle_auth():
        data = request.form if request.method == 'POST' else request.args
        if 'code' in data and 'id_token' in data:
            auth_data.update({'code': data['code'], 'id_token': data['id_token'], 'success': True})
        elif 'error' in data:
            auth_data.update({'error': data.get('error_description', 'Login failed'), 'success': False})
        return """<!DOCTYPE html>
<html><head><meta charset="UTF-8"><title>Autenticação Concluída</title>
<style>body{display:flex;justify-content:center;align-items:center;height:100vh;margin:0;font-family:sans-serif;background:#121212;color:#eaeaea}
.box{background:#1e1e1e;padding:40px;border-radius:16px;text-align:center}
h1{color:#4cafef}p{color:#bbb}</style></head>
<body><div class="box"><h1>✅ Autenticação concluída</h1><p>Você pode fechar esta janela.</p></div>
<script>setTimeout(()=>window.close(),3000)</script></body></html>"""
    
    return app

class AuthThread(QThread):
    auth_success = pyqtSignal(object, str)
    auth_error = pyqtSignal(str)
    
    def __init__(self, email):
        super().__init__()
        self.email = email
    
    def run(self):
        try:
            auth_data.update({'success': None, 'code': None, 'id_token': None})
            
            nonce = str(int(time.time() * 1000))
            auth_url = MicrosoftAuthSession.get_authentication_url(
                CONFIG['CLIENT_ID'], CONFIG['REDIRECT_URI'], self.email, nonce
            )
            
            # Inicia servidor Flask
            app = create_auth_app()
            threading.Thread(target=lambda: app.run(
                host='localhost', port=CONFIG['PORTWEB'], debug=False
            ), daemon=True).start()
            
            time.sleep(1)
            webbrowser.open(auth_url)
            
            # Aguarda resposta
            timeout = time.time() + 180
            while auth_data['success'] is None and time.time() < timeout:
                time.sleep(0.5)
            
            if auth_data['success'] and MicrosoftAuthSession.check_token_id(auth_data['id_token'], self.email, nonce):
                auth_session = MicrosoftAuthSession.authenticate(
                    CONFIG['CLIENT_ID'], CONFIG['CLIENT_ID'], auth_data['code'], CONFIG['REDIRECT_URI']
                )
                auth_session.email = self.email
                self.auth_success.emit(auth_session, self.email)
            else:
                self.auth_error.emit("Falha na autenticação")
        except Exception as e:
            self.auth_error.emit(str(e))

class MinecraftThread(QThread):
    status_update = pyqtSignal(str)
    progress_update = pyqtSignal(int)
    error_occurred = pyqtSignal(str)
    finished_success = pyqtSignal()
    
    def __init__(self, game_dir, auth_session, username):
        super().__init__()
        self.game_dir = game_dir
        self.auth_session = auth_session
        self.username = username
        self.context = Context(game_dir, game_dir)
    
    def run(self):
        try:
            self.game_dir.mkdir(exist_ok=True)
            
            # Sincroniza arquivos extras
            self.status_update.emit("Verificando arquivos extras...")
            self.progress_update.emit(10)
            self._sync_extras()
            
            self.status_update.emit("Preparando Minecraft...")
            self.progress_update.emit(55)
            version = FabricVersion.with_fabric(CONFIG['MINECRAFT_VERSION'], context=self.context)
            
            # Autenticação
            if self.auth_session:
                version.auth_session = self.auth_session
            else:
                version.set_auth_offline(self.username, None)
            
            self.status_update.emit("Instalando componentes...")
            self.progress_update.emit(70)
            
            env = version.install()
            
            # CORREÇÃO: Configuração JVM melhorada
            self.status_update.emit("Configurando JVM...")
            
            # Verifica se é sistema 32-bit ou 64-bit
            is_64bit = platform.machine().endswith('64')
            
            # Configuração de RAM mais segura
            ram_mb = int(CONFIG['RAM_SIZE'].replace('M', ''))
            if not is_64bit and ram_mb > 3072:  # Limita a 3GB em sistemas 32-bit
                ram_mb = 3072
                self.status_update.emit("Sistema 32-bit detectado, limitando RAM a 3GB...")
            
            ram_size = f"{ram_mb}M"
            
            # JVM args mais compatíveis
            jvm_args = [
                f"-Xmx{ram_size}",
                f"-Xms{min(512, ram_mb)}M",  # Xms menor que Xmx
                "-XX:+UseG1GC",
                "-XX:+UnlockExperimentalVMOptions",
                "-XX:G1NewSizePercent=20",
                "-XX:G1ReservePercent=20",
                "-XX:MaxGCPauseMillis=50",
                "-XX:G1HeapRegionSize=32M",
                "-Djava.awt.headless=false",  # Previne problemas de GUI
                "-Dfile.encoding=UTF-8"  # Encoding correto
            ]
            
            # Adiciona argumentos específicos para Windows
            if os.name == 'nt':
                jvm_args.extend([
                    "-Dos.name=Windows 10",
                    "-Dos.version=10.0"
                ])
            
            # CORREÇÃO: Aplicação correta dos argumentos JVM
            original_jvm_args = env.jvm_args.copy()
            
            # Mantém o executável Java original
            java_executable = original_jvm_args[0] if original_jvm_args else "java"
            
            # Remove argumentos conflitantes dos originais
            filtered_original_args = []
            for arg in original_jvm_args[1:]:
                if not any(arg.startswith(prefix) for prefix in ['-Xmx', '-Xms', '-XX:+UseG1GC']):
                    filtered_original_args.append(arg)
            
            # Combina argumentos customizados com os originais filtrados
            env.jvm_args = [java_executable] + jvm_args + filtered_original_args
            
            self.status_update.emit("Iniciando jogo...")
            self.progress_update.emit(100)
            
            self.finished_success.emit()
            env.run()
            
        except Exception as e:
            # Log mais detalhado do erro
            import traceback
            error_msg = f"Erro JVM: {str(e)}\nDetalhes: {traceback.format_exc()}"
            print(error_msg)  # Log para debug
            self.error_occurred.emit(str(e))
    
    def _sync_extras(self):
        try:
            # Obtém lista de arquivos do servidor
            if check_last(self.game_dir):
                response = requests.get(CONFIG['EXTRAS_JSON_URL'] + CONFIG['IGNORE_FILE'], timeout=10)
            else:
                response = requests.get(CONFIG['EXTRAS_JSON_URL'], timeout=10)
            
            if response.status_code != 200:
                return True
                
            remote_files = response.json()
            if not remote_files:
                return True
            
            # Verifica se precisa baixar
            needs_download = self._check_files_need_update(remote_files)
            
            if needs_download:
                self._download_and_extract_zip()
                
            return True
            
        except Exception as e:
            print(f"Erro na sincronização: {e}")
            return True
    
    def _check_files_need_update(self, remote_files):
        local_files = self._get_local_files()
        
        for file_info in remote_files:
            file_name = file_info['nome']
            expected_hash = file_info['hash']
            
            if file_name not in local_files:
                return True
            elif local_files[file_name]['hash'] != expected_hash:
                return True
        
        return False
    
    def _get_local_files(self):
        local_files = {}
        for item in self.game_dir.rglob('*'):
            if item.is_file() and not item.name.startswith(('last_login', 'icon', 'background')):
                relative_path = str(item.relative_to(self.game_dir)).replace(os.sep, '/')
                if not relative_path.startswith('./'):
                    relative_path = './' + relative_path
                hash_value = calculate_sha256(item)
                if hash_value:
                    local_files[relative_path] = {'hash': hash_value, 'path': item}
        return local_files
    
    def _download_and_extract_zip(self):
        try:
            self.status_update.emit("Baixando arquivos extras...")
            self.progress_update.emit(25)
            
            # Baixa o ZIP
            if check_last(self.game_dir):
                response = requests.get(CONFIG['EXTRAS_DOWNLOAD_URL'] + CONFIG['IGNORE_FILE'], stream=True, timeout=120)
            else:
                response = requests.get(CONFIG['EXTRAS_DOWNLOAD_URL'], stream=True, timeout=120)
            response.raise_for_status()
            
            # Salva em arquivo temporário
            with tempfile.NamedTemporaryFile(delete=False, suffix='.zip') as temp_zip:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        temp_zip.write(chunk)
                temp_zip_path = temp_zip.name
            
            self.status_update.emit("Extraindo arquivos...")
            self.progress_update.emit(45)
            
            # Extrai o ZIP
            with zipfile.ZipFile(temp_zip_path, 'r') as zip_ref:
                zip_ref.extractall(self.game_dir)
            
            # Remove arquivo temporário
            os.unlink(temp_zip_path)
            
        except Exception as e:
            print(f"Erro no download/extração: {e}")
            if 'temp_zip_path' in locals():
                try:
                    os.unlink(temp_zip_path)
                except:
                    pass

class MinecraftLauncher(QMainWindow):
    def __init__(self):
        super().__init__()
        self.game_dir = Path.home() / ".minecraftbr"
        self.game_dir.mkdir(exist_ok=True)
        self.auth_session = None
        self.username = None
        self.last_login_data = load_login_data(self.game_dir)
        self.auth_thread = None
        self.minecraft_thread = None
        self._pending_auth_email = None
        self.progress_timer = QTimer()
        self.current_progress = 0
        
        self.init_ui()
        self.load_background()

    def init_ui(self):
        self.setWindowTitle(CONFIG['Title'])
        # Define ícone da janela# Baixa o ícone da URL
        try:
            icon_url = "https://raw.githubusercontent.com/Comquister/MinecraftBR-Launcher/refs/heads/main/image/favicon.ico"
            response = requests.get(icon_url, timeout=10)
            if response.status_code == 200:
                pixmap = QPixmap()
                pixmap.loadFromData(response.content)
                self.setWindowIcon(QIcon(pixmap))
            else:
                print("Erro ao baixar o ícone")
        except Exception as e:
            print(f"Erro ao carregar ícone: {e}")

        self.setGeometry(100, 100, 450, 680)
        self.setStyleSheet("""
            QMainWindow {
                background-image: url(""" + str(self.game_dir) + "/background.png" + """);
                background-repeat: no-repeat;
                background-position: center;
            }

            QWidget {
                color: #FFFFFF;
                font-family: 'Segoe UI', Arial, sans-serif;
            }
            QLabel {
                color: #FFFFFF;
            }
            QRadioButton {
                color: #FFFFFF;
                font-size: 14px;
                padding: 8px;
                spacing: 10px;
            }
            QRadioButton::indicator {
                width: 18px;
                height: 18px;
            }
            QRadioButton::indicator:unchecked {
                border: 2px solid #CCCCCC;
                border-radius: 9px;
                background: transparent;
            }
            QRadioButton::indicator:checked {
                border: 2px solid #4CAF50;
                border-radius: 9px;
                background: #4CAF50;
            }
            QPushButton {
                background-color: rgba(60, 60, 60, 0.8);
                border: 1px solid #888;
                border-radius: 6px;
                color: white;
                font-size: 12px;
                padding: 8px;
            }
            QPushButton:hover {
                background-color: rgba(80, 80, 80, 0.9);
                border: 1px solid #AAA;
            }
        """)
        
        # Widget central
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Layout principal
        main_layout = QVBoxLayout(central_widget)
        main_layout.setSpacing(0)
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        # Header com botão config (posição absoluta)
        self.config_btn = QPushButton("⚙️", self)
        self.config_btn.setFixedSize(40, 40)
        self.config_btn.move(self.width() - 60, 20)
        self.config_btn.setStyleSheet("""
            QPushButton {
                background-color: rgba(0, 0, 0, 0.3);
                border: 1px solid rgba(255, 255, 255, 0.3);
                border-radius: 20px;
                font-size: 16px;
            }
            QPushButton:hover {
                background-color: rgba(0, 0, 0, 0.5);
            }
        """)
        self.config_btn.clicked.connect(self.on_config)
        
        # Spacer superior
        main_layout.addStretch()
        
        # Logo/Título
        self.logo = QLabel()
        self.logo.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Carrega logo da URL
        logo_url = "https://github.com/Comquister/MinecraftBR-Launcher/blob/main/logo.png?raw=true"
        try:
            response = requests.get(logo_url, timeout=10)
            if response.status_code == 200:
                pixmap = QPixmap()
                pixmap.loadFromData(response.content)
                self.logo.setPixmap(pixmap.scaledToWidth(300, Qt.TransformationMode.SmoothTransformation))
        except Exception as e:
            print(f"Erro ao carregar logo: {e}")

        main_layout.addWidget(self.logo)

        
        # Container centralizado com tamanho fixo
        container_wrapper = QHBoxLayout()
        container_wrapper.addStretch()
        
        container = QWidget()
        container.setFixedSize(330, 400)  # Tamanho fixo
        container.setStyleSheet("""
            QWidget {
                background-color: rgba(0, 0, 0, 0.7);
                border-radius: 15px;
                border: 1px solid rgba(255, 255, 255, 0.1);
            }
        """)
        container_layout = QVBoxLayout(container)
        container_layout.setSpacing(20)
        container_layout.setContentsMargins(40, 30, 40, 30)
        
        # Campo de usuário
        # user_label = QLabel("Usuário")
        # user_label.setStyleSheet("font-size: 14px; color: #CCCCCC; margin-bottom: 5px;")
        # container_layout.addWidget(user_label)
        
        self.user_display = QLabel("Nome de usuário ou e-mail")
        self.user_display.setStyleSheet("""
            QLabel {
                background-color: rgba(40, 40, 40, 0.8);
                border: 1px solid #666;
                border-radius: 6px;
                padding: 6px 6px;
                font-size: 14px;
                color: #CCCCCC;
            }
        """)
        container_layout.addWidget(self.user_display)
        
        # Opções de login
        login_options_layout = QVBoxLayout()
        login_options_layout.setSpacing(10)
        
        # Radio buttons para login
        self.login_group = QButtonGroup()
        
        # Último login se existir
        if self.last_login_data:
            login_type = self.last_login_data['type']
            if login_type == 'microsoft':
                email = self.last_login_data['data'].get('email', 'Email Microsoft')
                text = f"🔄 Último: {email[:10] + "..." if len(email) > 10 else email}"
            else:
                username = self.last_login_data['data'].get('username', 'Jogador')
                text = f"🔄 Último: {username}"
            
            self.last_radio = QRadioButton(text)
            self.last_radio.setChecked(True)
            self.login_group.addButton(self.last_radio, 0)
            login_options_layout.addWidget(self.last_radio)
            
            # Configura último login automaticamente
            self._setup_last_login()
        
        # Microsoft
        self.microsoft_radio = QRadioButton("🔐 Microsoft")
        self.login_group.addButton(self.microsoft_radio, 1)
        login_options_layout.addWidget(self.microsoft_radio)
        
        # Offline
        self.offline_radio = QRadioButton("👤 Offline")
        self.login_group.addButton(self.offline_radio, 2)
        login_options_layout.addWidget(self.offline_radio)
        
        # Conecta eventos
        self.login_group.buttonClicked.connect(self.on_login_selection)
        
        container_layout.addLayout(login_options_layout)
        
        # Botão jogar com progresso integrado
        self.play_btn = QPushButton("JOGAR")
        self.play_btn.setFixedHeight(50)
        self.play_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                        stop: 0 #4CAF50, stop: 1 #45a049);
                color: white;
                border: none;
                border-radius: 8px;
                font-size: 18px;
                font-weight: bold;
                text-transform: uppercase;
            }
            QPushButton:hover {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                        stop: 0 #5CBF60, stop: 1 #4CAF50);
            }
            QPushButton:disabled {
                background-color: #666666;
                color: #CCCCCC;
            }
            QPushButton:pressed {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                        stop: 0 #45a049, stop: 1 #3d8b40);
            }
        """)
        self.play_btn.clicked.connect(self.on_play)
        
        # Habilita se tiver último login
        self.play_btn.setEnabled(bool(self.last_login_data))
        
        container_layout.addWidget(self.play_btn)
        
        # Status
        status_layout = QHBoxLayout()
        self.status_label = QLabel("Pronto para jogar" if self.last_login_data else "Selecione o tipo de login")
        self.status_label.setStyleSheet("font-size: 12px; padding: 8px 12px; color: #CCCCCC;")
        status_layout.addWidget(self.status_label)
        status_layout.addStretch()
        
        about_btn = QPushButton("Sobre")
        about_btn.setStyleSheet("""
            QPushButton {
                background: transparent;
                border: none;
                color: #888888;
                font-size: 12px;
                text-decoration: underline;
            }
            QPushButton:hover {
                color: #CCCCCC;
            }
        """)
        status_layout.addWidget(about_btn)
        
        container_layout.addLayout(status_layout)
        
        # Adiciona container ao wrapper
        container_wrapper.addWidget(container)
        container_wrapper.addStretch()
        
        # Adiciona wrapper ao layout principal
        wrapper_widget = QWidget()
        wrapper_widget.setLayout(container_wrapper)
        main_layout.addWidget(wrapper_widget)
        
        # Spacer inferior
        main_layout.addStretch()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        # Reposiciona o botão config
        self.config_btn.move(self.width() - 60, 20)

    def update_play_button_progress(self, progress, text=""):
        if progress == 0:
            # Estado normal
            self.play_btn.setText("JOGAR")
            self.play_btn.setStyleSheet("""
                QPushButton {
                    background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                            stop: 0 #4CAF50, stop: 1 #45a049);
                    color: white;
                    border: none;
                    border-radius: 8px;
                    font-size: 18px;
                    font-weight: bold;
                    text-transform: uppercase;
                }
            """)
        else:
            # Estado de progresso
            progress_text = f"{progress}%" if not text else text
            self.play_btn.setText(progress_text)
            
            # Corrige o gradiente de progresso
            progress_percent = max(0.0, min(1.0, progress / 100.0))  # Garante que esteja entre 0 e 1
            stop_point = max(0.01, progress_percent)  # Evita valores muito próximos
            
            self.play_btn.setStyleSheet(f"""
                QPushButton {{
                    background: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 0,
                                            stop: 0 #2196F3,
                                            stop: {progress_percent:.2f} #2196F3,
                                            stop: {stop_point:.2f} #424242,
                                            stop: 1 #424242);
                    color: white;
                    border: none;
                    border-radius: 8px;
                    font-size: 16px;
                    font-weight: bold;
                }}
            """)

    def load_background(self):
        """Carrega background customizado ou usa gradiente padrão"""
        try:
            bg_path = download_background(self.game_dir)
            if bg_path:
                pixmap = QPixmap(str(bg_path))
                if not pixmap.isNull():
                    # aumenta a escala (exemplo: 4x maior → 64x64)
                    scale = 5
                    scaled_pixmap = pixmap.scaled(
                        pixmap.width() * scale,
                        pixmap.height() * scale,
                        Qt.AspectRatioMode.IgnoreAspectRatio,
                        Qt.TransformationMode.FastTransformation
                    )

                    brush = QBrush(scaled_pixmap)
                    palette = QPalette()
                    palette.setBrush(QPalette.ColorRole.Window, brush)
                    self.setPalette(palette)
                    return
        except Exception as e:
            print(f"Erro ao carregar background customizado: {e}")

    def _setup_last_login(self):
        if not self.last_login_data:
            return
            
        login_type = self.last_login_data['type']
        login_data = self.last_login_data['data']
        
        if login_type == 'offline':
            username = login_data.get('username', 'Jogador')
            if username:
                self.username = username
                self.user_display.setText(f"Offline: {username}")
                self.user_display.setStyleSheet(self.user_display.styleSheet() + "color: #FFFFFF;")
        elif login_type == 'microsoft':
            email = login_data.get('email', 'Email Microsoft')
            username = login_data.get('username', 'Usuário')
            self.user_display.setText(f"Microsoft: {username}")
            self.user_display.setStyleSheet(self.user_display.styleSheet() + "color: #FFFFFF;")

    def on_login_selection(self, button):
        button_id = self.login_group.id(button)
        
        if button_id == 0 and self.last_login_data:  # Último login
            self._handle_last_login()
        elif button_id == 1:  # Microsoft
            self._handle_microsoft_login()
        elif button_id == 2:  # Offline
            self._handle_offline_login()

    def _handle_last_login(self):
        if not self.last_login_data:
            return
            
        login_type = self.last_login_data['type']
        login_data = self.last_login_data['data']
        
        if login_type == 'microsoft':
            email = login_data.get('email', '')
            username = login_data.get('username', 'Usuário')
            if email:
                self.user_display.setText(f"Microsoft: {username}")
                self.user_display.setStyleSheet(self.user_display.styleSheet() + "color: #FFFFFF;")
                self.status_label.setText("Clique em JOGAR para reautenticar")
                self.play_btn.setEnabled(True)
        else:
            username = login_data.get('username', '')
            if username:
                self.username = username
                self.user_display.setText(f"Offline: {username}")
                self.user_display.setStyleSheet(self.user_display.styleSheet() + "color: #FFFFFF;")
                self.status_label.setText(f"Pronto para jogar como {username} (Offline)")
                self.play_btn.setEnabled(True)

    def _handle_microsoft_login(self):
        email, ok = QInputDialog.getText(self, "Login Microsoft", "Digite seu email Microsoft:")
        if ok and email.strip():
            self.user_display.setText(email.strip())
            self.user_display.setStyleSheet(self.user_display.styleSheet() + "color: #FFFFFF;")
            self.status_label.setText("Clique em JOGAR para autenticar")
            self.play_btn.setEnabled(True)
            self._pending_auth_email = email.strip()

    def _handle_offline_login(self):
        default_name = ""
        if self.last_login_data and self.last_login_data['type'] == 'offline':
            default_name = self.last_login_data['data'].get('username', os.getlogin())
        else:
            default_name = os.getlogin()
            
        username, ok = QInputDialog.getText(self, "Login Offline", "Nome do jogador:", text=default_name)
        if ok and username.strip():
            self.username = username.strip()
            self.auth_session = None
            self.user_display.setText(self.username)
            self.user_display.setStyleSheet(self.user_display.styleSheet() + "color: #FFFFFF;")
            self.status_label.setText(f"Pronto para jogar como {self.username} (Offline)")
            self.play_btn.setEnabled(True)
            save_login_data(self.game_dir, 'offline', {'username': self.username})

    def _start_auth(self, email):
        if self.auth_thread and self.auth_thread.isRunning():
            return
            
        self.auth_thread = AuthThread(email)
        self.auth_thread.auth_success.connect(self._on_auth_success)
        self.auth_thread.auth_error.connect(self._on_auth_error)
        self.auth_thread.start()
    
    def _on_auth_success(self, auth_session, email):
        self.auth_session = auth_session
        self.username = None
        username = getattr(auth_session, 'username', 'Usuário')
        
        self.user_display.setText(f"{username} ({email})")
        self.user_display.setStyleSheet(self.user_display.styleSheet() + "color: #FFFFFF;")
        self.status_label.setText(f"Autenticado como {username}. Iniciando jogo...")
        
        save_login_data(self.game_dir, 'microsoft', {'email': email, 'username': username})
        
        # Inicia o jogo automaticamente após autenticação bem-sucedida
        self.update_play_button_progress(10, "PREPARANDO...")
        
        self.minecraft_thread = MinecraftThread(self.game_dir, self.auth_session, self.username)
        self.minecraft_thread.status_update.connect(self.status_label.setText)
        self.minecraft_thread.progress_update.connect(self.on_progress_update)
        self.minecraft_thread.error_occurred.connect(self._on_minecraft_error)
        self.minecraft_thread.finished_success.connect(self.close)
        self.minecraft_thread.start()

    def _on_auth_error(self, error):
        self.play_btn.setEnabled(True)
        self.update_play_button_progress(0)  # Reseta o botão
        self.status_label.setText(f"Erro na autenticação: {error}")
        QMessageBox.critical(self, "Erro", f"Erro no login: {error}")

    def on_play(self):
        # Verifica se precisa fazer login primeiro
        selected_button = self.login_group.checkedButton()
        if not selected_button:
            QMessageBox.warning(self, "Aviso", "Selecione um tipo de login primeiro!")
            return
        
        button_id = self.login_group.id(selected_button)
        
        # Se é último login Microsoft ou novo Microsoft, inicia autenticação
        if ((button_id == 0 and self.last_login_data and self.last_login_data['type'] == 'microsoft') or 
            (button_id == 1)):
            
            if not self.auth_session:  # Precisa autenticar
                if button_id == 0:  # Último login
                    email = self.last_login_data['data'].get('email', '')
                else:  # Novo Microsoft
                    email = getattr(self, '_pending_auth_email', '')
                
                if not email:
                    QMessageBox.warning(self, "Erro", "Email não encontrado!")
                    return
                
                self.play_btn.setEnabled(False)
                self.status_label.setText("Autenticando...")
                self.update_play_button_progress(5, "AUTENTICANDO...")
                self._start_auth(email)
                return
        
        # Verificação final antes de iniciar
        if not self.auth_session and not self.username:
            QMessageBox.warning(self, "Aviso", "Configuração de login inválida!")
            return
        
        self.play_btn.setEnabled(False)
        self.update_play_button_progress(5, "INICIANDO...")
        
        self.minecraft_thread = MinecraftThread(self.game_dir, self.auth_session, self.username)
        self.minecraft_thread.status_update.connect(self.status_label.setText)
        self.minecraft_thread.progress_update.connect(self.on_progress_update)
        self.minecraft_thread.error_occurred.connect(self._on_minecraft_error)
        self.minecraft_thread.finished_success.connect(self.close)
        self.minecraft_thread.start()

    def on_progress_update(self, progress):
        self.current_progress = progress
        self.update_play_button_progress(progress)

    def _on_minecraft_error(self, error):
        self.status_label.setText("Erro ao iniciar")
        self.update_play_button_progress(0)  # Reseta o botão
        self.play_btn.setEnabled(True)
        QMessageBox.critical(self, "Erro", f"Erro: {error}")

    def on_config(self):
        game_dir_str = str(self.game_dir)
        
        info = f"""Configurações:

📁 Diretório: {game_dir_str}
🎮 Versão: {CONFIG['MINECRAFT_VERSION']}
💾 RAM: {CONFIG['RAM_SIZE']}

Deseja abrir o diretório do jogo?"""
        
        reply = QMessageBox.question(self, "Configurações", info,
                                   QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        
        if reply == QMessageBox.StandardButton.Yes:
            try:
                if os.name == 'nt':
                    os.startfile(game_dir_str)
                else:
                    subprocess.run(['xdg-open', game_dir_str])
            except Exception as e:
                QMessageBox.critical(self, "Erro", f"Erro ao abrir diretório: {e}")

def main():
    # Para debug - descomente a linha abaixo se precisar diagnosticar
    # diagnose_jvm_issues()
    
    app = QApplication(sys.argv)
    app.setApplicationName("MinecraftBr Launcher")
    
    launcher = MinecraftLauncher()
    launcher.show()
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()