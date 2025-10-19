from pydantic import BaseModel
class ATSecretIn(BaseModel): username:str; password:str
class ATSecretOut(BaseModel): ok: bool
