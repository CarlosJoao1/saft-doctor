from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Request
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from typing import Optional
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
import uuid
import json
try:
    from botocore.exceptions import ClientError  # type: ignore
except Exception:  # pragma: no cover
    class ClientError(Exception):
        pass

router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token")
SECRET_KEY = (os.getenv("SECRET_KEY", "change_me") or "change_me").strip()
ALGORITHM = "HS256"
USER_NOT_FOUND = "User not found"
UPLOAD_ROOT = os.getenv('UPLOAD_ROOT', '/var/saft/uploads')
DEFAULT_CHUNK_SIZE = int(os.getenv('UPLOAD_CHUNK_SIZE', str(5*1024*1024)))  # 5MB


def get_country(request: Request) -> str:
    # In future, derive from path/headers; reference request to satisfy linters
    _ = request
    return "pt"


def _jar_path() -> str:
    # Centralize JAR path resolution to avoid duplicated literals
    return os.getenv('FACTEMICLI_JAR_PATH', '/opt/factemi/FACTEMICLI.jar')

def _ensure_upload_root():
    """Create UPLOAD_ROOT if missing and log to stdout for Render visibility."""
    try:
        os.makedirs(UPLOAD_ROOT, mode=0o755, exist_ok=True)
        print(f"[UPLOAD] Diretório garantido: {UPLOAD_ROOT}")
    except Exception as e:
        print(f"[UPLOAD] ERRO ao criar {UPLOAD_ROOT}: {e}")
        raise

def _upload_paths(upload_id: str):
    _ensure_upload_root()
    base = os.path.join(UPLOAD_ROOT, upload_id)
    return base + '.meta', base + '.bin'


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


# --------------------------- Chunked Upload API ----------------------------
@router.post('/upload/start')
async def upload_start(request: Request, current=Depends(get_current_user)):
    body = await request.json()
    filename = body.get('filename') or 'upload.bin'
    size = int(body.get('size') or 0)
    upload_id = uuid.uuid4().hex
    meta_path, bin_path = _upload_paths(upload_id)
    print(f"[UPLOAD] START upload_id={upload_id}, filename={filename}, size={size}")
    # prepare file using asyncio.to_thread for I/O
    def _create_files():
        with open(bin_path, 'wb') as f:
            if size > 0:
                f.truncate(size)
        with open(meta_path, 'w', encoding='utf-8') as f:
            json.dump({'upload_id': upload_id, 'filename': filename, 'size': size, 'bin_path': bin_path}, f)
    try:
        await asyncio.to_thread(_create_files)
    except Exception as e:
        print(f"[UPLOAD] ERRO ao preparar upload: {e}")
        raise HTTPException(status_code=500, detail=f'Failed to prepare upload: {e}')
    return { 'ok': True, 'upload_id': upload_id, 'chunk_size': DEFAULT_CHUNK_SIZE }


@router.put('/upload/chunk')
async def upload_chunk(request: Request, upload_id: str, index: int = 0, offset: int | None = None, current=Depends(get_current_user)):
    meta_path, bin_path = _upload_paths(upload_id)
    if not os.path.isfile(meta_path) or not os.path.isfile(bin_path):
        raise HTTPException(status_code=404, detail='upload_id not found')
    if offset is None:
        offset = index * DEFAULT_CHUNK_SIZE
    data = await request.body()
    print(f"[UPLOAD] CHUNK {index} → offset={offset}, bytes={len(data)}")
    def _write_chunk():
        with open(bin_path, 'r+b') as f:
            f.seek(offset)
            f.write(data)
    try:
        await asyncio.to_thread(_write_chunk)
    except Exception as e:
        print(f"[UPLOAD] ERRO no chunk {index}: {e}")
        raise HTTPException(status_code=500, detail=f'Failed to write chunk: {e}')
    return { 'ok': True, 'bytes': len(data), 'offset': offset }


@router.post('/upload/finish')
async def upload_finish(request: Request, current=Depends(get_current_user)):
    body = await request.json()
    upload_id = body.get('upload_id')
    if not upload_id:
        raise HTTPException(status_code=400, detail='upload_id required')
    meta_path, bin_path = _upload_paths(upload_id)
    if not os.path.isfile(meta_path) or not os.path.isfile(bin_path):
        raise HTTPException(status_code=404, detail='upload not found')
    print(f"[UPLOAD] FINISH upload_id={upload_id}, path={bin_path}")
    # Just respond OK; use next endpoint to trigger validation on server side
    return { 'ok': True, 'upload_id': upload_id, 'path': bin_path }


@router.post('/validate-jar-by-upload')
async def validate_with_jar_by_upload(
    request: Request,
    upload_id: str,
    current=Depends(get_current_user),
    db=Depends(get_db),
    operation: str = 'validar',
    full: int = 0,
):
    # Locate uploaded file
    meta_path, bin_path = _upload_paths(upload_id)
    if not os.path.isfile(meta_path) or not os.path.isfile(bin_path):
        raise HTTPException(status_code=404, detail='upload not found')
    print(f"[VALIDATE] upload_id={upload_id}, operation={operation}, user={current['username']}")
    # Reuse existing flow by reading XML and executing JAR (similar to by_key)
    from core.saft_validator import parse_xml, extract_cli_params
    try:
        data = await asyncio.to_thread(lambda: open(bin_path, 'rb').read())
    except Exception as e:
        print(f"[VALIDATE] ERRO ao ler ficheiro: {e}")
        raise HTTPException(status_code=500, detail=f'Failed to read upload: {e}')
    try:
        root = parse_xml(data)
    except Exception as e:
        return { 'ok': False, 'error': f'Invalid XML: {e}', 'jar_path': _jar_path() }
    params = extract_cli_params(root)
    nif = params.get('nif'); year = params.get('year'); month = params.get('month')
    missing = [k for k in ['nif','year','month'] if not params.get(k)]
    if missing:
        return { 'ok': False, 'error': f"Missing fields in XML for CLI: {', '.join(missing)}" }
    # Delegate to validate_with_jar_by_key-like local execution
    # For brevity and to avoid duplication, call into the by_key implementation by mocking saft_path
    # But here we inline minimal subset
    country = get_country(request)
    repo = UsersRepo(db, country)
    u = await repo.get(current['username'])
    if not u:
        raise HTTPException(status_code=401, detail=USER_NOT_FOUND)
    selected_pass = await _select_at_password(repo, current['username'], nif)
    if not selected_pass and operation == 'enviar':
        return { 'ok': False, 'error': f'Operation "enviar" requires AT password for NIF {nif}. Save it first.' }

    # Build and run command (same TIMEOUT)
    jar_path = _jar_path()
    op = operation
    if selected_pass:
        cmd = ['java','-jar',jar_path,'-n',nif,'-p',selected_pass,'-a',year,'-m',month,'-op',op,'-i',bin_path]
        safe_cmd = [ ('***' if part==selected_pass else part) for part in cmd ]
    else:
        cmd = ['java','-jar',jar_path,'-op','validar','-i',bin_path]
        safe_cmd = list(cmd)
    TIMEOUT = int(os.getenv('FACTEMICLI_TIMEOUT','300'))
    try:
        proc = await asyncio.create_subprocess_exec(*cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
        try:
            stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=TIMEOUT)
        except asyncio.TimeoutError:
            proc.kill()
            return { 'ok': False, 'timeout': True, 'cmd_masked': safe_cmd, 'jar_path': jar_path }
        ok = (proc.returncode == 0)
        stdout_str = stdout.decode() if stdout else ''
        stderr_str = stderr.decode() if stderr else ''
        # No archive here to keep response smaller; UI will handle like other endpoints
        limit = 10000 if not full else None
        def trunc(s: str) -> str:
            if s is None: return ''
            if limit is None: return s
            return s if len(s) <= limit else (s[:limit] + '\n... [truncated]')
        return {
            'ok': ok,
            'returncode': proc.returncode,
            'stdout': trunc(stdout_str),
            'stderr': trunc(stderr_str),
            'args': {'nif':nif,'year':year,'month':month},
            'cmd_masked': safe_cmd,
            'jar_path': jar_path
        }
    except Exception as e:
        return { 'ok': False, 'error': f'{e.__class__.__name__}: {e}' }


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
    full: int = 0,  # set to 1 to disable truncation
    operation: str = 'validar',  # operation: 'validar' or 'enviar'
    dry_run: int = 0,  # set to 1 to return command without executing
):
    """Validate or submit a SAFT XML by invoking FACTEMICLI.jar with CLI params extracted from XML.

    Extracts: NIF (TaxRegistrationNumber), FiscalYear, and month from StartDate.
    Uses the user's stored AT password. Requires that FACTEMICLI.jar is installed.
    
    Args:
        file: SAFT XML file
        full: if 1, return full stdout/stderr (no truncation)
        operation: operation to perform - 'validar' (validation only) or 'enviar' (submit to AT)
        dry_run: if 1, return command without executing (preview mode)
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
        return {
            'ok': False,
            'error': f"Invalid XML: {str(e)}",
            'args': None,
            'cmd_masked': None,
            'jar_path': _jar_path(),
            'transcript': { 'error': 'invalid-xml' }
        }
    params = extract_cli_params(root)
    nif = params.get('nif'); year = params.get('year'); month = params.get('month')
    missing = [k for k in ['nif','year','month'] if not params.get(k)]
    if missing:
        return {
            'ok': False,
            'error': f"Missing fields in XML for CLI: {', '.join(missing)}",
            'args': {'nif': nif, 'year': year, 'month': month},
            'cmd_masked': None,
            'jar_path': _jar_path(),
            'transcript': { 'error': 'missing-fields' }
        }

    # Get AT password for this ident (prefer multi-entry by ident=NIF; fallback to legacy single 'at')
    country = get_country(request)
    username = current["username"]
    repo = UsersRepo(db, country)
    u = await repo.get(username)
    if not u:
        raise HTTPException(status_code=401, detail=USER_NOT_FOUND)
    selected_pass = await _select_at_password(repo, current['username'], nif)
    if not selected_pass:
        # Return would-be command with masked password placeholder
        jar_path = _jar_path()
        safe_cmd = ['java','-jar',jar_path,'-n',nif,'-p','***','-a',year,'-m',month,'-op',os.getenv('FACTEMICLI_VALIDATE_OP', 'validar'), os.getenv('FACTEMICLI_VALIDATE_FILE_FLAG', '-i'), saft_path]
        return {
            'ok': False,
            'error': "AT password not found for this NIF. Save it in Credenciais (ident=NIF).",
            'args': {'nif':nif,'year':year,'month':month},
            'cmd_masked': safe_cmd,
            'jar_path': jar_path,
            'transcript': { 'error': 'password-missing' }
        }

    # Build command
    jar_path = _jar_path()
    # Transcript container
    transcript = {
        'cwd': os.getcwd(),
        'jar': {'path': jar_path, 'exists': os.path.isfile(jar_path), 'size': None},
        'file': {'path': saft_path, 'size': None},
        'java_version': None,
        'args': {'nif': nif, 'year': year, 'month': month},
        'op': None,
        'cmd_masked': None,
    }
    try:
        if transcript['jar']['exists']:
            try:
                transcript['jar']['size'] = os.path.getsize(jar_path)
            except Exception:
                pass
        try:
            transcript['file']['size'] = os.path.getsize(saft_path)
        except Exception:
            pass
    except Exception:
        pass
    # Preflight: java -version
    try:
        proc_jv = await asyncio.create_subprocess_exec(
            'java','-version', stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
        )
        try:
            jv_out, jv_err = await asyncio.wait_for(proc_jv.communicate(), timeout=5)
        except asyncio.TimeoutError:
            proc_jv.kill()
            jv_out, jv_err = b'', b'Timeout checking java -version'
            rc = None
        else:
            rc = proc_jv.returncode
        transcript['java_version'] = {
            'returncode': rc,
            'stdout': (jv_out.decode() if jv_out else ''),
            'stderr': (jv_err.decode() if jv_err else ''),
        }
    except Exception as e:
        transcript['java_version'] = { 'error': f'{e.__class__.__name__}: {str(e)}' }
    
    # Use the operation parameter from the request (not environment variable)
    op = operation  # 'validar' or 'enviar'
    file_flag = os.getenv('FACTEMICLI_VALIDATE_FILE_FLAG', '-i')
    transcript['op'] = op

    if not transcript['jar']['exists']:
        # Return would-be command with masked password
        safe_cmd = ['java','-jar',jar_path,'-n',nif,'-p','***','-a',year,'-m',month,'-op',op, file_flag, saft_path]
        return {
            'ok': False,
            'error': 'FACTEMICLI.jar not found',
            'returncode': None,
            'stdout': '',
            'stderr': '',
            'args': transcript['args'],
            'cmd_masked': safe_cmd,
            'jar_path': jar_path,
            'transcript': transcript,
        }
    
    # Build command based on operation type
    # IMPORTANTE: O FACTEMICLI.jar aceita credenciais em ambas as operações
    # e dá output mais detalhado quando as usa, mesmo no 'validar'
    
    # Se temos password, usa comando completo (com credenciais)
    if selected_pass:
        cmd = ['java','-jar',jar_path,'-n',nif,'-p',selected_pass,'-a',year,'-m',month,'-op',op,'-i',saft_path]
        # Mask password
        safe_cmd = list(cmd)
        for i, part in enumerate(safe_cmd):
            if part == selected_pass:
                safe_cmd[i] = '***'
    else:
        # Sem password: usa comando simplificado
        # Para 'validar' funciona, mas dá menos detalhes
        # Para 'enviar' vai falhar (precisa credenciais)
        if op == 'enviar':
            # Enviar SEM password = erro
            safe_cmd = ['java','-jar',jar_path,'-n',nif,'-p','***','-a',year,'-m',month,'-op','enviar','-i',saft_path]
            return {
                'ok': False,
                'error': f'Operation "enviar" requires AT password for NIF {nif}. Save it in Credenciais first.',
                'returncode': None,
                'stdout': '',
                'stderr': '',
                'args': transcript['args'],
                'cmd_masked': safe_cmd,
                'jar_path': jar_path,
                'transcript': transcript,
            }
        # Validar sem password = OK, mas menos detalhes
        cmd = ['java','-jar',jar_path,'-op','validar','-i',saft_path]
        safe_cmd = list(cmd)
    
    transcript['cmd_masked'] = safe_cmd
    
    # If dry_run, return command without executing
    if dry_run:
        return {
            'ok': True,
            'dry_run': True,
            'returncode': None,
            'stdout': '',
            'stderr': '',
            'args': transcript['args'],
            'cmd_masked': safe_cmd,
            'jar_path': jar_path,
            'transcript': transcript,
            'message': f'Dry run - comando "{op}" não foi executado'
        }

    try:
        # Allow configurable timeout for large files/long validations
        TIMEOUT = int(os.getenv('FACTEMICLI_TIMEOUT', '300'))

        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        try:
            stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=TIMEOUT)
        except asyncio.TimeoutError:
            proc.kill()
            # Return a structured timeout result instead of raising, so the UI can show the command
            limit = 10000 if not full else None
            def trunc(s: str) -> str:
                if s is None: return ''
                if limit is None: return s
                return s if len(s) <= limit else (s[:limit] + '\n... [truncated]')
            return {
                'ok': False,
                'error': 'Validation timed out',
                'timeout': True,
                'returncode': None,
                'stdout': '',
                'stderr': '',
                'args': {'nif':nif,'year':year,'month':month},
                'cmd_masked': safe_cmd,
                'cmd': safe_cmd if os.getenv('EXPOSE_CMD','0')=='1' else None,
                'jar_path': jar_path,
                'transcript': transcript
            }
        ok = (proc.returncode == 0)
        
        # Decode outputs
        stdout_str = stdout.decode() if stdout else ''
        stderr_str = stderr.decode() if stderr else ''
        
        # Archive successful validations (compress + upload + save to DB)
        storage_key = None
        validation_id = None
        archive_error = None
        
        print(f"[DEBUG] Checking archiving conditions: ok={ok}, dry_run={dry_run}, returncode={proc.returncode}")
        
        if ok and not dry_run:
            try:
                from core.saft_archiver import (
                    parse_jar_response_xml,
                    is_validation_successful,
                    create_zip_filename,
                    compress_xml_to_zip,
                    generate_storage_key
                )
                from core.validation_history import ValidationHistoryRepo
                from core.storage import Storage
                import tempfile
                
                print(f"[DEBUG] Checking if validation successful...")
                # Check if validation was truly successful (has response code=200)
                is_successful = is_validation_successful(stdout_str, proc.returncode)
                print(f"[DEBUG] is_validation_successful returned: {is_successful}")
                print(f"[DEBUG] stdout_str preview: {stdout_str[:500]}")
                
                if is_successful:
                    # Parse statistics from JAR output
                    print(f"[DEBUG] Validation successful! Parsing stats...")
                    stats = parse_jar_response_xml(stdout_str)
                    print(f"[DEBUG] Parsed stats: {stats}")
                    
                    # Create ZIP filename: [NIF]_[YEAR]_[MONTH]_[DDHHMMSS].zip
                    zip_filename = create_zip_filename(nif, year, month)
                    print(f"[DEBUG] ZIP filename: {zip_filename}")
                    
                    # Compress XML to ZIP in temp directory
                    temp_zip = os.path.join(tempfile.gettempdir(), zip_filename)
                    original_name = file.filename or f'saft_{nif}_{year}_{month}.xml'
                    print(f"[DEBUG] Compressing XML from {saft_path} to {temp_zip}")
                    zip_size = compress_xml_to_zip(saft_path, temp_zip, original_filename=original_name)
                    print(f"[DEBUG] ZIP created, size: {zip_size} bytes")
                    
                    # Upload ZIP to Backblaze
                    storage_key = generate_storage_key(nif, year, month, zip_filename, country=country)
                    print(f"[DEBUG] Uploading to B2 with key: {storage_key}")
                    storage = Storage()
                    storage.client.upload_file(temp_zip, storage.bucket, storage_key)
                    print(f"[DEBUG] Upload successful!")
                    
                    # Save validation record to MongoDB
                    print(f"[DEBUG] Saving to MongoDB...")
                    history_repo = ValidationHistoryRepo(db, country=country)
                    validation_id = await history_repo.save_validation(
                        username=username,
                        nif=nif,
                        year=year,
                        month=month,
                        operation=op,
                        jar_stdout=stdout_str,
                        jar_stderr=stderr_str,
                        returncode=proc.returncode,
                        file_info={
                            'name': original_name,
                            'size': os.path.getsize(saft_path),
                            'zip_size': zip_size
                        },
                        statistics=stats,
                        response_xml=stats.get('raw_xml'),
                        storage_key=storage_key
                    )
                    print(f"[DEBUG] MongoDB save complete! validation_id: {validation_id}")
                    
                    # Clean up temp ZIP
                    try:
                        os.unlink(temp_zip)
                        print("[DEBUG] Temp ZIP cleaned up")
                    except Exception:
                        pass
                    
                    transcript['archive'] = {
                        'validation_id': validation_id,
                        'storage_key': storage_key,
                        'zip_filename': zip_filename,
                        'zip_size': zip_size
                    }
            except Exception as archive_ex:
                # Don't fail the whole request if archiving fails
                archive_error = f"{archive_ex.__class__.__name__}: {str(archive_ex)}"
                print(f"[ERROR] Archive failed: {archive_error}")
                import traceback
                traceback.print_exc()
                transcript['archive_error'] = archive_error
        
        # Truncation
        limit = 10000 if not full else None
        def trunc(s: str) -> str:
            if s is None: return ''
            if limit is None: return s
            return s if len(s) <= limit else (s[:limit] + '\n... [truncated]')
        
        response = {
            'ok': ok,
            'returncode': proc.returncode,
            'stdout': trunc(stdout_str),
            'stderr': trunc(stderr_str),
            'args': {'nif':nif,'year':year,'month':month},
            'cmd_masked': safe_cmd,
            'cmd': safe_cmd if os.getenv('EXPOSE_CMD','0')=='1' else None,
            'jar_path': jar_path,
            'transcript': transcript
        }
        
        # Add archive info if available
        if validation_id:
            response['validation_id'] = validation_id
            response['storage_key'] = storage_key
            response['archived'] = True
        if archive_error:
            response['archive_error'] = archive_error
        
        return response
    except HTTPException:
        raise
    except Exception as e:
        etype = e.__class__.__name__
        msg = str(e)
        hint = None
        if etype == 'FileNotFoundError':
            hint = "java executable not found on PATH or JAR path invalid"
        transcript['error'] = { 'type': etype, 'message': msg, 'hint': hint }
        return {
            'ok': False,
            'error': f"Failed to invoke JAR: {etype}: {msg}",
            'returncode': None,
            'stdout': '',
            'stderr': '',
            'args': {'nif':nif,'year':year,'month':month},
            'cmd_masked': transcript.get('cmd_masked'),
            'jar_path': jar_path,
            'transcript': transcript
        }


@router.post("/validate-jar-by-key")
async def validate_with_jar_by_key(
    body: PresignDownloadIn,
    request: Request,
    current=Depends(get_current_user),
    db=Depends(get_db),
    full: int = 0,
    operation: str = 'validar',
    dry_run: int = 0,
):
    """Validate or submit a SAFT XML that already exists in Backblaze, referenced by object_key.

    Downloads the object to a temp file and runs the same flow as validate_with_jar, avoiding large uploads.
    """
    from core.saft_validator import parse_xml, extract_cli_params
    from core.storage import Storage
    import tempfile

    country = get_country(request)
    username = current["username"]

    # Download to local temp file
    storage = Storage()
    saft_path = await storage.fetch_to_local(country, body.object_key)
    original_name = os.path.basename(body.object_key)

    # Read file bytes for XML parsing
    try:
        with open(saft_path, 'rb') as f:
            data = f.read()
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to read object: {e}")

    # Extract params
    try:
        root = parse_xml(data)
    except Exception as e:
        return {
            'ok': False,
            'error': f"Invalid XML: {str(e)}",
            'args': None,
            'cmd_masked': None,
            'jar_path': _jar_path(),
            'transcript': { 'error': 'invalid-xml' }
        }
    params = extract_cli_params(root)
    nif = params.get('nif'); year = params.get('year'); month = params.get('month')
    missing = [k for k in ['nif','year','month'] if not params.get(k)]
    if missing:
        return {
            'ok': False,
            'error': f"Missing fields in XML for CLI: {', '.join(missing)}",
            'args': {'nif': nif, 'year': year, 'month': month},
            'cmd_masked': None,
            'jar_path': _jar_path(),
            'transcript': { 'error': 'missing-fields' }
        }

    # Credentials
    repo = UsersRepo(db, country)
    u = await repo.get(username)
    if not u:
        raise HTTPException(status_code=401, detail=USER_NOT_FOUND)
    selected_pass = await _select_at_password(repo, username, nif)
    if not selected_pass and operation == 'enviar':
        return {
            'ok': False,
            'error': f'Operation "enviar" requires AT password for NIF {nif}. Save it in Credenciais first.',
            'returncode': None,
            'stdout': '',
            'stderr': '',
            'args': {'nif':nif,'year':year,'month':month},
            'cmd_masked': ['java','-jar',_jar_path(),' -n ',nif,' -p ','***',' -a ',year,' -m ',month,' -op ',operation,' -i ',saft_path],
            'jar_path': _jar_path(),
            'transcript': { 'op': operation }
        }

    # Build command as in validate_with_jar
    jar_path = _jar_path()
    op = operation
    if selected_pass:
        cmd = ['java','-jar',jar_path,'-n',nif,'-p',selected_pass,'-a',year,'-m',month,'-op',op,'-i',saft_path]
        safe_cmd = list(cmd)
        for i, part in enumerate(safe_cmd):
            if part == selected_pass:
                safe_cmd[i] = '***'
    else:
        cmd = ['java','-jar',jar_path,'-op','validar','-i',saft_path]
        safe_cmd = list(cmd)

    if dry_run:
        return {
            'ok': True,
            'dry_run': True,
            'returncode': None,
            'stdout': '',
            'stderr': '',
            'args': {'nif':nif,'year':year,'month':month},
            'cmd_masked': safe_cmd,
            'jar_path': jar_path,
            'message': f'Dry run - comando "{op}" não foi executado'
        }

    # Execute
    try:
        TIMEOUT = int(os.getenv('FACTEMICLI_TIMEOUT', '300'))
        proc = await asyncio.create_subprocess_exec(*cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
        try:
            stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=TIMEOUT)
        except asyncio.TimeoutError:
            proc.kill()
            return {
                'ok': False,
                'error': 'Validation timed out',
                'timeout': True,
                'returncode': None,
                'stdout': '',
                'stderr': '',
                'args': {'nif':nif,'year':year,'month':month},
                'cmd_masked': safe_cmd,
                'jar_path': jar_path,
            }
        ok = (proc.returncode == 0)
        stdout_str = stdout.decode() if stdout else ''
        stderr_str = stderr.decode() if stderr else ''

        # Archive if success (same as validate_with_jar)
        storage_key = None
        validation_id = None
        archive_error = None
        if ok and not dry_run:
            try:
                from core.saft_archiver import (
                    parse_jar_response_xml,
                    is_validation_successful,
                    create_zip_filename,
                    compress_xml_to_zip,
                    generate_storage_key
                )
                from core.validation_history import ValidationHistoryRepo
                from core.storage import Storage
                import tempfile

                if is_validation_successful(stdout_str, proc.returncode):
                    stats = parse_jar_response_xml(stdout_str)
                    zip_filename = create_zip_filename(nif, year, month)
                    temp_zip = os.path.join(tempfile.gettempdir(), zip_filename)
                    zip_size = compress_xml_to_zip(saft_path, temp_zip, original_filename=original_name)
                    storage_key = generate_storage_key(nif, year, month, zip_filename, country=country)
                    storage = Storage()
                    storage.client.upload_file(temp_zip, storage.bucket, storage_key)
                    history_repo = ValidationHistoryRepo(db, country=country)
                    validation_id = await history_repo.save_validation(
                        username=username,
                        nif=nif,
                        year=year,
                        month=month,
                        operation=op,
                        jar_stdout=stdout_str,
                        jar_stderr=stderr_str,
                        returncode=proc.returncode,
                        file_info={ 'name': original_name, 'size': os.path.getsize(saft_path), 'zip_size': zip_size },
                        statistics=stats,
                        response_xml=stats.get('raw_xml'),
                        storage_key=storage_key
                    )
                    try:
                        os.unlink(temp_zip)
                    except Exception:
                        pass
            except Exception as e:
                archive_error = f"{e.__class__.__name__}: {str(e)}"

        limit = 10000 if not full else None
        def trunc(s: str) -> str:
            if s is None: return ''
            if limit is None: return s
            return s if len(s) <= limit else (s[:limit] + '\n... [truncated]')

        resp = {
            'ok': ok,
            'returncode': proc.returncode,
            'stdout': trunc(stdout_str),
            'stderr': trunc(stderr_str),
            'args': {'nif':nif,'year':year,'month':month},
            'cmd_masked': safe_cmd,
            'jar_path': jar_path,
        }
        if validation_id:
            resp['validation_id'] = validation_id
            resp['storage_key'] = storage_key
            resp['archived'] = True
        if archive_error:
            resp['archive_error'] = archive_error
        return resp
    finally:
        try:
            os.unlink(saft_path)
        except Exception:
            pass


@router.get("/validation-history")
async def get_validation_history(
    request: Request,
    current=Depends(get_current_user),
    db=Depends(get_db),
    nif: Optional[str] = None,
    year: Optional[str] = None,
    month: Optional[str] = None,
    operation: Optional[str] = None,
    limit: int = 50,
    skip: int = 0
):
    """
    Get validation history for the current user
    
    Query parameters:
    - nif: Filter by NIF (optional)
    - year: Filter by fiscal year (optional)
    - month: Filter by fiscal month (optional)
    - operation: Filter by operation type ('validar' or 'enviar') (optional)
    - limit: Maximum number of results (default: 50, max: 100)
    - skip: Number of results to skip for pagination (default: 0)
    
    Returns:
        List of validation records with statistics, timestamps, and download links
    """
    from core.validation_history import ValidationHistoryRepo
    
    country = get_country(request)
    username = current["username"]
    
    # Limit max results
    if limit > 100:
        limit = 100
    
    history_repo = ValidationHistoryRepo(db, country=country)
    
    # Get records
    records = await history_repo.get_user_history(
        username=username,
        nif=nif,
        year=year,
        month=month,
        operation=operation,
        limit=limit,
        skip=skip
    )
    
    # Get total count for pagination
    total = await history_repo.count_user_validations(
        username=username,
        nif=nif,
        year=year,
        month=month
    )
    
    return {
        'ok': True,
        'records': records,
        'total': total,
        'limit': limit,
        'skip': skip,
        'has_more': (skip + len(records)) < total
    }


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
