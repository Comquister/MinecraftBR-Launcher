# Configuração
$pastaDestino = "$env:APPDATA\.minecraftbr"
$urlDownload  = "https://github.com/Comquister/MinecraftBR-Launcher/releases/download/release/minecraft.run.exe"
$nomeArquivo  = "minecraft.run.exe"
$caminhoCompleto = Join-Path $pastaDestino $nomeArquivo

# Cria pasta se não existir
if (!(Test-Path $pastaDestino)) {
    New-Item -ItemType Directory -Path $pastaDestino -Force | Out-Null
}

# Sempre baixa o arquivo (rápido e silencioso)
curl.exe -L -s -o "$caminhoCompleto" "$urlDownload"

# Executa o arquivo
Start-Process -FilePath $caminhoCompleto -WorkingDirectory $pastaDestino
