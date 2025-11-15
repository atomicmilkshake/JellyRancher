# PowerShell dev setup script for RavenMaven
# Creates a venv in .venv and installs requirements.txt
param(
    [string]$PythonExe = 'python',
    [string]$VenvDir = '.venv'
)

Write-Host "Creating virtual environment in $VenvDir using $PythonExe..."
try {
    & $PythonExe -m venv $VenvDir
} catch {
    Write-Error "Failed to create virtualenv. Ensure Python is installed and on PATH. Error: $_"
    exit 1
}

$py = Join-Path $VenvDir 'Scripts\python.exe'
if (-Not (Test-Path $py)) {
    Write-Error "Virtualenv python not found at $py"
    exit 1
}

Write-Host "Upgrading pip..."
& $py -m pip install --upgrade pip

if (Test-Path 'requirements.txt') {
    Write-Host "Installing requirements from requirements.txt..."
    & $py -m pip install -r requirements.txt
} else {
    Write-Warning "requirements.txt not found in repository root. Skipping pip install."
}

Write-Host "Dev setup complete. Activate the virtualenv with:"
    # Correct PowerShell dot-sourcing requires a space after the dot
    Write-Host "  . .\$VenvDir\Scripts\Activate.ps1"
    Write-Host "Or (cmd):  $VenvDir\Scripts\activate.bat"
