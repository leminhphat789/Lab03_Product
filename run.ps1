$ErrorActionPreference = 'Stop'
Set-Location -LiteralPath $PSScriptRoot
if (-not (Test-Path '.venv/Scripts/python.exe')) {
    python -m venv .venv
    if ($LASTEXITCODE -ne 0) { throw 'Cannot create Python virtual environment' }
}
& '.\.venv\Scripts\python.exe' -m pip install -r requirements.txt
if ($LASTEXITCODE -ne 0) { throw 'Cannot install dependencies' }
& '.\.venv\Scripts\python.exe' setup_db.py
if ($LASTEXITCODE -ne 0) { throw 'Start MySQL in XAMPP and check .env' }
Write-Host 'Start BTH2 at localhost:5001 before using product APIs.'
Write-Host 'Product service: http://localhost:5002/products'
& '.\.venv\Scripts\python.exe' app.py
