"""
Password Reset Token Repository
Manages password reset tokens in MongoDB
"""

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from datetime import datetime, timedelta
from typing import Optional
import secrets
import hashlib


class PasswordResetRepo:
    """Repository for password reset tokens"""

    def __init__(self, db: AsyncIOMotorDatabase):
        """
        Initialize repository

        Args:
            db: MongoDB database instance
        """
        self.db = db
        self.collection = db['password_reset_tokens']

    async def create_reset_token(self, username: str, email: str) -> str:
        """
        Create a new password reset token

        Args:
            username: Username requesting reset
            email: User's email address

        Returns:
            str: Reset token (to be sent via email)
        """
        # Generate secure random token
        token = secrets.token_urlsafe(32)  # 32 bytes = 256 bits

        # Hash token for storage (never store plain tokens)
        token_hash = hashlib.sha256(token.encode()).hexdigest()

        # Token expires in 1 hour
        expires_at = datetime.utcnow() + timedelta(hours=1)

        # Store in database
        await self.collection.insert_one({
            'username': username,
            'email': email,
            'token_hash': token_hash,
            'created_at': datetime.utcnow(),
            'expires_at': expires_at,
            'used': False
        })

        # Return plain token (only time it's in plain text)
        return token

    async def validate_token(self, token: str) -> Optional[dict]:
        """
        Validate a reset token

        Args:
            token: Reset token to validate

        Returns:
            dict: Token document if valid, None otherwise
        """
        # Hash provided token
        token_hash = hashlib.sha256(token.encode()).hexdigest()

        # Find token in database
        token_doc = await self.collection.find_one({
            'token_hash': token_hash,
            'used': False,
            'expires_at': {'$gt': datetime.utcnow()}
        })

        return token_doc

    async def mark_token_used(self, token: str):
        """
        Mark a token as used (can't be reused)

        Args:
            token: Reset token to mark as used
        """
        token_hash = hashlib.sha256(token.encode()).hexdigest()

        await self.collection.update_one(
            {'token_hash': token_hash},
            {
                '$set': {
                    'used': True,
                    'used_at': datetime.utcnow()
                }
            }
        )

    async def delete_expired_tokens(self):
        """Delete all expired tokens (cleanup task)"""
        result = await self.collection.delete_many({
            'expires_at': {'$lt': datetime.utcnow()}
        })
        return result.deleted_count

    async def delete_user_tokens(self, username: str):
        """
        Delete all reset tokens for a user

        Args:
            username: Username
        """
        await self.collection.delete_many({'username': username})
