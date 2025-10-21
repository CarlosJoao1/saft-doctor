"""
Validation History Repository - MongoDB collection for tracking SAFT validation history
Stores validation records with JAR output, statistics, and Backblaze storage links
"""
from datetime import datetime
from typing import Optional, Dict, Any, List
from motor.motor_asyncio import AsyncIOMotorDatabase


class ValidationHistoryRepo:
    """Repository for validation_history collection"""
    
    def __init__(self, db: AsyncIOMotorDatabase, country: str = 'pt'):
        self.db = db
        self.country = country
        self.collection = db['validation_history']
    
    async def create_indexes(self):
        """Create indexes for efficient queries"""
        await self.collection.create_index([('username', 1), ('validated_at', -1)])
        await self.collection.create_index([('nif', 1), ('year', 1), ('month', 1)])
        await self.collection.create_index('validated_at')
    
    async def save_validation(
        self,
        username: str,
        nif: str,
        year: str,
        month: str,
        operation: str,  # 'validar' or 'enviar'
        jar_stdout: str,
        jar_stderr: str,
        returncode: int,
        file_info: Dict[str, Any],
        statistics: Optional[Dict[str, Any]] = None,
        response_xml: Optional[str] = None,
        storage_key: Optional[str] = None,
        extra_data: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Save a validation record to the database
        
        Args:
            username: User who performed validation
            nif: Tax ID from the SAFT file
            year: Fiscal year
            month: Fiscal month
            operation: 'validar' or 'enviar'
            jar_stdout: Complete stdout from FACTEMICLI.jar
            jar_stderr: Complete stderr from FACTEMICLI.jar
            returncode: JAR process return code
            file_info: Dict with 'name', 'size', 'original_filename'
            statistics: Parsed statistics (totalFaturas, totalCreditos, totalDebitos)
            response_xml: Response XML from JAR (if available)
            storage_key: B2 object key where ZIP is stored
            extra_data: Any additional metadata
        
        Returns:
            Inserted document ID as string
        """
        doc = {
            'username': username,
            'country': self.country,
            'nif': nif,
            'year': year,
            'month': month,
            'operation': operation,
            'validated_at': datetime.utcnow(),
            'jar_output': {
                'stdout': jar_stdout,
                'stderr': jar_stderr,
                'returncode': returncode
            },
            'file_info': file_info,
            'statistics': statistics or {},
            'response_xml': response_xml,
            'storage_key': storage_key,
            'success': returncode == 0 and (statistics or {}).get('response_code') == '200',
            'extra_data': extra_data or {}
        }
        
        result = await self.collection.insert_one(doc)
        return str(result.inserted_id)
    
    async def get_user_history(
        self,
        username: str,
        nif: Optional[str] = None,
        year: Optional[str] = None,
        month: Optional[str] = None,
        operation: Optional[str] = None,
        limit: int = 50,
        skip: int = 0
    ) -> List[Dict[str, Any]]:
        """
        Get validation history for a user with optional filters
        
        Args:
            username: User to get history for
            nif: Filter by NIF (optional)
            year: Filter by year (optional)
            month: Filter by month (optional)
            operation: Filter by operation type (optional)
            limit: Max number of results
            skip: Number of results to skip (pagination)
        
        Returns:
            List of validation records
        """
        query = {'username': username, 'country': self.country}
        
        if nif:
            query['nif'] = nif
        if year:
            query['year'] = year
        if month:
            query['month'] = month
        if operation:
            query['operation'] = operation
        
        cursor = self.collection.find(query).sort('validated_at', -1).skip(skip).limit(limit)
        results = await cursor.to_list(length=limit)
        
        # Convert ObjectId to string
        for doc in results:
            doc['_id'] = str(doc['_id'])
        
        return results
    
    async def get_by_id(self, validation_id: str) -> Optional[Dict[str, Any]]:
        """Get a single validation record by ID"""
        from bson import ObjectId
        doc = await self.collection.find_one({'_id': ObjectId(validation_id)})
        if doc:
            doc['_id'] = str(doc['_id'])
        return doc
    
    async def count_user_validations(
        self,
        username: str,
        nif: Optional[str] = None,
        year: Optional[str] = None,
        month: Optional[str] = None
    ) -> int:
        """Count validation records for a user"""
        query = {'username': username, 'country': self.country}
        if nif:
            query['nif'] = nif
        if year:
            query['year'] = year
        if month:
            query['month'] = month
        
        return await self.collection.count_documents(query)
    
    async def get_latest_for_period(
        self,
        username: str,
        nif: str,
        year: str,
        month: str
    ) -> Optional[Dict[str, Any]]:
        """Get the most recent validation for a specific NIF/year/month"""
        doc = await self.collection.find_one(
            {
                'username': username,
                'country': self.country,
                'nif': nif,
                'year': year,
                'month': month
            },
            sort=[('validated_at', -1)]
        )
        if doc:
            doc['_id'] = str(doc['_id'])
        return doc
