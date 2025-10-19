from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Request
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
import os
from core.deps import get_db
USER_NOT_FOUND = "User not found"
from core.auth_repo import UsersRepo
from core.security import encrypt, decrypt
from core.models import ATSecretIn, ATSecretOut, PresignUploadIn, PresignUploadOut, PresignDownloadIn, PresignDownloadOut, ATEntryIn, ATEntryOut, ATEntryListOut
from core.storage import Storage
from core.submitter import Submitter
from core.analysis_repo import AnalysisRepo
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
USER_NOT_FOUND = "User not found"


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
        raise HTTPException(status_code=401, detail=USER_NOT_FOUND)
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
        return {"ok": out.returncode==0, "returncode": out.returncode, "stdout": stdout[:1000], "stderr": stderr[:1000], "preview": preview}
    except subprocess.TimeoutExpired:
        return {"ok": False, "error": "Timeout while invoking jar", "returncode": None}


@router.get("/java/version")
def java_version():
    try:
        out = subprocess.run(['java','-version'], capture_output=True, text=True, timeout=5)
        # java -version writes to stderr typically
        stdout = (out.stdout or '').strip()
        stderr = (out.stderr or '').strip()
        return { 'ok': out.returncode==0, 'stdout': stdout, 'stderr': stderr, 'returncode': out.returncode }
    except FileNotFoundError:
        return { 'ok': False, 'error': 'java executable not found on PATH' }
    except subprocess.TimeoutExpired:
        return { 'ok': False, 'error': 'Timeout while checking java -version' }


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


@router.post('/secrets/at/entries', response_model=ATSecretOut)
async def upsert_at_entry(
    entry: ATEntryIn,
    request: Request,
    current=Depends(get_current_user),
    db=Depends(get_db),
):
    """Save or update a credential entry keyed by ident (e.g., NIF)."""
    if not entry.ident or not entry.password:
        raise HTTPException(status_code=400, detail='ident and password are required')
    country = get_country(request)
    repo = UsersRepo(db, country)
    await repo.upsert_at_entry(current['username'], encrypt(entry.ident), encrypt(entry.password))
    return ATSecretOut(ok=True)


@router.get('/secrets/at/entries', response_model=ATEntryListOut)
async def list_at_entries(
    request: Request,
    current=Depends(get_current_user),
    db=Depends(get_db),
):
    """List credential entries (ident masked) for the current user."""
    country = get_country(request)
    repo = UsersRepo(db, country)
    entries = await repo.get_at_entries(current['username'])
    items = []
    for enc_ident, meta in entries.items():
        ident = None
        try:
            ident = decrypt(enc_ident)
        except Exception:
            pass
        if not ident:
            continue
        masked = (ident[0] + '***') if len(ident) <= 5 else (ident[:3] + '****' + ident[-2:])
        updated_val = meta.get('updated_at') if isinstance(meta, dict) else None
        updated_str = None
        if hasattr(updated_val, 'isoformat'):
            try:
                updated_str = updated_val.isoformat()
            except Exception:
                updated_str = None
        elif isinstance(updated_val, str):
            updated_str = updated_val
        items.append(ATEntryOut(ident=masked, updated_at=updated_str))
    return ATEntryListOut(ok=True, items=items)


async def _select_at_password(repo: UsersRepo, username: str, nif: str) -> str | None:
    """Select the AT password for given nif from at_entries; fallback to legacy single 'at'."""
    from core.security import decrypt
    u = await repo.get(username)
    if not u:
        return None
    # Try multi-entry first
    try:
        entries = await repo.get_at_entries(username)
        for enc_ident, meta in entries.items():
            try:
                ident_plain = decrypt(enc_ident)
            except Exception:
                ident_plain = None
            if ident_plain and ident_plain == nif:
                try:
                    return decrypt(meta.get('pass')) if meta and meta.get('pass') else None
                except Exception:
                    return None
    except Exception:
        pass
    # Fallback
    try:
        if u.get('at') and u['at'].get('pass'):
            return decrypt(u['at']['pass'])
    except Exception:
        return None
    return None


@router.get('/secrets/at/status')
async def at_secret_status(request: Request, current=Depends(get_current_user), db=Depends(get_db)):
    country = get_country(request)
    repo = UsersRepo(db, country)
    u = await repo.get(current["username"])
    at = u.get('at') if u else None
    if not at:
        return { 'ok': False, 'has_credentials': False }
    # Mask username (first 3 chars + **** + last 2 if available)
    try:
        from core.security import decrypt
        user = decrypt(at['user']) if at.get('user') else None
    except Exception:
        user = None
    masked = None
    if user:
        if len(user) <= 5:
            masked = user[0] + '***'
        else:
            masked = user[:3] + '****' + user[-2:]
    return {
        'ok': True,
        'has_credentials': True,
        'username_masked': masked,
        'updated_at': at.get('updated_at')
    }


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


@router.post('/analyze')
async def analyze_file(
    request: Request,
    file: UploadFile = File(...),
    current=Depends(get_current_user),
    db=Depends(get_db),
):
    """Analyze an uploaded SAFT XML, persist the issues, and save correct files to storage.

    - Parses XML safely. If invalid, status='invalid-xml'.
    - Runs basic validation; status='ok' if no errors, else 'errors'.
    - If status='ok', saves file to B2 and records object_key.
    - Persists a record in the analyses repository and returns it.
    """
    country = get_country(request)
    repo = AnalysisRepo(db, country)
    from core.saft_validator import parse_xml, validate_saft
    data = await file.read()
    issues = []
    summary = {}
    status = 'ok'
    try:
        root = parse_xml(data)
        issues, summary = validate_saft(root)
        status = 'ok' if not any(i.get('level') == 'error' for i in issues) else 'errors'
    except Exception as e:
        status = 'invalid-xml'
        issues = [{ 'level': 'error', 'code': 'XML_INVALID', 'message': str(e), 'path': '/' }]

    object_key = None
    if status == 'ok':
        storage = Storage()
        object_key = await storage.put(country, file.filename, data, content_type=file.content_type)

    record = await repo.create(
        current['username'],
        {
            'filename': file.filename,
            'content_type': file.content_type,
            'status': status,
            'issues': issues,
            'summary': summary,
            'object_key': object_key,
            'country': country,
        }
    )
    # Convert ObjectId for response if needed
    record['_id'] = str(record['_id'])
    return record


@router.get('/analyses')
async def list_analyses(
    request: Request,
    current=Depends(get_current_user),
    db=Depends(get_db),
):
    country = get_country(request)
    repo = AnalysisRepo(db, country)
    items = await repo.list_for_user(current['username'])
    for it in items:
        it['_id'] = str(it['_id'])
    return { 'items': items }


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

    # Get AT password for this ident (prefer multi-entry by ident=NIF; fallback to legacy single 'at')
    country = get_country(request)
    repo = UsersRepo(db, country)
    u = await repo.get(current["username"])
    if not u:
        raise HTTPException(status_code=401, detail=USER_NOT_FOUND)
    selected_pass = await _select_at_password(repo, current['username'], nif)
    if not selected_pass:
        raise HTTPException(status_code=400, detail="AT password not found for this NIF. Save it in Credenciais (ident=NIF).")

    # Build command
    jar_path = _jar_path()
    if not os.path.isfile(jar_path):
        raise HTTPException(status_code=400, detail=f"FACTEMICLI.jar not found at {jar_path}")
    # Some tools expect @ before the path to indicate file input; keep close to provided spec
    input_arg = '@' + saft_path
    cmd = ['java','-jar',jar_path,'-n',nif,'-p',selected_pass,'-a',year,'-m',month,'-op','enviar','-i',input_arg]

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
        # Prepare masked command for diagnostics
        safe_cmd = list(cmd)
        try:
            for i, part in enumerate(safe_cmd):
                if part == selected_pass:
                    safe_cmd[i] = '***'
        except Exception:
            pass
        return {
            'ok': ok,
            'returncode': proc.returncode,
            'output': preview,
            'stdout': (stdout.decode() if stdout else '')[:4000],
            'stderr': (stderr.decode() if stderr else '')[:4000],
            'args': {'nif':nif,'year':year,'month':month},
            'cmd': safe_cmd if os.getenv('EXPOSE_CMD','0')=='1' else None
        }
    except HTTPException:
        raise
    except Exception as e:
        etype = e.__class__.__name__
        msg = str(e)
        hint = None
        if etype == 'FileNotFoundError':
            hint = "java executable not found on PATH or JAR path invalid"
        detail = f"Failed to invoke JAR: {etype}: {msg}"
        if hint:
            detail += f" (hint: {hint})"
        raise HTTPException(status_code=500, detail=detail)


@router.post("/submit")
async def submit(
    request: Request, object_key: str, current=Depends(get_current_user), db=Depends(get_db)
):
    """Submit a previously uploaded SAFT using FACTEMICLI.jar, selecting password by NIF from XML.

    - Fetches the object to local disk
    - Parses XML to extract NIF/year/month
    - Looks up matching AT password in at_entries by ident=NIF; falls back to legacy single 'at'
    - Invokes the JAR and returns diagnostics (masked command, stdout/stderr)
    """
    from core.saft_validator import parse_xml, extract_cli_params
    from core.security import decrypt
    country = get_country(request)
    storage = Storage()
    local_path = await storage.fetch_to_local(country, object_key)
    # Parse XML to get NIF
    try:
        data = await asyncio.to_thread(Path(local_path).read_bytes)
        root = parse_xml(data)
        params = extract_cli_params(root)
        nif = params.get('nif'); year = params.get('year'); month = params.get('month')
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid XML: {str(e)}")
    if not (nif and year and month):
        raise HTTPException(status_code=400, detail="Missing nif/year/month in XML")

    repo = UsersRepo(db, country)
    u = await repo.get(current["username"])
    if not u:
        raise HTTPException(status_code=401, detail=USER_NOT_FOUND)
    selected_pass = await _select_at_password(repo, current['username'], nif)
    if not selected_pass:
        raise HTTPException(status_code=400, detail=f"AT password not found for NIF {nif}. Save it under Credenciais.")

    # Build command similar to validate-jar
    jar_path = _jar_path()
    if not os.path.isfile(jar_path):
        raise HTTPException(status_code=400, detail=f"FACTEMICLI.jar not found at {jar_path}")
    input_arg = '@' + local_path
    cmd = ['java','-jar',jar_path,'-n',nif,'-p',selected_pass,'-a',year,'-m',month,'-op','enviar','-i',input_arg]
    try:
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        try:
            stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=60)
        except asyncio.TimeoutError:
            proc.kill()
            raise HTTPException(status_code=504, detail="Submission timed out")
        out_text = (stdout.decode() if stdout else '') + (('\n' + stderr.decode()) if stderr else '')
        ok = (proc.returncode == 0)
        safe_cmd = list(cmd)
        try:
            for i, part in enumerate(safe_cmd):
                if part == selected_pass:
                    safe_cmd[i] = '***'
        except Exception:
            pass
        if not ok:
            raise HTTPException(status_code=502, detail={
                'message': 'Submission failed',
                'returncode': proc.returncode,
                'stdout': (stdout.decode() if stdout else '')[:4000],
                'stderr': (stderr.decode() if stderr else '')[:4000],
                'cmd': safe_cmd if os.getenv('EXPOSE_CMD','0')=='1' else None,
                'args': {'nif':nif,'year':year,'month':month}
            })
        return { 'ok': True, 'output': out_text[:4000], 'returncode': proc.returncode, 'args': {'nif':nif,'year':year,'month':month}, 'cmd': safe_cmd if os.getenv('EXPOSE_CMD','0')=='1' else None }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to invoke JAR: {e.__class__.__name__}: {str(e)}")
