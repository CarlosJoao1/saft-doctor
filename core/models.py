from pydantic import BaseModel
from typing import Optional, Dict, List

class ATSecretIn(BaseModel): username:str; password:str
class ATSecretOut(BaseModel): ok: bool

# Password Reset Models
class PasswordResetRequestIn(BaseModel):
	username: str

class PasswordResetRequestOut(BaseModel):
	ok: bool
	message: str

class PasswordResetConfirmIn(BaseModel):
	token: str
	new_password: str

class PasswordResetConfirmOut(BaseModel):
	ok: bool
	message: str

class ATEntryIn(BaseModel):
	ident: str  # e.g., NIF
	password: str

class ATEntryOut(BaseModel):
	ident: str
	password: Optional[str] = None
	updated_at: Optional[str] = None

class ATEntryListOut(BaseModel):
	ok: bool
	items: List[ATEntryOut]

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
