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

param([switch]$atalho,[switch]$nostart)
$d="$env:APPDATA\.minecraftbr";$r="Comquister/MinecraftBR-Launcher";[void](mkdir $d -f 2>$null)
$j=irm "https://api.github.com/repos/$r/releases/latest";$a=$j.assets|?{$_.name-like"*.exe"}|select -f 1
if(!$a){throw"Nenhum .exe encontrado"}
$p="$d\$($a.name)";$u=$a.browser_download_url
$h1=if(test-path $p){(gi $p|filehash).hash}
curl.exe -L -s -o $p $u
$h2=(gi $p|filehash).hash
if($h1-ne$h2){"Atualizado"}else{"Mesmo arquivo"}
if($atalho){
$ws=New-Object -ComObject WScript.Shell
$s=$ws.CreateShortcut("$env:USERPROFILE\Desktop\MinecraftBR.lnk")
$s.TargetPath=$p;$s.WorkingDirectory=$d;$s.IconLocation=$p;$s.Save()
"Atalho criado na área de trabalho"
}
if(!$nostart){start $p -WorkingDirectory $d}