import requests

releasesgithub = requests.get("https://api.github.com/repos/Comquister/MinecraftBR-Launcher/releases/latest").json()["assets"]
a = next(a["browser_download_url"] for a in releasesgithub if a["name"].endswith(".mrpack"))
print(a)
