#!/bin/bash
# Start both backend and frontend for local development

echo "🚀 Starting Climate Risk Platform..."
echo ""

# Start backend
echo "[Backend] Starting FastAPI on http://localhost:8000"
cd backend
source venv/bin/activate 2>/dev/null || (python3 -m venv venv && source venv/bin/activate && pip install -r requirements.txt)
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!
cd ..

# Start frontend
echo "[Frontend] Starting Next.js on http://localhost:3000"
cd frontend
npm run dev &
FRONTEND_PID=$!
cd ..

echo ""
echo "✅ Backend:  http://localhost:8000 (Swagger: http://localhost:8000/docs)"
echo "✅ Frontend: http://localhost:3000"
echo ""
echo "Press Ctrl+C to stop both servers"

trap "kill $BACKEND_PID $FRONTEND_PID 2>/dev/null" EXIT
wait
