# Configuração
$pastaDestino = "$env:APPDATA\.minecraftbr"
$repo         = "Comquister/MinecraftBR-Launcher"

Write-Host "Pasta destino: $pastaDestino"
Write-Host "Repositório GitHub: $repo"

# Cria pasta se não existir
if (!(Test-Path $pastaDestino)) {
    Write-Host "Pasta não encontrada. Criando..."
    New-Item -ItemType Directory -Path $pastaDestino -Force | Out-Null
} else {
    Write-Host "Pasta já existe."
}

# Pega os dados da última release pelo GitHub API
Write-Host "Buscando última release no GitHub..."
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

Write-Host "Arquivo encontrado: $nomeArquivo"
Write-Host "URL de download: $urlDownload"

# Função para calcular SHA256
function Get-FileSHA256($path) {
    if (Test-Path $path) {
        $hash = Get-FileHash -Path $path -Algorithm SHA256
        return $hash.Hash
    }
    return $null
}

# Calcula SHA256 do arquivo existente (se houver)
$hashExistente = Get-FileSHA256 $caminhoCompleto
if ($hashExistente) {
    Write-Host "SHA256 do arquivo existente: $hashExistente"
} else {
    Write-Host "Nenhum arquivo existente para comparar."
}

# Baixa o .exe usando curl.exe
Write-Host "Baixando arquivo..."
curl.exe -L -s -o "$caminhoCompleto" "$urlDownload"

# Calcula SHA256 do arquivo baixado
$hashBaixado = Get-FileSHA256 $caminhoCompleto
Write-Host "SHA256 do arquivo baixado: $hashBaixado"

# Compara os hashes
if ($hashExistente -and $hashExistente -eq $hashBaixado) {
    Write-Host "O arquivo baixado é idêntico ao existente. Nenhuma atualização necessária."
} else {
    Write-Host "Arquivo atualizado ou novo. Preparando para executar..."
    # Executa o arquivo
    Start-Process -FilePath $caminhoCompleto -WorkingDirectory $pastaDestino
    Write-Host "Arquivo executado com sucesso."
}
