# =============================
# MinecraftBR Launcher - Instalador Inteligente
# =============================

# Configurações
$appName = "MinecraftBR Launcher"
$installPath = "$env:USERPROFILE\.minecraftbr"
$pythonPath = "$installPath\python"
$pythonExe = "$pythonPath\python.exe"
$pythonwExe = "$pythonPath\pythonw.exe"
$requiredVersion = "3.13"
$requiredPackages = @("requests", "portablemc", "PyQt6", "flask", 'psutil')

# =============================
# Funções de Interface
# =============================

function Show-Header {
    Clear-Host
    Write-Host "╔════════════════════════════════════════════╗" -ForegroundColor Cyan
    Write-Host "║          🎮 MinecraftBR Launcher           ║" -ForegroundColor Cyan
    Write-Host "║         Instalador Automático v2.0         ║" -ForegroundColor Cyan
    Write-Host "╚════════════════════════════════════════════╝" -ForegroundColor Cyan
    Write-Host ""
}

function Show-Status {
    param([string]$Message, [string]$Status = "info")
    $icons = @{
        "info" = "ℹ️"
        "success" = "✅"
        "warning" = "⚠️"
        "error" = "❌"
        "working" = "⏳"
    }
    
    $colors = @{
        "info" = "Cyan"
        "success" = "Green"
        "warning" = "Yellow"
        "error" = "Red"
        "working" = "Yellow"
    }
    
    Write-Host "$($icons[$Status]) $Message" -ForegroundColor $colors[$Status]
}

function Show-Progress {
    param([string]$Activity, [int]$PercentComplete, [string]$Status = "")
    Write-Progress -Activity $Activity -PercentComplete $PercentComplete -Status $Status
}

function Confirm-Action {
    param([string]$Message)
    Write-Host ""
    Write-Host $Message -ForegroundColor Yellow
    $response = Read-Host "Continuar? (S/n)"
    return ($response -eq "s" -or $response -eq "S" -or $response -eq "")
}

# =============================
# Funções de Verificação
# =============================

function Test-SystemRequirements {
    $requirements = @{
        "Memoria ram" = (Get-CimInstance Win32_ComputerSystem).TotalPhysicalMemory -ge 3GB
        "Permissões de Escrita" = Test-Path $env:USERPROFILE -PathType Container
        "PowerShell 5.0+" = $PSVersionTable.PSVersion.Major -ge 5
    }
    
    Show-Status "Verificando requisitos do sistema..." "working"
    Start-Sleep 1
    
    $allGood = $true
    foreach ($req in $requirements.GetEnumerator()) {
        if ($req.Value) {
            Show-Status "$($req.Key): OK" "success"
        } else {
            Show-Status "$($req.Key): FALHOU" "error"
            $allGood = $false
        }
        Start-Sleep 0.2
    }
    
    return $allGood
}

function Get-InstallationStatus {
    $status = @{
        "PythonInstalled" = $false
        "PackagesInstalled" = $false
        "LauncherReady" = $false
        "InstallSize" = 0
    }
    
    if (Test-Path $pythonExe) {
        try {
            $version = & $pythonExe -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')" 2>$null
            if ($version -and $version.StartsWith($requiredVersion)) {
                $status.PythonInstalled = $true
                
                # Verificar pacotes
                $installedPackages = 0
                foreach ($package in $requiredPackages) {
                    try {
                        & $pythonExe -c "import $package" 2>$null
                        if ($LASTEXITCODE -eq 0) { $installedPackages++ }
                    } catch {}
                }
                
                $status.PackagesInstalled = ($installedPackages -eq $requiredPackages.Count)
                $status.LauncherReady = $status.PackagesInstalled
            }
        } catch {}
    }
    
    if (Test-Path $installPath) {
        $status.InstallSize = (Get-ChildItem $installPath -Recurse -File | Measure-Object -Property Length -Sum).Sum / 1MB
    }
    
    return $status
}

# =============================
# Funções de Instalação
# =============================

function Install-PythonEmbedded {
    if (!(Confirm-Action "Deseja instalar o Python ${requiredVersion}? (Necessário ~50MB de espaço)")) {
        Show-Status "Instalação do Python cancelada pelo usuário." "info"
        return $false
    }
   
    Show-Status "Preparando instalação do Python $requiredVersion..." "working"
   
    # Limpar instalação anterior
    if (Test-Path $pythonPath) {
        Show-Status "Removendo versão anterior..." "working"
        Remove-Item $pythonPath -Recurse -Force -ErrorAction SilentlyContinue
    }
   
    New-Item -ItemType Directory -Path $pythonPath -Force | Out-Null
   
    Show-Progress "Instalando Python" 15 "Baixando Python $requiredVersion..."
   
    $url = "https://www.python.org/ftp/python/3.13.7/python-3.13.7-embed-amd64.zip"
    $zipFile = "$pythonPath\python.zip"
   
    try {
        # Download do Python
        & curl.exe -L -o $zipFile $url --connect-timeout 60 --max-time 300 --fail --silent --show-error
       
        Show-Progress "Instalando Python" 35 "Extraindo arquivos..."
        Expand-Archive $zipFile $pythonPath -Force
        Remove-Item $zipFile -Force
       
        Show-Progress "Instalando Python" 50 "Configurando ambiente..."
       
        # Configurar Python para usar site-packages
        $zipLib = Get-ChildItem "$pythonPath\python*.zip" | Select-Object -First 1
        $pthFile = "$pythonPath\python313._pth"
        $pthContent = @"
$($zipLib.Name)
.
Lib\site-packages
import site
"@
        [IO.File]::WriteAllText($pthFile, $pthContent)
       
        New-Item -ItemType Directory -Path "$pythonPath\Lib\site-packages" -Force | Out-Null
       
        Show-Progress "Instalando Python" 70 "Baixando get-pip..."
        
        # Baixar get-pip.py
        $getPipUrl = "https://bootstrap.pypa.io/get-pip.py"
        $getPipFile = "$pythonPath\get-pip.py"
        & curl.exe -L -o $getPipFile $getPipUrl --connect-timeout 30 --max-time 120 --fail --silent --show-error
        
        Show-Progress "Instalando Python" 85 "Instalando pip..."
        
        # Instalar pip usando get-pip.py
        # $pipInstallResult = & $pythonExe $getPipFile --no-warn-script-location 2>&1
        & $pythonExe $getPipFile --no-warn-script-location 2>&1
        
        # Limpar arquivo get-pip.py
        Remove-Item $getPipFile -Force -ErrorAction SilentlyContinue
       
        Show-Progress "Instalando Python" 100 "Concluído!"
        Start-Sleep 1
        Write-Progress -Activity "Instalando Python" -Completed
       
        Show-Status "Python $requiredVersion instalado com sucesso!" "success"
        return $true
    } catch {
        Show-Status "Erro ao instalar Python: $($_.Exception.Message)" "error"
        # Limpar arquivos em caso de erro
        if (Test-Path $getPipFile) { Remove-Item $getPipFile -Force -ErrorAction SilentlyContinue }
        return $false
    }
}

function Install-Packages {
    if (!(Confirm-Action "Deseja instalar os pacotes necessários para o launcher?")) {
        Show-Status "Instalação de pacotes cancelada pelo usuário." "info"
        return $false
    }
    
    Show-Status "Instalando pacotes necessários..." "working"
    
    $totalPackages = $requiredPackages.Count
    $currentPackage = 0
    
    foreach ($package in $requiredPackages) {
        $currentPackage++
        $percentComplete = ($currentPackage / $totalPackages) * 100
        
        Show-Progress "Instalando Pacotes" $percentComplete "Instalando $package..."
        
        try {
            & $pythonExe -m pip install $package --upgrade --no-warn-script-location --disable-pip-version-check --quiet 2>$null
            if ($LASTEXITCODE -eq 0) {
                Show-Status "$package instalado!" "success"
            } else {
                Show-Status "Erro ao instalar $package" "error"
            }
        } catch {
            Show-Status "Erro ao instalar ${package}: $($_.Exception.Message)" "error"
        }
        Start-Sleep 0.5
    }
    
    Write-Progress -Activity "Instalando Pacotes" -Completed
    return $true
}

function New-DesktopShortcut {
    $desktopPath = [Environment]::GetFolderPath("Desktop")
    $shortcutPath = "$desktopPath\$appName.lnk"
    
    if (Test-Path $shortcutPath) {
        if (!(Confirm-Action "Atalho já existe. Deseja recriar?")) {
            Show-Status "Criação do atalho cancelada pelo usuário." "info"
            return
        }
    } else {
        if (!(Confirm-Action "Deseja criar um atalho na área de trabalho?")) {
            Show-Status "Criação do atalho cancelada pelo usuário." "info"
            return
        }
    }
    
    try {
        $WScriptShell = New-Object -ComObject WScript.Shell
        $shortcut = $WScriptShell.CreateShortcut($shortcutPath)
        $shortcut.TargetPath = "$pythonwExe"
        $shortcut.Arguments = "-c ""exec(__import__('requests').get('https://raw.githubusercontent.com/Comquister/MinecraftBR-Launcher/refs/heads/main/minecraft.py').text)"""
        $shortcut.WorkingDirectory = $env:USERPROFILE
        $shortcut.Description = $appName
        
        # Tentar definir ícone
        $iconPath = "$installPath\favicon.ico"
        $faviconurl = "https://minecraftbr.com/image/favicon.ico"
    
        & curl.exe -L -o $iconPath $faviconurl --connect-timeout 60 --max-time 300 --fail --silent --show-error

        if (Test-Path $iconPath) {
            $shortcut.IconLocation = $iconPath
        }
        
        $shortcut.Save()
        Show-Status "Atalho criado na área de trabalho!" "success"
    } catch {
        Show-Status "Erro ao criar atalho: $($_.Exception.Message)" "error"
    }
}

# =============================
# Menu Principal
# =============================

function Show-Menu {
    $status = Get-InstallationStatus
    
    Write-Host "📊 Status da Instalação:" -ForegroundColor White
    Write-Host "   Python ${requiredVersion}: " -NoNewline
    if ($status.PythonInstalled) { 
        Write-Host "✅ Instalado" -ForegroundColor Green 
    } else { 
        Write-Host "❌ Não instalado" -ForegroundColor Red 
    }
    
    Write-Host "   Pacotes necessários: " -NoNewline
    if ($status.PackagesInstalled) { 
        Write-Host "✅ Instalados" -ForegroundColor Green 
    } else { 
        Write-Host "❌ Não instalados" -ForegroundColor Red 
    }
    
    Write-Host "   Launcher: " -NoNewline
    if ($status.LauncherReady) { 
        Write-Host "✅ Pronto para usar" -ForegroundColor Green 
    } else { 
        Write-Host "⚠️ Necessita instalação" -ForegroundColor Yellow 
    }
    
    if ($status.InstallSize -gt 0) {
        Write-Host "   Tamanho: " -NoNewline
        Write-Host "$([math]::Round($status.InstallSize, 1)) MB" -ForegroundColor Cyan
    }
    
    Write-Host ""
    Write-Host "🎮 O que você deseja fazer?" -ForegroundColor White
    Write-Host ""
    
    if ($status.LauncherReady) {
        Write-Host "1️⃣  🚀 Executar MinecraftBR Launcher" -ForegroundColor Green
    } else {
        Write-Host "1️⃣  Instalação Automática (Recomendado)" -ForegroundColor Green
    }
    
    Write-Host "2️⃣  🔧 Reparar/Reinstalar" -ForegroundColor Yellow
    Write-Host "3️⃣  📋 Informações Detalhadas" -ForegroundColor Cyan
    Write-Host "4️⃣  🔗 Criar Atalho na Área de Trabalho" -ForegroundColor Magenta
    Write-Host "5️⃣  🗑️  Desinstalar Completamente" -ForegroundColor Red
    Write-Host "0️⃣  Sair" -ForegroundColor Gray
    Write-Host ""
    
    return $status
}

function Start-AutoInstallation {
    Write-Host ""
    Write-Host "🔍 INSTALAÇÃO AUTOMÁTICA" -ForegroundColor Cyan
    Write-Host "Este processo irá:" -ForegroundColor White
    Write-Host "• Verificar os requisitos do seu sistema" -ForegroundColor Gray
    Write-Host "• Baixar e instalar Python $requiredVersion (~50MB)" -ForegroundColor Gray
    Write-Host "• Instalar os pacotes necessários (~20MB)" -ForegroundColor Gray
    Write-Host "• Preparar o launcher para uso" -ForegroundColor Gray
    Write-Host ""
    
    if (!(Confirm-Action "Deseja continuar com a instalação automática?")) {
        Show-Status "Instalação cancelada pelo usuário." "info"
        Read-Host "Pressione Enter para continuar"
        return
    }
    
    if (!(Test-SystemRequirements)) {
        Show-Status "Seu sistema não atende aos requisitos mínimos." "error"
        Read-Host "Pressione Enter para continuar"
        return
    }
    
    Show-Status "Sistema compatível! Prosseguindo com a instalação..." "success"
    Start-Sleep 2
    
    if (Install-PythonEmbedded) {
        if (Install-Packages) {
            Show-Status "🎉 Instalação concluída com sucesso!" "success"
            Show-Status "Você já pode executar o MinecraftBR Launcher!" "info"
        } else {
            Show-Status "Python instalado, mas houve problemas com os pacotes." "warning"
        }
    } else {
        Show-Status "Falha na instalação do Python." "error"
    }
    
    Write-Host ""
    Read-Host "Pressione Enter para continuar"
}

function Start-Launcher {
    if (!(Confirm-Action "Deseja executar o MinecraftBR Launcher agora?")) {
        Show-Status "Execução do launcher cancelada pelo usuário." "info"
        Start-Sleep 2
        return
    }
    
    if (Test-Path $pythonwExe) {
        Show-Status "Iniciando MinecraftBR Launcher..." "working"
        try {
            Start-Process $pythonwExe -ArgumentList "-c", """exec(__import__('requests').get('https://raw.githubusercontent.com/Comquister/MinecraftBR-Launcher/refs/heads/main/minecraft.py').text)"""
            Show-Status "Launcher iniciado! Verifique a bandeja do sistema." "success"
            Start-Sleep 3
            Exit-PSSession
        } catch {
            Show-Status "Erro ao iniciar: $($_.Exception.Message)" "error"
        }
    } else {
        Show-Status "Launcher não está instalado. Execute a instalação primeiro." "error"
    }
    Start-Sleep 2
}

function Show-DetailedInfo {
    Clear-Host
    Show-Header
    
    $status = Get-InstallationStatus
    
    Write-Host "📋 Informações Detalhadas" -ForegroundColor White
    Write-Host "═══════════════════════════" -ForegroundColor Gray
    Write-Host ""
    Write-Host "🔧 Configuração:"
    Write-Host "   Caminho de instalação: $installPath"
    Write-Host "   Python: $pythonExe"
    Write-Host "   Versão necessária: $requiredVersion"
    Write-Host ""
    
    if ($status.PythonInstalled) {
        Write-Host "🐍 Informações do Python:"
        try {
            $version = & $pythonExe --version 2>&1
            Write-Host "   Versão: $version" -ForegroundColor Green
            
            Write-Host ""
            Write-Host "📦 Pacotes instalados:"
            & $pythonExe -m pip list --format=columns 2>$null
        } catch {
            Write-Host "   Erro ao obter informações" -ForegroundColor Red
        }
    }
    
    Write-Host ""
    Read-Host "Pressione Enter para voltar ao menu"
}

function Remove-Installation {
    Write-Host ""
    Write-Host "⚠️  ATENÇÃO: REMOÇÃO COMPLETA" -ForegroundColor Red
    Write-Host "Esta ação irá remover:" -ForegroundColor Yellow
    Write-Host "• Todo o Python instalado" -ForegroundColor Gray
    Write-Host "• Todos os pacotes e dependências" -ForegroundColor Gray
    Write-Host "• Configurações do launcher" -ForegroundColor Gray
    Write-Host "• Atalho da área de trabalho" -ForegroundColor Gray
    Write-Host ""
    
    if (!(Confirm-Action "Tem CERTEZA que deseja desinstalar TUDO?")) {
        Show-Status "Desinstalação cancelada." "info"
        Start-Sleep 2
        return
    }
    
    # Segunda confirmação para operação destrutiva
    Write-Host ""
    Write-Host "⚠️  ÚLTIMA CHANCE!" -ForegroundColor Red
    $finalConfirm = Read-Host "Digite 'REMOVER' (em maiúsculas) para confirmar"
    
    if ($finalConfirm -ne "REMOVER") {
        Show-Status "Desinstalação cancelada por confirmação incorreta." "info"
        Start-Sleep 2
        return
    }
    
    Show-Status "Removendo instalação..." "working"
    
    try {
        if (Test-Path $installPath) {
            Remove-Item $installPath -Recurse -Force -ErrorAction Stop
        }
        
        # Remover atalho se existir
        $desktopPath = [Environment]::GetFolderPath("Desktop")
        $shortcutPath = "$desktopPath\$appName.lnk"
        if (Test-Path $shortcutPath) {
            Remove-Item $shortcutPath -Force
        }
        
        Show-Status "MinecraftBR Launcher removido completamente!" "success"
    } catch {
        Show-Status "Erro durante a remoção: $($_.Exception.Message)" "error"
    }
    
    Start-Sleep 2
}

# =============================
# Loop Principal
# =============================

Show-Header
Write-Host "👋 Bem-vindo ao instalador do MinecraftBR Launcher!" -ForegroundColor Green
Write-Host ""
Write-Host "Este instalador irá te guiar através do processo de instalação," -ForegroundColor White
Write-Host "sempre perguntando antes de fazer qualquer alteração no seu sistema." -ForegroundColor White
Write-Host ""
Read-Host "Pressione Enter para começar"

do {
    Show-Header
    $status = Show-Menu
    
    $choice = Read-Host "Digite sua escolha (0-5)"
    
    switch ($choice) {
        "1" {
            if ($status.LauncherReady) {
                Start-Launcher
            } else {
                Start-AutoInstallation
            }
        }
        "2" {
            Write-Host ""
            Write-Host "🔧 REPARAR/REINSTALAR" -ForegroundColor Yellow
            Write-Host "Isso irá remover a instalação atual e instalar tudo novamente." -ForegroundColor White
            
            if (Confirm-Action "Deseja continuar com a reinstalação?") {
                if (Test-Path $installPath) {
                    Remove-Item $installPath -Recurse -Force -ErrorAction SilentlyContinue
                }
                Start-AutoInstallation
            } else {
                Show-Status "Reinstalação cancelada pelo usuário." "info"
                Start-Sleep 2
            }
        }
        "3" {
            Show-DetailedInfo
        }
        "4" {
            New-DesktopShortcut
            Start-Sleep 2
        }
        "5" {
            Remove-Installation
        }
        "0" {
            Show-Status "Obrigado por usar o MinecraftBR Launcher! 🎮" "success"
            Start-Sleep 1
            break
        }
        default {
            Show-Status "Opção inválida! Digite um número de 0 a 5." "warning"
            Start-Sleep 1
        }
    }
} while ($choice -ne "0")

Write-Host ""
Write-Host "Até mais! 👋" -ForegroundColor Cyan