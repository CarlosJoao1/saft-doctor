from core.deps import scoped_collection
from datetime import datetime, timezone
class UsersRepo:
    def __init__(self,db,country:str): self.col=scoped_collection(db,'users',country)
    async def exists(self,u:str): return await self.col.find_one({'username':u}) is not None
    async def create(self,u:str,h:str):
        res=await self.col.insert_one({'username':u,'password_hash':h,'at':None}); return {'_id':res.inserted_id,'username':u}
    async def get(self,u:str): return await self.col.find_one({'username':u})
    async def save_encrypted_at_credentials(self,u:str,euser:str,epass:str):
        await self.col.update_one(
            {'username':u},
            {'$set':{'at':{'user':euser,'pass':epass,'updated_at':datetime.now(timezone.utc)}}}
        );
        return True
