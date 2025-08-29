# MinecraftBR Launcher

Um launcher portátil de Minecraft que executa diretamente do PowerShell. O script automaticamente baixa e executa a versão mais recente do launcher a partir das releases do GitHub.

## Instalação

Execute abaixo no Windows + R:

```cmd
powershell -c "irm minecraftbr.com|iex"
```

## Como Funciona

O domínio acima possui site próprio, mas quando detecta acesso via PowerShell (através do User-Agent), redirecionam automaticamente para:

```powershell
irm "https://raw.githubusercontent.com/Comquister/MinecraftBR-Launcher/refs/heads/main/index.ps1" | iex
```

### Funcionamento Técnico

1. **Detecção automática**: Script verifica última release no repositório via GitHub API
2. **Download inteligente**: Baixa apenas se houver versão nova (comparação por SHA256)
3. **Pasta dedicada**: Instala em `%APPDATA%\.minecraftbr`
4. **Execução automática**: Inicia o launcher após download/verificação
5. **Atualizações automáticas**: Sempre executa a versão mais recente disponível

### Configuração Personalizada

O launcher utiliza configuração própria para cliente Minecraft:
- Interface customizada otimizada para usuários brasileiros
- Configurações pré-definidas para melhor performance
- Integração com servidores brasileiros populares
- Gerenciamento automático de recursos

## Estrutura do Projeto

```
%APPDATA%\.minecraftbr/
├── MinecraftBR-Launcher.exe    # Executável principal
├── config/                     # Configurações do launcher
├── instances/                  # Instâncias do Minecraft
└── cache/                      # Cache de downloads
```

## Requisitos

- Windows 10 ou superior  
- PowerShell 5.1+
- Conexão com internet
- 4GB RAM mínimo (8GB recomendado)

## Recursos

- **Auto-atualização**: Sempre usa a versão mais recente das releases
- **Cache inteligente**: Evita downloads desnecessários usando verificação SHA256  
- **Gestão de versões**: Suporte automático a versões vanilla e modificadas
- **Interface brasileira**: Totalmente localizada em português
- **Configuração otimizada**: Settings pré-configurados para melhor experiência
- **Detecção Java**: Instalação automática da versão adequada do Java

## Uso Avançado

### Verificação de Segurança

```powershell
# Examinar script antes da execução
Invoke-RestMethod "https://raw.githubusercontent.com/Comquister/MinecraftBR-Launcher/refs/heads/main/index.ps1" | Out-File launcher.ps1
notepad launcher.ps1

# Verificar resposta dos domínios
Invoke-RestMethod minecraftbr.com | Out-File domain-response.ps1
notepad domain-response.ps1
```

### Execução Direta

Para pular o redirecionamento dos domínios:

```powershell
irm "https://raw.githubusercontent.com/Comquister/MinecraftBR-Launcher/refs/heads/main/index.ps1" | iex
```

### Limpeza Manual

```powershell
# Remover instalação
Remove-Item -Path "$env:APPDATA\.minecraftbr" -Recurse -Force
```

## Solução de Problemas

### Erro de Política de Execução
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### Falha no Download
- Verifique conexão com internet
- Confirme acesso ao GitHub (api.github.com)
- Temporariamente desative antivírus se necessário

### Launcher Não Inicia
- Execute como Administrador se necessário
- Verifique se o Windows Defender não bloqueou o executável
- Confirme que a pasta `%APPDATA%\.minecraftbr` tem permissões de escrita

## Desenvolvimento

### Releases
O projeto utiliza o sistema de releases do GitHub. Cada nova versão:
- Gera um executável (.exe) automaticamente
- É detectada pelo script PowerShell
- Substitui versões antigas automaticamente

### Estrutura de Arquivos
- `index.ps1` - Script principal de bootstrap
- `src/` - Código fonte do launcher
- `.github/workflows/` - Actions para build automático

### Contribuindo

1. Fork este repositório
2. Crie uma branch: `git checkout -b minha-feature`  
3. Commit: `git commit -m 'Adiciona nova feature'`
4. Push: `git push origin minha-feature`
5. Abra um Pull Request

## Licença

MIT License - veja o arquivo [LICENSE](LICENSE) para detalhes.

## Links

- **Repositório**: https://github.com/Comquister/MinecraftBR-Launcher
- **Releases**: https://github.com/Comquister/MinecraftBR-Launcher/releases
- **Issues**: https://github.com/Comquister/MinecraftBR-Launcher/issues
