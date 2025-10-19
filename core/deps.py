import os, motor.motor_asyncio
_client=None

def _inst():
    global _client
    if _client is None:
        _client = motor.motor_asyncio.AsyncIOMotorClient(os.getenv('MONGO_URI'))
    return _client

def get_db():
    return _inst()[os.getenv('MONGO_DB','saft_doctor')]

def scoped_collection(db,name,country):
    strat=os.getenv('MONGO_SCOPING','collection_prefix')
    if strat=='collection_prefix': return db[f"{country}_{name}"]
    elif strat=='database_per_country': return _inst()[f"{os.getenv('MONGO_DB','saft_doctor')}_{country}"][name]
    return db[f"{country}_{name}"]
