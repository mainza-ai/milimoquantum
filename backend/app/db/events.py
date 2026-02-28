"""Milimo Quantum — Real-Time Event Fabric.

Binds SQLAlchemy session events to the Sync Engine and WebSocket Manager.
This eliminates polling by triggering sync/broadcast immediately on commit.
"""
import logging
from sqlalchemy import event
from sqlalchemy.orm import Session
from app.db.models import Experiment, Conversation, Message
from app.experiments.sync_engine import trigger_sync, broadcast_p2p

logger = logging.getLogger(__name__)

def setup_listeners():
    """Register event listeners on key models."""
    
    @event.listens_for(Session, "after_commit")
    def receive_after_commit(session):
        """Triggered after any successful database commit."""
        # For now, we trigger a global sync check if any changes happened.
        # In a more granular setup, we'd track which objects changed.
        trigger_sync()

    @event.listens_for(Experiment, "after_insert")
    def experiment_after_insert(mapper, connection, target):
        """Broadcast new experiments to peers immediately."""
        # Note: target is the Experiment instance.
        # We wrap in a try/except to ensure DB commit isn't blocked by network issues.
        try:
            import asyncio
            from app.routes.sync import manager
            
            # Simple dict representation
            data = {
                "id": target.id,
                "name": target.name,
                "backend": target.backend,
                "status": "created",
                "timestamp": target.created_at.isoformat() if target.created_at else None
            }
            
            # Try to get the running loop (this usually happens in the FastAPI main thread)
            try:
                loop = asyncio.get_running_loop()
                if loop.is_running():
                    loop.create_task(manager.broadcast({
                        "type": "new_experiment",
                        "data": data
                    }))
            except RuntimeError:
                # No running loop (e.g. running in a script)
                pass
                
        except Exception as e:
            logger.warning(f"Failed to trigger real-time broadcast: {e}")

    logger.info("Real-time Event Fabric listeners registered.")
