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
import sys, platform, psutil, zipfile, subprocess, json, hashlib, random, concurrent.futures, pickle, webbrowser, requests, time, threading, os, shutil, logging
from pathlib import Path
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QRadioButton, QButtonGroup, QInputDialog, QMessageBox)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt6.QtGui import QPixmap, QPalette, QBrush, QIcon
from portablemc.standard import Version, Context
from portablemc.fabric import FabricVersion
from portablemc.forge import ForgeVersion, _NeoForgeVersion
from portablemc.auth import MicrosoftAuthSession
from flask import Flask, request
def calculate_optimal_ram():
    total_ram_gb = psutil.virtual_memory().total / (1024**3)
    available_ram_gb = max(1, total_ram_gb - 2)
    optimal_ram_gb = min(available_ram_gb * 0.7, 12)
    return max(1, int(optimal_ram_gb * 1024))
def calculate_sha256(file_path):
    """Calcula SHA256 de um arquivo"""
    sha256_hash = hashlib.sha256()
    try:
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return f"sha256:{sha256_hash.hexdigest()}"
    except Exception:
        return None
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
releasesgithub = requests.get("https://api.github.com/repos/Comquister/MinecraftBR-Modpack/releases/latest").json()["assets"]
CONFIG = {
    'Title': 'MinecraftBr Launcher',
    'GameDir': Path(os.getenv("APPDATA")) / ".minecraftbr",
    'RAM_SIZE': f"{calculate_optimal_ram()}M",
    'CLIENT_ID': "708e91b5-99f8-4a1d-80ec-e746cbb24771",
    'MRPACK_URL': str(next(a["browser_download_url"] for a in releasesgithub if a["name"].endswith(".mrpack"))),
    'MRPACK_HASH': str(next(a["digest"] for a in releasesgithub if a["name"].endswith(".mrpack"))),
    'PORTWEB': random.randint(49152, 65535)
}
CONFIG['REDIRECT_URI'] = f"http://localhost:{CONFIG['PORTWEB']}/code"
CONFIG_PROTECTION = {'enabled': (CONFIG['GameDir'] / "options.txt").exists(), 'protected_files': ['config/distanthorizons.toml', 'options.txt', 'servers.dat']}
auth_data = {'success': None, 'code': None, 'id_token': None}
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
def is_protected_file(file_path): return CONFIG_PROTECTION['enabled'] and any(str(file_path).replace('\\', '/').endswith(protected) for protected in CONFIG_PROTECTION.get('protected_files', []))
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
class ModDownloader:
    def __init__(self, game_dir, progress_callback=None):
        self.game_dir = game_dir
        self.progress_callback = progress_callback
        self.download_stats = {'total': 0, 'completed': 0, 'failed': 0, 'skipped': 0}
        self.stats_lock = threading.Lock()
    def _update_progress(self):
        with self.stats_lock:
            total = self.download_stats['total']
            completed = self.download_stats['completed'] + self.download_stats['failed'] + self.download_stats['skipped']
            if total > 0 and self.progress_callback:
                progress = int((completed / total) * 100)
                self.progress_callback(40 + int(progress * 0.15))
    def _download_single_mod(self, file_info):
        try:
            file_path = Path(file_info['path'])
            full_path = self.game_dir / file_path
            full_path.parent.mkdir(parents=True, exist_ok=True)
            expected_sha256 = file_info.get('hashes', {}).get('sha256')
            if full_path.exists() and expected_sha256:
                current_hash = calculate_sha256(full_path)
                if current_hash == expected_sha256:
                    with self.stats_lock:
                        self.download_stats['skipped'] += 1
                    self._update_progress()
                    return {'status': 'skipped', 'file': str(file_path)}
            downloads = file_info.get('downloads', [])
            if not downloads:
                with self.stats_lock:
                    self.download_stats['failed'] += 1
                self._update_progress()
                return {'status': 'failed', 'file': str(file_path), 'error': 'No download URLs'}
            for attempt, download_url in enumerate(downloads):
                try:
                    timeout = min(120, max(30, file_info.get('fileSize', 1000000) // 100000))
                    response = requests.get(
                        download_url, 
                        timeout=timeout,
                        stream=True,
                        headers={'User-Agent': 'MinecraftBR-Launcher/1.0'}
                    )
                    response.raise_for_status()
                    total_size = int(response.headers.get('content-length', 0))
                    downloaded = 0
                    with open(full_path, 'wb') as f:
                        for chunk in response.iter_content(chunk_size=8192):
                            if chunk:
                                f.write(chunk)
                                downloaded += len(chunk)
                    if expected_sha256:
                        downloaded_hash = calculate_sha256(full_path)
                        if downloaded_hash != expected_sha256:
                            full_path.unlink()
                            if attempt == len(downloads) - 1:
                                raise Exception(f"Hash incorreto: esperado {expected_sha256}, obtido {downloaded_hash}")
                            continue
                    with self.stats_lock:
                        self.download_stats['completed'] += 1
                    self._update_progress()
                    return {'status': 'success', 'file': str(file_path)}
                except Exception as e:
                    if full_path.exists():
                        full_path.unlink()
                    if attempt == len(downloads) - 1:
                        with self.stats_lock:
                            self.download_stats['failed'] += 1
                        self._update_progress()
                        return {'status': 'failed', 'file': str(file_path), 'error': str(e)}
        except Exception as e:
            with self.stats_lock:
                self.download_stats['failed'] += 1
            self._update_progress()
            return {'status': 'failed', 'file': file_info.get('path', 'unknown'), 'error': str(e)}
    def download_mods_parallel(self, files_list, max_workers=None):
        if not files_list:
            return {'success': True, 'results': []}
        if max_workers is None:
            cpu_count = psutil.cpu_count(logical=False) or 4
            max_workers = min(cpu_count * 2, 8)
        files_to_process = []
        for file_info in files_list:
            file_path = Path(file_info['path'])
            full_path = self.game_dir / file_path
            expected_sha256 = file_info.get('hashes', {}).get('sha256')
            needs_download = True
            if full_path.exists() and expected_sha256:
                current_hash = calculate_sha256(full_path)
                if current_hash == expected_sha256:
                    needs_download = False 
            if needs_download:
                files_to_process.append(file_info)
        print(f"Iniciando download paralelo: {len(files_to_process)} arquivos com {max_workers} workers")
        self.download_stats = {
            'total': len(files_list),
            'completed': len(files_list) - len(files_to_process),
            'failed': 0,
            'skipped': len(files_list) - len(files_to_process)
        }
        if not files_to_process:
            print("Todos os mods já estão atualizados")
            return {'success': True, 'results': []}
        results = []
        failed_downloads = []
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers, thread_name_prefix="ModDownload") as executor:
            future_to_file = {
                executor.submit(self._download_single_mod, file_info): file_info 
                for file_info in files_to_process
            }
            for future in concurrent.futures.as_completed(future_to_file):
                file_info = future_to_file[future]
                try:
                    result = future.result(timeout=300)
                    results.append(result)
                    if result['status'] == 'failed':
                        failed_downloads.append({
                            'file': result['file'],
                            'error': result.get('error', 'Unknown error')
                        })
                except concurrent.futures.TimeoutError:
                    failed_downloads.append({
                        'file': file_info.get('path', 'unknown'),
                        'error': 'Download timeout'
                    })
                    with self.stats_lock:
                        self.download_stats['failed'] += 1
                    self._update_progress()
                except Exception as e:
                    failed_downloads.append({
                        'file': file_info.get('path', 'unknown'),
                        'error': str(e)
                    })
                    with self.stats_lock:
                        self.download_stats['failed'] += 1
                    self._update_progress()
        with self.stats_lock:
            total = self.download_stats['total']
            completed = self.download_stats['completed']
            failed = self.download_stats['failed']
            skipped = self.download_stats['skipped']
        print(f"Download concluído: {completed} sucessos, {failed} falhas, {skipped} pulados de {total} total")
        if failed_downloads:
            print("Falhas de download:")
            for fail in failed_downloads[:5]:
                print(f"  - {fail['file']}: {fail['error']}")
            if len(failed_downloads) > 5:
                print(f"  ... e mais {len(failed_downloads) - 5} falhas")
        return {
            'success': failed == 0,
            'results': results,
            'stats': self.download_stats,
            'failed_downloads': failed_downloads
        }
class AuthThread(QThread):
    auth_success = pyqtSignal(object, str)
    auth_error = pyqtSignal(str)
    
    def __init__(self, email):
        super().__init__()
        self.email = email
    
    def run(self):
        try:
            self.game_dir.mkdir(exist_ok=True)
            
            self.status_update.emit("Verificando modpack...")
            self.progress_update.emit(5)
            
            if not self._sync_mrpack():
                raise Exception("Falha na sincronização do modpack")
                
            minecraft_version = self._get_minecraft_version_from_mrpack()
            modloader_info = self._get_modloader_from_mrpack()
            
            if not minecraft_version:
                raise Exception("Versão do Minecraft não encontrada")
                
            print(f"Iniciando {minecraft_version} com {modloader_info['name']}")
            
            self.status_update.emit(f"Preparando {minecraft_version}...")
            self.progress_update.emit(60)
            
            # Criação da versão com timeout
            version = self._create_version(minecraft_version, modloader_info)
            
            self.status_update.emit("Instalando componentes...")
            self.progress_update.emit(75)
            
            # Instalação com timeout
            env = self._install_with_timeout(version)
            
            self.status_update.emit("Configurando JVM...")
            self._configure_jvm(env)
            
            self.status_update.emit("Iniciando jogo...")
            self.progress_update.emit(95)
            
            print("Tudo pronto - iniciando Minecraft...")
            self.finished_success.emit()
            
            # Pequena pausa antes de iniciar
            time.sleep(1)
            env.run()
            
        except Exception as e:
            import traceback
            error_msg = f"Erro: {str(e)}\nDetalhes: {traceback.format_exc()}"
            print(f"ERRO CRÍTICO: {error_msg}")
            self.error_occurred.emit(str(e))

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
        self.mrpack_data = None
    def run(self):
        try:
            self.game_dir.mkdir(exist_ok=True)
            self.status_update.emit("Verificando modpack...")
            self.progress_update.emit(5)
            if not self._sync_mrpack():
                self.error_occurred.emit("Erro ao sincronizar modpack")
                return
            minecraft_version = self._get_minecraft_version_from_mrpack()
            modloader_info = self._get_modloader_from_mrpack()
            if not minecraft_version:
                self.error_occurred.emit("Versão do Minecraft não encontrada no modpack")
                return
            self.status_update.emit(f"Preparando {minecraft_version} com {modloader_info['name']}...")
            self.progress_update.emit(60)
            if modloader_info['name'] == 'fabric-loader':
                version = FabricVersion.with_fabric(minecraft_version, modloader_info['version'], context=self.context)
            elif modloader_info['name'] == 'forge':
                version = ForgeVersion(f"{minecraft_version}-{modloader_info['version']}", context=self.context)
            elif modloader_info['name'] == 'neoforge':
                version = _NeoForgeVersion(modloader_info['version'], context=self.context)
            else:
                version = Version(minecraft_version, context=self.context)
            if self.auth_session:
                version.auth_session = self.auth_session
            else:
                version.set_auth_offline(self.username, None)
            self.status_update.emit("Instalando componentes...")
            self.progress_update.emit(75)
            env = version.install()
            self.status_update.emit("Configurando JVM...")
            is_64bit = platform.machine().endswith('64')
            ram_mb = int(CONFIG['RAM_SIZE'].replace('M', ''))
            if not is_64bit and ram_mb > 3072:
                ram_mb = 3072
                self.status_update.emit("Sistema 32-bit detectado, limitando RAM a 3GB...")
            ram_size = f"{ram_mb}M"
            jvm_args = [
                f"-Xmx{ram_size}",
                f"-Xms{min(512, ram_mb)}M",
                "-XX:+UseG1GC",
                "-XX:+UnlockExperimentalVMOptions",
                "-XX:G1NewSizePercent=20",
                "-XX:G1ReservePercent=20",
                "-XX:MaxGCPauseMillis=50",
                "-XX:G1HeapRegionSize=32M",
                "-Djava.awt.headless=false",
                "-Dfile.encoding=UTF-8"
            ]
            if os.name == 'nt':
                jvm_args.extend([
                    "-Dos.name=Windows 10",
                    "-Dos.version=10.0"
                ])
            original_jvm_args = env.jvm_args.copy()
            java_executable = original_jvm_args[0] if original_jvm_args else "java"
            filtered_original_args = []
            for arg in original_jvm_args[1:]:
                if not any(arg.startswith(prefix) for prefix in ['-Xmx', '-Xms', '-XX:+UseG1GC']):
                    filtered_original_args.append(arg)
            env.jvm_args = [java_executable] + jvm_args + filtered_original_args
            self.status_update.emit("Iniciando jogo...")
            self.progress_update.emit(100)
            self.finished_success.emit()
            env.run()
        except Exception as e:
            import traceback
            error_msg = f"Erro: {str(e)}\nDetalhes: {traceback.format_exc()}"
            print(error_msg)
            self.error_occurred.emit(str(e))
    def _create_version(self, minecraft_version, modloader_info):
        try:
            if modloader_info['name'] == 'fabric-loader':
                version = FabricVersion.with_fabric(minecraft_version, modloader_info['version'], context=self.context)
            elif modloader_info['name'] == 'forge':
                version = ForgeVersion(f"{minecraft_version}-{modloader_info['version']}", context=self.context)
            elif modloader_info['name'] == 'neoforge':
                version = _NeoForgeVersion(modloader_info['version'], context=self.context)
            else:
                version = Version(minecraft_version, context=self.context)
                
            # Configurar autenticação
            if self.auth_session:
                version.auth_session = self.auth_session
            else:
                version.set_auth_offline(self.username, None)
                
            return version
            
        except Exception as e:
            print(f"Erro ao criar versão: {e}")
            raise e
    def _install_with_timeout(self, version):
        try:
            # Timeout de 5 minutos para instalação
            import signal
            
            def timeout_handler(signum, frame):
                raise TimeoutError("Timeout na instalação do Minecraft")
                
            if hasattr(signal, 'SIGALRM'):  # Unix/Linux
                signal.signal(signal.SIGALRM, timeout_handler)
                signal.alarm(300)  # 5 minutos
                
            env = version.install()
            
            if hasattr(signal, 'SIGALRM'):
                signal.alarm(0)  # Cancela timeout
                
            return env
            
        except TimeoutError:
            print("Timeout na instalação - processo pode estar travado")
            raise Exception("Timeout na instalação do Minecraft")
        except Exception as e:
            print(f"Erro na instalação: {e}")
            raise e
    def _configure_jvm(self, env):
        try:
            is_64bit = platform.machine().endswith('64')
            ram_mb = int(CONFIG['RAM_SIZE'].replace('M', ''))
            
            if not is_64bit and ram_mb > 3072:
                ram_mb = 3072
                print("Sistema 32-bit - RAM limitada a 3GB")
                
            ram_size = f"{ram_mb}M"
            
            # Argumentos JVM otimizados
            jvm_args = [
                f"-Xmx{ram_size}",
                f"-Xms{min(512, ram_mb)}M",
                "-XX:+UseG1GC",
                "-XX:+UnlockExperimentalVMOptions",
                "-XX:G1NewSizePercent=20",
                "-XX:G1ReservePercent=20",
                "-XX:MaxGCPauseMillis=50",
                "-XX:G1HeapRegionSize=32M",
                "-Djava.awt.headless=false",
                "-Dfile.encoding=UTF-8",
                "-XX:+DisableExplicitGC"  # Previne GC explícito
            ]
            
            if os.name == 'nt':
                jvm_args.extend([
                    "-Dos.name=Windows 10",
                    "-Dos.version=10.0"
                ])
                
            # Preservar Java executable
            original_args = env.jvm_args.copy()
            java_executable = original_args[0] if original_args else "java"
            
            # Filtrar argumentos conflitantes
            filtered_args = []
            skip_prefixes = ['-Xmx', '-Xms', '-XX:+UseG1GC']
            
            for arg in original_args[1:]:
                if not any(arg.startswith(prefix) for prefix in skip_prefixes):
                    filtered_args.append(arg)
                    
            env.jvm_args = [java_executable] + jvm_args + filtered_args
            print(f"JVM configurada: {ram_size} RAM")
            
        except Exception as e:
            print(f"Erro na configuração JVM: {e}")
            raise e
    def _sync_mrpack(self):
        """Sincroniza o arquivo .mrpack e extrai seus conteúdos"""
        try:
            mrpack_path = self.game_dir / "modpack.zip"
            mrpack_hash_path = self.game_dir / "modpack.zip.sha256"
            
            # Verifica se precisa baixar
            needs_download = True
            
            if mrpack_path.exists() and CONFIG.get('MRPACK_HASH'):
                # Compara hash local com hash remoto do GitHub
                try:
                    remote_hash = CONFIG['MRPACK_HASH']
                    local_hash = calculate_sha256(mrpack_path)
                    if local_hash and local_hash == remote_hash:
                        needs_download = False
                        print(f"Hash local coincide com remoto: {local_hash}")
                    else:
                        print(f"Hash local ({local_hash}) != Hash remoto ({remote_hash})")
                except Exception as e:
                    print(f"Erro ao verificar hash: {e}")
            
            if needs_download:
                self.status_update.emit("Baixando modpack...")
                self.progress_update.emit(10)
                
                # Baixa o arquivo .mrpack
                response = requests.get(CONFIG['MRPACK_URL'], stream=True, timeout=120)
                response.raise_for_status()
                
                total_size = int(response.headers.get('content-length', 0))
                downloaded = 0
                
                with open(mrpack_path, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
                            downloaded += len(chunk)
                            if total_size > 0:
                                progress = 10 + int((downloaded / total_size) * 20)
                                self.progress_update.emit(progress)
                
                # Sempre calcula e salva o hash do arquivo baixado
                hash_value = calculate_sha256(mrpack_path)
                if hash_value:
                    with open(mrpack_hash_path, 'w') as f:
                        f.write(hash_value)
                    print(f"Hash calculado e salvo: {hash_value}")
                
                # Verifica se o hash do arquivo baixado coincide com o esperado
                if CONFIG.get('MRPACK_HASH') and hash_value != CONFIG['MRPACK_HASH']:
                    print(f"AVISO: Hash do arquivo baixado ({hash_value}) não coincide com esperado ({CONFIG['MRPACK_HASH']})")
            else:
                print("Arquivo já está atualizado, pulando download")
            
            self.status_update.emit("Extraindo modpack...")
            self.progress_update.emit(35)
            
            # Extrai e processa o .mrpack
            return self._extract_mrpack(mrpack_path)
            
        except Exception as e:
            print(f"Erro na sincronização do mrpack: {e}")
            return False
    def _extract_mrpack(self, mrpack_path):
        try:
            temp_dir = self.game_dir / "temp_mrpack"
            if temp_dir.exists():
                shutil.rmtree(temp_dir)
            temp_dir.mkdir()
            with zipfile.ZipFile(mrpack_path, 'r') as zip_ref:
                zip_ref.extractall(temp_dir)
            index_path = temp_dir / "modrinth.index.json"
            if not index_path.exists():
                raise Exception("modrinth.index.json não encontrado no modpack")
            with open(index_path, 'r', encoding='utf-8') as f:
                self.mrpack_data = json.load(f)
            files = self.mrpack_data.get('files', [])
            mods_dir = self.game_dir / "mods"
            mods_dir.mkdir(exist_ok=True)
            self.status_update.emit("Limpando mods antigos...")
            self.progress_update.emit(35)
            self._clean_old_mods(mods_dir, files)
            self.status_update.emit("Baixando mods (paralelo)...")
            self.progress_update.emit(40)
            downloader = ModDownloader(self.game_dir, self.progress_update.emit)
            download_result = downloader.download_mods_parallel(files)
            if not download_result['success']:
                failed_count = len(download_result['failed_downloads'])
                if failed_count > len(files) * 0.1:  # Mais de 10% falharam
                    raise Exception(f"Muitas falhas no download: {failed_count} arquivos")
                else:
                    print(f"Download concluído com {failed_count} falhas menores")
            self.status_update.emit("Aplicando overrides...")
            self.progress_update.emit(55)
            self._apply_overrides(temp_dir)
            shutil.rmtree(temp_dir)
            return True
        except Exception as e:
            print(f"Erro na extração do mrpack: {e}")
            return False
    def _download_mod_file(self, file_info, base_dir):
        try:
            file_path = Path(file_info['path'])
            full_path = base_dir / file_path
            full_path.parent.mkdir(parents=True, exist_ok=True)
            expected_sha256 = file_info.get('hashes', {}).get('sha256')
            if full_path.exists() and expected_sha256:
                current_hash = calculate_sha256(full_path)
                if current_hash == expected_sha256:
                    return True
            downloads = file_info.get('downloads', [])
            if not downloads:
                print(f"Nenhuma URL de download para {file_path}")
                return False
            for download_url in downloads:
                try:
                    response = requests.get(download_url, timeout=60)
                    response.raise_for_status()
                    with open(full_path, 'wb') as f:
                        f.write(response.content)
                    if expected_sha256:
                        downloaded_hash = calculate_sha256(full_path)
                        if downloaded_hash != expected_sha256:
                            print(f"Hash incorreto para {file_path}")
                            full_path.unlink()
                            continue
                    return True
                except Exception as e:
                    print(f"Erro ao baixar {download_url}: {e}")
                    if full_path.exists():
                        full_path.unlink()
                    continue
            return False
        except Exception as e:
            print(f"Erro no download do arquivo {file_info.get('path', 'desconhecido')}: {e}")
            return False
    def _clean_old_mods(self, mods_dir, valid_files):
        try:
            if not mods_dir.exists():
                return
            valid_paths = set()
            for file_info in valid_files:
                file_path = file_info['path']
                if file_path.startswith('mods/'):
                    mod_path = Path(file_path[5:])
                    valid_paths.add(mod_path)
            temp_dir = self.game_dir / "temp_mrpack"
            override_dirs = ['overrides', 'client-overrides']
            for override_name in override_dirs:
                override_mods_path = temp_dir / override_name / "mods"
                if override_mods_path.exists():
                    for override_mod in override_mods_path.rglob('*'):
                        if override_mod.is_file():
                            relative_path = override_mod.relative_to(override_mods_path)
                            valid_paths.add(relative_path)
            for existing_file in mods_dir.rglob('*'):
                if existing_file.is_file():
                    relative_path = existing_file.relative_to(mods_dir)
                    if relative_path not in valid_paths:
                        existing_file.unlink()
                        print(f"Removido: {relative_path}")
        except Exception as e:
            print(f"Erro ao limpar mods antigos: {e}")
    def backup_protected_configs(self):
        backup_dir = self.game_dir / "config_backups"
        backup_dir.mkdir(exist_ok=True)
        backed_up = []
        for protected in CONFIG_PROTECTION.get('protected_files', []):
            config_path = self.game_dir / protected
            if config_path.exists():
                backup_path = backup_dir / f"{config_path.name}.backup"
                shutil.copy2(config_path, backup_path)
                backed_up.append(protected)
        return backed_up
    def restore_protected_configs(self):
        backup_dir = self.game_dir / "config_backups"
        if not backup_dir.exists(): return []
        restored = []
        for protected in CONFIG_PROTECTION.get('protected_files', []):
            config_path = self.game_dir / protected
            backup_path = backup_dir / f"{Path(protected).name}.backup"
            if backup_path.exists():
                config_path.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(backup_path, config_path)
                restored.append(protected)
        return restored
    def _get_minecraft_version_from_mrpack(self):
        try:
            if not self.mrpack_data:
                return None
            dependencies = self.mrpack_data.get('dependencies', {})
            return dependencies.get('minecraft')
        except Exception as e:
            print(f"Erro ao obter versão do Minecraft: {e}")
            return None
    def _get_modloader_from_mrpack(self):
        try:
            if not self.mrpack_data:
                return {'name': 'vanilla', 'version': None}
            dependencies = self.mrpack_data.get('dependencies', {})
            modloaders = [
                ('fabric-loader', 'fabric-loader'),
                ('forge', 'forge'),
                ('neoforge', 'neoforge'),
                ('quilt-loader', 'quilt-loader')
            ]
            for key, name in modloaders:
                if key in dependencies:
                    return {
                        'name': name,
                        'version': dependencies[key]
                    }
            return {'name': 'vanilla', 'version': None}
        except Exception as e:
            print(f"Erro ao obter modloader: {e}")
            return {'name': 'vanilla', 'version': None}
    def _apply_overrides(self, temp_dir):
        try:
            backed_up = self.backup_protected_configs() if CONFIG_PROTECTION['enabled'] else []
            if backed_up: print(f"Backup de configs protegidas: {backed_up}")
            
            override_dirs = ['overrides', 'client-overrides']
            files_applied = 0
            
            for override_name in override_dirs:
                override_path = temp_dir / override_name
                if override_path.exists() and override_path.is_dir():
                    for item in override_path.rglob('*'):
                        if item.is_file():
                            relative_path = item.relative_to(override_path)
                            target_path = self.game_dir / relative_path
                            
                            if is_protected_file(relative_path):
                                print(f"Arquivo protegido ignorado: {relative_path}")
                                continue
                                
                            target_path.parent.mkdir(parents=True, exist_ok=True)
                            shutil.copy2(item, target_path)
                            files_applied += 1
            
            print(f"Aplicados {files_applied} arquivos de override")
            
            if CONFIG_PROTECTION['enabled']:
                restored = self.restore_protected_configs()
                if restored: print(f"Configs restauradas: {restored}")
                
            # IMPORTANTE: Emitir sinal de progresso após completar
            self.progress_update.emit(58)
            print("Overrides aplicados com sucesso - continuando...")
            
        except Exception as e:
            print(f"Erro ao aplicar overrides: {e}")
            raise e  # Re-propaga o erro
class MinecraftLauncher(QMainWindow):
    def __init__(self):
        super().__init__()
        self.game_dir = CONFIG['GameDir']
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
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setSpacing(0)
        main_layout.setContentsMargins(0, 0, 0, 0)
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
        self.atalho = QPushButton("🏷️", self)
        self.atalho.setFixedSize(40, 40)
        self.atalho.move(20, 20)
        self.atalho.setStyleSheet("""
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
        self.atalho.clicked.connect(self.on_atalho)
        main_layout.addStretch()
        self.logo = QLabel()
        self.logo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        logo_url = "https://github.com/Comquister/MinecraftBR-Launcher/blob/main/image/logo.png?raw=true"
        try:
            response = requests.get(logo_url, timeout=10)
            if response.status_code == 200:
                pixmap = QPixmap()
                pixmap.loadFromData(response.content)
                self.logo.setPixmap(pixmap.scaledToWidth(300, Qt.TransformationMode.SmoothTransformation))
        except Exception as e:
            print(f"Erro ao carregar logo: {e}")
        main_layout.addWidget(self.logo)
        container_wrapper = QHBoxLayout()
        container_wrapper.addStretch()
        container = QWidget()
        container.setFixedSize(330, 400)
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
        login_options_layout = QVBoxLayout()
        login_options_layout.setSpacing(10)
        self.login_group = QButtonGroup()
        if self.last_login_data:
            login_type = self.last_login_data['type']
            if login_type == 'microsoft':
                email = self.last_login_data['data'].get('email', 'Email Microsoft')
                short_email = email[:10] + "..." if len(email) > 10 else email
                text = f"🔄 Último: {short_email}"
            else:
                username = self.last_login_data['data'].get('username', 'Jogador')
                text = f"🔄 Último: {username}"
            self.last_radio = QRadioButton(text)
            self.last_radio.setChecked(True)
            self.login_group.addButton(self.last_radio, 0)
            login_options_layout.addWidget(self.last_radio)
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
        about_btn.clicked.connect(self.on_about)
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
        self.update_play_button_progress(10, "PREPARANDO...")
        self.minecraft_thread = MinecraftThread(self.game_dir, self.auth_session, self.username)
        self.minecraft_thread.status_update.connect(self.status_label.setText)
        self.minecraft_thread.progress_update.connect(self.on_progress_update)
        self.minecraft_thread.error_occurred.connect(self._on_minecraft_error)
        self.minecraft_thread.finished_success.connect(self.close)
        self.minecraft_thread.start()
    def _on_auth_error(self, error):
        self.play_btn.setEnabled(True)
        self.update_play_button_progress(0)
        self.status_label.setText(f"Erro na autenticação: {error}")
        QMessageBox.critical(self, "Erro", f"Erro no login: {error}")
    def on_play(self):
        # Verificar se já existe thread rodando
        if self.minecraft_thread and self.minecraft_thread.isRunning():
            print("Processo já em andamento...")
            return
            
        selected_button = self.login_group.checkedButton()
        if not selected_button:
            QMessageBox.warning(self, "Aviso", "Selecione um tipo de login primeiro!")
            return
            
        button_id = self.login_group.id(selected_button)
        
        # Reset do estado
        self.current_progress = 0
        
        # Lógica de autenticação...
        if ((button_id == 0 and self.last_login_data and self.last_login_data['type'] == 'microsoft') or (button_id == 1)):
            if not self.auth_session:
                email = self.last_login_data['data'].get('email', '') if button_id == 0 else getattr(self, '_pending_auth_email', '')
                if not email:
                    QMessageBox.warning(self, "Erro", "Email não encontrado!")
                    return
                    
                self.play_btn.setEnabled(False)
                self.status_label.setText("Autenticando...")
                self.update_play_button_progress(5, "AUTENTICANDO...")
                self._start_auth(email)
                return
                
        if not self.auth_session and not self.username:
            QMessageBox.warning(self, "Aviso", "Configuração de login inválida!")
            return
            
        print(f"Iniciando com auth_session={bool(self.auth_session)}, username={self.username}")
        
        self.play_btn.setEnabled(False)
        self.update_play_button_progress(5, "INICIANDO...")
        
        self.minecraft_thread = MinecraftThread(self.game_dir, self.auth_session, self.username)
        self.minecraft_thread.status_update.connect(self.status_label.setText)
        self.minecraft_thread.progress_update.connect(self.on_progress_update)
        self.minecraft_thread.error_occurred.connect(self._on_minecraft_error)
        self.minecraft_thread.finished_success.connect(self._on_minecraft_success)
        self.minecraft_thread.start()
    def _on_minecraft_success(self):
        print("Minecraft iniciado com sucesso - fechando launcher")
        self.close()
    def on_progress_update(self, progress):
        self.current_progress = progress
        self.update_play_button_progress(progress)
    def _on_minecraft_error(self, error):
        print(f"Erro reportado pela thread: {error}")
        self.status_label.setText(f"Erro: {error}")
        self.update_play_button_progress(0)
        self.play_btn.setEnabled(True)
        
        # Cleanup da thread
        if self.minecraft_thread:
            self.minecraft_thread.quit()
            self.minecraft_thread.wait(5000)  # Aguarda 5s
            self.minecraft_thread = None
            
        QMessageBox.critical(self, "Erro", f"Falha ao iniciar Minecraft:\n{error}")
    def on_config(self):
        game_dir_str = str(self.game_dir)
        
        info = f"""Configurações:

📁 Diretório: {game_dir_str}
📦 Modpack: {CONFIG['MRPACK_URL']}
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
    def on_atalho(self):
        reply = QMessageBox.question(self, "Criar Atalho", "Deseja criar um atalho na área de trabalho?", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            try:
                if os.name == 'nt':
                    ps_cmd = f'$WshShell = New-Object -comObject WScript.Shell; $Shortcut = $WshShell.CreateShortcut("$([Environment]::GetFolderPath(\'Desktop\'))\\MinecraftBr.lnk"); $Shortcut.TargetPath = "{sys.argv[0]}"; $Shortcut.WorkingDirectory = "{os.path.dirname(sys.argv[0])}"; $Shortcut.Save()'
                    subprocess.run(['powershell', '-Command', ps_cmd], check=True)
                else:
                    desktop = os.path.join(os.path.expanduser('~'), 'Desktop')
                    shortcut_path = os.path.join(desktop, 'Launcher.desktop')
                    with open(shortcut_path, 'w') as f:
                        f.write(f"[Desktop Entry]\nType=Application\nName=Launcher\nExec=python {sys.argv[0]}\nPath={os.path.dirname(sys.argv[0])}\nTerminal=false")
                    os.chmod(shortcut_path, 0o755)
                QMessageBox.information(self, "Sucesso", "Atalho criado na área de trabalho!")
            except Exception as e:
                QMessageBox.critical(self, "Erro", f"Erro ao criar atalho: {e}")
    def on_about(self):
        about_text = f"""
{CONFIG['Title']}

🎮 Launcher personalizado para Minecraft
📦 Sistema de modpacks .mrpack
💾 RAM otimizada: {CONFIG['RAM_SIZE']}

Desenvolvido para a comunidade MinecraftBR
        """
        QMessageBox.about(self, "Sobre", about_text.strip())
class AutoUpdater:
    def __init__(self):
        self.github_api_url = "https://api.github.com/repos/Comquister/MinecraftBR-Launcher/releases/latest"
        self.current_exe_path = Path(sys.argv[0]).resolve()
        self.is_windows = platform.system() == "Windows"
    def calculate_exe_hash(self, file_path):
        try:
            sha256_hash = hashlib.sha256()
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(8192), b""):
                    sha256_hash.update(chunk)
            return sha256_hash.hexdigest()
        except Exception as e:
            print(f"Erro ao calcular hash do executável: {e}")
            return None
    def get_latest_release_info(self):
        try:
            response = requests.get(self.github_api_url, timeout=10)
            response.raise_for_status()
            release_data = response.json()
            exe_name = "MinecraftBr.exe" if self.is_windows else "MinecraftBr"
            for asset in release_data.get("assets", []):
                if asset["name"] == exe_name:
                    return {
                        "version": release_data["tag_name"],
                        "download_url": asset["browser_download_url"],
                        "size": asset["size"],
                        "hash": asset.get("digest", "").replace("sha256:", "") if asset.get("digest") else None,
                        "release_notes": release_data.get("body", "")
                    }
            print(f"Executável {exe_name} não encontrado nos assets da release")
            return None
        except Exception as e:
            print(f"Erro ao buscar informações de atualização: {e}")
            return None
    def needs_update(self):
        if not self.current_exe_path.exists():
            print("Executável atual não encontrado")
            return False, None
        release_info = self.get_latest_release_info()
        if not release_info:
            print("Não foi possível obter informações da release")
            return False, None
        current_hash = self.calculate_exe_hash(self.current_exe_path)
        if not current_hash:
            print("Não foi possível calcular hash do executável atual")
            return False, None
        remote_hash = release_info.get("hash")
        if not remote_hash:
            print("Hash remoto não disponível")
            return False, None
        needs_update = current_hash.lower() != remote_hash.lower()
        if needs_update:
            print(f"Atualização disponível:")
            print(f"  Versão: {release_info['version']}")
            print(f"  Hash atual: {current_hash}")
            print(f"  Hash remoto: {remote_hash}")
        else:
            print("Executável está atualizado")
        
        return needs_update, release_info
    
    def build_update_command(self, download_url, target_path):
        exe_name = os.path.basename(target_path)
        exe_dir = os.path.dirname(target_path)
        temp_exe = os.path.join(exe_dir, f"{exe_name}.new")
        if self.is_windows:
            resp = requests.get(download_url, timeout=30)
            with open(temp_exe, 'wb') as f: f.write(resp.content)
            cmd = f'Start-Sleep 2; Remove-Item -Force \\"{target_path}\\"; Move-Item \\"{temp_exe}\\" \\"{target_path}\\"; Add-Type -AssemblyName System.Windows.Forms; [System.Windows.Forms.MessageBox]::Show(\\"Atualização concluída! Você pode iniciar o aplicativo.\\", \\"Atualização\\", [System.Windows.Forms.MessageBoxButtons]::OK, [System.Windows.Forms.MessageBoxIcon]::Information)'
            return f'start powershell -c "{cmd}"'
        else:
            bash_cmd = f'''echo "Iniciando..."; url="{download_url}"; path="{target_path}"; bak="$path.backup"; tmp="$path.tmp"; pkill -f "$(basename "$path")" 2>/dev/null; sleep 2; [ -f "$path" ] && cp "$path" "$bak" && echo "Backup criado"; echo "Baixando..."; if curl -L -o "$tmp" "$url" --connect-timeout 30 --max-time 120; then [ -f "$path" ] && rm "$path"; mv "$tmp" "$path"; chmod +x "$path"; echo "Sucesso!"; [ -f "$bak" ] && rm "$bak"; else echo "Erro!"; [ -f "$bak" ] && mv "$bak" "$path" && echo "Backup restaurado"; fi; echo "Pressione Enter..."; read'''
            return f'bash -c "{bash_cmd}"'
    
    def start_update_process(self, release_info):
        try:
            commands = self.build_update_command(
                release_info["download_url"], 
                str(self.current_exe_path)
            )
            os.system(commands)
            sys.exit()
            
        except Exception as e:
            print(f"Erro ao iniciar processo de atualização: {e}")
            return False
    
    def check_and_update(self):
        try:
            needs_update, release_info = self.needs_update()
            
            if not needs_update:
                return True
            if not QApplication.instance():
                app = QApplication(sys.argv)
                app_created = True
            else:
                app_created = False
            version = release_info.get("version", "Desconhecida")
            size_mb = release_info.get("size", 0) / (1024 * 1024)
            message = f"""Nova versão disponível!

Versão atual: Desatualizada
Nova versão: {version}
Tamanho: {size_mb:.1f} MB

Deseja atualizar agora?

Notas da versão:
{release_info.get('release_notes', 'Sem notas disponíveis')[:200]}...
"""
            msg_box = QMessageBox()
            msg_box.setWindowTitle("Atualização Disponível")
            msg_box.setText(message)
            msg_box.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No | QMessageBox.StandardButton.Cancel)
            msg_box.button(QMessageBox.StandardButton.Yes).setText("Atualizar")
            msg_box.button(QMessageBox.StandardButton.No).setText("Continuar sem atualizar")
            msg_box.button(QMessageBox.StandardButton.Cancel).setText("Fechar")
            result = msg_box.exec()
            if app_created:
                app.quit()
            if result == QMessageBox.StandardButton.Yes:
                print("Iniciando processo de atualização...")
                if self.start_update_process(release_info):
                    print("Processo de atualização iniciado. Fechando aplicação...")
                    sys.exit(0)
                else:
                    print("Erro ao iniciar atualização. Continuando...")
                    return True
                    
            elif result == QMessageBox.StandardButton.No:
                print("Continuando sem atualizar...")
                return True
                
            else:
                print("Fechando aplicação...")
                sys.exit(0)
        
        except Exception as e:
            print(f"Erro no sistema de atualização: {e}")
            return True
def check_for_updates():
    updater = AutoUpdater()
    return updater.check_and_update()
def main():
    if not sys.argv[0].endswith(".py"):
        if not check_for_updates():
            sys.exit(1)
    app = QApplication(sys.argv)
    app.setApplicationName("MinecraftBr Launcher")
    launcher = MinecraftLauncher()
    launcher.show()
    sys.exit(app.exec())
if __name__ == "__main__":
    main()