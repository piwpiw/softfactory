#!/usr/bin/env python3
"""
⚡ WebSocket Server — 실시간 업데이트
"""

import asyncio
import json
import os
from flask import Flask, render_template_string
from flask_socketio import SocketIO, emit, join_room
from datetime import datetime, timezone

app = Flask(__name__)
app.config['SECRET_KEY'] = 'jarvis-secret'
socketio = SocketIO(app, cors_allowed_origins="*")

class LiveMonitor:
    def __init__(self):
        self.metrics = {
            "requests_per_sec": 1245,
            "error_rate": 0.02,
            "latency_ms": 145,
            "memory_mb": 256,
            "uptime_percent": 99.98,
        }
        self.tasks = []
        self.deployments = []

    async def broadcast_metrics(self):
        """실시간 메트릭 브로드캐스트"""
        while True:
            await asyncio.sleep(5)

            # 메트릭 업데이트 (시뮬레이션)
            self.metrics["requests_per_sec"] += asyncio.get_event_loop().time() % 100
            self.metrics["error_rate"] = max(0.01, self.metrics["error_rate"] - 0.001)
            self.metrics["latency_ms"] += asyncio.get_event_loop().time() % 20 - 10

            socketio.emit("metrics_update", {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "metrics": self.metrics
            }, broadcast=True)

    async def broadcast_task_update(self, task_id, progress, status):
        """Task 진행률 업데이트"""
        socketio.emit("task_update", {
            "task_id": task_id,
            "progress": progress,
            "status": status,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }, broadcast=True)

monitor = LiveMonitor()

@app.route("/")
def index():
    """실시간 대시보드"""
    return render_template_string("""
    <!DOCTYPE html>
    <html>
    <head>
        <title>🤖 JARVIS Live Monitor</title>
        <script src="https://cdn.socket.io/4.5.4/socket.io.min.js"></script>
        <style>
            body { font-family: monospace; background: #1a1a1a; color: #00ff00; padding: 20px; }
            .metric { margin: 10px 0; padding: 10px; background: #2a2a2a; border-left: 3px solid #00ff00; }
            .value { float: right; font-weight: bold; }
            h1 { color: #00ff00; }
        </style>
    </head>
    <body>
        <h1>🤖 JARVIS Live Monitor</h1>
        <div id="metrics"></div>

        <script>
            const socket = io();

            socket.on('connect', () => {
                console.log('✅ Connected to WebSocket');
            });

            socket.on('metrics_update', (data) => {
                const metrics = data.metrics;
                document.getElementById('metrics').innerHTML = `
                    <div class="metric">
                        📊 Requests/sec
                        <span class="value">${Math.round(metrics.requests_per_sec)}</span>
                    </div>
                    <div class="metric">
                        ⚠️ Error Rate
                        <span class="value">${metrics.error_rate.toFixed(4)}%</span>
                    </div>
                    <div class="metric">
                        ⏱️ Latency
                        <span class="value">${Math.round(metrics.latency_ms)}ms</span>
                    </div>
                    <div class="metric">
                        💾 Memory
                        <span class="value">${metrics.memory_mb}MB / 512MB</span>
                    </div>
                    <div class="metric">
                        🟢 Uptime
                        <span class="value">${metrics.uptime_percent}%</span>
                    </div>
                    <div class="metric">
                        ⏰ Updated
                        <span class="value">${new Date(data.timestamp).toLocaleTimeString()}</span>
                    </div>
                `;
            });

            socket.on('task_update', (data) => {
                console.log('📌 Task update:', data);
            });
        </script>
    </body>
    </html>
    """)

@socketio.on('connect')
def handle_connect():
    """클라이언트 연결"""
    emit('response', {'message': '✅ Connected to JARVIS WebSocket'})
    print("✅ Client connected")

@socketio.on('disconnect')
def handle_disconnect():
    """클라이언트 연결 해제"""
    print("❌ Client disconnected")

@socketio.on('request_metrics')
def handle_request_metrics():
    """메트릭 요청"""
    emit('metrics_update', {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "metrics": monitor.metrics
    })

@socketio.on('task_progress')
def handle_task_progress(data):
    """Task 진행률"""
    socketio.emit('task_update', data, broadcast=True)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5001))
    print(f"""
    ⚡ WebSocket Server
    🚀 Running on http://0.0.0.0:{port}/
    🔗 Real-time monitoring enabled
    """)
    socketio.run(app, host="0.0.0.0", port=port, debug=False)
