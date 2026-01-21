Param(
    [string]$PythonExe = "C:/Users/Sarah/AppData/Local/Programs/Python/Python312/python.exe",
    [string]$Name = "ProjektAstras"
)

# Resolve project root (tools/..)
$ProjectRoot = Resolve-Path "$PSScriptRoot\.."
Set-Location $ProjectRoot

Write-Host "Using Python executable: $PythonExe"

# Ensure PyInstaller is available
& $PythonExe -m PyInstaller --version > $null 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "PyInstaller not available for this Python. Install with: & $PythonExe -m pip install pyinstaller" -ForegroundColor Yellow
    exit 1
}

$dist = Join-Path $ProjectRoot "main.onefile-build\dist"
$work = Join-Path $ProjectRoot "main.onefile-build\build"
$spec = Join-Path $ProjectRoot "main.onefile-build\spec"

# Create output directories
New-Item -ItemType Directory -Force -Path $dist | Out-Null
New-Item -ItemType Directory -Force -Path $work | Out-Null
New-Item -ItemType Directory -Force -Path $spec | Out-Null

$entry = Join-Path $ProjectRoot "frontend\main.py"

# Data folders to include so get_static_path(...) works inside the onefile bundle
$add = @(
    "$(Join-Path $ProjectRoot 'static');static",
    "$(Join-Path $ProjectRoot 'i18n');i18n"
)

$cmd = @(
    "--noconfirm",
    "--clean",
    "--onefile",
    "--name", $Name,
    "--distpath", $dist,
    "--workpath", $work,
    "--specpath", $spec
)

foreach ($a in $add) { $cmd += "--add-data"; $cmd += $a }

Write-Host "Running PyInstaller..."
& $PythonExe -m PyInstaller @cmd $entry
if ($LASTEXITCODE -ne 0) {
    Write-Host "PyInstaller failed with exit code $LASTEXITCODE" -ForegroundColor Red
    exit $LASTEXITCODE
}

Write-Host "Built executable at: $(Join-Path $dist ($Name + '.exe'))"

# Optional: cleanup intermediate PyInstaller files so only the final exe remains in main.onefile-build\dist
try {
    Remove-Item -Recurse -Force -ErrorAction SilentlyContinue $work
    Remove-Item -Recurse -Force -ErrorAction SilentlyContinue $spec
    Get-ChildItem -Path $ProjectRoot -Filter "*.spec" -Recurse | Remove-Item -Force -ErrorAction SilentlyContinue
    Write-Host "Cleaned up temporary PyInstaller files."
} catch {
    Write-Host "Warning: cleanup failed: $_" -ForegroundColor Yellow
}
