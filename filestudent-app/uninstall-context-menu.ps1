<#
Retire le menu contextuel FileStudent de l'explorateur Windows.
N'a pas besoin des droits administrateur (memes cles HKCU que l'installation).
#>

$verbIds = @(
    "FileStudent_ToPDF", "FileStudent_ToWord", "FileStudent_ToImage",
    "FileStudent_ToMarkdown", "FileStudent_Compress", "FileStudent_Enhance",
    "FileStudent_Split", "FileStudent_Repair", "FileStudent_Redact",
    "FileStudent_Watermark", "FileStudent_Protect", "FileStudent_DetectAI",
    "FileStudent_Open"
)
foreach ($id in $verbIds) {
    Remove-Item -Path "HKCU:\Software\Classes\*\shell\$id" -Recurse -Force -ErrorAction SilentlyContinue
}

Remove-Item -Path "HKCU:\Software\Classes\Directory\shell\FileStudent_Archive" -Recurse -Force -ErrorAction SilentlyContinue
Remove-Item -Path "HKCU:\Software\Classes\Directory\shell\FileStudent_OpenFolder" -Recurse -Force -ErrorAction SilentlyContinue
Remove-Item -Path "HKCU:\Software\Classes\Directory\Background\shell\FileStudent" -Recurse -Force -ErrorAction SilentlyContinue

Write-Host "Menu contextuel FileStudent retire."
