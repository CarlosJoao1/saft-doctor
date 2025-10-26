from core.deps import scoped_collection
from datetime import datetime, timezone
from typing import Optional

class SMTPConfigRepo:
    """Repository for SMTP configuration (system-wide, sysadmin only)"""

    def __init__(self, db, country: str):
        # Store in system collection (not country-scoped)
        self.col = db['smtp_config']

    async def get_config(self) -> Optional[dict]:
        """Get SMTP configuration"""
        return await self.col.find_one({'_id': 'smtp'})

    async def save_config(self, config: dict):
        """Save SMTP configuration"""
        await self.col.update_one(
            {'_id': 'smtp'},
            {
                '$set': {
                    **config,
                    'updated_at': datetime.now(timezone.utc)
                }
            },
            upsert=True
        )
        return True

    async def delete_config(self):
        """Delete SMTP configuration (revert to environment variables)"""
        await self.col.delete_one({'_id': 'smtp'})
        return True
