from __future__ import annotations
from typing import Any, Dict, Optional
from datetime import datetime, timezone
from core.deps import scoped_collection

class AnalysisRepo:
    """Repository for storing analysis results of uploaded files.

    Document shape:
    {
      _id: ObjectId,
      username: str,
      object_key: str | None,
      filename: str | None,
      content_type: str | None,
      created_at: datetime,
      country: str,
      status: str,  # 'ok' | 'errors' | 'invalid-xml'
      issues: list[dict],
      summary: dict,
    }
    """
    def __init__(self, db, country: str):
        self.col = scoped_collection(db, 'analyses', country)

    async def create(self, username: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        doc = {
            'username': username,
            'created_at': datetime.now(timezone.utc),
            **payload,
        }
        res = await self.col.insert_one(doc)
        doc['_id'] = res.inserted_id
        return doc

    async def get(self, _id) -> Optional[Dict[str, Any]]:
        return await self.col.find_one({ '_id': _id })

    async def list_for_user(self, username: str, limit: int = 50):
        cur = self.col.find({ 'username': username }).sort('created_at', -1).limit(limit)
        return [d async for d in cur]
