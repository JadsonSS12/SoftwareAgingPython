from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, Float, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime
import json

from .database import Base

class ClientSession(Base):
    __tablename__ = "client_sessions"
    
    id = Column(String(36), primary_key=True)
    client_id = Column(String(100), index=True, nullable=False)
    username = Column(String(100))
    connected_at = Column(DateTime, default=func.now())
    disconnected_at = Column(DateTime, nullable=True)
    last_seen = Column(DateTime, default=func.now(), onupdate=func.now())
    ip_address = Column(String(45))
    subscriptions = Column(Text, default="[]")
    is_connected = Column(Boolean, default=True)
    
    def get_subscriptions(self) -> list:
        return json.loads(self.subscriptions or "[]")
    
    def set_subscriptions(self, subscriptions: list):
        self.subscriptions = json.dumps(subscriptions)

class MessageLog(Base):
    __tablename__ = "message_logs"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp = Column(DateTime, default=func.now())
    topic = Column(String(512), index=True, nullable=False)
    qos = Column(Integer, default=0)
    retain = Column(Boolean, default=False)
    payload = Column(Text)
    payload_size = Column(Integer)
    client_id = Column(String(100), index=True)
    direction = Column(String(10))  # 'in' or 'out'

class BrokerStats(Base):
    __tablename__ = "broker_stats"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp = Column(DateTime, default=func.now())
    connected_clients = Column(Integer, default=0)
    messages_received = Column(Integer, default=0)
    messages_sent = Column(Integer, default=0)
    subscriptions_active = Column(Integer, default=0)
    memory_usage_mb = Column(Float, default=0.0)
    cpu_percent = Column(Float, default=0.0)

class TopicInfo(Base):
    __tablename__ = "topic_info"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    topic = Column(String(512), unique=True, index=True, nullable=False)
    subscriber_count = Column(Integer, default=0)
    last_message_at = Column(DateTime, nullable=True)
    last_message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=func.now())

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(100), unique=True, index=True, nullable=False)
    email = Column(String(255), unique=True, index=True)
    hashed_password = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True)
    is_admin = Column(Boolean, default=False)
    created_at = Column(DateTime, default=func.now())
    last_login = Column(DateTime, nullable=True)