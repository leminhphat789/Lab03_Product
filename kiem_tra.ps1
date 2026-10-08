$ErrorActionPreference = 'Stop'
Set-Location -LiteralPath $PSScriptRoot
& '.\.venv\Scripts\python.exe' -m unittest -v
if ($LASTEXITCODE -ne 0) { throw 'Python tests failed' }
Write-Host 'For the Postman collection, start BTH2 :5001 and BTH3 :5002, then import Lab03_Product.postman_collection.json.'
