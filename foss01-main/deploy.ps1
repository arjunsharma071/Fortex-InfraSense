# deploy.ps1 - PowerShell deployment script for InfraSense AI
Write-Host "🚀 Deploying InfraSense AI..." -ForegroundColor Cyan

# 1. Setup virtual environment
Write-Host "📦 Setting up virtual environment..." -ForegroundColor Yellow
python -m venv venv
.\venv\Scripts\Activate.ps1

# 2. Install dependencies
Write-Host "📥 Installing dependencies..." -ForegroundColor Yellow
pip install -r requirements.txt

# 3. Create necessary directories
Write-Host "📁 Creating directories..." -ForegroundColor Yellow
New-Item -ItemType Directory -Force -Path "data\sample_data" | Out-Null
New-Item -ItemType Directory -Force -Path "reports" | Out-Null

# 4. Start backend
Write-Host "🔧 Starting backend server..." -ForegroundColor Yellow
Set-Location backend
Start-Process -NoNewWindow -FilePath "python" -ArgumentList "-m", "uvicorn", "server:app", "--host", "0.0.0.0", "--port", "8000"
Set-Location ..

# 5. Wait for backend to start
Start-Sleep -Seconds 3

Write-Host ""
Write-Host "✅ Deployment complete!" -ForegroundColor Green
Write-Host "🌐 Application: http://localhost:8000" -ForegroundColor Cyan
Write-Host "📚 API Docs: http://localhost:8000/docs" -ForegroundColor Cyan
