from fastapi import FastAPI, HTTPException, Depends, status, Security, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import json
import logging

from .config import BrokerConfig
from .mqtt_broker import MQTTBrokerManager
from .database import DatabaseManager
from .models import ClientSession, MessageLog, BrokerStats, TopicInfo

logger = logging.getLogger(__name__)

# Pydantic Models
class ClientInfo(BaseModel):
    client_id: str
    username: Optional[str] = None
    connected_at: str
    last_seen: str
    ip_address: str
    subscriptions: List[str]
    is_connected: bool

class TopicInfoModel(BaseModel):
    topic: str
    subscriber_count: int
    last_message_at: Optional[str] = None
    last_message: Optional[str] = None

class PublishMessage(BaseModel):
    topic: str
    payload: str
    qos: int = Field(0, ge=0, le=2)
    retain: bool = False

class BrokerStatus(BaseModel):
    status: str
    uptime: float
    connected_clients: int
    messages_received: int
    messages_sent: int
    subscriptions: int
    topics_count: int
    memory_usage_mb: Optional[float] = None
    cpu_percent: Optional[float] = None

class HealthCheck(BaseModel):
    status: str
    timestamp: str
    mqtt_broker: bool
    database: bool

# Security
security = HTTPBearer()

class APIServer:
    def __init__(self, config: BrokerConfig, mqtt_manager: MQTTBrokerManager, db_manager: DatabaseManager):
        self.config = config
        self.mqtt_manager = mqtt_manager
        self.db_manager = db_manager
        
        self.app = FastAPI(
            title="MQTT Broker API",
            description="REST API for MQTT Broker Management",
            version="1.0.0",
            docs_url="/api/docs",
            redoc_url="/api/redoc"
        )
        
        self.setup_middleware()
        self.setup_security()
        self.setup_routes()

    
    def setup_middleware(self):
        """Setup API middleware"""
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=self.config.api.cors_origins,
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
    
    def setup_security(self):
        """Setup security dependencies"""
        
        async def verify_api_key(
            credentials: HTTPAuthorizationCredentials = Security(security)
        ) -> bool:
            if self.config.api.api_key:
                if credentials.credentials != self.config.api.api_key:
                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail="Invalid API Key",
                        headers={"WWW-Authenticate": "Bearer"},
                    )
            return True
        
        self.verify_api_key = verify_api_key
    
    def setup_routes(self):
        """Setup API routes"""
        
        # Health check (public)
        @self.app.get("/api/health", response_model=HealthCheck)
        async def health_check():
            """Health check endpoint"""
            # Check MQTT broker status
            mqtt_status = self.mqtt_manager._running if self.mqtt_manager else False
            
            # Check database connectivity
            db_status = False
            try:
                with self.db_manager.get_session() as session:
                    session.execute("SELECT 1")
                    db_status = True
            except:
                db_status = False
            
            return HealthCheck(
                status="healthy" if mqtt_status and db_status else "unhealthy",
                timestamp=datetime.now().isoformat(),
                mqtt_broker=mqtt_status,
                database=db_status
            )
        
        # Status (public)
        @self.app.get("/api/status", response_model=BrokerStatus)
        async def get_status():
            """Get broker status"""
            status_info = self.mqtt_manager.get_status()
            
            # Add system stats
            import psutil
            process = psutil.Process()
            status_info["memory_usage_mb"] = process.memory_info().rss / 1024 / 1024
            status_info["cpu_percent"] = process.cpu_percent()
            
            return BrokerStatus(**status_info)
        
        # Protected routes (require API key)
        @self.app.get("/api/clients", response_model=List[ClientInfo], dependencies=[Depends(self.verify_api_key)])
        async def get_clients(connected_only: bool = True):
            """Get connected clients"""
            if connected_only:
                # Get from broker memory
                return self.mqtt_manager.get_connected_clients()
            else:
                # Get from database
                with self.db_manager.get_session() as session:
                    query = session.query(ClientSession)
                    if connected_only:
                        query = query.filter_by(is_connected=True)
                    
                    clients = query.order_by(ClientSession.connected_at.desc()).limit(100).all()
                    
                    return [
                        ClientInfo(
                            client_id=client.client_id,
                            username=client.username,
                            connected_at=client.connected_at.isoformat(),
                            last_seen=client.last_seen.isoformat(),
                            ip_address=client.ip_address,
                            subscriptions=client.get_subscriptions(),
                            is_connected=client.is_connected
                        )
                        for client in clients
                    ]
        
        @self.app.get("/api/clients/{client_id}", response_model=ClientInfo, dependencies=[Depends(self.verify_api_key)])
        async def get_client(client_id: str):
            """Get specific client details"""
            with self.db_manager.get_session() as session:
                client = session.query(ClientSession).filter_by(
                    client_id=client_id
                ).order_by(ClientSession.connected_at.desc()).first()
                
                if not client:
                    raise HTTPException(status_code=404, detail="Client not found")
                
                return ClientInfo(
                    client_id=client.client_id,
                    username=client.username,
                    connected_at=client.connected_at.isoformat(),
                    last_seen=client.last_seen.isoformat(),
                    ip_address=client.ip_address,
                    subscriptions=client.get_subscriptions(),
                    is_connected=client.is_connected
                )
        
        @self.app.get("/api/topics", response_model=List[TopicInfoModel], dependencies=[Depends(self.verify_api_key)])
        async def get_topics(active_only: bool = True):
            """Get topics"""
            if active_only:
                # Get from broker memory
                topics = self.mqtt_manager.get_topics()
                return [
                    TopicInfoModel(
                        topic=topic["topic"],
                        subscriber_count=topic["subscriber_count"]
                    )
                    for topic in topics
                ]
            else:
                # Get from database
                with self.db_manager.get_session() as session:
                    topics = session.query(TopicInfo).order_by(
                        TopicInfo.subscriber_count.desc()
                    ).limit(100).all()
                    
                    return [
                        TopicInfoModel(
                            topic=topic.topic,
                            subscriber_count=topic.subscriber_count,
                            last_message_at=topic.last_message_at.isoformat() if topic.last_message_at else None,
                            last_message=topic.last_message
                        )
                        for topic in topics
                    ]
        
        @self.app.post("/api/publish", dependencies=[Depends(self.verify_api_key)])
        async def publish_message(message: PublishMessage):
            """Publish a message to a topic"""
            success = await self.mqtt_manager.publish_message(
                message.topic,
                message.payload,
                message.qos,
                message.retain
            )
            
            if success:
                return {"status": "success", "message": "Published successfully"}
            else:
                raise HTTPException(status_code=500, detail="Failed to publish message")
        
        @self.app.get("/api/messages", dependencies=[Depends(self.verify_api_key)])
        async def get_messages(
            topic: Optional[str] = None,
            client_id: Optional[str] = None,
            limit: int = 100,
            offset: int = 0
        ):
            """Get message logs"""
            with self.db_manager.get_session() as session:
                query = session.query(MessageLog)
                
                if topic:
                    query = query.filter_by(topic=topic)
                if client_id:
                    query = query.filter_by(client_id=client_id)
                
                total = query.count()
                messages = query.order_by(
                    MessageLog.timestamp.desc()
                ).offset(offset).limit(limit).all()
                
                return {
                    "total": total,
                    "limit": limit,
                    "offset": offset,
                    "messages": [
                        {
                            "id": msg.id,
                            "timestamp": msg.timestamp.isoformat(),
                            "topic": msg.topic,
                            "qos": msg.qos,
                            "retain": msg.retain,
                            "payload": msg.payload,
                            "payload_size": msg.payload_size,
                            "client_id": msg.client_id,
                            "direction": msg.direction
                        }
                        for msg in messages
                    ]
                }
        
        @self.app.get("/api/stats/history", dependencies=[Depends(self.verify_api_key)])
        async def get_stats_history(hours: int = 24):
            """Get historical statistics"""
            cutoff_time = datetime.now() - timedelta(hours=hours)
            
            with self.db_manager.get_session() as session:
                stats = session.query(BrokerStats).filter(
                    BrokerStats.timestamp >= cutoff_time
                ).order_by(BrokerStats.timestamp.asc()).all()
                
                return [
                    {
                        "timestamp": stat.timestamp.isoformat(),
                        "connected_clients": stat.connected_clients,
                        "messages_received": stat.messages_received,
                        "messages_sent": stat.messages_sent,
                        "subscriptions_active": stat.subscriptions_active,
                        "memory_usage_mb": stat.memory_usage_mb,
                        "cpu_percent": stat.cpu_percent
                    }
                    for stat in stats
                ]
        
        # Dashboard (public)
        @self.app.get("/", response_class=HTMLResponse)
        async def dashboard():
            """Serve dashboard page"""
            return """
            <!DOCTYPE html>
            <html>
            <head>
                <title>MQTT Broker Dashboard</title>
                <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
                <style>
                    * { margin: 0; padding: 0; box-sizing: border-box; }
                    body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, sans-serif; background: #f5f5f5; color: #333; }
                    .container { max-width: 1200px; margin: 0 auto; padding: 20px; }
                    header { background: #007bff; color: white; padding: 20px; border-radius: 8px; margin-bottom: 30px; }
                    h1 { font-size: 24px; margin-bottom: 10px; }
                    .stats-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; margin-bottom: 30px; }
                    .stat-card { background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
                    .stat-value { font-size: 32px; font-weight: bold; color: #007bff; margin: 10px 0; }
                    .stat-label { color: #666; font-size: 14px; }
                    .chart-container { background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); margin-bottom: 30px; }
                    .table-container { background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); margin-bottom: 30px; }
                    table { width: 100%; border-collapse: collapse; }
                    th, td { padding: 12px; text-align: left; border-bottom: 1px solid #eee; }
                    th { background: #f8f9fa; font-weight: 600; }
                    tr:hover { background: #f8f9fa; }
                    .status-indicator { display: inline-block; width: 10px; height: 10px; border-radius: 50%; margin-right: 8px; }
                    .status-online { background: #28a745; }
                    .status-offline { background: #dc3545; }
                </style>
            </head>
            <body>
                <div class="container">
                    <header>
                        <h1>MQTT Broker Dashboard</h1>
                        <p>Real-time monitoring and management</p>
                    </header>
                    
                    <div class="stats-grid" id="stats"></div>
                    
                    <div class="chart-container">
                        <h2>Client Connections</h2>
                        <canvas id="connectionsChart"></canvas>
                    </div>
                    
                    <div class="table-container">
                        <h2>Connected Clients</h2>
                        <table id="clientsTable">
                            <thead>
                                <tr>
                                    <th>Client ID</th>
                                    <th>Username</th>
                                    <th>IP Address</th>
                                    <th>Connected</th>
                                    <th>Subscriptions</th>
                                </tr>
                            </thead>
                            <tbody></tbody>
                        </table>
                    </div>
                    
                    <div class="table-container">
                        <h2>Active Topics</h2>
                        <table id="topicsTable">
                            <thead>
                                <tr>
                                    <th>Topic</th>
                                    <th>Subscribers</th>
                                    <th>Last Message</th>
                                </tr>
                            </thead>
                            <tbody></tbody>
                        </table>
                    </div>
                </div>
                
                <script>
                    let connectionsChart;
                    
                    async function updateDashboard() {
                        try {
                            // Update stats
                            const statusRes = await fetch('/api/status');
                            const status = await statusRes.json();
                            
                            document.getElementById('stats').innerHTML = `
                                <div class="stat-card">
                                    <div class="stat-label">Connected Clients</div>
                                    <div class="stat-value">${status.connected_clients}</div>
                                </div>
                                <div class="stat-card">
                                    <div class="stat-label">Total Messages</div>
                                    <div class="stat-value">${status.messages_received + status.messages_sent}</div>
                                </div>
                                <div class="stat-card">
                                    <div class="stat-label">Uptime</div>
                                    <div class="stat-value">${Math.floor(status.uptime / 3600)}h ${Math.floor((status.uptime % 3600) / 60)}m</div>
                                </div>
                                <div class="stat-card">
                                    <div class="stat-label">Active Topics</div>
                                    <div class="stat-value">${status.topics_count}</div>
                                </div>
                            `;
                            
                            // Update clients table
                            const clientsRes = await fetch('/api/clients');
                            const clients = await clientsRes.json();
                            
                            const clientsBody = clients.map(client => `
                                <tr>
                                    <td>${client.client_id}</td>
                                    <td>${client.username || 'Anonymous'}</td>
                                    <td>${client.ip_address}</td>
                                    <td>${new Date(client.connected_at).toLocaleString()}</td>
                                    <td>${client.subscriptions.length}</td>
                                </tr>
                            `).join('');
                            
                            document.querySelector('#clientsTable tbody').innerHTML = clientsBody;
                            
                            // Update topics table
                            const topicsRes = await fetch('/api/topics');
                            const topics = await topicsRes.json();
                            
                            const topicsBody = topics.map(topic => `
                                <tr>
                                    <td>${topic.topic}</td>
                                    <td>${topic.subscriber_count}</td>
                                    <td>${topic.last_message_at ? new Date(topic.last_message_at).toLocaleString() : 'Never'}</td>
                                </tr>
                            `).join('');
                            
                            document.querySelector('#topicsTable tbody').innerHTML = topicsBody;
                            
                            // Update chart
                            const statsRes = await fetch('/api/stats/history?hours=6');
                            const stats = await statsRes.json();
                            
                            if (connectionsChart) {
                                connectionsChart.destroy();
                            }
                            
                            const ctx = document.getElementById('connectionsChart').getContext('2d');
                            connectionsChart = new Chart(ctx, {
                                type: 'line',
                                data: {
                                    labels: stats.map(s => new Date(s.timestamp).toLocaleTimeString()),
                                    datasets: [{
                                        label: 'Connected Clients',
                                        data: stats.map(s => s.connected_clients),
                                        borderColor: '#007bff',
                                        backgroundColor: 'rgba(0, 123, 255, 0.1)',
                                        fill: true
                                    }]
                                },
                                options: {
                                    responsive: true,
                                    maintainAspectRatio: false,
                                    scales: {
                                        y: {
                                            beginAtZero: true
                                        }
                                    }
                                }
                            });
                            
                        } catch (error) {
                            console.error('Failed to update dashboard:', error);
                        }
                    }
                    
                    // Update every 5 seconds
                    setInterval(updateDashboard, 5000);
                    updateDashboard();
                </script>
            </body>
            </html>
            """