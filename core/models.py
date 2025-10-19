from pydantic import BaseModel
from typing import Optional, Dict

class ATSecretIn(BaseModel): username:str; password:str
class ATSecretOut(BaseModel): ok: bool

class PresignUploadIn(BaseModel):
	filename: str
	content_type: Optional[str] = None

class PresignUploadOut(BaseModel):
	url: str
	headers: Dict[str, str]
	object: str
	expires_in: int

class PresignDownloadIn(BaseModel):
	object_key: str

class PresignDownloadOut(BaseModel):
	url: str
	object: str
	expires_in: int
