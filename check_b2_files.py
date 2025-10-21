#!/usr/bin/env python3
from core.storage import Storage

storage = Storage()
response = storage.client.list_objects(
    Bucket=storage.bucket, 
    Prefix='pt/saft-archives/501789227/2025/09/', 
    MaxKeys=10
)
contents = response.get('Contents', [])
print(f'Files found in B2: {len(contents)}')
for obj in contents:
    size_mb = obj['Size'] / 1024 / 1024
    print(f'  ✅ {obj["Key"]} ({size_mb:.2f} MB)')
