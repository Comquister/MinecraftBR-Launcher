# Script PowerShell para criar pasta, baixar e executar arquivo
# Configuração
$pastaDestino = "$env:APPDATA\.minecraftbr"
$urlDownload = "https://github.com/Comquister/MinecraftBR-Launcher/releases/download/release/minecraft.run.exe"  # SUBSTITUA pela URL real
$nomeArquivo = "minecraft.run.exe"  # SUBSTITUA pelo nome do arquivo
$caminhoCompleto = Join-Path $pastaDestino $nomeArquivo

try {
    # Verifica se a pasta existe, se não, cria
    if (!(Test-Path -Path $pastaDestino)) {
        Write-Host "Criando pasta: $pastaDestino" -ForegroundColor Green
        New-Item -ItemType Directory -Path $pastaDestino -Force | Out-Null
    } else {
        Write-Host "Pasta já existe: $pastaDestino" -ForegroundColor Yellow
    }

    # Verifica se o arquivo já existe
    if (Test-Path -Path $caminhoCompleto) {
        Write-Host "Arquivo já existe: $caminhoCompleto" -ForegroundColor Yellow
        $resposta = Read-Host "Deseja baixar novamente? (S/N)"
        if ($resposta -notmatch "^[Ss]$") {
            Write-Host "Pulando download..." -ForegroundColor Blue
        } else {
            Remove-Item $caminhoCompleto -Force
        }
    }

    # Baixa o arquivo se não existir ou foi escolhido baixar novamente
    if (!(Test-Path -Path $caminhoCompleto)) {
        Write-Host "Baixando arquivo de: $urlDownload" -ForegroundColor Green
        Write-Host "Destino: $caminhoCompleto" -ForegroundColor Green
        
        # Usando Invoke-WebRequest para download
        $progressPreference = 'SilentlyContinue'  # Remove barra de progresso para melhor performance
        Invoke-WebRequest -Uri $urlDownload -OutFile $caminhoCompleto -UseBasicParsing
        $progressPreference = 'Continue'
        
        Write-Host "Download concluído!" -ForegroundColor Green
    }

    # Verifica se o arquivo foi baixado com sucesso
    if (Test-Path -Path $caminhoCompleto) {
        Write-Host "Executando: $caminhoCompleto" -ForegroundColor Green
        
        # Executa o arquivo
        Start-Process -FilePath $caminhoCompleto -WorkingDirectory $pastaDestino
        
        Write-Host "Arquivo executado com sucesso!" -ForegroundColor Green
    } else {
        throw "Erro: Arquivo não foi encontrado após o download"
    }

} catch {
    Write-Host "ERRO: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host "Pressione qualquer tecla para sair..."
    $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
    exit 1
}

Write-Host "Script finalizado. Pressione qualquer tecla para sair..." -ForegroundColor Cyan
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")