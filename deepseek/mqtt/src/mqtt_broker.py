import asyncio
import logging
from typing import Dict, List, Optional, Any, Set
import time
import uuid
import json
from datetime import datetime
import psutil

from amqtt.broker import Broker
from amqtt.client import MQTTClient
from amqtt.mqtt.constants import QOS_0, QOS_1, QOS_2

from .config import BrokerConfig
from .database import DatabaseManager
from .models import ClientSession, MessageLog, BrokerStats, TopicInfo

logger = logging.getLogger(__name__)

class MQTTBrokerManager:
    def __init__(self, config: BrokerConfig, db_manager: DatabaseManager):
        self.config = config
        self.db_manager = db_manager
        self.broker: Optional[Broker] = None
        self.clients: Dict[str, Dict] = {}
        self.topics: Dict[str, Set[str]] = {}  # topic -> set of client_ids
        self.stats = {
            "connected_clients": 0,
            "messages_received": 0,
            "messages_sent": 0,
            "subscriptions": 0,
            "start_time": time.time()
        }
        self._running = False
        
    async def start(self):
        """Start the MQTT broker"""
        try:
            broker_config = self.config.get_mqtt_broker_config()
            self.broker = Broker(broker_config)
            
            # Set up event handlers
            self.broker.on_client_connected = self._on_client_connected
            self.broker.on_client_disconnected = self._on_client_disconnected
            self.broker.on_message_published = self._on_message_published
            self.broker.on_client_subscribed = self._on_client_subscribed
            self.broker.on_client_unsubscribed = self._on_client_unsubscribed
            
            await self.broker.start()
            self._running = True
            
            # Start background tasks
            asyncio.create_task(self._stats_monitor())
            asyncio.create_task(self._cleanup_task())
            
            logger.info(f"MQTT Broker started on {self.config.mqtt.host}:{self.config.mqtt.port}")
            logger.info(f"WebSocket MQTT available on port {self.config.mqtt.websocket_port}")
            
            if self.config.ssl.enabled:
                logger.info(f"SSL MQTT available on port {self.config.mqtt.ssl_port}")
                
        except Exception as e:
            logger.error(f"Failed to start MQTT broker: {e}")
            raise
    
    async def stop(self):
        """Stop the MQTT broker gracefully"""
        self._running = False
        if self.broker:
            await self.broker.shutdown()
            logger.info("MQTT Broker stopped")
    
    async def _on_client_connected(self, client_id: str, username: Optional[str], ip_address: str):
        """Handle client connection"""
        session_id = str(uuid.uuid4())
        self.clients[client_id] = {
            'session_id': session_id,
            'username': username,
            'ip_address': ip_address,
            'connected_at': datetime.now(),
            'subscriptions': []
        }
        
        with self.db_manager.get_session() as session:
            db_session = ClientSession(
                id=session_id,
                client_id=client_id,
                username=username,
                ip_address=ip_address,
                connected_at=datetime.now(),
                is_connected=True
            )
            session.add(db_session)
        
        self.stats["connected_clients"] = len(self.clients)
        logger.info(f"Client connected: {client_id} ({username}) from {ip_address}")
    
    async def _on_client_disconnected(self, client_id: str):
        """Handle client disconnection"""
        if client_id in self.clients:
            client = self.clients[client_id]
            session_id = client['session_id']
            
            with self.db_manager.get_session() as session:
                db_session = session.query(ClientSession).filter_by(id=session_id).first()
                if db_session:
                    db_session.disconnected_at = datetime.now()
                    db_session.is_connected = False
            
            # Remove from topics
            for topic, subscribers in self.topics.items():
                if client_id in subscribers:
                    subscribers.remove(client_id)
            
            del self.clients[client_id]
            self.stats["connected_clients"] = len(self.clients)
            
            logger.info(f"Client disconnected: {client_id}")
    
    async def _on_message_published(self, client_id: str, topic: str, payload: bytes, qos: int, retain: bool):
        """Handle published message"""
        self.stats["messages_received"] += 1
        
        payload_str = payload.decode('utf-8', errors='ignore')
        payload_size = len(payload)
        
        # Log message to database
        with self.db_manager.get_session() as session:
            message_log = MessageLog(
                topic=topic,
                qos=qos,
                retain=retain,
                payload=payload_str,
                payload_size=payload_size,
                client_id=client_id,
                direction='in'
            )
            session.add(message_log)
            
            # Update topic info
            topic_info = session.query(TopicInfo).filter_by(topic=topic).first()
            if not topic_info:
                topic_info = TopicInfo(topic=topic)
                session.add(topic_info)
            
            topic_info.last_message_at = datetime.now()
            topic_info.last_message = payload_str[:1000]  # Store first 1000 chars
            topic_info.subscriber_count = len(self.topics.get(topic, set()))
        
        logger.debug(f"Message published to {topic} by {client_id}: {payload_str[:100]}...")
    
    async def _on_client_subscribed(self, client_id: str, topic: str, qos: int):
        """Handle client subscription"""
        if client_id in self.clients:
            self.clients[client_id]['subscriptions'].append(topic)
        
        if topic not in self.topics:
            self.topics[topic] = set()
        self.topics[topic].add(client_id)
        
        self.stats["subscriptions"] = sum(len(subscribers) for subscribers in self.topics.values())
        
        # Update database
        with self.db_manager.get_session() as session:
            db_session = session.query(ClientSession).filter_by(
                client_id=client_id, 
                is_connected=True
            ).order_by(ClientSession.connected_at.desc()).first()
            
            if db_session:
                subscriptions = db_session.get_subscriptions()
                subscriptions.append(topic)
                db_session.set_subscriptions(subscriptions)
        
        logger.info(f"Client {client_id} subscribed to {topic} with QoS {qos}")
    
    async def _on_client_unsubscribed(self, client_id: str, topic: str):
        """Handle client unsubscription"""
        if client_id in self.clients:
            if topic in self.clients[client_id]['subscriptions']:
                self.clients[client_id]['subscriptions'].remove(topic)
        
        if topic in self.topics and client_id in self.topics[topic]:
            self.topics[topic].remove(client_id)
            if not self.topics[topic]:
                del self.topics[topic]
        
        self.stats["subscriptions"] = sum(len(subscribers) for subscribers in self.topics.values())
        
        # Update database
        with self.db_manager.get_session() as session:
            db_session = session.query(ClientSession).filter_by(
                client_id=client_id, 
                is_connected=True
            ).order_by(ClientSession.connected_at.desc()).first()
            
            if db_session:
                subscriptions = db_session.get_subscriptions()
                if topic in subscriptions:
                    subscriptions.remove(topic)
                db_session.set_subscriptions(subscriptions)
        
        logger.info(f"Client {client_id} unsubscribed from {topic}")
    
    async def _stats_monitor(self):
        """Monitor and log broker statistics"""
        while self._running:
            try:
                await asyncio.sleep(30)  # Update every 30 seconds
                
                # Get system stats
                process = psutil.Process()
                memory_mb = process.memory_info().rss / 1024 / 1024
                cpu_percent = process.cpu_percent()
                
                # Save stats to database
                with self.db_manager.get_session() as session:
                    stats = BrokerStats(
                        connected_clients=self.stats["connected_clients"],
                        messages_received=self.stats["messages_received"],
                        messages_sent=self.stats["messages_sent"],
                        subscriptions_active=self.stats["subscriptions"],
                        memory_usage_mb=memory_mb,
                        cpu_percent=cpu_percent
                    )
                    session.add(stats)
                
                logger.debug(
                    f"Stats: {self.stats['connected_clients']} clients, "
                    f"{self.stats['messages_received']} msgs received, "
                    f"{self.stats['subscriptions']} subscriptions"
                )
                
            except Exception as e:
                logger.error(f"Error in stats monitor: {e}")
    
    async def _cleanup_task(self):
        """Clean up old sessions periodically"""
        while self._running:
            try:
                await asyncio.sleep(3600)  # Run every hour
                
                with self.db_manager.get_session() as session:
                    # Mark old sessions as disconnected
                    cutoff_time = datetime.now() - timedelta(hours=24)
                    old_sessions = session.query(ClientSession).filter(
                        ClientSession.is_connected == True,
                        ClientSession.last_seen < cutoff_time
                    ).all()
                    
                    for session_obj in old_sessions:
                        session_obj.is_connected = False
                        session_obj.disconnected_at = session_obj.last_seen
                    
                    # Delete old message logs (keep 30 days)
                    log_cutoff = datetime.now() - timedelta(days=30)
                    session.query(MessageLog).filter(
                        MessageLog.timestamp < log_cutoff
                    ).delete()
                    
                    logger.info(f"Cleanup: marked {len(old_sessions)} sessions as disconnected")
                    
            except Exception as e:
                logger.error(f"Error in cleanup task: {e}")
    
    def get_status(self) -> Dict[str, Any]:
        """Get broker status"""
        return {
            "status": "running" if self._running else "stopped",
            "uptime": time.time() - self.stats["start_time"],
            "connected_clients": self.stats["connected_clients"],
            "messages_received": self.stats["messages_received"],
            "messages_sent": self.stats["messages_sent"],
            "subscriptions": self.stats["subscriptions"],
            "topics_count": len(self.topics)
        }
    
    def get_connected_clients(self) -> List[Dict[str, Any]]:
        """Get list of connected clients"""
        clients_list = []
        for client_id, client_info in self.clients.items():
            clients_list.append({
                "client_id": client_id,
                "username": client_info.get("username"),
                "ip_address": client_info.get("ip_address"),
                "connected_at": client_info.get("connected_at").isoformat(),
                "subscriptions": client_info.get("subscriptions", [])
            })
        return clients_list
    
    def get_topics(self) -> List[Dict[str, Any]]:
        """Get list of active topics"""
        topics_list = []
        for topic, subscribers in self.topics.items():
            topics_list.append({
                "topic": topic,
                "subscriber_count": len(subscribers),
                "subscribers": list(subscribers)
            })
        return topics_list
    
    async def publish_message(self, topic: str, payload: str, qos: int = 0, retain: bool = False):
        """Publish a message from the broker"""
        if self.broker:
            # This would need access to internal broker methods
            # For now, we'll create a client to publish
            try:
                client = MQTTClient()
                await client.connect(f"mqtt://{self.config.mqtt.host}:{self.config.mqtt.port}")
                await client.publish(topic, payload.encode(), qos=qos, retain=retain)
                await client.disconnect()
                
                self.stats["messages_sent"] += 1
                logger.info(f"Published message to {topic}")
                return True
            except Exception as e:
                logger.error(f"Failed to publish message: {e}")
                return False
        return False