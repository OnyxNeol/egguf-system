# EGGUF Windows Uninstaller — Removes file type associations
# Run: powershell -ExecutionPolicy Bypass -File uninstall_windows.ps1

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "  EGGUF Windows Uninstaller" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""

Write-Host "[1/4] Removing .egguf associations ..." -ForegroundColor Yellow
Remove-Item "HKCR:\.egguf" -Recurse -Force -ErrorAction SilentlyContinue
Remove-Item "HKCR:\EGGUF.File" -Recurse -Force -ErrorAction SilentlyContinue
Remove-Item "HKCU:\Software\Classes\.egguf" -Recurse -Force -ErrorAction SilentlyContinue

Write-Host "[2/4] Removing .efe associations ..." -ForegroundColor Yellow
Remove-Item "HKCR:\.efe" -Recurse -Force -ErrorAction SilentlyContinue
Remove-Item "HKCR:\EFE.File" -Recurse -Force -ErrorAction SilentlyContinue
Remove-Item "HKCU:\Software\Classes\.efe" -Recurse -Force -ErrorAction SilentlyContinue

Write-Host "[3/4] Removing .gguf associations ..." -ForegroundColor Yellow
Remove-Item "HKCR:\.gguf" -Recurse -Force -ErrorAction SilentlyContinue
Remove-Item "HKCR:\GGUF.File" -Recurse -Force -ErrorAction SilentlyContinue
Remove-Item "HKCU:\Software\Classes\.gguf" -Recurse -Force -ErrorAction SilentlyContinue

Write-Host "[4/4] Notifying shell ..." -ForegroundColor Yellow
Add-Type -TypeDefinition @"
using System;
using System.Runtime.InteropServices;
public class Shell32U {
    [DllImport("shell32.dll")]
    public static extern void SHChangeNotify(int wEventId, int uFlags, IntPtr dwItem1, IntPtr dwItem2);
}
"@
[Shell32U]::SHChangeNotify(0x08000000, 0, [IntPtr]::Zero, [IntPtr]::Zero)

Write-Host ""
Write-Host "  Uninstall complete." -ForegroundColor Green
Write-Host "  The egguf.exe file is NOT removed — delete it manually if needed." -ForegroundColor Gray
Write-Host ""
Read-Host "Press Enter to exit"
