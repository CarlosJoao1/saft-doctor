from core.deps import scoped_collection
from datetime import datetime, timezone
class UsersRepo:
    def __init__(self,db,country:str): self.col=scoped_collection(db,'users',country)
    async def exists(self,u:str): return await self.col.find_one({'username':u}) is not None
    async def create(self,u:str,h:str,email:str=None):
        # Check if this is the first user (make them sysadmin)
        count = await self.col.count_documents({})
        role = 'sysadmin' if count == 0 else 'user'
        res=await self.col.insert_one({'username':u,'password_hash':h,'email':email,'role':role,'at':None,'created_at':datetime.now(timezone.utc)}); return {'_id':res.inserted_id,'username':u,'role':role}
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

    async def delete_at_entry(self, u: str, ident_enc: str):
        """Delete a specific AT entry by encrypted ident"""
        await self.col.update_one(
            { 'username': u },
            { '$unset': { f'at_entries.{ident_enc}': '' } }
        )
        return True

    async def update_password(self, u: str, new_hash: str):
        """Update user password"""
        await self.col.update_one(
            { 'username': u },
            { '$set': { 'password_hash': new_hash, 'password_updated_at': datetime.now(timezone.utc) } }
        )
        return True

    async def update_email(self, u: str, email: str):
        """Update user email"""
        await self.col.update_one(
            { 'username': u },
            { '$set': { 'email': email, 'email_updated_at': datetime.now(timezone.utc) } }
        )
        return True
