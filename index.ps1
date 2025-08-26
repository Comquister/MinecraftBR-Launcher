# Configuração
$pastaDestino = "$env:APPDATA\.minecraftbr"
$repo         = "Comquister/MinecraftBR-Launcher"

# Cria pasta se não existir
if (!(Test-Path $pastaDestino)) {
    New-Item -ItemType Directory -Path $pastaDestino -Force | Out-Null
}

# Pega os dados da última release pelo GitHub API
$releaseJson = curl.exe -s -H "User-Agent: PowerShell" "https://api.github.com/repos/$repo/releases/latest" | ConvertFrom-Json

# Procura o primeiro asset que seja .exe
$asset = $releaseJson.assets | Where-Object { $_.name -like "*.exe" } | Select-Object -First 1

if ($null -eq $asset) {
    Write-Error "Nenhum arquivo .exe encontrado na última release."
    exit 1
}

# Define nomes
$nomeArquivo = $asset.name
$caminhoCompleto = Join-Path $pastaDestino $nomeArquivo
$urlDownload = $asset.browser_download_url

# Baixa o .exe usando curl.exe
curl.exe -L -s -o "$caminhoCompleto" "$urlDownload"

# Executa o arquivo
Start-Process -FilePath $caminhoCompleto -WorkingDirectory $pastaDestino
