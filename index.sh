#!/bin/bash

# =============================
# MinecraftBR Launcher - Instalador Linux
# =============================

# Configurações
APP_NAME="MinecraftBR Launcher"
INSTALL_PATH="$HOME/.minecraftbr"
PYTHON_PATH="$INSTALL_PATH/python"
PYTHON_EXE="$PYTHON_PATH/bin/python3"
REQUIRED_VERSION="3.13"
REQUIRED_PACKAGES=("requests" "portablemc" "PyQt6" "flask" "psutil")

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# =============================
# Funções de Interface
# =============================

show_header() {
    clear
    echo -e "${CYAN}╔════════════════════════════════════════════╗${NC}"
    echo -e "${CYAN}║          🎮 MinecraftBR Launcher           ║${NC}"
    echo -e "${CYAN}║         Instalador Linux v1.0              ║${NC}"
    echo -e "${CYAN}╚════════════════════════════════════════════╝${NC}"
    echo ""
}

show_status() {
    local message="$1"
    local status="${2:-info}"
    
    case $status in
        "info")    echo -e "ℹ️  ${CYAN}$message${NC}" ;;
        "success") echo -e "✅ ${GREEN}$message${NC}" ;;
        "warning") echo -e "⚠️  ${YELLOW}$message${NC}" ;;
        "error")   echo -e "❌ ${RED}$message${NC}" ;;
        "working") echo -e "⏳ ${YELLOW}$message${NC}" ;;
    esac
}

confirm_action() {
    local message="$1"
    echo ""
    echo -e "${YELLOW}$message${NC}"
    read -p "Continuar? (S/n): " response
    case $response in
        [nN]|[nN][oO]) return 1 ;;
        *) return 0 ;;
    esac
}

# =============================
# Funções de Verificação
# =============================

test_system_requirements() {
    show_status "Verificando requisitos do sistema..." "working"
    sleep 1
    
    local all_good=true
    
    # Verificar memória RAM (pelo menos 3GB)
    local ram_kb=$(grep MemTotal /proc/meminfo | awk '{print $2}')
    local ram_gb=$((ram_kb / 1024 / 1024))
    
    if [ $ram_gb -ge 3 ]; then
        show_status "Memória RAM ($ram_gb GB): OK" "success"
    else
        show_status "Memória RAM ($ram_gb GB): Insuficiente (mín. 3GB)" "error"
        all_good=false
    fi
    
    # Verificar permissões de escrita
    if [ -w "$HOME" ]; then
        show_status "Permissões de escrita: OK" "success"
    else
        show_status "Permissões de escrita: FALHOU" "error"
        all_good=false
    fi
    
    # Verificar se tem curl ou wget
    if command -v curl > /dev/null || command -v wget > /dev/null; then
        show_status "Ferramenta de download: OK" "success"
    else
        show_status "curl ou wget: NÃO ENCONTRADO" "error"
        all_good=false
    fi
    
    # Verificar se tem python3
    if command -v python3 > /dev/null; then
        local py_version=$(python3 --version 2>&1 | grep -oP '\d+\.\d+')
        show_status "Python3 do sistema ($py_version): OK" "success"
    else
        show_status "Python3 do sistema: NÃO ENCONTRADO" "warning"
        show_status "Será instalado Python portátil" "info"
    fi
    
    if $all_good; then
        return 0
    else
        return 1
    fi
}

get_installation_status() {
    local python_installed=false
    local packages_installed=false
    local launcher_ready=false
    local install_size=0
    
    # Verificar se o Python existe
    if [ -f "$PYTHON_EXE" ]; then
        local version=$($PYTHON_EXE -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')" 2>/dev/null)
        if [[ "$version" == "3."* ]]; then
            python_installed=true
            
            # Verificar pacotes
            local installed_count=0
            for package in "${REQUIRED_PACKAGES[@]}"; do
                if $PYTHON_EXE -c "import $package" 2>/dev/null; then
                    ((installed_count++))
                fi
            done
            
            if [ $installed_count -eq ${#REQUIRED_PACKAGES[@]} ]; then
                packages_installed=true
                launcher_ready=true
            fi
        fi
    fi
    
    # Calcular tamanho da instalação
    if [ -d "$INSTALL_PATH" ]; then
        install_size=$(du -sm "$INSTALL_PATH" 2>/dev/null | cut -f1)
    fi
    
    # Retornar status via variáveis globais
    PYTHON_INSTALLED=$python_installed
    PACKAGES_INSTALLED=$packages_installed
    LAUNCHER_READY=$launcher_ready
    INSTALL_SIZE=${install_size:-0}
}

# =============================
# Funções de Instalação
# =============================

install_python() {
    if ! confirm_action "Deseja instalar o Python ${REQUIRED_VERSION}? (Necessário ~100MB de espaço)"; then
        show_status "Instalação do Python cancelada pelo usuário." "info"
        return 1
    fi
    
    show_status "Preparando instalação do Python $REQUIRED_VERSION..." "working"
    
    # Limpar instalação anterior
    if [ -d "$PYTHON_PATH" ]; then
        show_status "Removendo versão anterior..." "working"
        rm -rf "$PYTHON_PATH"
    fi
    
    mkdir -p "$PYTHON_PATH"
    
    # URL do Python (usando pyenv-like approach ou sistema)
    show_status "Tentando instalar Python via sistema..." "working"
    
    # Verificar gerenciador de pacotes e instalar python3-venv
    if command -v apt > /dev/null; then
        show_status "Detectado sistema baseado em Debian/Ubuntu" "info"
        show_status "Você pode precisar instalar: sudo apt install python3 python3-pip python3-venv" "info"
    elif command -v yum > /dev/null; then
        show_status "Detectado sistema baseado em Red Hat/CentOS" "info"
        show_status "Você pode precisar instalar: sudo yum install python3 python3-pip" "info"
    elif command -v pacman > /dev/null; then
        show_status "Detectado Arch Linux" "info"
        show_status "Você pode precisar instalar: sudo pacman -S python python-pip" "info"
    fi
    
    # Criar ambiente virtual
    if command -v python3 > /dev/null; then
        show_status "Criando ambiente virtual..." "working"
        python3 -m venv "$PYTHON_PATH"
        
        if [ -f "$PYTHON_EXE" ]; then
            show_status "Python instalado com sucesso!" "success"
            return 0
        else
            show_status "Erro ao criar ambiente virtual" "error"
            return 1
        fi
    else
        show_status "Python3 não encontrado no sistema. Instale primeiro:" "error"
        show_status "Ubuntu/Debian: sudo apt install python3 python3-pip python3-venv" "info"
        show_status "CentOS/RHEL: sudo yum install python3 python3-pip" "info"
        show_status "Arch: sudo pacman -S python python-pip" "info"
        return 1
    fi
}

install_packages() {
    if ! confirm_action "Deseja instalar os pacotes necessários para o launcher?"; then
        show_status "Instalação de pacotes cancelada pelo usuário." "info"
        return 1
    fi
    
    show_status "Instalando pacotes necessários..." "working"
    
    local total_packages=${#REQUIRED_PACKAGES[@]}
    local current_package=0
    
    for package in "${REQUIRED_PACKAGES[@]}"; do
        ((current_package++))
        echo -ne "Instalando pacotes... [$current_package/$total_packages] $package\r"
        
        if $PYTHON_EXE -m pip install "$package" --upgrade --quiet 2>/dev/null; then
            show_status "$package instalado!" "success"
        else
            show_status "Erro ao instalar $package" "error"
        fi
        sleep 0.5
    done
    
    echo "" # Nova linha após o progresso
    return 0
}

create_desktop_shortcut() {
    local desktop_path="$HOME/Desktop"
    local shortcut_path="$desktop_path/$APP_NAME.desktop"
    
    if [ -f "$shortcut_path" ]; then
        if ! confirm_action "Atalho já existe. Deseja recriar?"; then
            show_status "Criação do atalho cancelada pelo usuário." "info"
            return
        fi
    else
        if ! confirm_action "Deseja criar um atalho na área de trabalho?"; then
            show_status "Criação do atalho cancelada pelo usuário." "info"
            return
        fi
    fi
    
    # Criar arquivo .desktop
    cat > "$shortcut_path" << EOF
[Desktop Entry]
Version=1.0
Type=Application
Name=$APP_NAME
Comment=Launcher para Minecraft
Exec=$PYTHON_EXE -c "exec(__import__('requests').get('https://raw.githubusercontent.com/Comquister/MinecraftBR-Launcher/refs/heads/main/minecraft.py').text)"
Icon=minecraft
Terminal=false
Categories=Game;
StartupNotify=true
EOF
    
    chmod +x "$shortcut_path"
    show_status "Atalho criado na área de trabalho!" "success"
}

# =============================
# Menu Principal
# =============================

show_menu() {
    get_installation_status
    
    echo -e "${NC}📊 Status da Instalação:"
    
    echo -n "   Python ${REQUIRED_VERSION}: "
    if $PYTHON_INSTALLED; then
        echo -e "${GREEN}✅ Instalado${NC}"
    else
        echo -e "${RED}❌ Não instalado${NC}"
    fi
    
    echo -n "   Pacotes necessários: "
    if $PACKAGES_INSTALLED; then
        echo -e "${GREEN}✅ Instalados${NC}"
    else
        echo -e "${RED}❌ Não instalados${NC}"
    fi
    
    echo -n "   Launcher: "
    if $LAUNCHER_READY; then
        echo -e "${GREEN}✅ Pronto para usar${NC}"
    else
        echo -e "${YELLOW}⚠️ Necessita instalação${NC}"
    fi
    
    if [ $INSTALL_SIZE -gt 0 ]; then
        echo -e "   Tamanho: ${CYAN}${INSTALL_SIZE} MB${NC}"
    fi
    
    echo ""
    echo -e "${NC}🎮 O que você deseja fazer?"
    echo ""
    
    if $LAUNCHER_READY; then
        echo -e "${GREEN}1️⃣  🚀 Executar MinecraftBR Launcher${NC}"
    else
        echo -e "${GREEN}1️⃣  Instalação Automática (Recomendado)${NC}"
    fi
    
    echo -e "${YELLOW}2️⃣  🔧 Reparar/Reinstalar${NC}"
    echo -e "${CYAN}3️⃣  📋 Informações Detalhadas${NC}"
    echo -e "${BLUE}4️⃣  🔗 Criar Atalho na Área de Trabalho${NC}"
    echo -e "${RED}5️⃣  🗑️  Desinstalar Completamente${NC}"
    echo -e "0️⃣  Sair"
    echo ""
}

start_auto_installation() {
    echo ""
    echo -e "${CYAN}🔍 INSTALAÇÃO AUTOMÁTICA${NC}"
    echo -e "${NC}Este processo irá:"
    echo -e "• Verificar os requisitos do seu sistema"
    echo -e "• Criar um ambiente virtual Python"
    echo -e "• Instalar os pacotes necessários (~50MB)"
    echo -e "• Preparar o launcher para uso"
    echo ""
    
    if ! confirm_action "Deseja continuar com a instalação automática?"; then
        show_status "Instalação cancelada pelo usuário." "info"
        read -p "Pressione Enter para continuar"
        return
    fi
    
    if ! test_system_requirements; then
        show_status "Seu sistema não atende aos requisitos mínimos." "error"
        read -p "Pressione Enter para continuar"
        return
    fi
    
    show_status "Sistema compatível! Prosseguindo com a instalação..." "success"
    sleep 2
    
    if install_python; then
        if install_packages; then
            show_status "🎉 Instalação concluída com sucesso!" "success"
            show_status "Você já pode executar o MinecraftBR Launcher!" "info"
        else
            show_status "Python instalado, mas houve problemas com os pacotes." "warning"
        fi
    else
        show_status "Falha na instalação do Python." "error"
    fi
    
    echo ""
    read -p "Pressione Enter para continuar"
}

start_launcher() {
    if ! confirm_action "Deseja executar o MinecraftBR Launcher agora?"; then
        show_status "Execução do launcher cancelada pelo usuário." "info"
        sleep 2
        return
    fi
    
    if [ -f "$PYTHON_EXE" ]; then
        show_status "Iniciando MinecraftBR Launcher..." "working"
        $PYTHON_EXE -c "exec(__import__('requests').get('https://raw.githubusercontent.com/Comquister/MinecraftBR-Launcher/refs/heads/main/minecraft.py').text)" &
        show_status "Launcher iniciado!" "success"
        sleep 3
        exit 0
    else
        show_status "Launcher não está instalado. Execute a instalação primeiro." "error"
    fi
    sleep 2
}

show_detailed_info() {
    clear
    show_header
    
    get_installation_status
    
    echo -e "${NC}📋 Informações Detalhadas"
    echo "═══════════════════════════"
    echo ""
    echo "🔧 Configuração:"
    echo "   Caminho de instalação: $INSTALL_PATH"
    echo "   Python: $PYTHON_EXE"
    echo "   Versão necessária: $REQUIRED_VERSION"
    echo ""
    
    if $PYTHON_INSTALLED && [ -f "$PYTHON_EXE" ]; then
        echo "🐍 Informações do Python:"
        local version=$($PYTHON_EXE --version 2>&1)
        echo -e "   Versão: ${GREEN}$version${NC}"
        
        echo ""
        echo "📦 Pacotes instalados:"
        $PYTHON_EXE -m pip list 2>/dev/null || echo "   Erro ao listar pacotes"
    fi
    
    echo ""
    read -p "Pressione Enter para voltar ao menu"
}

remove_installation() {
    echo ""
    echo -e "${RED}⚠️  ATENÇÃO: REMOÇÃO COMPLETA${NC}"
    echo -e "${YELLOW}Esta ação irá remover:${NC}"
    echo "• Todo o ambiente Python instalado"
    echo "• Todos os pacotes e dependências"
    echo "• Configurações do launcher"
    echo "• Atalho da área de trabalho"
    echo ""
    
    if ! confirm_action "Tem CERTEZA que deseja desinstalar TUDO?"; then
        show_status "Desinstalação cancelada." "info"
        sleep 2
        return
    fi
    
    # Segunda confirmação
    echo ""
    echo -e "${RED}⚠️  ÚLTIMA CHANCE!${NC}"
    read -p "Digite 'REMOVER' (em maiúsculas) para confirmar: " final_confirm
    
    if [ "$final_confirm" != "REMOVER" ]; then
        show_status "Desinstalação cancelada por confirmação incorreta." "info"
        sleep 2
        return
    fi
    
    show_status "Removendo instalação..." "working"
    
    # Remover diretório de instalação
    if [ -d "$INSTALL_PATH" ]; then
        rm -rf "$INSTALL_PATH"
    fi
    
    # Remover atalho se existir
    local shortcut_path="$HOME/Desktop/$APP_NAME.desktop"
    if [ -f "$shortcut_path" ]; then
        rm -f "$shortcut_path"
    fi
    
    show_status "MinecraftBR Launcher removido completamente!" "success"
    sleep 2
}

# =============================
# Loop Principal
# =============================

main() {
    show_header
    echo -e "${GREEN}👋 Bem-vindo ao instalador do MinecraftBR Launcher!${NC}"
    echo ""
    echo -e "${NC}Este instalador irá te guiar através do processo de instalação,"
    echo "sempre perguntando antes de fazer qualquer alteração no seu sistema."
    echo ""
    read -p "Pressione Enter para começar"
    
    while true; do
        show_header
        show_menu
        
        read -p "Digite sua escolha (0-5): " choice
        
        case $choice in
            "1")
                if $LAUNCHER_READY; then
                    start_launcher
                else
                    start_auto_installation
                fi
                ;;
            "2")
                echo ""
                echo -e "${YELLOW}🔧 REPARAR/REINSTALAR${NC}"
                echo "Isso irá remover a instalação atual e instalar tudo novamente."
                
                if confirm_action "Deseja continuar com a reinstalação?"; then
                    if [ -d "$INSTALL_PATH" ]; then
                        rm -rf "$INSTALL_PATH"
                    fi
                    start_auto_installation
                else
                    show_status "Reinstalação cancelada pelo usuário." "info"
                    sleep 2
                fi
                ;;
            "3")
                show_detailed_info
                ;;
            "4")
                create_desktop_shortcut
                sleep 2
                ;;
            "5")
                remove_installation
                ;;
            "0")
                show_status "Obrigado por usar o MinecraftBR Launcher! 🎮" "success"
                sleep 1
                break
                ;;
            *)
                show_status "Opção inválida! Digite um número de 0 a 5." "warning"
                sleep 1
                ;;
        esac
    done
    
    echo ""
    echo -e "${CYAN}Até mais! 👋${NC}"
}

# Executar o programa principal
main