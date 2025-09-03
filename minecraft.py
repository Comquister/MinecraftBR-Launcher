import os,sys,json,zipfile,requests,shutil,hashlib,concurrent.futures,platform
from pathlib import Path
from portablemc.standard import Version,Context
from portablemc.fabric import FabricVersion

def get_latest_release():return requests.get("https://api.github.com/repos/Comquister/MinecraftBR-Modpack/releases/latest").json()

def calc_sha256(f):
    h=hashlib.sha256()
    try:
        with open(f,"rb")as x:
            for b in iter(lambda:x.read(4096),b""):h.update(b)
        return f"sha256:{h.hexdigest()}"
    except:return None

def download_file(url,path):
    r=requests.get(url,stream=True,timeout=120)
    r.raise_for_status()
    with open(path,'wb')as f:
        for chunk in r.iter_content(8192):
            if chunk:f.write(chunk)

def download_mod(f,game_dir):
    fp=game_dir/Path(f['path'])
    fp.parent.mkdir(parents=True,exist_ok=True)
    h=f.get('hashes',{}).get('sha256')
    if fp.exists()and h and calc_sha256(fp)==h:return True
    for url in f.get('downloads',[]):
        try:
            download_file(url,fp)
            if not h or calc_sha256(fp)==h:return True
            fp.unlink()
        except:pass
    return False

class AutoUpdater:
    def __init__(self):self.github_api_url,self.current_exe_path,self.is_windows="https://api.github.com/repos/Comquister/MinecraftBR-Launcher/releases/latest",Path(sys.argv[0]).resolve(),platform.system()=="Windows"
    def calculate_exe_hash(self,file_path):
        try:
            h=hashlib.sha256()
            with open(file_path,"rb")as f:
                for chunk in iter(lambda:f.read(8192),b""):h.update(chunk)
            return h.hexdigest()
        except:return None
    def get_latest_release_info(self):
        try:
            r=requests.get(self.github_api_url,timeout=10);r.raise_for_status();data=r.json()
            exe_name="MinecraftBr.exe"if self.is_windows else"MinecraftBr"
            for asset in data.get("assets",[]):
                if asset["name"]==exe_name:return{'version':data["tag_name"],'download_url':asset["browser_download_url"],'size':asset["size"],'hash':asset.get("digest","").replace("sha256:","")if asset.get("digest")else None}
            return None
        except:return None
    def needs_update(self):
        if not self.current_exe_path.exists():return False,None
        release_info=self.get_latest_release_info()
        if not release_info:return False,None
        current_hash,remote_hash=self.calculate_exe_hash(self.current_exe_path),release_info.get("hash")
        if not current_hash or not remote_hash:return False,None
        return current_hash.lower()!=remote_hash.lower(),release_info
    def build_update_command(self,download_url,target_path):
        temp_exe=os.path.join(os.path.dirname(target_path),f"{os.path.basename(target_path)}.new")
        if self.is_windows:
            resp=requests.get(download_url,timeout=30)
            with open(temp_exe,'wb')as f:f.write(resp.content)
            cmd=f'Start-Sleep 2;Remove-Item -Force \\"{target_path}\\";Move-Item \\"{temp_exe}\\" \\"{target_path}\\";Write-Host \\"Atualização concluída!\\";'
            return f'start powershell -WindowStyle Hidden -c "{cmd}"'
        else:
            bash_cmd=f'echo "Iniciando...";url="{download_url}";path="{target_path}";tmp="$path.tmp";pkill -f "$(basename "$path")" 2>/dev/null;sleep 2;echo "Baixando...";if curl -L -o "$tmp" "$url" --connect-timeout 30 --max-time 120;then rm "$path";mv "$tmp" "$path";chmod +x "$path";echo "Sucesso!";else echo "Erro!";fi;'
            return f'bash -c "{bash_cmd}"'
    def start_update_process(self,release_info):
        try:os.system(self.build_update_command(release_info["download_url"],str(self.current_exe_path)));sys.exit()
        except:return False
    def check_and_update(self):
        try:
            needs_update,release_info=self.needs_update()
            if not needs_update:return True
            print(f"Nova versão {release_info['version']} disponível! Atualizando...")
            return self.start_update_process(release_info)
        except:return True

def main():
    if not sys.argv[0].endswith(".py")and not AutoUpdater().check_and_update():sys.exit(1)
    
    base_dir=Path(os.getenv("APPDATA"))/".minecraftbr"if os.name=='nt'else Path.home()/".minecraftbr"
    base_dir.mkdir(exist_ok=True)
    
    latest=get_latest_release()
    tag=latest["tag_name"]
    version_file=base_dir/"current_version.txt"
    
    if version_file.exists():
        with open(version_file,'r')as f:current_tag=f.read().strip()
        if current_tag==tag:
            print(f"Versão {tag} já instalada, iniciando...")
            game_dir=base_dir/"instancias"/tag
            with open(game_dir/"modrinth.index.json",'r')as f:mrpack_data=json.load(f)
            mc_ver=mrpack_data.get('dependencies',{}).get('minecraft')
            fabric_ver=mrpack_data.get('dependencies',{}).get('fabric-loader')
            print(f"Iniciando Minecraft {mc_ver} com Fabric {fabric_ver}...")
            context=Context(game_dir,game_dir)
            version=FabricVersion.with_fabric(mc_ver,fabric_ver,context=context)
            version.set_auth_offline("null",None)
            env=version.install()
            env.run()
            return
    
    mrpack_url=next(a["browser_download_url"]for a in latest["assets"]if a["name"].endswith(".mrpack"))
    game_dir=base_dir/"instancias"/tag
    game_dir.mkdir(parents=True,exist_ok=True)
    
    options_exists=(game_dir/"options.txt").exists()
    print(f"Baixando modpack {tag}...")
    
    mrpack_path=game_dir/"modpack.zip"
    download_file(mrpack_url,mrpack_path)
    
    with zipfile.ZipFile(mrpack_path,'r')as z:
        with z.open("modrinth.index.json")as f:mrpack_data=json.load(f)
        
        temp_dir=game_dir/"temp"
        temp_dir.mkdir(exist_ok=True)
        z.extractall(temp_dir)
        
        if options_exists:
            for override_dir in ["overrides","client-overrides"]:
                src=temp_dir/override_dir
                if src.exists():
                    for item in ["config","mods"]:
                        src_item=src/item
                        if src_item.exists():shutil.copytree(src_item,game_dir/item,dirs_exist_ok=True)
        else:
            for override_dir in ["overrides","client-overrides"]:
                src=temp_dir/override_dir
                if src.exists():
                    for item in src.iterdir():
                        dst=game_dir/item.name
                        if item.is_dir():shutil.copytree(item,dst,dirs_exist_ok=True)
                        else:shutil.copy2(item,dst)
        
        shutil.rmtree(temp_dir)
    
    with open(game_dir/"modrinth.index.json",'w')as f:json.dump(mrpack_data,f)
    
    print("Baixando mods...")
    files=mrpack_data.get('files',[])
    with concurrent.futures.ThreadPoolExecutor(max_workers=4)as executor:
        list(executor.map(lambda f:download_mod(f,game_dir),files))
    
    with open(version_file,'w')as f:f.write(tag)
    
    mc_ver=mrpack_data.get('dependencies',{}).get('minecraft')
    fabric_ver=mrpack_data.get('dependencies',{}).get('fabric-loader')
    
    print(f"Iniciando Minecraft {mc_ver} com Fabric {fabric_ver}...")
    context=Context(game_dir,game_dir)
    version=FabricVersion.with_fabric(mc_ver,fabric_ver,context=context)
    version.set_auth_offline("")
    env=version.install()
    env.run()

if __name__=="__main__":main()