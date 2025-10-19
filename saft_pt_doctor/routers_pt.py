from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Request
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
import os
from core.deps import get_db
from core.auth_repo import UsersRepo
from core.security import encrypt, decrypt
from core.models import ATSecretIn, ATSecretOut, PresignUploadIn, PresignUploadOut, PresignDownloadIn, PresignDownloadOut
from core.storage import Storage
from core.submitter import Submitter
import os
import os.path
import subprocess

router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token")
SECRET_KEY = os.getenv("SECRET_KEY", "change_me")
ALGORITHM = "HS256"


def get_country(request: Request) -> str:
    # In future, derive from path/headers; reference request to satisfy linters
    _ = request
    return "pt"


async def get_current_user(
    request: Request, token: str = Depends(oauth2_scheme), db=Depends(get_db)
):
    country = get_country(request)
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")
        if not username:
            raise HTTPException(status_code=401, detail="Invalid token")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")
    repo = UsersRepo(db, country)
    u = await repo.get(username)
    if not u:
        raise HTTPException(status_code=401, detail="User not found")
    return {"username": username, "country": country}


@router.get("/health")
def health_pt():
    return {"status": "ok", "country": "pt"}


@router.get("/jar/status")
def jar_status():
    path=os.getenv('FACTEMICLI_JAR_PATH','/opt/factemi/FACTEMICLI.jar')
    exists=os.path.isfile(path)
    size=None
    if exists:
        try:
            size=os.path.getsize(path)
        except Exception:
            size=None
    return {"ok": exists, "path": path, "size": size}


@router.get("/jar/run-check")
def jar_run_check():
    path=os.getenv('FACTEMICLI_JAR_PATH','/opt/factemi/FACTEMICLI.jar')
    if not os.path.isfile(path):
        return {"ok": False, "error": f"FACTEMICLI.jar not found at {path}", "path": path}
    try:
        # Run a quick invocation; many jars print usage without args
        out=subprocess.run(['java','-jar',path], capture_output=True, text=True, timeout=5)
        stdout=(out.stdout or '').strip()
        stderr=(out.stderr or '').strip()
        preview=(stdout or stderr)[:2000]
        return {"ok": out.returncode==0, "returncode": out.returncode, "preview": preview}
    except subprocess.TimeoutExpired:
        return {"ok": False, "error": "Timeout while invoking jar", "returncode": None}


@router.post("/secrets/at", response_model=ATSecretOut)
async def save_at_secret(
    secret: ATSecretIn,
    request: Request,
    current=Depends(get_current_user),
    db=Depends(get_db),
):
    country = get_country(request)
    repo = UsersRepo(db, country)
    await repo.save_encrypted_at_credentials(
        current["username"], encrypt(secret.username), encrypt(secret.password)
    )
    return ATSecretOut(ok=True)


@router.post("/files/upload")
async def upload_file(
    request: Request, file: UploadFile = File(...), current=Depends(get_current_user)
):
    country = get_country(request)
    storage = Storage()
    key = await storage.put(
        country, file.filename, await file.read(), content_type=file.content_type
    )
    return {"ok": True, "object": key}


@router.post("/files/presign-upload", response_model=PresignUploadOut)
async def presign_upload(
    body: PresignUploadIn, request: Request, current=Depends(get_current_user)
):
    country = get_country(request)
    storage = Storage()
    out = await storage.presign_put(country, body.filename, content_type=body.content_type)
    return out


@router.post("/files/presign-download", response_model=PresignDownloadOut)
async def presign_download(
    body: PresignDownloadIn, request: Request, current=Depends(get_current_user)
):
    country = get_country(request)
    storage = Storage()
    out = await storage.presign_get(country, body.object_key)
    return out


@router.post("/submit")
async def submit(
    request: Request, object_key: str, current=Depends(get_current_user), db=Depends(get_db)
):
    country = get_country(request)
    storage = Storage()
    local_path = await storage.fetch_to_local(country, object_key)
    repo = UsersRepo(db, country)
    u = await repo.get(current["username"])
    if not u or not u.get("at"):
        raise HTTPException(status_code=400, detail="AT credentials not set")
    at_user = decrypt(u["at"]["user"])
    at_pass = decrypt(u["at"]["pass"])
    ok, out = Submitter().submit(local_path, at_user, at_pass)
    if not ok:
        raise HTTPException(status_code=502, detail=out)
    return {"ok": True, "output": out}
