#!/bin/bash
# deploy.sh - Complete deployment script for InfraSense AI
echo "🚀 Deploying InfraSense AI..."

# 1. Setup virtual environment
echo "📦 Setting up virtual environment..."
python3 -m venv venv
source venv/bin/activate

# 2. Install dependencies
echo "📥 Installing dependencies..."
pip install -r requirements.txt

# 3. Create necessary directories
echo "📁 Creating directories..."
mkdir -p data/sample_data
mkdir -p reports

# 4. Start backend
echo "🔧 Starting backend server..."
cd backend
uvicorn server:app --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!
cd ..

# 5. Wait for backend to start
sleep 3

echo ""
echo "✅ Deployment complete!"
echo "🌐 Application: http://localhost:8000"
echo "📚 API Docs: http://localhost:8000/docs"
echo ""
echo "To stop the server, run: kill $BACKEND_PID"
