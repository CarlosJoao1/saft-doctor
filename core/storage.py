import os,tempfile,boto3
from botocore.config import Config

class Storage:
    def __init__(self):
        self.endpoint = os.getenv('B2_ENDPOINT')
        self.region = os.getenv('B2_REGION')
        self.bucket = os.getenv('B2_BUCKET')
        # Use path-style addressing for better browser compatibility with CORS/presigned URLs
        self.client = boto3.client(
            's3',
            endpoint_url=self.endpoint,
            region_name=self.region,
            aws_access_key_id=os.getenv('B2_KEY_ID'),
            aws_secret_access_key=os.getenv('B2_APP_KEY'),
            config=Config(s3={'addressing_style': 'path'})
        )
    async def put(self,country,key,data,content_type=None):
        full=f"{country}/{key}" if not key.startswith(f"{country}/") else key
        extra={'ContentType':content_type} if content_type else {}
        self.client.put_object(Bucket=self.bucket,Key=full,Body=data,**extra); return full
    async def fetch_to_local(self,country,key):
        full=key if key.startswith(f"{country}/") else f"{country}/{key}"
        tmp=tempfile.NamedTemporaryFile(delete=False,suffix='_saft.xml'); self.client.download_file(self.bucket,full,tmp.name); return tmp.name

    async def presign_put(self, country, key, content_type=None, expires=900):
        """Generate a pre-signed URL for uploading via HTTP PUT."""
        full = key if key.startswith(f"{country}/") else f"{country}/{key}"
        params = { 'Bucket': self.bucket, 'Key': full }
        if content_type:
            params['ContentType'] = content_type
        url = self.client.generate_presigned_url('put_object', Params=params, ExpiresIn=expires)
        headers = { 'Content-Type': content_type } if content_type else {}
        return { 'url': url, 'headers': headers, 'object': full, 'expires_in': expires }

    async def presign_get(self, country, key, expires=900):
        """Generate a pre-signed URL for downloading via HTTP GET."""
        full = key if key.startswith(f"{country}/") else f"{country}/{key}"
        url = self.client.generate_presigned_url('get_object', Params={ 'Bucket': self.bucket, 'Key': full }, ExpiresIn=expires)
        return { 'url': url, 'object': full, 'expires_in': expires }
