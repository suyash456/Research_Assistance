#!/bin/bash

echo "========================================"
echo "Personal AI Research Assistant"
echo "========================================"
echo ""

echo "Activating virtual environment..."
source venv/bin/activate

echo "Starting API Server..."
python main.py &
API_PID=$!

echo "Waiting for API to start..."
sleep 5

echo "Starting Streamlit UI..."
streamlit run app.py &
UI_PID=$!

echo ""
echo "========================================"
echo "Both servers are running!"
echo "API: http://localhost:8000"
echo "UI: http://localhost:8501"
echo "========================================"
echo ""
echo "Press Ctrl+C to stop all servers"

# Wait for both processes
wait $API_PID $UI_PID
