# Script PowerShell para preparar las funciones Lambda y el layer de MySQL

Write-Host "Preparando funciones Lambda y layer de MySQL..." -ForegroundColor Green

# Directorio base
$SCRIPT_DIR = Split-Path -Parent $MyInvocation.MyCommand.Path
$PROJECT_ROOT = Split-Path -Parent $SCRIPT_DIR
$LAMBDA_DIR = Join-Path $PROJECT_ROOT "modules\lambda"

# Crear directorio para layer
Write-Host "1. Creando layer de MySQL..." -ForegroundColor Yellow
$LAYER_DIR = Join-Path $LAMBDA_DIR "layers\python"
New-Item -ItemType Directory -Force -Path $LAYER_DIR | Out-Null

# Instalar pymysql en el layer
Write-Host "   Instalando pymysql..." -ForegroundColor Yellow
pip install pymysql -t $LAYER_DIR
if ($LASTEXITCODE -ne 0) {
    python -m pip install pymysql -t $LAYER_DIR
}

# Crear ZIP del layer
Write-Host "   Creando ZIP del layer..." -ForegroundColor Yellow
$LAYER_PARENT = Split-Path -Parent $LAYER_DIR
Set-Location $LAYER_DIR
Compress-Archive -Path * -DestinationPath "..\mysql-layer.zip" -Force
Set-Location $PROJECT_ROOT
Write-Host "   ✅ Layer creado: layers/mysql-layer.zip" -ForegroundColor Green

# Crear ZIPs de las funciones Lambda
Write-Host "2. Creando ZIPs de funciones Lambda..." -ForegroundColor Yellow
$FUNCTIONS_DIR = Join-Path $LAMBDA_DIR "functions"
Set-Location $FUNCTIONS_DIR

$functions = @("create_order", "validator", "anomaly", "sync", "audit", "check_consistency")

foreach ($func in $functions) {
    $pyFile = "$func.py"
    if (Test-Path $pyFile) {
        Write-Host "   Creando ${func}.zip..." -ForegroundColor Yellow
        Compress-Archive -Path $pyFile -DestinationPath "${func}.zip" -Force
        Write-Host "   ✅ ${func}.zip creado" -ForegroundColor Green
    } else {
        Write-Host "   ⚠️  ${pyFile} no encontrado, saltando..." -ForegroundColor Yellow
    }
}

Set-Location $PROJECT_ROOT

Write-Host ""
Write-Host "✅ Preparación completada!" -ForegroundColor Green
Write-Host ""
Write-Host "Archivos creados:"
Write-Host "  - modules/lambda/layers/mysql-layer.zip"
Write-Host "  - modules/lambda/functions/*.zip"
Write-Host ""
Write-Host "Ahora puedes ejecutar 'terraform init' y 'terraform apply'" -ForegroundColor Cyan

