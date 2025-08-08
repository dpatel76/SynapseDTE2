"""
Real-time test progress tracking server
Provides a web interface to monitor test execution progress
"""

import asyncio
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
import aiofiles
from aiohttp import web
import aiohttp_cors

logger = logging.getLogger(__name__)

class TestProgressServer:
    def __init__(self, results_dir: str = "test_results", port: int = 8888):
        self.results_dir = Path(results_dir)
        self.port = port
        self.app = web.Application()
        self.setup_routes()
        self.setup_cors()
        
    def setup_routes(self):
        """Setup API routes"""
        self.app.router.add_get('/', self.serve_dashboard)
        self.app.router.add_get('/api/progress', self.get_progress)
        self.app.router.add_get('/api/results', self.get_results)
        self.app.router.add_get('/api/failed-tests', self.get_failed_tests)
        self.app.router.add_get('/api/logs', self.get_logs)
        self.app.router.add_static('/screenshots', self.results_dir / 'screenshots')
        
    def setup_cors(self):
        """Setup CORS for API access"""
        cors = aiohttp_cors.setup(self.app, defaults={
            "*": aiohttp_cors.ResourceOptions(
                allow_credentials=True,
                expose_headers="*",
                allow_headers="*",
                allow_methods="*"
            )
        })
        
        for route in list(self.app.router.routes()):
            if not route.resource.canonical.startswith('/screenshots'):
                cors.add(route)
    
    async def serve_dashboard(self, request):
        """Serve the HTML dashboard"""
        html_content = '''
<!DOCTYPE html>
<html>
<head>
    <title>SynapseDTE Test Progress Monitor</title>
    <style>
        * { box-sizing: border-box; }
        body { 
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            margin: 0;
            padding: 0;
            background: #f5f7fa;
            color: #333;
        }
        .header {
            background: #2c3e50;
            color: white;
            padding: 20px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        .container {
            max-width: 1400px;
            margin: 0 auto;
            padding: 20px;
        }
        .metrics-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        .metric-card {
            background: white;
            border-radius: 10px;
            padding: 20px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.05);
            text-align: center;
            transition: transform 0.2s;
        }
        .metric-card:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 20px rgba(0,0,0,0.1);
        }
        .metric-value {
            font-size: 36px;
            font-weight: bold;
            margin: 10px 0;
        }
        .metric-label {
            color: #7f8c8d;
            font-size: 14px;
            text-transform: uppercase;
            letter-spacing: 1px;
        }
        .passed { color: #27ae60; }
        .failed { color: #e74c3c; }
        .skipped { color: #95a5a6; }
        .running { color: #3498db; }
        
        .progress-container {
            background: white;
            border-radius: 10px;
            padding: 20px;
            margin-bottom: 30px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.05);
        }
        .progress-bar {
            height: 30px;
            background: #ecf0f1;
            border-radius: 15px;
            overflow: hidden;
            position: relative;
        }
        .progress-fill {
            height: 100%;
            background: linear-gradient(90deg, #3498db, #2ecc71);
            transition: width 0.5s ease;
            display: flex;
            align-items: center;
            justify-content: center;
            color: white;
            font-weight: bold;
        }
        
        .test-grid {
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 20px;
        }
        .test-section {
            background: white;
            border-radius: 10px;
            padding: 20px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.05);
        }
        .test-section h3 {
            margin-top: 0;
            color: #2c3e50;
            border-bottom: 2px solid #ecf0f1;
            padding-bottom: 10px;
        }
        
        .test-list {
            max-height: 400px;
            overflow-y: auto;
        }
        .test-item {
            padding: 10px;
            margin: 5px 0;
            border-radius: 5px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            background: #f8f9fa;
            transition: all 0.2s;
        }
        .test-item:hover {
            background: #e9ecef;
        }
        .test-item.failed {
            background: #ffebee;
            border-left: 4px solid #e74c3c;
        }
        .test-item.passed {
            background: #e8f5e9;
            border-left: 4px solid #27ae60;
        }
        .test-item.running {
            background: #e3f2fd;
            border-left: 4px solid #3498db;
            animation: pulse 2s infinite;
        }
        
        @keyframes pulse {
            0% { opacity: 1; }
            50% { opacity: 0.7; }
            100% { opacity: 1; }
        }
        
        .test-name {
            font-size: 14px;
            flex-grow: 1;
            margin-right: 10px;
            word-break: break-word;
        }
        .test-status {
            font-size: 12px;
            padding: 4px 8px;
            border-radius: 4px;
            text-transform: uppercase;
            font-weight: bold;
            white-space: nowrap;
        }
        .status-passed { background: #27ae60; color: white; }
        .status-failed { background: #e74c3c; color: white; }
        .status-running { background: #3498db; color: white; }
        .status-skipped { background: #95a5a6; color: white; }
        
        .logs-section {
            background: #2c3e50;
            color: #ecf0f1;
            border-radius: 10px;
            padding: 20px;
            margin-top: 20px;
            font-family: 'Courier New', monospace;
            font-size: 12px;
            max-height: 300px;
            overflow-y: auto;
        }
        
        .refresh-info {
            text-align: center;
            color: #7f8c8d;
            margin-top: 20px;
            font-size: 14px;
        }
        
        .error-details {
            font-size: 12px;
            color: #e74c3c;
            margin-top: 5px;
            font-style: italic;
        }
        
        @media (max-width: 768px) {
            .test-grid {
                grid-template-columns: 1fr;
            }
            .metrics-grid {
                grid-template-columns: repeat(2, 1fr);
            }
        }
    </style>
</head>
<body>
    <div class="header">
        <div class="container">
            <h1 style="margin: 0;">🧪 SynapseDTE Test Progress Monitor</h1>
            <p style="margin: 5px 0 0 0; opacity: 0.8;">Real-time test execution tracking</p>
        </div>
    </div>
    
    <div class="container">
        <div class="metrics-grid">
            <div class="metric-card">
                <div class="metric-label">Total Tests</div>
                <div class="metric-value" id="total-tests">0</div>
            </div>
            <div class="metric-card">
                <div class="metric-label">Completed</div>
                <div class="metric-value" id="completed-tests">0</div>
            </div>
            <div class="metric-card">
                <div class="metric-label">Passed</div>
                <div class="metric-value passed" id="passed-tests">0</div>
            </div>
            <div class="metric-card">
                <div class="metric-label">Failed</div>
                <div class="metric-value failed" id="failed-tests">0</div>
            </div>
            <div class="metric-card">
                <div class="metric-label">Success Rate</div>
                <div class="metric-value" id="success-rate">0%</div>
            </div>
            <div class="metric-card">
                <div class="metric-label">Duration</div>
                <div class="metric-value" id="duration">0s</div>
            </div>
        </div>
        
        <div class="progress-container">
            <h3>Overall Progress</h3>
            <div class="progress-bar">
                <div class="progress-fill" id="progress-bar" style="width: 0%">
                    <span id="progress-text">0%</span>
                </div>
            </div>
        </div>
        
        <div class="test-grid">
            <div class="test-section">
                <h3>🔴 Failed Tests</h3>
                <div class="test-list" id="failed-tests-list">
                    <p style="text-align: center; color: #7f8c8d;">No failed tests yet</p>
                </div>
            </div>
            
            <div class="test-section">
                <h3>🏃 Currently Running</h3>
                <div class="test-list" id="running-tests-list">
                    <p style="text-align: center; color: #7f8c8d;">No tests running</p>
                </div>
            </div>
        </div>
        
        <div class="logs-section">
            <h3 style="margin-top: 0;">📋 Recent Logs</h3>
            <div id="logs-content">Waiting for test execution to start...</div>
        </div>
        
        <div class="refresh-info">
            Auto-refreshing every 2 seconds | Last update: <span id="last-update">Never</span>
        </div>
    </div>
    
    <script>
        let startTime = null;
        
        async function updateProgress() {
            try {
                // Fetch progress data
                const progressResponse = await fetch('/api/progress');
                const progress = await progressResponse.json();
                
                // Update metrics
                document.getElementById('total-tests').textContent = progress.total_tests;
                document.getElementById('completed-tests').textContent = progress.completed_tests;
                document.getElementById('passed-tests').textContent = progress.passed_tests;
                document.getElementById('failed-tests').textContent = progress.failed_tests;
                document.getElementById('success-rate').textContent = progress.success_rate.toFixed(1) + '%';
                
                // Update duration
                if (progress.start_time && !startTime) {
                    startTime = new Date(progress.start_time);
                }
                if (startTime) {
                    const duration = Math.floor((new Date() - startTime) / 1000);
                    const minutes = Math.floor(duration / 60);
                    const seconds = duration % 60;
                    document.getElementById('duration').textContent = 
                        minutes > 0 ? `${minutes}m ${seconds}s` : `${seconds}s`;
                }
                
                // Update progress bar
                const progressBar = document.getElementById('progress-bar');
                const progressText = document.getElementById('progress-text');
                progressBar.style.width = progress.progress_percentage.toFixed(1) + '%';
                progressText.textContent = progress.progress_percentage.toFixed(1) + '%';
                
                // Fetch failed tests
                const failedResponse = await fetch('/api/failed-tests');
                const failedTests = await failedResponse.json();
                updateFailedTests(failedTests);
                
                // Fetch recent results for running tests
                const resultsResponse = await fetch('/api/results?limit=10&status=running');
                const runningTests = await resultsResponse.json();
                updateRunningTests(runningTests);
                
                // Fetch logs
                const logsResponse = await fetch('/api/logs?lines=20');
                const logs = await logsResponse.text();
                document.getElementById('logs-content').textContent = logs || 'No logs available';
                
                // Update last refresh time
                document.getElementById('last-update').textContent = new Date().toLocaleTimeString();
                
            } catch (error) {
                console.error('Error updating progress:', error);
            }
        }
        
        function updateFailedTests(tests) {
            const container = document.getElementById('failed-tests-list');
            if (tests.length === 0) {
                container.innerHTML = '<p style="text-align: center; color: #7f8c8d;">No failed tests yet</p>';
                return;
            }
            
            container.innerHTML = tests.map(test => `
                <div class="test-item failed">
                    <div>
                        <div class="test-name">${test.test_name}</div>
                        <div class="error-details">${test.error}</div>
                    </div>
                    <span class="test-status status-failed">FAILED</span>
                </div>
            `).join('');
        }
        
        function updateRunningTests(tests) {
            const container = document.getElementById('running-tests-list');
            if (tests.length === 0) {
                container.innerHTML = '<p style="text-align: center; color: #7f8c8d;">No tests running</p>';
                return;
            }
            
            container.innerHTML = tests.map(test => `
                <div class="test-item running">
                    <div class="test-name">${test.test_name}</div>
                    <span class="test-status status-running">RUNNING</span>
                </div>
            `).join('');
        }
        
        // Initial update
        updateProgress();
        
        // Auto-refresh every 2 seconds
        setInterval(updateProgress, 2000);
    </script>
</body>
</html>
        '''
        return web.Response(text=html_content, content_type='text/html')
    
    async def get_progress(self, request):
        """Get current test progress"""
        summary_file = self.results_dir / 'test_summary.json'
        if summary_file.exists():
            async with aiofiles.open(summary_file, 'r') as f:
                data = json.loads(await f.read())
                return web.json_response(data.get('test_run', {}))
        
        # Return empty progress if no data yet
        return web.json_response({
            'total_tests': 0,
            'completed_tests': 0,
            'passed_tests': 0,
            'failed_tests': 0,
            'skipped_tests': 0,
            'success_rate': 0,
            'progress_percentage': 0,
            'start_time': None
        })
    
    async def get_results(self, request):
        """Get test results with optional filtering"""
        results_file = self.results_dir / 'test_results.json'
        if not results_file.exists():
            return web.json_response([])
        
        async with aiofiles.open(results_file, 'r') as f:
            results = json.loads(await f.read())
        
        # Apply filters
        status = request.query.get('status')
        if status:
            results = [r for r in results if r.get('status') == status]
        
        limit = int(request.query.get('limit', 100))
        results = results[:limit]
        
        return web.json_response(results)
    
    async def get_failed_tests(self, request):
        """Get all failed tests"""
        results_file = self.results_dir / 'test_results.json'
        if not results_file.exists():
            return web.json_response([])
        
        async with aiofiles.open(results_file, 'r') as f:
            results = json.loads(await f.read())
        
        failed_tests = [r for r in results if r.get('status') == 'failed']
        return web.json_response(failed_tests)
    
    async def get_logs(self, request):
        """Get recent log lines"""
        log_file = self.results_dir / 'comprehensive_test.log'
        if not log_file.exists():
            return web.Response(text='No logs available')
        
        lines = int(request.query.get('lines', 50))
        
        async with aiofiles.open(log_file, 'r') as f:
            content = await f.read()
            log_lines = content.split('\n')
            recent_lines = log_lines[-lines:] if len(log_lines) > lines else log_lines
            return web.Response(text='\n'.join(recent_lines))
    
    def run(self):
        """Start the progress server"""
        web.run_app(self.app, host='0.0.0.0', port=self.port)

if __name__ == '__main__':
    server = TestProgressServer()
    print(f"Starting test progress server on http://localhost:{server.port}")
    server.run()