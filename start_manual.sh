#!/bin/bash

# Script to start the application manually (without Docker)

echo "Starting CT Scan Centers Dashboard..."

# Start backend in background
echo "Starting backend server..."
cd backend
source venv/bin/activate
uvicorn main:app --host 0.0.0.0 --port 5050 &
BACKEND_PID=$!
cd ..

# Wait a moment for backend to start
sleep 3

# Check if backend started successfully
if ps -p $BACKEND_PID > /dev/null; then
    echo "Backend server started successfully (PID: $BACKEND_PID)"
else
    echo "Failed to start backend server"
    exit 1
fi

# Start frontend in background
echo "Starting frontend server..."
cd frontend
npm start &
FRONTEND_PID=$!
cd ..

# Wait a moment for frontend to start
sleep 5

# Check if frontend started successfully
if ps -p $FRONTEND_PID > /dev/null; then
    echo "Frontend server started successfully (PID: $FRONTEND_PID)"
else
    echo "Failed to start frontend server"
    # Kill backend if frontend failed to start
    kill $BACKEND_PID 2>/dev/null
    exit 1
fi

echo ""
echo "Application is now running!"
echo "Frontend: http://localhost:3030"
echo "Backend API: http://localhost:5050"
echo ""
echo "Press Ctrl+C to stop both servers"

# Wait for user to press Ctrl+C
trap "echo 'Stopping servers...'; kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; exit 0" INT TERM

# Keep script running until interrupted
while true; do
    sleep 1
done