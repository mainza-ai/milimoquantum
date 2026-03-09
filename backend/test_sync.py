import logging
from app.db import init_db
from app.experiments.registry import log_run
from app.experiments.sync_engine import push_local_to_cloud
from app.db.local_cache import get_local_session
from app.db import get_session as get_cloud_session
from app.db.models import Experiment

logging.basicConfig(level=logging.INFO)

def main():
    print("Initializing databases...")
    init_db()  # Ensures local SQLite schema is also loaded

    print("Logging offline run to local cache...")
    run_data = log_run(project="sync_test", circuit_name="Offline VQE", notes="Attempting offline sync")
    run_id = run_data.get("run_id")
    print(f"Run ID: {run_id}")
    
    local_session = get_local_session()
    local_exp = local_session.query(Experiment).filter_by(id=run_id).first()
    print(f"Local exists: {local_exp is not None}, is_synced: {local_exp.is_synced if local_exp else None}")
    local_session.close()
    
    cloud_session = get_cloud_session()
    cloud_exp = cloud_session.query(Experiment).filter_by(id=run_id).first()
    print(f"Cloud exists BEFORE sync: {cloud_exp is not None}")
    cloud_session.close()
    
    print("Testing manual sync engine push...")
    success = push_local_to_cloud(run_id)
    print(f"Sync successful: {success}")
    
    cloud_session = get_cloud_session()
    cloud_exp = cloud_session.query(Experiment).filter_by(id=run_id).first()
    print(f"Cloud exists AFTER sync: {cloud_exp is not None}")
    if cloud_exp:
        print(f"Cloud record name: {cloud_exp.name}")
    cloud_session.close()
    
    local_session = get_local_session()
    local_exp = local_session.query(Experiment).filter_by(id=run_id).first()
    print(f"Local is_synced AFTER sync: {local_exp.is_synced if local_exp else None}")
    local_session.close()

if __name__ == "__main__":
    main()
