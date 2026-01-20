"""
Optional: More advanced dashboard with WebSocket updates
"""
import asyncio
import json
import logging
from typing import Dict, Any
from fastapi import WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse

logger = logging.getLogger(__name__)

class DashboardManager:
    def __init__(self, mqtt_manager):
        self.mqtt_manager = mqtt_manager
        self.active_connections: Dict[str, WebSocket] = {}
        
    async def websocket_endpoint(self, websocket: WebSocket):
        await websocket.accept()
        connection_id = id(websocket)
        self.active_connections[connection_id] = websocket
        
        try:
            while True:
                # Send updates every second
                await asyncio.sleep(1)
                
                status = self.mqtt_manager.get_status()
                clients = self.mqtt_manager.get_connected_clients()
                topics = self.mqtt_manager.get_topics()
                
                update = {
                    "type": "update",
                    "data": {
                        "status": status,
                        "clients": clients,
                        "topics": topics
                    }
                }
                
                await websocket.send_json(update)
                
        except WebSocketDisconnect:
            del self.active_connections[connection_id]
        except Exception as e:
            logger.error(f"WebSocket error: {e}")
            del self.active_connections[connection_id]
    
    def get_dashboard_html(self) -> HTMLResponse:
        """Return enhanced dashboard with WebSocket"""
        html = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>MQTT Broker - Live Dashboard</title>
            <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
            <style>
                /* ... enhanced styles ... */
            </style>
        </head>
        <body>
            <div class="container">
                <h1>Live MQTT Broker Dashboard</h1>
                <div id="connection-status">Connecting...</div>
                <!-- Dashboard content -->
            </div>
            <script>
                const ws = new WebSocket(`ws://${window.location.host}/ws/dashboard`);
                
                ws.onmessage = function(event) {
                    const data = JSON.parse(event.data);
                    updateDashboard(data.data);
                };
                
                ws.onopen = function() {
                    document.getElementById('connection-status').innerHTML = 
                        '<span class="status-online"></span> Connected';
                };
                
                ws.onclose = function() {
                    document.getElementById('connection-status').innerHTML = 
                        '<span class="status-offline"></span> Disconnected';
                };
            </script>
        </body>
        </html>
        """
        return HTMLResponse(html)