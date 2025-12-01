from typing import Dict, Set
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime, timedelta
from app.api import deps
from app.core.config import settings
from app.models.active_session import ActiveSession
from app.schemas.watch import ActivePlayer, GameState
import json

router = APIRouter()

class ConnectionManager:
    def __init__(self):
        # Map of connection_id -> websocket
        self.active_connections: Dict[str, WebSocket] = {}
        # Map of connection_id -> set of player_ids they're watching
        self.connection_subscriptions: Dict[str, Set[str]] = {}
    
    async def connect(self, websocket: WebSocket, connection_id: str):
        await websocket.accept()
        self.active_connections[connection_id] = websocket
        self.connection_subscriptions[connection_id] = set()
    
    def disconnect(self, connection_id: str):
        if connection_id in self.active_connections:
            del self.active_connections[connection_id]
        if connection_id in self.connection_subscriptions:
            del self.connection_subscriptions[connection_id]
    
    async def send_personal_message(self, message: dict, connection_id: str):
        if connection_id in self.active_connections:
            try:
                await self.active_connections[connection_id].send_json(message)
            except Exception as e:
                print(f"Error sending message to {connection_id}: {e}")
                self.disconnect(connection_id)
    
    async def broadcast(self, message: dict, player_id: str = None):
        """Broadcast message to all connections watching a specific player, or all if player_id is None"""
        disconnected = []
        for connection_id, websocket in self.active_connections.items():
            subscriptions = self.connection_subscriptions.get(connection_id, set())
            # If player_id is None, broadcast to all. Otherwise, only to those subscribed to this player
            if player_id is None or player_id in subscriptions or len(subscriptions) == 0:
                try:
                    await websocket.send_json(message)
                except Exception as e:
                    print(f"Error broadcasting to {connection_id}: {e}")
                    disconnected.append(connection_id)
        
        # Clean up disconnected connections
        for connection_id in disconnected:
            self.disconnect(connection_id)
    
    def subscribe(self, connection_id: str, player_id: str):
        if connection_id in self.connection_subscriptions:
            self.connection_subscriptions[connection_id].add(player_id)
    
    def unsubscribe(self, connection_id: str, player_id: str):
        if connection_id in self.connection_subscriptions:
            self.connection_subscriptions[connection_id].discard(player_id)

manager = ConnectionManager()

@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """
    WebSocket endpoint for real-time game state updates.
    Clients can subscribe to specific players or receive all updates.
    """
    import uuid
    connection_id = str(uuid.uuid4())
    await manager.connect(websocket, connection_id)
    
    try:
        # Send initial connection confirmation
        await websocket.send_json({
            "type": "connected",
            "connectionId": connection_id,
            "message": "Connected to Snake Game WebSocket"
        })
        
        while True:
            # Receive message from client
            data = await websocket.receive_text()
            
            try:
                message = json.loads(data)
                message_type = message.get("type")
                
                if message_type == "subscribe":
                    # Subscribe to specific player updates
                    player_id = message.get("playerId")
                    if player_id:
                        manager.subscribe(connection_id, player_id)
                        await websocket.send_json({
                            "type": "subscribed",
                            "playerId": player_id
                        })
                
                elif message_type == "unsubscribe":
                    # Unsubscribe from specific player
                    player_id = message.get("playerId")
                    if player_id:
                        manager.unsubscribe(connection_id, player_id)
                        await websocket.send_json({
                            "type": "unsubscribed",
                            "playerId": player_id
                        })
                
                elif message_type == "ping":
                    # Heartbeat
                    await websocket.send_json({"type": "pong"})
                
            except json.JSONDecodeError:
                await websocket.send_json({
                    "type": "error",
                    "message": "Invalid JSON format"
                })
            except Exception as e:
                await websocket.send_json({
                    "type": "error",
                    "message": str(e)
                })
    
    except WebSocketDisconnect:
        manager.disconnect(connection_id)
    except Exception as e:
        print(f"WebSocket error: {e}")
        manager.disconnect(connection_id)

async def broadcast_player_update(player_id: str, player_data: dict):
    """Helper function to broadcast player update to subscribed clients"""
    await manager.broadcast({
        "type": "player:update",
        "playerId": player_id,
        "data": player_data
    }, player_id=player_id)

async def broadcast_player_join(player_id: str, player_data: dict):
    """Helper function to broadcast player join event"""
    await manager.broadcast({
        "type": "player:join",
        "playerId": player_id,
        "data": player_data
    })

async def broadcast_player_leave(player_id: str):
    """Helper function to broadcast player leave event"""
    await manager.broadcast({
        "type": "player:leave",
        "playerId": player_id
    })

