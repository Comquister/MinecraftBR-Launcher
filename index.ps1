Write-Output @"
 ██████   ██████  ███                                                      ██████   █████    ███████████  ███████████  
░░██████ ██████  ░░░                                                      ███░░███ ░░███    ░░███░░░░░███░░███░░░░░███
 ░███░█████░███  ████  ████████    ██████   ██████  ████████   ██████    ░███ ░░░  ███████   ░███    ░███ ░███    ░███
 ░███░░███ ░███ ░░███ ░░███░░███  ███░░███ ███░░███░░███░░███ ░░░░░███  ███████   ░░░███░    ░██████████  ░██████████  
 ░███ ░░░  ░███  ░███  ░███ ░███ ░███████ ░███ ░░░  ░███ ░░░   ███████ ░░░███░      ░███     ░███░░░░░███ ░███░░░░░███
 ░███      ░███  ░███  ░███ ░███ ░███░░░  ░███  ███ ░███      ███░░███   ░███       ░███ ███ ░███    ░███ ░███    ░███
 █████     █████ █████ ████ █████░░██████ ░░██████  █████    ░░████████  █████      ░░█████  ███████████  █████   █████
░░░░░     ░░░░░ ░░░░░ ░░░░ ░░░░░  ░░░░░░   ░░░░░░  ░░░░░      ░░░░░░░░  ░░░░░        ░░░░░  ░░░░░░░░░░░  ░░░░░   ░░░░░
"@

$ErrorActionPreference = "Stop"
$ProgressPreference = "SilentlyContinue"

$downloadDir = "$env:APPDATA\.minecraftbr"
$repoPath = "Comquister/MinecraftBR-Launcher"

try {
    if (!(Test-Path $downloadDir)) {
        New-Item -ItemType Directory -Path $downloadDir -Force | Out-Null
    }

    Write-Output "Buscando última versão..."
    $releaseData = Invoke-RestMethod -Uri "https://api.github.com/repos/$repoPath/releases/latest" -UseBasicParsing
    $exeAsset = $releaseData.assets | Where-Object { $_.name -like "*.exe" } | Select-Object -First 1

    if (!$exeAsset) {
        throw "Nenhum arquivo .exe encontrado no release"
    }

    $localPath = Join-Path $downloadDir $exeAsset.name
    $downloadUrl = $exeAsset.browser_download_url

    $currentHash = $null
    if (Test-Path $localPath) {
        $currentHash = (Get-FileHash $localPath -Algorithm SHA256).Hash
    }

    Write-Output "Baixando $($exeAsset.name)..."
    Invoke-WebRequest -Uri $downloadUrl -OutFile $localPath -UseBasicParsing

    $newHash = (Get-FileHash $localPath -Algorithm SHA256).Hash

    if ($currentHash -ne $newHash) {
        Write-Output "✅ Launcher atualizado com sucesso!"
    } else {
        Write-Output "ℹ️  Launcher já está na versão mais recente"
    }

    if ($atalho) {
        $desktopPath = [Environment]::GetFolderPath("Desktop")
        $shortcutPath = Join-Path $desktopPath "MinecraftBR.lnk"
        
        $wshell = New-Object -ComObject WScript.Shell
        $shortcut = $wshell.CreateShortcut($shortcutPath)
        $shortcut.TargetPath = $localPath
        $shortcut.WorkingDirectory = $downloadDir
        $shortcut.IconLocation = $localPath
        $shortcut.Save()
        
        Write-Output "🔗 Atalho criado na área de trabalho"
    }

    if (!$nostart) {
        Write-Output "🚀 Iniciando MinecraftBR Launcher..."
        Start-Process -FilePath $localPath -WorkingDirectory $downloadDir
    }
}
catch {
    Write-Error "❌ Erro: $($_.Exception.Message)"
    exit 1
}