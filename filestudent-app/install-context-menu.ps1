<#
Installe le menu contextuel FileStudent dans l'explorateur Windows :
clic droit sur un fichier, sur un dossier, ou sur le bureau (fond d'un
dossier). Chaque action est une entree directe, prefixee "FileStudent -",
pas un sous-menu en cascade : ce mecanisme s'est avere peu fiable en
pratique (l'entree principale s'affiche mais reste vide au survol sur
certaines configurations).

N'a PAS besoin des droits administrateur : tout est ecrit sous
HKEY_CURRENT_USER, valable uniquement pour l'utilisateur qui l'execute.

Usage :
    .\install-context-menu.ps1
    .\install-context-menu.ps1 -ExePath "C:\chemin\vers\FileStudent.exe"

Si Windows refuse d'executer le script (politique d'execution), lancez :
    powershell -ExecutionPolicy Bypass -File install-context-menu.ps1
#>
param(
    [string]$ExePath = (Join-Path $PSScriptRoot "dist\FileStudent.exe")
)

if (-not (Test-Path $ExePath)) {
    Write-Error "Introuvable : $ExePath`nConstruisez d'abord l'executable avec build.bat."
    exit 1
}
$ExePath = (Resolve-Path $ExePath).Path

function New-DirectVerb {
    param([string]$ParentKey, [string]$Id, [string]$Label, [string]$Command)
    $verbKey = "$ParentKey\$Id"
    New-Item -Path $verbKey -Force | Out-Null
    Set-ItemProperty -Path $verbKey -Name "(Default)" -Value $Label
    Set-ItemProperty -Path $verbKey -Name "Icon" -Value "`"$ExePath`""
    New-Item -Path "$verbKey\command" -Force | Out-Null
    Set-ItemProperty -Path "$verbKey\command" -Name "(Default)" -Value $Command
}

# --- Entrees directes sur un fichier, tous types confondus ---
$fileParent = "HKCU:\Software\Classes\*\shell"
New-DirectVerb $fileParent "FileStudent_ToPDF" "FileStudent - Convertir en PDF" "`"$ExePath`" --action=to-pdf --file=`"%1`""
New-DirectVerb $fileParent "FileStudent_ToWord" "FileStudent - Convertir en Word (.docx)" "`"$ExePath`" --action=to-word --file=`"%1`""
New-DirectVerb $fileParent "FileStudent_ToImage" "FileStudent - Convertir en image (PNG)" "`"$ExePath`" --action=to-image --file=`"%1`""
New-DirectVerb $fileParent "FileStudent_ToMarkdown" "FileStudent - Convertir en Markdown" "`"$ExePath`" --action=to-md --file=`"%1`""
New-DirectVerb $fileParent "FileStudent_Compress" "FileStudent - Reduire la taille" "`"$ExePath`" --action=compress --file=`"%1`""
New-DirectVerb $fileParent "FileStudent_Enhance" "FileStudent - Ameliorer l'image" "`"$ExePath`" --action=enhance --file=`"%1`""
New-DirectVerb $fileParent "FileStudent_Split" "FileStudent - Diviser en pages" "`"$ExePath`" --action=split --file=`"%1`""
New-DirectVerb $fileParent "FileStudent_Repair" "FileStudent - Reparer le PDF" "`"$ExePath`" --action=repair --file=`"%1`""
New-DirectVerb $fileParent "FileStudent_Redact" "FileStudent - Censurer un texte..." "`"$ExePath`" --action=redact --file=`"%1`""
New-DirectVerb $fileParent "FileStudent_Watermark" "FileStudent - Ajouter un filigrane..." "`"$ExePath`" --action=watermark --file=`"%1`""
New-DirectVerb $fileParent "FileStudent_Protect" "FileStudent - Proteger par mot de passe..." "`"$ExePath`" --action=protect --file=`"%1`""
New-DirectVerb $fileParent "FileStudent_DetectAI" "FileStudent - Detecter texte IA" "`"$ExePath`" --action=detect-ai --file=`"%1`""
New-DirectVerb $fileParent "FileStudent_Open" "FileStudent - Ouvrir dans FileStudent" "`"$ExePath`" --file=`"%1`""

# --- Entrees directes sur un dossier (clic droit sur le dossier lui-meme) ---
$folderParent = "HKCU:\Software\Classes\Directory\shell"
New-DirectVerb $folderParent "FileStudent_Archive" "FileStudent - Compresser en .tar.gz" "`"$ExePath`" --action=archive --file=`"%1`""
New-DirectVerb $folderParent "FileStudent_OpenFolder" "FileStudent - Ouvrir" "`"$ExePath`""

# --- Entree sur le fond d'un dossier ou du bureau ---
$bgKey = "HKCU:\Software\Classes\Directory\Background\shell\FileStudent"
New-Item -Path $bgKey -Force | Out-Null
Set-ItemProperty -Path $bgKey -Name "(Default)" -Value "Ouvrir FileStudent"
Set-ItemProperty -Path $bgKey -Name "Icon" -Value "`"$ExePath`""
New-Item -Path "$bgKey\command" -Force | Out-Null
Set-ItemProperty -Path "$bgKey\command" -Name "(Default)" -Value "`"$ExePath`""

Write-Host "Menu contextuel FileStudent installe (15 entrees : fichiers, dossiers, bureau)."
Write-Host "Si les entrees n'apparaissent pas tout de suite, redemarrez l'explorateur Windows"
Write-Host "(gestionnaire des taches > Explorateur Windows > Redemarrer)."
