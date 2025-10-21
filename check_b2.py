#!/usr/bin/env python3
"""Check Backblaze B2 for archived files"""
from core.storage import Storage

storage = Storage()
try:
    # List objects with prefix pt/saft-archives/
    response = storage.client.list_objects(
        Bucket=storage.bucket, 
        Prefix='pt/saft-archives/', 
        MaxKeys=10
    )
    contents = response.get('Contents', [])
    print(f'Objects found: {len(contents)}')
    for obj in contents:
        print(f'  - {obj["Key"]} ({obj["Size"]} bytes)')
except Exception as e:
    print(f'Error: {e}')
    import traceback
    traceback.print_exc()
