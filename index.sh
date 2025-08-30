#!/bin/bash
echo ' ██████   ██████  ███                                                      ██████   █████    ███████████  ███████████  
░░██████ ██████  ░░░                                                      ███░░███ ░░███    ░░███░░░░░███░░███░░░░░███
 ░███░█████░███  ████  ████████    ██████   ██████  ████████   ██████    ░███ ░░░  ███████   ░███    ░███ ░███    ░███
 ░███░░███ ░███ ░░███ ░░███░░███  ███░░███ ███░░███░░███░░███ ░░░░░███  ███████   ░░░███░    ░██████████  ░██████████  
 ░███ ░░░  ░███  ░███  ░███ ░███ ░███████ ░███ ░░░  ░███ ░░░   ███████ ░░░███░      ░███     ░███░░░░░███ ░███░░░░░███
 ░███      ░███  ░███  ░███ ░███ ░███░░░  ░███  ███ ░███      ███░░███   ░███       ░███ ███ ░███    ░███ ░███    ░███
 █████     █████ █████ ████ █████░░██████ ░░██████  █████    ░░████████  █████      ░░█████  ███████████  █████   █████
░░░░░     ░░░░░ ░░░░░ ░░░░ ░░░░░  ░░░░░░   ░░░░░░  ░░░░░      ░░░░░░░░  ░░░░░        ░░░░░  ░░░░░░░░░░░  ░░░░░   ░░░░░'
atalho=false;nostart=false;[[ "$*" =~ --atalho ]]&&atalho=true;[[ "$*" =~ --nostart ]]&&nostart=true
d="$HOME/.minecraftbr";r="Comquister/MinecraftBR-Launcher";mkdir -p "$d" 2>/dev/null
j=$(curl -s "https://api.github.com/repos/$r/releases/latest");a=$(echo "$j"|jq -r '.assets[]|select(.name|test("MinecraftBr$"))|.browser_download_url'|head -1)
[[ -z "$a" ]]&&{echo "Nenhum arquivo MinecraftBr encontrado";exit 1;}
p="$d/MinecraftBr";h1="";[[ -f "$p" ]]&&h1=$(sha256sum "$p"|cut -d' ' -f1)
curl -L -s -o "$p" "$a";chmod +x "$p";h2=$(sha256sum "$p"|cut -d' ' -f1)
[[ "$h1" != "$h2" ]]&&echo "Atualizado"||echo "Mesmo arquivo"
$atalho&&{echo "[Desktop Entry]
Name=MinecraftBR
Exec=$p
Path=$d
Icon=$p
Type=Application
Terminal=false" > "$HOME/Desktop/MinecraftBR.desktop";chmod +x "$HOME/Desktop/MinecraftBR.desktop";echo "Atalho criado na área de trabalho";}
$nostart||cd "$d"&&./"$(basename "$p")"