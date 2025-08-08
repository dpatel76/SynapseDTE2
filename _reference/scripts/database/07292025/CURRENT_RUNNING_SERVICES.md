# Currently Running Services for SynapseDTE

Generated: 2025-07-29 22:40 PST

## Active Processes

### 1. React Frontend
```bash
# Process ID: 74755
# Started: Saturday 7:00 PM (2 days ago)
# Parent Process: npm start (PID: 74735)
node /Users/dineshpatel/code/projects/SynapseDTE/frontend/node_modules/react-scripts/scripts/start.js
```
- Running on port 3000 (http://localhost:3000)
- Using react-scripts (Create React App)
- TypeScript checking processes also running (PIDs: 74759, 74760)
- Has been running stable for 2 days

### 2. FastAPI Application (Backend)
```bash
# Process ID: 54794
# Started: 10:40 PM
python /Users/dineshpatel/code/projects/SynapseDTE/venv/bin/uvicorn app.main:app --reload --port 8000
```
- Running on port 8000
- Auto-reload enabled (development mode)
- Using virtual environment

### 3. Temporal Workers (2 instances)
```bash
# Process ID: 86467 (Started: 12:29 PM)
python -m app.temporal.worker

# Process ID: 87119 (Started: 12:32 PM)
python -m app.temporal.worker
```
- Two worker processes running
- Processing Temporal workflow activities
- Connected to Temporal server on localhost:7233

### 4. Temporal Server (Docker)
```bash
# Container: temporal-server
# Image: temporalio/auto-setup:latest
# Port: 7233
# Uptime: 2 weeks
```

### 5. Temporal UI (Docker)
```bash
# Container: temporal-ui
# Image: temporalio/ui:latest
# Port: 8088 (mapped from 8080)
# URL: http://localhost:8088
# Uptime: 2 weeks
```

### 6. Temporal PostgreSQL (Docker)
```bash
# Container: temporal-postgresql
# Image: postgres:14
# Port: 5434 (mapped from 5432)
# Database: temporal
# Uptime: 2 weeks
```

### 7. Temporal Admin Tools (Docker)
```bash
# Container: temporal-admin-tools
# Image: temporalio/admin-tools:latest
# Status: Running (sleep mode)
# Uptime: 2 weeks
```

## How These Were Started

### Application Services

1. **React Frontend**:
   ```bash
   # Start command:
   cd /Users/dineshpatel/code/projects/SynapseDTE/frontend
   npm install  # First time only
   npm start
   ```
   - Runs on http://localhost:3000
   - Auto-opens browser
   - Hot reload enabled

### Backend Services (Python)

2. **FastAPI Application**:
   ```bash
   # Manual start command:
   cd /Users/dineshpatel/code/projects/SynapseDTE
   source venv/bin/activate
   uvicorn app.main:app --reload --port 8000
   ```

3. **Temporal Workers**:
   ```bash
   # Manual start command (run twice for 2 workers):
   cd /Users/dineshpatel/code/projects/SynapseDTE
   source venv/bin/activate
   python -m app.temporal.worker
   ```

### Docker Services (Temporal Infrastructure)

All Temporal services were started using Docker Compose:
```bash
# Start command:
docker-compose -f docker-compose.temporal.yml up -d

# Check status:
docker-compose -f docker-compose.temporal.yml ps
```

## Service Dependencies

```
Main Application DB (PostgreSQL)
└── Port: 5432 (not shown in processes - likely system service)

Temporal Infrastructure
├── Temporal PostgreSQL (Docker)
│   └── Port: 5434
├── Temporal Server (Docker)
│   └── Port: 7233
├── Temporal UI (Docker)
│   └── Port: 8088
└── Temporal Admin Tools (Docker)

Application Stack
├── React Frontend
│   └── Port: 3000
├── FastAPI Backend
│   └── Port: 8000
└── Temporal Workers (2x)
    └── Connect to: localhost:7233
```

## Verification Commands

```bash
# Check Frontend is running
curl http://localhost:3000
# Or open in browser
open http://localhost:3000

# Check FastAPI is running
curl http://localhost:8000/health

# Check Temporal UI
open http://localhost:8088

# Check all Docker containers
docker ps | grep temporal

# Check Python processes
ps aux | grep -E "uvicorn|temporal.worker" | grep -v grep

# Check ports in use
lsof -i :3000  # React Frontend
lsof -i :8000  # FastAPI
lsof -i :7233  # Temporal Server
lsof -i :8088  # Temporal UI
lsof -i :5434  # Temporal PostgreSQL
```

## Startup Script Reference

According to the documentation, there should be a unified startup script:
```bash
# Expected location (from docs):
./start_all_services.sh

# But this script was not found in the current deployment
```

## Manual Service Management

### To Stop Services:
```bash
# Stop Frontend
pkill -f "react-scripts start"

# Stop Python processes
pkill -f "uvicorn app.main:app"
pkill -f "app.temporal.worker"

# Stop Docker services
docker-compose -f docker-compose.temporal.yml down
```

### To Restart Services:
```bash
# Start Docker services first
docker-compose -f docker-compose.temporal.yml up -d

# Wait for Temporal to be ready
sleep 10

# Start Frontend
cd /Users/dineshpatel/code/projects/SynapseDTE/frontend
npm start &

# Start FastAPI
cd /Users/dineshpatel/code/projects/SynapseDTE
source venv/bin/activate
uvicorn app.main:app --reload --port 8000 &

# Start Temporal workers (2 instances)
python -m app.temporal.worker &
python -m app.temporal.worker &
```

## Notes

1. The Temporal Docker containers have been running for 2 weeks (stable)
2. The Python processes were started more recently (today)
3. Frontend has been running for 2 days (very stable)
4. No unified startup script was found, suggesting manual startup
5. The system is using separate databases:
   - Main app DB on port 5432
   - Temporal DB on port 5434