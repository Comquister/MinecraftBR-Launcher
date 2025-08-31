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
import sys,platform,psutil,zipfile,subprocess,json,hashlib,random,concurrent.futures,pickle,webbrowser,requests,time,threading,os,shutil,logging
from pathlib import Path
from PyQt6.QtWidgets import *
from PyQt6.QtCore import Qt,QThread,pyqtSignal,QTimer
from PyQt6.QtGui import QPixmap,QPalette,QBrush,QIcon
from portablemc.standard import Version,Context
from portablemc.fabric import FabricVersion
from portablemc.forge import ForgeVersion,_NeoForgeVersion
from portablemc.auth import MicrosoftAuthSession
from flask import Flask,request

def calc_ram():return max(1024,int(min(max(1,psutil.virtual_memory().total/(1024**3)-2)*0.7,12)*1024))
def calc_sha256(f):
    h=hashlib.sha256()
    try:
        with open(f,"rb")as x:
            for b in iter(lambda:x.read(4096),b""):h.update(b)
        return f"sha256:{h.hexdigest()}"
    except:return None
def diagnose_jvm():print(f"=== DIAGNÓSTICO JVM ===\nSO: {platform.system()} {platform.release()}\nArquitetura: {platform.machine()}\nRAM Total: {psutil.virtual_memory().total/(1024**3):.1f} GB\nRAM configurada: {calc_ram()}M\n{'✓ Sistema 64-bit - sem limitações de RAM'if platform.machine().endswith('64')else'⚠ Sistema 32-bit - RAM limitada a 3GB'}\n=========================")

releases=requests.get("https://api.github.com/repos/Comquister/MinecraftBR-Modpack/releases/latest").json()["assets"]
CONFIG={'Title':'MinecraftBr Launcher','GameDir':Path(os.getenv("APPDATA"))/".minecraftbr",'RAM_SIZE':f"{calc_ram()}M",'CLIENT_ID':"708e91b5-99f8-4a1d-80ec-e746cbb24771",'MRPACK_URL':str(next(a["browser_download_url"]for a in releases if a["name"].endswith(".mrpack"))),'MRPACK_HASH':str(next(a["digest"]for a in releases if a["name"].endswith(".mrpack"))),'PORTWEB':random.randint(49152,65535)}
CONFIG['REDIRECT_URI']=f"http://localhost:{CONFIG['PORTWEB']}/code"
CONFIG_PROTECTION={'enabled':(CONFIG['GameDir']/"options.txt").exists(),'protected_files':['config/distanthorizons.toml','options.txt','servers.dat','meteor-client/']}
auth_data={'success':None,'code':None,'id_token':None}

def save_login_data(d,t,x):
    try:
        with open(d/"last_login.dat",'wb')as f:pickle.dump({'type':t,'data':x},f)
    except Exception as e:print(f"Erro ao salvar login: {e}")
def load_login_data(d):
    try:
        p=d/"last_login.dat"
        if p.exists():
            with open(p,'rb')as f:return pickle.load(f)
    except Exception as e:print(f"Erro ao carregar login: {e}")
    return None
def is_protected_file(f):return CONFIG_PROTECTION['enabled']and any(str(f).replace('\\','/').endswith(p)for p in CONFIG_PROTECTION.get('protected_files',[]))
def download_bg(d):
    p=d/"background.png"
    if not p.exists():
        try:
            r=requests.get("https://github.com/Comquister/MinecraftBR-Launcher/blob/main/image/background.png?raw=true",timeout=10)
            if r.status_code==200:
                with open(p,'wb')as f:f.write(r.content)
        except Exception as e:print(f"Erro ao baixar background: {e}");return None
    return p if p.exists()else None

def create_auth_app():
    app=Flask(__name__)
    app.logger.disabled=True
    logging.getLogger('werkzeug').setLevel(logging.ERROR)
    @app.route('/code',methods=['GET','POST'])
    def handle_auth():
        data=request.form if request.method=='POST'else request.args
        if 'code'in data and 'id_token'in data:auth_data.update({'code':data['code'],'id_token':data['id_token'],'success':True})
        elif 'error'in data:auth_data.update({'error':data.get('error_description','Login failed'),'success':False})
        return"""<!DOCTYPE html><html><head><meta charset="UTF-8"><title>Autenticação Concluída</title><style>body{display:flex;justify-content:center;align-items:center;height:100vh;margin:0;font-family:sans-serif;background:#121212;color:#eaeaea}.box{background:#1e1e1e;padding:40px;border-radius:16px;text-align:center}h1{color:#4cafef}p{color:#bbb}</style></head><body><div class="box"><h1>✅ Autenticação concluída</h1><p>Você pode fechar esta janela.</p></div><script>setTimeout(()=>window.close(),3000)</script></body></html>"""
    return app

class ModDownloader:
    def __init__(self,d,cb=None):self.game_dir,self.progress_callback,self.download_stats,self.stats_lock=d,cb,{'total':0,'completed':0,'failed':0,'skipped':0},threading.Lock()
    def _update_progress(self):
        with self.stats_lock:
            t,c=self.download_stats['total'],self.download_stats['completed']+self.download_stats['failed']+self.download_stats['skipped']
            if t>0 and self.progress_callback:self.progress_callback(40+int((c/t)*15))
    def _download_single_mod(self,f):
        try:
            p,fp=Path(f['path']),self.game_dir/Path(f['path'])
            fp.parent.mkdir(parents=True,exist_ok=True)
            h=f.get('hashes',{}).get('sha256')
            if fp.exists()and h and calc_sha256(fp)==h:
                with self.stats_lock:self.download_stats['skipped']+=1
                self._update_progress();return{'status':'skipped','file':str(p)}
            downloads=f.get('downloads',[])
            if not downloads:
                with self.stats_lock:self.download_stats['failed']+=1
                self._update_progress();return{'status':'failed','file':str(p),'error':'No download URLs'}
            for i,url in enumerate(downloads):
                try:
                    r=requests.get(url,timeout=min(120,max(30,f.get('fileSize',1000000)//100000)),stream=True,headers={'User-Agent':'MinecraftBR-Launcher/1.0'})
                    r.raise_for_status()
                    with open(fp,'wb')as x:
                        for chunk in r.iter_content(chunk_size=8192):
                            if chunk:x.write(chunk)
                    if h and calc_sha256(fp)!=h:
                        fp.unlink()
                        if i==len(downloads)-1:raise Exception(f"Hash incorreto")
                        continue
                    with self.stats_lock:self.download_stats['completed']+=1
                    self._update_progress();return{'status':'success','file':str(p)}
                except Exception as e:
                    if fp.exists():fp.unlink()
                    if i==len(downloads)-1:
                        with self.stats_lock:self.download_stats['failed']+=1
                        self._update_progress();return{'status':'failed','file':str(p),'error':str(e)}
        except Exception as e:
            with self.stats_lock:self.download_stats['failed']+=1
            self._update_progress();return{'status':'failed','file':f.get('path','unknown'),'error':str(e)}
    def download_mods_parallel(self,files,max_workers=None):
        if not files:return{'success':True,'results':[]}
        max_workers=max_workers or min((psutil.cpu_count(logical=False)or 4)*2,8)
        to_process=[f for f in files if not(self.game_dir/Path(f['path'])).exists()or calc_sha256(self.game_dir/Path(f['path']))!=f.get('hashes',{}).get('sha256')]
        self.download_stats={'total':len(files),'completed':len(files)-len(to_process),'failed':0,'skipped':len(files)-len(to_process)}
        if not to_process:return{'success':True,'results':[]}
        results,failed=[],[]
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers,thread_name_prefix="ModDownload")as executor:
            futures={executor.submit(self._download_single_mod,f):f for f in to_process}
            for future in concurrent.futures.as_completed(futures):
                try:
                    r=future.result(timeout=300)
                    results.append(r)
                    if r['status']=='failed':failed.append({'file':r['file'],'error':r.get('error','Unknown error')})
                except Exception as e:
                    failed.append({'file':futures[future].get('path','unknown'),'error':str(e)})
                    with self.stats_lock:self.download_stats['failed']+=1
                    self._update_progress()
        return{'success':len(failed)==0,'results':results,'stats':self.download_stats,'failed_downloads':failed}

class AuthThread(QThread):
    auth_success,auth_error=pyqtSignal(object,str),pyqtSignal(str)
    def __init__(self,email):super().__init__();self.email=email
    def run(self):
        try:
            auth_data.update({'success':None,'code':None,'id_token':None})
            nonce=str(int(time.time()*1000))
            auth_url=MicrosoftAuthSession.get_authentication_url(CONFIG['CLIENT_ID'],CONFIG['REDIRECT_URI'],self.email,nonce)
            threading.Thread(target=lambda:create_auth_app().run(host='localhost',port=CONFIG['PORTWEB'],debug=False),daemon=True).start()
            time.sleep(1);webbrowser.open(auth_url)
            timeout=time.time()+180
            while auth_data['success']is None and time.time()<timeout:time.sleep(0.5)
            if auth_data['success']and MicrosoftAuthSession.check_token_id(auth_data['id_token'],self.email,nonce):
                auth_session=MicrosoftAuthSession.authenticate(CONFIG['CLIENT_ID'],CONFIG['CLIENT_ID'],auth_data['code'],CONFIG['REDIRECT_URI'])
                auth_session.email=self.email;self.auth_success.emit(auth_session,self.email)
            else:self.auth_error.emit("Falha na autenticação")
        except Exception as e:self.auth_error.emit(str(e))

class MinecraftThread(QThread):
    status_update,progress_update,error_occurred,finished_success=pyqtSignal(str),pyqtSignal(int),pyqtSignal(str),pyqtSignal()
    def __init__(self,d,auth,user):super().__init__();self.game_dir,self.auth_session,self.username,self.context,self.mrpack_data=d,auth,user,Context(d,d),None
    def run(self):
        try:
            self.game_dir.mkdir(exist_ok=True)
            self.status_update.emit("Verificando modpack...");self.progress_update.emit(5)
            if not self._sync_mrpack():self.error_occurred.emit("Erro ao sincronizar modpack");return
            mc_ver,mod_info=self._get_minecraft_version_from_mrpack(),self._get_modloader_from_mrpack()
            if not mc_ver:self.error_occurred.emit("Versão do Minecraft não encontrada no modpack");return
            self.status_update.emit(f"Preparando {mc_ver} com {mod_info['name']}...");self.progress_update.emit(60)
            if mod_info['name']=='fabric-loader':version=FabricVersion.with_fabric(mc_ver,mod_info['version'],context=self.context)
            elif mod_info['name']=='forge':version=ForgeVersion(f"{mc_ver}-{mod_info['version']}",context=self.context)
            elif mod_info['name']=='neoforge':version=_NeoForgeVersion(mod_info['version'],context=self.context)
            else:version=Version(mc_ver,context=self.context)
            if self.auth_session:version.auth_session=self.auth_session
            else:version.set_auth_offline(self.username,None)
            self.status_update.emit("Instalando componentes...");self.progress_update.emit(75)
            env=version.install();self.status_update.emit("Configurando JVM...")
            is_64bit,ram_mb=platform.machine().endswith('64'),int(CONFIG['RAM_SIZE'].replace('M',''))
            if not is_64bit and ram_mb>3072:ram_mb=3072;self.status_update.emit("Sistema 32-bit detectado, limitando RAM a 3GB...")
            jvm_args=[f"-Xmx{ram_mb}M",f"-Xms{min(512,ram_mb)}M","-XX:+UseG1GC","-XX:+UnlockExperimentalVMOptions","-XX:G1NewSizePercent=20","-XX:G1ReservePercent=20","-XX:MaxGCPauseMillis=50","-XX:G1HeapRegionSize=32M","-Djava.awt.headless=false","-Dfile.encoding=UTF-8"]
            if os.name=='nt':jvm_args.extend(["-Dos.name=Windows 10","-Dos.version=10.0"])
            orig=env.jvm_args.copy()
            env.jvm_args=[orig[0]if orig else"java"]+jvm_args+[a for a in orig[1:]if not any(a.startswith(p)for p in['-Xmx','-Xms','-XX:+UseG1GC'])]
            self.status_update.emit("Iniciando jogo...");self.progress_update.emit(100);self.finished_success.emit();env.run()
        except Exception as e:import traceback;print(f"Erro: {str(e)}\nDetalhes: {traceback.format_exc()}");self.error_occurred.emit(str(e))
    def _sync_mrpack(self):
        try:
            mrpack_path,mrpack_hash_path=self.game_dir/"modpack.zip",self.game_dir/"modpack.zip.sha256"
            needs_download=True
            if mrpack_path.exists()and CONFIG.get('MRPACK_HASH'):
                local_hash=calc_sha256(mrpack_path)
                if local_hash and local_hash==CONFIG['MRPACK_HASH']:needs_download=False
            if needs_download:
                self.status_update.emit("Baixando modpack...");self.progress_update.emit(10)
                r=requests.get(CONFIG['MRPACK_URL'],stream=True,timeout=120);r.raise_for_status()
                total,downloaded=int(r.headers.get('content-length',0)),0
                with open(mrpack_path,'wb')as f:
                    for chunk in r.iter_content(chunk_size=8192):
                        if chunk:f.write(chunk);downloaded+=len(chunk)
                        if total>0:self.progress_update.emit(10+int((downloaded/total)*20))
                hash_value=calc_sha256(mrpack_path)
                if hash_value:
                    with open(mrpack_hash_path,'w')as f:f.write(hash_value)
            self.status_update.emit("Extraindo modpack...");self.progress_update.emit(35)
            return self._extract_mrpack(mrpack_path)
        except Exception as e:print(f"Erro na sincronização do mrpack: {e}");return False
    def _extract_mrpack(self,p):
        try:
            temp_dir=self.game_dir/"temp_mrpack"
            if temp_dir.exists():shutil.rmtree(temp_dir)
            temp_dir.mkdir()
            with zipfile.ZipFile(p,'r')as z:z.extractall(temp_dir)
            index_path=temp_dir/"modrinth.index.json"
            if not index_path.exists():raise Exception("modrinth.index.json não encontrado no modpack")
            with open(index_path,'r',encoding='utf-8')as f:self.mrpack_data=json.load(f)
            files=self.mrpack_data.get('files',[])
            mods_dir=self.game_dir/"mods";mods_dir.mkdir(exist_ok=True)
            self.status_update.emit("Limpando mods antigos...");self.progress_update.emit(35)
            self._clean_old_mods(mods_dir,files);self.status_update.emit("Baixando mods (paralelo)...");self.progress_update.emit(40)
            downloader=ModDownloader(self.game_dir,self.progress_update.emit)
            result=downloader.download_mods_parallel(files)
            if not result['success']and len(result['failed_downloads'])>len(files)*0.1:raise Exception(f"Muitas falhas no download: {len(result['failed_downloads'])} arquivos")
            self.status_update.emit("Aplicando overrides...");self.progress_update.emit(55)
            self._apply_overrides(temp_dir);shutil.rmtree(temp_dir)
            return True
        except Exception as e:print(f"Erro na extração do mrpack: {e}");return False
    def _clean_old_mods(self,mods_dir,valid_files):
        try:
            if not mods_dir.exists():return
            valid_paths={Path(f['path'][5:])for f in valid_files if f['path'].startswith('mods/')}
            temp_dir=self.game_dir/"temp_mrpack"
            for override_name in['overrides','client-overrides']:
                override_mods_path=temp_dir/override_name/"mods"
                if override_mods_path.exists():
                    for override_mod in override_mods_path.rglob('*'):
                        if override_mod.is_file():valid_paths.add(override_mod.relative_to(override_mods_path))
            for f in mods_dir.rglob('*'):
                if f.is_file():
                    relative_path=f.relative_to(mods_dir)
                    if relative_path not in valid_paths:f.unlink()
        except Exception as e:print(f"Erro ao limpar mods antigos: {e}")
    def backup_protected_configs(self):
        backup_dir=self.game_dir/"config_backups";backup_dir.mkdir(exist_ok=True);backed_up=[]
        for p in CONFIG_PROTECTION.get('protected_files',[]):
            config_path=self.game_dir/p
            if config_path.exists():backup_path=backup_dir/f"{config_path.name}.backup";shutil.copy2(config_path,backup_path);backed_up.append(p)
        return backed_up
    def restore_protected_configs(self):
        backup_dir=self.game_dir/"config_backups"
        if not backup_dir.exists():return[]
        restored=[]
        for p in CONFIG_PROTECTION.get('protected_files',[]):
            config_path,backup_path=self.game_dir/p,backup_dir/f"{Path(p).name}.backup"
            if backup_path.exists():config_path.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(backup_path,config_path);restored.append(p)
        return restored
    def _get_minecraft_version_from_mrpack(self):
        try:return self.mrpack_data.get('dependencies',{}).get('minecraft')if self.mrpack_data else None
        except:return None
    def _get_modloader_from_mrpack(self):
        try:
            if not self.mrpack_data:return{'name':'vanilla','version':None}
            deps=self.mrpack_data.get('dependencies',{})
            for key,name in[('fabric-loader','fabric-loader'),('forge','forge'),('neoforge','neoforge'),('quilt-loader','quilt-loader')]:
                if key in deps:return{'name':name,'version':deps[key]}
            return{'name':'vanilla','version':None}
        except:return{'name':'vanilla','version':None}
    def _apply_overrides(self,temp_dir):
        try:
            backed_up=self.backup_protected_configs()if CONFIG_PROTECTION['enabled']else[]
            for override_name in['overrides','client-overrides']:
                override_path=temp_dir/override_name
                if override_path.exists()and override_path.is_dir():
                    for item in override_path.rglob('*'):
                        if item.is_file():
                            relative_path=item.relative_to(override_path)
                            if is_protected_file(relative_path):continue
                            target_path=self.game_dir/relative_path;target_path.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(item,target_path)
            if CONFIG_PROTECTION['enabled']:self.restore_protected_configs()
        except Exception as e:print(f"Erro ao aplicar overrides: {e}")

class MinecraftLauncher(QMainWindow):
    def __init__(self):
        super().__init__()
        self.game_dir=CONFIG['GameDir'];self.game_dir.mkdir(exist_ok=True)
        self.auth_session,self.username,self.last_login_data=None,None,load_login_data(self.game_dir)
        self.auth_thread,self.minecraft_thread,self._pending_auth_email=None,None,None
        self.progress_timer,self.current_progress=QTimer(),0
        self.init_ui();self.load_background()
    def init_ui(self):
        self.setWindowTitle(CONFIG['Title'])
        try:
            r=requests.get("https://raw.githubusercontent.com/Comquister/MinecraftBR-Launcher/refs/heads/main/image/favicon.ico",timeout=10)
            if r.status_code==200:p=QPixmap();p.loadFromData(r.content);self.setWindowIcon(QIcon(p))
        except:pass
        self.setGeometry(100,100,450,680)
        self.setStyleSheet("""QMainWindow{background-image:url("""+str(self.game_dir)+"""/background.png);background-repeat:no-repeat;background-position:center}QWidget{color:#FFFFFF;font-family:'Segoe UI',Arial,sans-serif}QLabel{color:#FFFFFF}QRadioButton{color:#FFFFFF;font-size:14px;padding:8px;spacing:10px}QRadioButton::indicator{width:18px;height:18px}QRadioButton::indicator:unchecked{border:2px solid #CCCCCC;border-radius:9px;background:transparent}QRadioButton::indicator:checked{border:2px solid #4CAF50;border-radius:9px;background:#4CAF50}QPushButton{background-color:rgba(60,60,60,0.8);border:1px solid #888;border-radius:6px;color:white;font-size:12px;padding:8px}QPushButton:hover{background-color:rgba(80,80,80,0.9);border:1px solid #AAA}""")
        central_widget=QWidget();self.setCentralWidget(central_widget);main_layout=QVBoxLayout(central_widget);main_layout.setSpacing(0);main_layout.setContentsMargins(0,0,0,0)
        self.config_btn=QPushButton("⚙️",self);self.config_btn.setFixedSize(40,40);self.config_btn.move(self.width()-60,20)
        self.config_btn.setStyleSheet("QPushButton{background-color:rgba(0,0,0,0.3);border:1px solid rgba(255,255,255,0.3);border-radius:20px;font-size:16px}QPushButton:hover{background-color:rgba(0,0,0,0.5)}")
        self.config_btn.clicked.connect(self.on_config)
        self.atalho=QPushButton("🏷️",self);self.atalho.setFixedSize(40,40);self.atalho.move(20,20)
        self.atalho.setStyleSheet("QPushButton{background-color:rgba(0,0,0,0.3);border:1px solid rgba(255,255,255,0.3);border-radius:20px;font-size:16px}QPushButton:hover{background-color:rgba(0,0,0,0.5)}")
        self.atalho.clicked.connect(self.on_atalho)
        main_layout.addStretch()
        self.logo=QLabel();self.logo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        try:
            r=requests.get("https://github.com/Comquister/MinecraftBR-Launcher/blob/main/image/logo.png?raw=true",timeout=10)
            if r.status_code==200:p=QPixmap();p.loadFromData(r.content);self.logo.setPixmap(p.scaledToWidth(300,Qt.TransformationMode.SmoothTransformation))
        except:pass
        main_layout.addWidget(self.logo)
        container_wrapper=QHBoxLayout();container_wrapper.addStretch();container=QWidget();container.setFixedSize(330,400)
        container.setStyleSheet("QWidget{background-color:rgba(0,0,0,0.7);border-radius:15px;border:1px solid rgba(255,255,255,0.1)}")
        container_layout=QVBoxLayout(container);container_layout.setSpacing(20);container_layout.setContentsMargins(40,30,40,30)
        self.user_display=QLabel("Nome de usuário ou e-mail")
        self.user_display.setStyleSheet("QLabel{background-color:rgba(40,40,40,0.8);border:1px solid #666;border-radius:6px;padding:6px 6px;font-size:14px;color:#CCCCCC}")
        container_layout.addWidget(self.user_display)
        login_options_layout=QVBoxLayout();login_options_layout.setSpacing(10);self.login_group=QButtonGroup()
        if self.last_login_data:
            t,d=self.last_login_data['type'],self.last_login_data['data']
            text=f"🔄 Último: {(d.get('email','Email Microsoft')[:10]+'...'if len(d.get('email',''))>10 else d.get('email','Email Microsoft'))if t=='microsoft'else d.get('username','Jogador')}"
            self.last_radio=QRadioButton(text);self.last_radio.setChecked(True);self.login_group.addButton(self.last_radio,0);login_options_layout.addWidget(self.last_radio);self._setup_last_login()
        self.microsoft_radio=QRadioButton("🔐 Microsoft");self.login_group.addButton(self.microsoft_radio,1);login_options_layout.addWidget(self.microsoft_radio)
        self.offline_radio=QRadioButton("👤 Offline");self.login_group.addButton(self.offline_radio,2);login_options_layout.addWidget(self.offline_radio)
        self.login_group.buttonClicked.connect(self.on_login_selection);container_layout.addLayout(login_options_layout)
        self.play_btn=QPushButton("JOGAR");self.play_btn.setFixedHeight(50)
        self.play_btn.setStyleSheet("QPushButton{background:qlineargradient(x1:0,y1:0,x2:0,y2:1,stop:0 #4CAF50,stop:1 #45a049);color:white;border:none;border-radius:8px;font-size:18px;font-weight:bold;text-transform:uppercase}QPushButton:hover{background:qlineargradient(x1:0,y1:0,x2:0,y2:1,stop:0 #5CBF60,stop:1 #4CAF50)}QPushButton:disabled{background-color:#666666;color:#CCCCCC}QPushButton:pressed{background:qlineargradient(x1:0,y1:0,x2:0,y2:1,stop:0 #45a049,stop:1 #3d8b40)}")
        self.play_btn.clicked.connect(self.on_play);self.play_btn.setEnabled(bool(self.last_login_data));container_layout.addWidget(self.play_btn)
        status_layout=QHBoxLayout();self.status_label=QLabel("Pronto para jogar"if self.last_login_data else"Selecione o tipo de login")
        self.status_label.setStyleSheet("font-size:12px;padding:8px 12px;color:#CCCCCC;");status_layout.addWidget(self.status_label);status_layout.addStretch()
        about_btn=QPushButton("Sobre");about_btn.setStyleSheet("QPushButton{background:transparent;border:none;color:#888888;font-size:12px;text-decoration:underline}QPushButton:hover{color:#CCCCCC}")
        about_btn.clicked.connect(self.on_about);status_layout.addWidget(about_btn);container_layout.addLayout(status_layout)
        container_wrapper.addWidget(container);container_wrapper.addStretch();wrapper_widget=QWidget();wrapper_widget.setLayout(container_wrapper);main_layout.addWidget(wrapper_widget);main_layout.addStretch()
    def resizeEvent(self,event):super().resizeEvent(event);self.config_btn.move(self.width()-60,20)
    def update_play_button_progress(self,progress,text=""):
        if progress==0:self.play_btn.setText("JOGAR");self.play_btn.setStyleSheet("QPushButton{background:qlineargradient(x1:0,y1:0,x2:0,y2:1,stop:0 #4CAF50,stop:1 #45a049);color:white;border:none;border-radius:8px;font-size:18px;font-weight:bold;text-transform:uppercase}")
        else:
            self.play_btn.setText(f"{progress}%"if not text else text)
            p=max(0.0,min(1.0,progress/100.0));s=max(0.01,p)
            self.play_btn.setStyleSheet(f"QPushButton{{background:qlineargradient(x1:0,y1:0,x2:1,y2:0,stop:0 #2196F3,stop:{p:.2f} #2196F3,stop:{s:.2f} #424242,stop:1 #424242);color:white;border:none;border-radius:8px;font-size:16px;font-weight:bold}}")
    def load_background(self):
        try:
            bg_path=download_bg(self.game_dir)
            if bg_path:
                pixmap=QPixmap(str(bg_path))
                if not pixmap.isNull():
                    scaled_pixmap=pixmap.scaled(pixmap.width()*5,pixmap.height()*5,Qt.AspectRatioMode.IgnoreAspectRatio,Qt.TransformationMode.FastTransformation)
                    brush=QBrush(scaled_pixmap);palette=QPalette();palette.setBrush(QPalette.ColorRole.Window,brush);self.setPalette(palette);return
        except Exception as e:print(f"Erro ao carregar background: {e}")
    def _setup_last_login(self):
        if not self.last_login_data:return
        t,d=self.last_login_data['type'],self.last_login_data['data']
        if t=='offline':
            u=d.get('username','Jogador')
            if u:self.username=u;self.user_display.setText(f"Offline: {u}");self.user_display.setStyleSheet(self.user_display.styleSheet()+"color:#FFFFFF;")
        elif t=='microsoft':
            e,u=d.get('email','Email Microsoft'),d.get('username','Usuário')
            self.user_display.setText(f"Microsoft: {u}");self.user_display.setStyleSheet(self.user_display.styleSheet()+"color:#FFFFFF;")
    def on_login_selection(self,button):
        button_id=self.login_group.id(button)
        if button_id==0 and self.last_login_data:self._handle_last_login()
        elif button_id==1:self._handle_microsoft_login()
        elif button_id==2:self._handle_offline_login()
    def _handle_last_login(self):
        if not self.last_login_data:return
        t,d=self.last_login_data['type'],self.last_login_data['data']
        if t=='microsoft':
            e,u=d.get('email',''),d.get('username','Usuário')
            if e:self.user_display.setText(f"Microsoft: {u}");self.user_display.setStyleSheet(self.user_display.styleSheet()+"color:#FFFFFF;");self.status_label.setText("Clique em JOGAR para reautenticar");self.play_btn.setEnabled(True)
        else:
            u=d.get('username','')
            if u:self.username=u;self.user_display.setText(f"Offline: {u}");self.user_display.setStyleSheet(self.user_display.styleSheet()+"color:#FFFFFF;");self.status_label.setText(f"Pronto para jogar como {u} (Offline)");self.play_btn.setEnabled(True)
    def _handle_microsoft_login(self):
        email,ok=QInputDialog.getText(self,"Login Microsoft","Digite seu email Microsoft:")
        if ok and email.strip():self.user_display.setText(email.strip());self.user_display.setStyleSheet(self.user_display.styleSheet()+"color:#FFFFFF;");self.status_label.setText("Clique em JOGAR para autenticar");self.play_btn.setEnabled(True);self._pending_auth_email=email.strip()
    def _handle_offline_login(self):
        default_name=""
        if self.last_login_data and self.last_login_data['type']=='offline':default_name=self.last_login_data['data'].get('username',os.getlogin())
        else:default_name=os.getlogin()
        username,ok=QInputDialog.getText(self,"Login Offline","Nome do jogador:",text=default_name)
        if ok and username.strip():self.username=username.strip();self.auth_session=None;self.user_display.setText(self.username);self.user_display.setStyleSheet(self.user_display.styleSheet()+"color:#FFFFFF;");self.status_label.setText(f"Pronto para jogar como {self.username} (Offline)");self.play_btn.setEnabled(True);save_login_data(self.game_dir,'offline',{'username':self.username})
    def _start_auth(self,email):
        if self.auth_thread and self.auth_thread.isRunning():return
        self.auth_thread=AuthThread(email);self.auth_thread.auth_success.connect(self._on_auth_success);self.auth_thread.auth_error.connect(self._on_auth_error);self.auth_thread.start()
    def _on_auth_success(self,auth_session,email):
        self.auth_session,self.username=auth_session,None
        username=getattr(auth_session,'username','Usuário');self.user_display.setText(f"{username} ({email})");self.user_display.setStyleSheet(self.user_display.styleSheet()+"color:#FFFFFF;");self.status_label.setText(f"Autenticado como {username}. Iniciando jogo...");save_login_data(self.game_dir,'microsoft',{'email':email,'username':username});self.update_play_button_progress(10,"PREPARANDO...")
        self.minecraft_thread=MinecraftThread(self.game_dir,self.auth_session,self.username);self.minecraft_thread.status_update.connect(self.status_label.setText);self.minecraft_thread.progress_update.connect(self.on_progress_update);self.minecraft_thread.error_occurred.connect(self._on_minecraft_error);self.minecraft_thread.finished_success.connect(self.close);self.minecraft_thread.start()
    def _on_auth_error(self,error):self.play_btn.setEnabled(True);self.update_play_button_progress(0);self.status_label.setText(f"Erro na autenticação: {error}");QMessageBox.critical(self,"Erro",f"Erro no login: {error}")
    def on_play(self):
        selected_button=self.login_group.checkedButton()
        if not selected_button:QMessageBox.warning(self,"Aviso","Selecione um tipo de login primeiro!");return
        button_id=self.login_group.id(selected_button)
        if((button_id==0 and self.last_login_data and self.last_login_data['type']=='microsoft')or(button_id==1)):
            if not self.auth_session:
                email=self.last_login_data['data'].get('email','')if button_id==0 else getattr(self,'_pending_auth_email','')
                if not email:QMessageBox.warning(self,"Erro","Email não encontrado!");return
                self.play_btn.setEnabled(False);self.status_label.setText("Autenticando...");self.update_play_button_progress(5,"AUTENTICANDO...");self._start_auth(email);return
        if not self.auth_session and not self.username:QMessageBox.warning(self,"Aviso","Configuração de login inválida!");return
        self.play_btn.setEnabled(False);self.update_play_button_progress(5,"INICIANDO...");self.minecraft_thread=MinecraftThread(self.game_dir,self.auth_session,self.username);self.minecraft_thread.status_update.connect(self.status_label.setText);self.minecraft_thread.progress_update.connect(self.on_progress_update);self.minecraft_thread.error_occurred.connect(self._on_minecraft_error);self.minecraft_thread.finished_success.connect(self.close);self.minecraft_thread.start()
    def on_progress_update(self,progress):self.current_progress=progress;self.update_play_button_progress(progress)
    def _on_minecraft_error(self,error):self.status_label.setText("Erro ao iniciar");self.update_play_button_progress(0);self.play_btn.setEnabled(True);QMessageBox.critical(self,"Erro",f"Erro: {error}")
    def on_config(self):
        info=f"Configurações:\n\n📁 Diretório: {str(self.game_dir)}\n📦 Modpack: {CONFIG['MRPACK_URL']}\n💾 RAM: {CONFIG['RAM_SIZE']}\n\nDeseja abrir o diretório do jogo?"
        reply=QMessageBox.question(self,"Configurações",info,QMessageBox.StandardButton.Yes|QMessageBox.StandardButton.No)
        if reply==QMessageBox.StandardButton.Yes:
            try:
                if os.name=='nt':os.startfile(str(self.game_dir))
                else:subprocess.run(['xdg-open',str(self.game_dir)])
            except Exception as e:QMessageBox.critical(self,"Erro",f"Erro ao abrir diretório: {e}")
    def on_atalho(self):
        reply=QMessageBox.question(self,"Criar Atalho","Deseja criar um atalho na área de trabalho?",QMessageBox.StandardButton.Yes|QMessageBox.StandardButton.No)
        if reply==QMessageBox.StandardButton.Yes:
            try:
                if os.name=='nt':subprocess.run(['powershell','-WindowStyle','Hidden','-Command',f'$WshShell=New-Object -comObject WScript.Shell;$Shortcut=$WshShell.CreateShortcut("$([Environment]::GetFolderPath(\'Desktop\'))\\MinecraftBr.lnk");$Shortcut.TargetPath="{sys.argv[0]}";$Shortcut.WorkingDirectory="{os.path.dirname(sys.argv[0])}";$Shortcut.Save()'],check=True)
                else:
                    desktop=os.path.join(os.path.expanduser('~'),'Desktop');shortcut_path=os.path.join(desktop,'Launcher.desktop')
                    with open(shortcut_path,'w')as f:f.write(f"[Desktop Entry]\nType=Application\nName=Launcher\nExec=python {sys.argv[0]}\nPath={os.path.dirname(sys.argv[0])}\nTerminal=false");os.chmod(shortcut_path,0o755)
                QMessageBox.information(self,"Sucesso","Atalho criado na área de trabalho!")
            except Exception as e:QMessageBox.critical(self,"Erro",f"Erro ao criar atalho: {e}")
    def on_about(self):QMessageBox.about(self,"Sobre",f"{CONFIG['Title']}\n\n🎮 Launcher personalizado para Minecraft\n📦 Sistema de modpacks .mrpack\n💾 RAM otimizada: {CONFIG['RAM_SIZE']}\n\nDesenvolvido para a comunidade MinecraftBR")

class AutoUpdater:
    def __init__(self):self.github_api_url,self.current_exe_path,self.is_windows="https://api.github.com/repos/Comquister/MinecraftBR-Launcher/releases/latest",Path(sys.argv[0]).resolve(),platform.system()=="Windows"
    def calculate_exe_hash(self,file_path):
        try:
            h=hashlib.sha256()
            with open(file_path,"rb")as f:
                for chunk in iter(lambda:f.read(8192),b""):h.update(chunk)
            return h.hexdigest()
        except Exception as e:print(f"Erro ao calcular hash do executável: {e}");return None
    def get_latest_release_info(self):
        try:
            r=requests.get(self.github_api_url,timeout=10);r.raise_for_status();data=r.json()
            exe_name="MinecraftBr.exe"if self.is_windows else"MinecraftBr"
            for asset in data.get("assets",[]):
                if asset["name"]==exe_name:return{'version':data["tag_name"],'download_url':asset["browser_download_url"],'size':asset["size"],'hash':asset.get("digest","").replace("sha256:","")if asset.get("digest")else None,'release_notes':data.get("body","")}
            return None
        except Exception as e:print(f"Erro ao buscar informações de atualização: {e}");return None
    def needs_update(self):
        if not self.current_exe_path.exists():return False,None
        release_info=self.get_latest_release_info()
        if not release_info:return False,None
        current_hash,remote_hash=self.calculate_exe_hash(self.current_exe_path),release_info.get("hash")
        if not current_hash or not remote_hash:return False,None
        return current_hash.lower()!=remote_hash.lower(),release_info
    def build_update_command(self,download_url,target_path):
        exe_name,exe_dir,temp_exe=os.path.basename(target_path),os.path.dirname(target_path),os.path.join(os.path.dirname(target_path),f"{os.path.basename(target_path)}.new")
        if self.is_windows:
            resp=requests.get(download_url,timeout=30)
            with open(temp_exe,'wb')as f:f.write(resp.content)
            cmd=f'Start-Sleep 2;Remove-Item -Force \\"{target_path}\\";Move-Item \\"{temp_exe}\\" \\"{target_path}\\";Add-Type -AssemblyName System.Windows.Forms;[System.Windows.Forms.MessageBox]::Show(\\"Atualização concluída! Você pode iniciar o aplicativo.\\",\\"Atualização\\");'
            return f'start powershell -WindowStyle Hidden -c "{cmd}"'
        else:
            bash_cmd=f'echo "Iniciando...";url="{download_url}";path="{target_path}";bak="$path.backup";tmp="$path.tmp";pkill -f "$(basename "$path")" 2>/dev/null;sleep 2;[ -f "$path" ]&&cp "$path" "$bak"&&echo "Backup criado";echo "Baixando...";if curl -L -o "$tmp" "$url" --connect-timeout 30 --max-time 120;then [ -f "$path" ]&&rm "$path";mv "$tmp" "$path";chmod +x "$path";echo "Sucesso!";[ -f "$bak" ]&&rm "$bak";else echo "Erro!";[ -f "$bak" ]&&mv "$bak" "$path"&&echo "Backup restaurado";fi;echo "Pressione Enter...";read'
            return f'bash -c "{bash_cmd}"'
    def start_update_process(self,release_info):
        try:os.system(self.build_update_command(release_info["download_url"],str(self.current_exe_path)));sys.exit()
        except Exception as e:print(f"Erro ao iniciar processo de atualização: {e}");return False
    def check_and_update(self):
        try:
            needs_update,release_info=self.needs_update()
            if not needs_update:return True
            if not QApplication.instance():app=QApplication(sys.argv);app_created=True
            else:app_created=False
            version,size_mb=release_info.get("version","Desconhecida"),release_info.get("size",0)/(1024*1024)
            message=f"Nova versão disponível!\n\nVersão atual: Desatualizada\nNova versão: {version}\nTamanho: {size_mb:.1f} MB\n\nDeseja atualizar agora?\n\nNotas da versão:\n{release_info.get('release_notes','Sem notas disponíveis')[:200]}..."
            msg_box=QMessageBox();msg_box.setWindowTitle("Atualização Disponível");msg_box.setText(message);msg_box.setStandardButtons(QMessageBox.StandardButton.Yes|QMessageBox.StandardButton.No|QMessageBox.StandardButton.Cancel)
            msg_box.button(QMessageBox.StandardButton.Yes).setText("Atualizar");msg_box.button(QMessageBox.StandardButton.No).setText("Continuar sem atualizar");msg_box.button(QMessageBox.StandardButton.Cancel).setText("Fechar")
            result=msg_box.exec()
            if app_created:app.quit()
            if result==QMessageBox.StandardButton.Yes:return self.start_update_process(release_info)and sys.exit(0)or True
            elif result==QMessageBox.StandardButton.No:return True
            else:sys.exit(0)
        except Exception as e:print(f"Erro no sistema de atualização: {e}");return True

def check_for_updates():return AutoUpdater().check_and_update()
def main():
    if not sys.argv[0].endswith(".py")and not check_for_updates():sys.exit(1)
    app=QApplication(sys.argv);app.setApplicationName("MinecraftBr Launcher");launcher=MinecraftLauncher();launcher.show();sys.exit(app.exec())
if __name__=="__main__":main()