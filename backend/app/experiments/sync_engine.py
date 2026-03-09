"""Milimo Quantum — Offline Sync Engine.

Merges local offline SQLite runs with the central PostgreSQL database.
Handles conflict resolution (Last-Write-Wins caching) and peer broadcasting.
"""
from __future__ import annotations

import asyncio
import logging


from app.db import get_session as get_cloud_session
from app.db.local_cache import get_local_session
from app.db.models import Experiment
from app.routes.sync import manager as ws_manager

logger = logging.getLogger(__name__)


def merge_dicts(local_params: dict, remote_params: dict) -> dict:
    """Merge JSON parameters.
    
    Strategy:
    - Lists (comments, shared_with) are unioned.
    - Other keys use Last-Write-Wins (assumes local is the most recent offline write).
    """
    merged = dict(remote_params)
    for k, v in local_params.items():
        if k in ("comments", "shared_with") and isinstance(v, list):
            existing = merged.get(k, [])
            if isinstance(existing, list):
                # Simple union for now. More complex rules would need timestamp sorting.
                merged[k] = existing + [item for item in v if item not in existing]
            else:
                merged[k] = v
        else:
            merged[k] = v
    return merged


def push_local_to_cloud(run_id: str) -> bool:
    """Push a specific run from local SQLite to cloud Postgres."""
    local_session = get_local_session()
    cloud_session = get_cloud_session()
    
    try:
        local_exp = local_session.query(Experiment).filter_by(id=run_id).first()
        if not local_exp:
            return False
            
        remote_exp = cloud_session.query(Experiment).filter_by(id=run_id).first()
        
        if remote_exp:
            # Conflict Resolution
            remote_exp.name = local_exp.name or remote_exp.name
            remote_exp.backend = local_exp.backend or remote_exp.backend
            remote_exp.shots = local_exp.shots or remote_exp.shots
            remote_exp.results = local_exp.results or remote_exp.results
            
            # Merge JSON fields
            remote_exp.parameters = merge_dicts(local_exp.parameters or {}, remote_exp.parameters or {})
            
            # Combine tags
            all_tags = set(remote_exp.tags or [])
            all_tags.update(local_exp.tags or [])
            remote_exp.tags = sorted(list(all_tags))
            
            remote_exp.runtime_ms = local_exp.runtime_ms or remote_exp.runtime_ms
            logger.info(f"Merged local experiment {run_id} into cloud")
        else:
            # Insert new
            new_exp = Experiment(
                id=local_exp.id,
                project=local_exp.project,
                name=local_exp.name,
                circuit_code=local_exp.circuit_code,
                backend=local_exp.backend,
                shots=local_exp.shots,
                results=local_exp.results,
                parameters=local_exp.parameters,
                tags=local_exp.tags,
                created_at=local_exp.created_at,
                runtime_ms=local_exp.runtime_ms,
                # is_synced gets set True later, we don't store it in remote
            )
            cloud_session.add(new_exp)
            logger.info(f"Pushed local experiment {run_id} to cloud")

        cloud_session.commit()
        
        # Mark local as synced
        local_exp.is_synced = True
        local_session.commit()
        return True
        
    except Exception as e:
        cloud_session.rollback()
        local_session.rollback()
        logger.error(f"Failed to sync {run_id} to cloud: {e}")
        return False
    finally:
        cloud_session.close()
        local_session.close()


async def broadcast_p2p(run_data: dict):
    """Broadcast the new run to all peers in the LAN via WebSocket."""
    # Convert dates to iso strings for JSON serialization
    safe_data = dict(run_data)
    if "created_at" in safe_data and hasattr(safe_data["created_at"], "isoformat"):
        safe_data["created_at"] = safe_data["created_at"].isoformat()
        
    packet = {
        "type": "new_experiment_run",
        "data": safe_data
    }
    await ws_manager.broadcast(packet)
    logger.info(f"Broadcasted experiment {run_data.get('run_id')} to peers")


# Global event to trigger sync immediately
_sync_event = asyncio.Event()

def trigger_sync():
    """Trigger the background sync loop to run immediately."""
    _sync_event.set()

async def sync_loop():
    """Background loop to sync offline experiments reactively."""
    while True:
        try:
            # Wait for event permanently without polling
            await _sync_event.wait()
            _sync_event.clear()
            logger.debug("Sync triggered by database event")

            local_session = get_local_session()
            unsynced = local_session.query(Experiment).filter_by(is_synced=False).all()
            
            for exp in unsynced:
                success = push_local_to_cloud(exp.id)
                if not success:
                    logger.warning(f"Will retry sync for {exp.id} later.")
                    
            local_session.close()
        except Exception as e:
            logger.error(f"Error in sync loop: {e}")
            await asyncio.sleep(5) # Cooldown on error
