import os, pytest
from fastapi.testclient import TestClient

os.environ.setdefault("APP_ENV","test")
os.environ.setdefault("SECRET_KEY","test_secret")
os.environ.setdefault("MASTER_KEY","gAAAAABkTestKeyNotReal1234567890abcdefghi==")
os.environ.setdefault("MONGO_URI","mongodb://mongo:27017")
os.environ.setdefault("MONGO_DB","saft_doctor_test")
os.environ.setdefault("DEFAULT_COUNTRY","pt")

class LocalStorage:
    def __init__(self): self._data = {}
    async def put(self, country, key, data, content_type=None):
        k=f"{country}/{key}"; self._data[k]=data; return k
    async def fetch_to_local(self, country, key):
        import tempfile
        k=key if key.startswith(f"{country}/") else f"{country}/{key}"
        path=tempfile.NamedTemporaryFile(delete=False, suffix='_saft.xml').name
        with open(path,'wb') as f: f.write(self._data[k])
        return path
    async def presign_put(self, country, key, content_type=None, expires=900):
        full=key if key.startswith(f"{country}/") else f"{country}/{key}"
        return { 'url': f'https://example.com/put/{full}', 'headers': {'Content-Type': content_type} if content_type else {}, 'object': full, 'expires_in': expires }
    async def presign_get(self, country, key, expires=900):
        full=key if key.startswith(f"{country}/") else f"{country}/{key}"
        return { 'url': f'https://example.com/get/{full}', 'object': full, 'expires_in': expires }

@pytest.fixture(autouse=True)
def patch_storage(monkeypatch):
    import core.storage as storage_mod
    monkeypatch.setattr(storage_mod, "Storage", LocalStorage)
    yield

@pytest.fixture
def client(monkeypatch):
    import core.auth_repo as repo_mod
    users={}
    class FakeRepo(repo_mod.UsersRepo):
        def __init__(self, db=None, country:str='pt'): self.users=users; self.country=country
        async def exists(self, u): return u in self.users
        async def create(self, u, h): self.users[u]={'username':u,'password_hash':h,'at':None,'_id':'1'}; return {'_id':'1','username':u}
        async def get(self, u): return self.users.get(u)
        async def save_encrypted_at_credentials(self, u, eu, ep): self.users[u]['at']={'user':eu,'pass':ep}; return True
    monkeypatch.setattr(repo_mod, "UsersRepo", FakeRepo)

    import core.security as sec
    monkeypatch.setattr(sec, "encrypt", lambda s: "enc:"+s)
    monkeypatch.setattr(sec, "decrypt", lambda s: s.split("enc:")[1])

    from services.main_clean import app
    return TestClient(app)
