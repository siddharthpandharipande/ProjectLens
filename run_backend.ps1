# Run ProjectLens Backend using the dedicated virtual environment
$backendDir = Join-Path $PSScriptRoot "backend"
Set-Location -Path $backendDir
& ".\.venv\Scripts\python.exe" -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8001

