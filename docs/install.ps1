Write-Host "🦆 Installing Astral uv..."
Invoke-WebRequest -Uri "https://astral.sh/uv/install.ps1" -UseBasicParsing | Invoke-Expression

# CRITICAL WINDOWS FIX: Force PowerShell to refresh environment variables in the current session
$env:Path = [System.Environment]::GetEnvironmentVariable("Path","User") + ";" + [System.Environment]::GetEnvironmentVariable("Path","Machine")

Write-Host "🦆 Installing Posthorn..."
uv tool install --force posthorn

# Refresh PATH one more time to capture the new Posthorn executable
$env:Path = [System.Environment]::GetEnvironmentVariable("Path","User") + ";" + [System.Environment]::GetEnvironmentVariable("Path","Machine")

Write-Host "🦆 Validating installation..."
if (Get-Command "posthorn" -ErrorAction SilentlyContinue) {
    Write-Host "✨ All done! Run 'posthorn' to launch the daemon." -ForegroundColor Green
} else {
    Write-Host "⚠️ Installation finished, but you may need to restart PowerShell before running 'posthorn'." -ForegroundColor Yellow
}
