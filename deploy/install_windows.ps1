# EGGUF Windows Installer — Registers .egguf and .efe file types
# No logo, no icon — completely blank as requested.
# Run: Right-click -> Run with PowerShell, or: powershell -ExecutionPolicy Bypass -File install_windows.ps1

$ErrorActionPreference = "Stop"

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "  EGGUF Windows Installer" -ForegroundColor Cyan
Write-Host "  Extensible GGUF System" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""

# Find executable
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$Exe = Join-Path $ScriptDir "egguf.exe"
if (-not (Test-Path $Exe)) {
    $Exe = Join-Path $ScriptDir "bin\egguf.exe"
}
if (-not (Test-Path $Exe)) {
    # Check if running from same dir
    $Exe = Join-Path $PWD "egguf.exe"
}
if (-not (Test-Path $Exe)) {
    Write-Host "ERROR: egguf.exe not found." -ForegroundColor Red
    Write-Host "Expected: egguf.exe in the same folder as this script."
    Write-Host "Build it with: python build_full.py" -ForegroundColor Yellow
    Read-Host "Press Enter to exit"
    exit 1
}

$ExePath = (Resolve-Path $Exe).Path

Write-Host "[1/7] Registering .egguf file type ..." -ForegroundColor Green
New-Item -Path "HKCR:\.egguf" -Force | Out-Null
Set-ItemProperty "HKCR:\.egguf" -Name "(Default)" -Value "EGGUF.File"
New-Item -Path "HKCR:\EGGUF.File" -Force | Out-Null
Set-ItemProperty "HKCR:\EGGUF.File" -Name "(Default)" -Value "Extensible GGUF File"
New-Item -Path "HKCR:\EGGUF.File\DefaultIcon" -Force | Out-Null
Set-ItemProperty "HKCR:\EGGUF.File\DefaultIcon" -Name "(Default)" -Value ""
New-Item -Path "HKCR:\EGGUF.File\shell\open\command" -Force | Out-Null
Set-ItemProperty "HKCR:\EGGUF.File\shell\open\command" -Name "(Default)" -Value "`"$ExePath`" `"%1`""
New-Item -Path "HKCR:\EGGUF.File\shell\open" -Force | Out-Null
Set-ItemProperty "HKCR:\EGGUF.File\shell\open" -Name "(Default)" -Value "Open with EGGUF"

Write-Host "[2/7] Registering .efe file type ..." -ForegroundColor Green
New-Item -Path "HKCR:\.efe" -Force | Out-Null
Set-ItemProperty "HKCR:\.efe" -Name "(Default)" -Value "EFE.File"
New-Item -Path "HKCR:\EFE.File" -Force | Out-Null
Set-ItemProperty "HKCR:\EFE.File" -Name "(Default)" -Value "Extensions For EGGUF"
New-Item -Path "HKCR:\EFE.File\DefaultIcon" -Force | Out-Null
Set-ItemProperty "HKCR:\EFE.File\DefaultIcon" -Name "(Default)" -Value ""
New-Item -Path "HKCR:\EFE.File\shell\open\command" -Force | Out-Null
Set-ItemProperty "HKCR:\EFE.File\shell\open\command" -Name "(Default)" -Value "`"$ExePath`" `"%1`""
New-Item -Path "HKCR:\EFE.File\shell\open" -Force | Out-Null
Set-ItemProperty "HKCR:\EFE.File\shell\open" -Name "(Default)" -Value "Open with EGGUF"

Write-Host "[3/7] Registering .gguf file type for conversion ..." -ForegroundColor Green
New-Item -Path "HKCR:\.gguf" -Force | Out-Null
Set-ItemProperty "HKCR:\.gguf" -Name "(Default)" -Value "GGUF.File"
New-Item -Path "HKCR:\GGUF.File" -Force | Out-Null
Set-ItemProperty "HKCR:\GGUF.File" -Name "(Default)" -Value "GGUF Model File"
New-Item -Path "HKCR:\GGUF.File\DefaultIcon" -Force | Out-Null
Set-ItemProperty "HKCR:\GGUF.File\DefaultIcon" -Name "(Default)" -Value ""
New-Item -Path "HKCR:\GGUF.File\shell\open\command" -Force | Out-Null
Set-ItemProperty "HKCR:\GGUF.File\shell\open\command" -Name "(Default)" -Value "`"$ExePath`" `"%1`""
New-Item -Path "HKCR:\GGUF.File\shell\open" -Force | Out-Null
Set-ItemProperty "HKCR:\GGUF.File\shell\open" -Name "(Default)" -Value "Open with EGGUF"

Write-Host "[4/7] Registering for current user ..." -ForegroundColor Green
New-Item -Path "HKCU:\Software\Classes\.egguf" -Force | Out-Null
Set-ItemProperty "HKCU:\Software\Classes\.egguf" -Name "(Default)" -Value "EGGUF.File"
New-Item -Path "HKCU:\Software\Classes\.efe" -Force | Out-Null
Set-ItemProperty "HKCU:\Software\Classes\.efe" -Name "(Default)" -Value "EFE.File"
New-Item -Path "HKCU:\Software\Classes\.gguf" -Force | Out-Null
Set-ItemProperty "HKCU:\Software\Classes\.gguf" -Name "(Default)" -Value "GGUF.File"

Write-Host "[5/7] Adding to user PATH ..." -ForegroundColor Green
$UserPath = [Environment]::GetEnvironmentVariable("PATH", "User")
$ExeDir = Split-Path -Parent $ExePath
if ($UserPath -notlike "*$ExeDir*") {
    [Environment]::SetEnvironmentVariable("PATH", "$UserPath;$ExeDir", "User")
    Write-Host "  Added $ExeDir to user PATH"
} else {
    Write-Host "  Already in PATH"
}

Write-Host "[6/7] Notifying shell of changes ..." -ForegroundColor Green
# SHChangeNotify to refresh icons and file associations
Add-Type -TypeDefinition @"
using System;
using System.Runtime.InteropServices;
public class Shell32 {
    [DllImport("shell32.dll")]
    public static extern void SHChangeNotify(int wEventId, int uFlags, IntPtr dwItem1, IntPtr dwItem2);
}
"@
[Shell32]::SHChangeNotify(0x08000000, 0, [IntPtr]::Zero, [IntPtr]::Zero)

Write-Host "[7/7] Done!" -ForegroundColor Green
Write-Host ""
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "  Installation complete!" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "  .egguf files now open with EGGUF" -ForegroundColor White
Write-Host "  .efe files now open with EGGUF" -ForegroundColor White
Write-Host "  .gguf files now open with EGGUF (converts)" -ForegroundColor White
Write-Host ""
Write-Host "  Double-click any .egguf file to start." -ForegroundColor White
Write-Host "  Double-click any .gguf to convert." -ForegroundColor White
Write-Host ""
Write-Host "  CLI: egguf open model.egguf" -ForegroundColor Gray
Write-Host "       egguf convert model.gguf" -ForegroundColor Gray
Write-Host "       egguf scan extension.efe" -ForegroundColor Gray
Write-Host "       egguf apply model.egguf extension.efe" -ForegroundColor Gray
Write-Host ""
Write-Host "  To uninstall: run uninstall_windows.ps1" -ForegroundColor Yellow
Write-Host ""
Read-Host "Press Enter to exit"
