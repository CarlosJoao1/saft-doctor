import os, motor.motor_asyncio
from urllib.parse import urlparse
_client=None

def _inst():
    global _client
    if _client is None:
        # Prefer explicit MONGO_URI; fallback to local docker-compose Mongo service
        uri = os.getenv('MONGO_URI') or 'mongodb://mongo:27017'
        _client = motor.motor_asyncio.AsyncIOMotorClient(uri)
    return _client

def get_db():
    return _inst()[os.getenv('MONGO_DB','saft_doctor')]

def scoped_collection(db,name,country):
    strat=os.getenv('MONGO_SCOPING','collection_prefix')
    if strat=='collection_prefix': return db[f"{country}_{name}"]
    elif strat=='database_per_country': return _inst()[f"{os.getenv('MONGO_DB','saft_doctor')}_{country}"][name]
    return db[f"{country}_{name}"]
