from core.deps import scoped_collection
from datetime import datetime, timezone
class UsersRepo:
    def __init__(self,db,country:str): self.col=scoped_collection(db,'users',country)
    async def exists(self,u:str): return await self.col.find_one({'username':u}) is not None
    async def create(self,u:str,h:str):
        res=await self.col.insert_one({'username':u,'password_hash':h,'at':None,'created_at':datetime.now(timezone.utc)}); return {'_id':res.inserted_id,'username':u}
    async def get(self,u:str): return await self.col.find_one({'username':u})
    async def save_encrypted_at_credentials(self,u:str,euser:str,epass:str):
        await self.col.update_one(
            {'username':u},
            {'$set':{'at':{'user':euser,'pass':epass,'updated_at':datetime.now(timezone.utc)}}},
            upsert=True
        );
        return True

    # Multi-entry management keyed by 'ident' (e.g., NIF). Stored under 'at_entries' dict where key is encrypted ident.
    async def upsert_at_entry(self, u: str, ident_enc: str, pass_enc: str):
        await self.col.update_one(
            { 'username': u },
            { '$set': { f'at_entries.{ident_enc}': { 'pass': pass_enc, 'updated_at': datetime.now(timezone.utc) } } },
            upsert=True
        )
        return True

    async def get_at_entries(self, u: str):
        doc = await self.col.find_one({ 'username': u }, { 'at_entries': 1, '_id': 0 })
        return (doc or {}).get('at_entries') or {}
