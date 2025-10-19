import os
from cryptography.fernet import Fernet
MASTER_KEY=os.getenv('MASTER_KEY')
if not MASTER_KEY: raise RuntimeError('MASTER_KEY is not set')
_f=Fernet(MASTER_KEY.encode() if not MASTER_KEY.startswith('gAAAA') else MASTER_KEY)
def encrypt(s:str)->str: return _f.encrypt(s.encode()).decode()
def decrypt(s:str)->str: return _f.decrypt(s.encode()).decode()
