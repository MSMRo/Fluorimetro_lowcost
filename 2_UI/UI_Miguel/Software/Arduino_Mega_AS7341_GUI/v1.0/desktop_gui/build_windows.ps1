$ErrorActionPreference = 'Stop'

$ProjectDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $ProjectDir

$PythonCandidates = @(
    (Join-Path $ProjectDir '.venv\Scripts\python.exe'),
    (Join-Path $ProjectDir '..\..\..\..\..\.venv\Scripts\python.exe')
)
$Python = $PythonCandidates | Where-Object { Test-Path $_ } | Select-Object -First 1
if (-not $Python) {
    $Python = (Get-Command python -ErrorAction Stop).Source
}

& $Python -m pip install -r requirements.txt
& $Python -m pip install 'pyinstaller>=6.22.3'
& $Python -m PyInstaller --noconfirm --clean --onefile --windowed `
    --name 'Fluorimetro-AS7341' `
    --add-data 'assets;assets' `
    app.py

Write-Host "Executable created at: $ProjectDir\dist\Fluorimetro-AS7341.exe"