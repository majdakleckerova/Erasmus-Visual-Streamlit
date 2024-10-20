docker-compose up --build -d
timeout /t 3 >nul
start http://localhost:8501