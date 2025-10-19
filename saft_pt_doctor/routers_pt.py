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
from pathlib import Path
import asyncio
try:
    from botocore.exceptions import ClientError  # type: ignore
except Exception:  # pragma: no cover
    class ClientError(Exception):
        pass

router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token")
SECRET_KEY = os.getenv("SECRET_KEY", "change_me")
ALGORITHM = "HS256"


def get_country(request: Request) -> str:
    # In future, derive from path/headers; reference request to satisfy linters
    _ = request
    return "pt"


def _jar_path() -> str:
    # Centralize JAR path resolution to avoid duplicated literals
    return os.getenv('FACTEMICLI_JAR_PATH', '/opt/factemi/FACTEMICLI.jar')


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
    path=_jar_path()
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
    path=_jar_path()
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


@router.post("/jar/install")
async def jar_install(
    body: PresignDownloadIn, request: Request, current=Depends(get_current_user)
):
    """Download the JAR from Backblaze (S3-compatible) into FACTEMICLI_JAR_PATH.

    Provide the B2 object key (with or without the country prefix). Example:
    { "object_key": "pt/tools/FACTEMICLI.jar" }
    """
    country = get_country(request)
    storage = Storage()
    # Normalize object key to include country prefix
    full = body.object_key if body.object_key.startswith(f"{country}/") else f"{country}/{body.object_key}"

    # Ensure target directory exists
    target_path = _jar_path()
    Path(os.path.dirname(target_path)).mkdir(parents=True, exist_ok=True)

    # Download from bucket to target path
    try:
        storage.client.download_file(storage.bucket, full, target_path)
    except ClientError as e:
        code = (e.response.get('Error', {}).get('Code') if hasattr(e, 'response') else None) or 'ClientError'
        # Map common S3 error codes
        if code in ('NoSuchKey', '404'):
            raise HTTPException(status_code=404, detail=f"Object not found: {full}")
        if code in ('AccessDenied', '403'):
            raise HTTPException(status_code=403, detail=f"Access denied downloading {full}. Check B2 key permissions (readFiles / s3:GetObject) and bucket policy.")
        raise HTTPException(status_code=502, detail=f"Storage error ({code}) while downloading {full}.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error while downloading {full}: {str(e)}")

    size = None
    try:
        size = os.path.getsize(target_path)
    except Exception:
        pass
    return {"ok": True, "path": target_path, "size": size, "object": full}


@router.post("/validate-jar")
async def validate_with_jar(
    request: Request,
    file: UploadFile = File(...),
    current=Depends(get_current_user),
    db=Depends(get_db),
):
    """Validate a SAFT XML by invoking FACTEMICLI.jar with CLI params extracted from XML.

    Extracts: NIF (TaxRegistrationNumber), FiscalYear, and month from StartDate.
    Uses the user's stored AT password. Requires that FACTEMICLI.jar is installed.
    """
    from core.saft_validator import parse_xml, extract_cli_params
    from core.security import decrypt
    import tempfile

    # Prepare local temp file (perform sync I/O in a worker thread to keep endpoint responsive)
    data = await file.read()
    def _write_tmp(payload: bytes) -> str:
        with tempfile.NamedTemporaryFile(delete=False, suffix='.xml') as tmp:
            tmp.write(payload)
            return tmp.name
    saft_path = await asyncio.to_thread(_write_tmp, data)

    # Extract params from XML
    try:
        root = parse_xml(data)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid XML: {str(e)}")
    params = extract_cli_params(root)
    nif = params.get('nif'); year = params.get('year'); month = params.get('month')
    missing = [k for k in ['nif','year','month'] if not params.get(k)]
    if missing:
        raise HTTPException(status_code=400, detail=f"Missing fields in XML for CLI: {', '.join(missing)}")

    # Get AT password
    country = get_country(request)
    repo = UsersRepo(db, country)
    u = await repo.get(current["username"])
    if not u or not u.get("at"):
        raise HTTPException(status_code=400, detail="AT credentials not set")
    at_pass = decrypt(u["at"]["pass"])

    # Build command
    jar_path = _jar_path()
    if not os.path.isfile(jar_path):
        raise HTTPException(status_code=400, detail=f"FACTEMICLI.jar not found at {jar_path}")
    # Some tools expect @ before the path to indicate file input; keep close to provided spec
    input_arg = '@' + saft_path
    cmd = ['java','-jar',jar_path,'-n',nif,'-p',at_pass,'-a',year,'-m',month,'-op','enviar','-i',input_arg]

    try:
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        try:
            stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=30)
        except asyncio.TimeoutError:
            proc.kill()
            raise HTTPException(status_code=504, detail="Validation timed out")
        out_text = (stdout.decode() if stdout else '') + (('\n' + stderr.decode()) if stderr else '')
        ok = (proc.returncode == 0)
        preview = out_text[:4000]
        return { 'ok': ok, 'returncode': proc.returncode, 'output': preview, 'args': {'nif':nif,'year':year,'month':month} }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to invoke JAR: {str(e)}")


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
