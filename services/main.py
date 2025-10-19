import os
from fastapi import FastAPI, Depends, HTTPException, UploadFile, File, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from jose import jwt, JWTError
from core.deps import get_db
from core.auth_utils import create_access_token, hash_password, verify_password
from core.auth_repo import UsersRepo
from core.logging_config import setup_logging, get_logger
from core.middleware import RequestLoggingMiddleware
from pydantic import BaseModel, Field

def country_from_request(request: Request) -> str:
    parts=[p for p in request.url.path.split('/') if p]
    if parts and parts[0] in {'pt','es','fr','it','de'}: return parts[0]
    return os.getenv('DEFAULT_COUNTRY','pt')

# Setup logging
setup_logging(level=os.getenv('LOG_LEVEL', 'INFO'))
logger = get_logger(__name__)

SECRET_KEY=os.getenv('SECRET_KEY','change_me')
ALGORITHM='HS256'

# Validate critical configuration (log error but do not crash app)
if SECRET_KEY == 'change_me' and os.getenv('APP_ENV') == 'prod':
    logger.error("SECRET_KEY is using default value in production. Set SECRET_KEY in environment.")

app = FastAPI(
    title='SAFT Doctor (multi-country)', 
    version='0.2.0',
    description="""
    API multi-país para processamento e submissão de arquivos SAFT (Standard Audit File for Tax purposes).
    
    ## Países Suportados
    - 🇵🇹 Portugal: `/pt/*`
    
    ## Funcionalidades
    - Autenticação JWT com suporte multi-país
    - Upload seguro de arquivos SAFT
    - Submissão automática às autoridades tributárias
    - Armazenamento encriptado de credenciais
    """,
    contact={
        "name": "SAFT Doctor Team",
        "email": "support@saft-doctor.com"
    },
    license_info={
        "name": "MIT License",
        "url": "https://opensource.org/licenses/MIT"
    }
)

# Add middlewares
app.add_middleware(RequestLoggingMiddleware)
app.add_middleware(
    CORSMiddleware, 
    allow_origins=os.getenv('CORS_ORIGINS', '*').split(','),
    allow_credentials=True, 
    allow_methods=['*'], 
    allow_headers=['*']
)

# Mount static folder for future assets (JS/CSS)
try:
    app.mount('/static', StaticFiles(directory='static'), name='static')
except Exception:
    # If static folder missing at runtime, ignore
    pass

oauth2_scheme = OAuth2PasswordBearer(tokenUrl='/auth/token')

@app.get('/', response_class=HTMLResponse, tags=['UI'], summary='SAFT Validator')
def root_ui():
    """Serve the SAFT Validator UI at root."""
    # Avoid stale cache serving old JS/HTML in browsers/CDNs
    return HTMLResponse(content=UI_HTML, headers={'Cache-Control': 'no-store'})

@app.get('/info', tags=['Health'], summary='API Info')
def api_info():
    """JSON info with links and status."""
    return {
        'name': 'SAFT Doctor API',
        'status': 'ok',
        'env': os.getenv('APP_ENV','dev'),
        'docs': '/docs',
        'openapi': '/openapi.json',
        'health': '/health',
        'countries': ['pt']
    }

@app.get('/pt', tags=['Portugal'], summary='Portugal Root')
def pt_root():
    """Country root for Portugal with quick links."""
    return {
        'country': 'pt',
        'health': '/pt/health',
        'auth': {
            'register': '/auth/register',
            'token': '/auth/token'
        },
        'files': {
            'upload': '/pt/files/upload'
        },
        'submit': '/pt/submit'
    }

@app.get('/health', tags=['Health'], summary="Health Check")
def health():
    """
    Health check endpoint para monitorização do serviço.
    
    Returns:
        dict: Status do serviço e ambiente atual
    """
    env = os.getenv('APP_ENV','dev')
    logger.info(f"Health check requested - Environment: {env}")
    return {'status':'ok','env': env}

class RegisterIn(BaseModel):
    username: str = Field(min_length=1)
    password: str = Field(min_length=1)

@app.post('/auth/register', tags=['Authentication'], summary="Register User")
async def register(user: RegisterIn, request: Request, db=Depends(get_db)):
    """
    Registar novo utilizador no sistema.
    
    Args:
        user: Dados do utilizador (username, password)
        request: Request HTTP para determinar país
        db: Ligação à base de dados
        
    Returns:
        dict: Dados do utilizador criado
        
    Raises:
        HTTPException: Se o username já existir
    """
    country=country_from_request(request)
    repo=UsersRepo(db,country)
    
    logger.info("User registration attempt", extra={
        "username": user.username,
        "country": country
    })
    
    # 1) Check duplicates (DB)
    try:
        if await repo.exists(user.username): 
            logger.warning("Registration failed - username already exists", extra={
                "username": user.username,
                "country": country
            })
            raise HTTPException(status_code=400, detail='Username already exists')
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Registration 'exists' check failed", extra={"error": str(e)})
        raise HTTPException(status_code=503, detail='Database unavailable (exists check). Verify MONGO_URI/MONGO_DB and Atlas network access.')

    # 2) Hash password (crypto)
    try:
        pwd_hash = hash_password(user.password)
    except Exception as e:
        logger.error("Password hashing failed", extra={"error": str(e), "type": e.__class__.__name__})
        # Return sanitized diagnostic to help operator resolve environment issues
        raise HTTPException(status_code=500, detail=f"Server crypto error while hashing password: {e.__class__.__name__}")

    # 3) Create user (DB)
    try:
        created=await repo.create(user.username, pwd_hash)
        logger.info("User registered successfully", extra={
            "user_id": str(created['_id']),
            "username": created['username'],
            "country": country
        })
        return {'id':str(created['_id']),'username':created['username'],'country':country}
    except Exception as e:
        logger.error("Registration failed at create", extra={"error": str(e)})
        raise HTTPException(status_code=503, detail='Database unavailable (create). Verify MONGO_URI/MONGO_DB and Atlas network access.')

@app.post('/auth/token', tags=['Authentication'], summary="User Login")
async def login(form_data: OAuth2PasswordRequestForm = Depends(), request: Request = None, db=Depends(get_db)):
    """
    Autenticar utilizador e obter token de acesso.
    
    Args:
        form_data: Credenciais do utilizador (username, password)
        request: Request HTTP para determinar país
        db: Ligação à base de dados
        
    Returns:
        dict: Token de acesso e tipo
        
    Raises:
        HTTPException: Se as credenciais forem inválidas
    """
    country=country_from_request(request)
    repo=UsersRepo(db,country)
    
    logger.info("Login attempt", extra={
        "username": form_data.username,
        "country": country
    })
    
    # 1) Fetch user (DB)
    try:
        u=await repo.get(form_data.username)
    except Exception as e:
        logger.error("Login failed at get(user)", extra={"error": str(e)})
        raise HTTPException(status_code=503, detail='Database unavailable (get user).')

    # 2) Verify password (crypto)
    try:
        if not u or not verify_password(form_data.password, u['password_hash']): 
            logger.warning("Login failed - invalid credentials", extra={
                "username": form_data.username,
                "country": country
            })
            raise HTTPException(status_code=400, detail='Incorrect username or password')
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Password verification failed", extra={"error": str(e)})
        raise HTTPException(status_code=500, detail='Server crypto error while verifying password.')

    # 3) Issue token
    token=create_access_token({'sub':form_data.username,'cty':country})
    logger.info("Login successful", extra={
        "username": form_data.username,
        "country": country
    })
    return {'access_token':token,'token_type':'bearer'}

# Moved below get_current_user definition to ensure symbol resolution

@app.get('/health/db', tags=['Health'], summary='Database Health')
async def health_db(db=Depends(get_db)):
    try:
        # Ping the server
        await db.command('ping')
        return { 'ok': True }
    except Exception as e:
        return { 'ok': False, 'error': str(e) }

async def get_current_user(request: Request, token: str = Depends(oauth2_scheme), db=Depends(get_db)):
    """
    Obter utilizador atual a partir do token JWT.
    
    Args:
        request: Request HTTP para determinar país
        token: Token JWT
        db: Ligação à base de dados
        
    Returns:
        dict: Dados do utilizador atual
        
    Raises:
        HTTPException: Se o token for inválido ou utilizador não existir
    """
    country=country_from_request(request)
    try:
        payload=jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username=payload.get('sub')
        if not username: 
            logger.warning("Invalid token - no username in payload")
            raise HTTPException(status_code=401, detail='Invalid token')
    except JWTError as e:
        logger.warning("JWT decode error", extra={"error": str(e)})
        raise HTTPException(status_code=401, detail='Invalid token')
    
    repo=UsersRepo(db,country)
    u=await repo.get(username)
    if not u: 
        logger.warning("User not found", extra={
            "username": username,
            "country": country
        })
        raise HTTPException(status_code=401, detail='User not found')
    
    return {'username':username,'country':country}

from saft_pt_doctor.routers_pt import router as router_pt
app.include_router(router_pt, prefix='/pt')

@app.get('/auth/me', tags=['Authentication'], summary='Current user')
async def auth_me(current=Depends(get_current_user)):
    return current

@app.on_event('startup')
async def _bootstrap_default_user():
    """Optionally bootstrap a default user if BOOTSTRAP_USER/PASS are set.

    This helps local/dev environments log in without manual registration.
    """
    u = os.getenv('BOOTSTRAP_USER')
    p = os.getenv('BOOTSTRAP_PASS')
    country = os.getenv('DEFAULT_COUNTRY','pt')
    if not (u and p):
        return
    try:
        db = get_db()
        repo = UsersRepo(db, country)
        exists = await repo.exists(u)
        if not exists:
            await repo.create(u, hash_password(p))
            logger.info("Bootstrap user created", extra={"username": u, "country": country})
        else:
            logger.info("Bootstrap user exists", extra={"username": u, "country": country})
    except Exception as e:
        logger.warning("Bootstrap user failed", extra={"error": str(e)})

# --- Simple UX for SAFT validation ---
UI_HTML = """
<!doctype html>
<html lang="en">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>SAFT Doctor • Validator</title>
    <style>
        body { font-family: system-ui, -apple-system, Segoe UI, Roboto, sans-serif; margin: 2rem; }
        header { margin-bottom: 1rem; }
        .card { border: 1px solid #e5e7eb; border-radius: 8px; padding: 1rem; max-width: 760px; }
        .row { display: flex; gap: 1rem; align-items: center; }
        .mt { margin-top: 1rem; }
        .btn { background: #111827; color: white; border: 0; padding: .6rem 1rem; border-radius: 6px; cursor: pointer; }
        .btn:disabled { opacity: .5; cursor: not-allowed; }
        pre { background: #0b1020; color: #e5e7eb; padding: 1rem; border-radius: 8px; overflow:auto; }
        .ok { color: #065f46; }
        .warn { color: #92400e; }
        .err { color: #991b1b; }
        .tabs { display: flex; gap: .5rem; margin-bottom: 1rem; }
        .tab { padding: .5rem .8rem; border: 1px solid #e5e7eb; border-bottom: none; border-radius: 6px 6px 0 0; background: #f9fafb; cursor: pointer; }
        .tab.active { background: white; font-weight: 600; }
        .tabpanel { display: none; }
        .tabpanel.active { display: block; }
        .note { background: #fff7ed; border: 1px solid #fed7aa; color: #7c2d12; padding: .8rem; border-radius: 8px; }
        .log-header { display:flex; align-items:center; justify-content: space-between; }
        .log-actions { display:flex; gap:.5rem; }
    </style>
    <script>
            const state = { token: null, objectKey: null, file: null };
            function logLine(msg) {
                const el = document.getElementById('log');
                const ts = new Date().toISOString();
                el.textContent += `[${ts}] ${msg}\n`;
                el.scrollTop = el.scrollHeight;
            }
            function clearLog() { const el = document.getElementById('log'); el.textContent=''; }
            window.addEventListener('error', (e) => {
                try { setStatus('JS error: ' + (e.message || '(no message)')); } catch(_){}
            });

        function showTab(id) {
            for (const el of document.querySelectorAll('.tab')) el.classList.remove('active');
            for (const el of document.querySelectorAll('.tabpanel')) el.classList.remove('active');
            const btn = document.querySelector(`[data-tab="${id}"]`);
            const panel = document.getElementById(`panel-${id}`);
            if (btn && panel) { btn.classList.add('active'); panel.classList.add('active'); }
        }

        async function validate() {
            const fileInput = document.getElementById('file');
            const out = document.getElementById('out');
            const btn = document.getElementById('btn');
            out.textContent = '';
            if (!fileInput.files.length) { out.textContent = 'Choose a SAFT XML file'; return; }
            const f = fileInput.files[0];
            const fd = new FormData();
            fd.append('file', f);
            btn.disabled = true; btn.textContent = 'Validating…';
            try {
                const res = await fetch('/ui/validate', { method: 'POST', body: fd });
                const data = await res.json();
                out.textContent = JSON.stringify(data, null, 2);
            } catch (e) {
                out.textContent = 'Error: ' + e;
            } finally {
                btn.disabled = false; btn.textContent = 'Validate';
            }
        }

            async function validateWithJar() {
                if (!state.token) { setStatus('Login first.'); return; }
                const fileInput = document.getElementById('file');
                const out = document.getElementById('out');
                const cmdEl = document.getElementById('cmd_mask');
                if (!fileInput.files.length) { setStatus('Choose a SAFT XML file'); return; }
                setStatus('Validating via FACTEMICLI.jar…');
                logLine('Validate with JAR clicked. Preparing upload…');
                const f = fileInput.files[0];
                const fd = new FormData(); fd.append('file', f);
                try {
                    const r = await fetch('/pt/validate-jar?full=1', { method: 'POST', headers: { 'Authorization': 'Bearer ' + state.token }, body: fd });
                    const txt = await r.text();
                    let data=null; try { data = txt ? JSON.parse(txt) : null; } catch(_){ }
                    // Always show body even on errors
                    out.textContent = data ? JSON.stringify(data, null, 2) : (txt || '(no body)');
                    if (data && data.cmd_masked && Array.isArray(data.cmd_masked)) {
                        cmdEl.textContent = data.cmd_masked.join(' ');
                        logLine('Command (masked): ' + data.cmd_masked.join(' '));
                        if (typeof data.returncode !== 'undefined' && data.returncode !== null) {
                            logLine('Return code: ' + data.returncode + (data.ok === false ? ' (error)' : ''));
                        }
                        if (data.stderr) {
                            const preview = (data.stderr.length > 400 ? data.stderr.slice(0, 400) + '…' : data.stderr);
                            if (preview.trim()) logLine('Stderr preview: ' + preview.replace(/\n/g,' | '));
                        }
                    } else {
                        cmdEl.textContent = '(n/a)';
                        logLine('No command returned by API.');
                    }
                    setStatus(r.ok ? 'JAR validation done.' : ('JAR validation HTTP ' + r.status));
                } catch (e) {
                    setStatus('JAR validation error: ' + e.message);
                    logLine('Error during JAR validation: ' + e.message);
                }
            }

            async function checkJarStatus() {
                const out = document.getElementById('out');
                out.textContent = 'Checking JAR status…';
                try {
                    const r = await fetch('/pt/jar/status');
                    const j = await r.json();
                    out.textContent = JSON.stringify(j, null, 2);
                } catch (e) {
                    out.textContent = 'Error: ' + e;
                }
            }

            async function runJarCheck() {
                const out = document.getElementById('out');
                out.textContent = 'Running JAR check…';
                try {
                    const r = await fetch('/pt/jar/run-check');
                    const j = await r.json();
                    out.textContent = JSON.stringify(j, null, 2);
                } catch (e) {
                    out.textContent = 'Error: ' + e;
                }
            }

            async function checkJavaVersion() {
                const out = document.getElementById('out');
                out.textContent = 'Checking Java version…';
                try {
                    const r = await fetch('/pt/java/version');
                    const j = await r.json();
                    out.textContent = JSON.stringify(j, null, 2);
                } catch (e) {
                    out.textContent = 'Error: ' + e;
                }
            }

            async function installJar() {
                if (!state.token) { setStatus('Login first.'); return; }
                const key = (document.getElementById('jar_key').value || '').trim();
                if (!key) { setStatus('Provide an object_key.'); return; }
                setStatus('Installing JAR…');
                try {
                    const r = await fetch('/pt/jar/install', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json', 'Authorization': 'Bearer ' + state.token },
                        body: JSON.stringify({ object_key: key })
                    });
                    const txt = await r.text();
                    let data = null;
                    try { data = txt ? JSON.parse(txt) : null; } catch (_) { /* keep as text */ }
                    if (!r.ok) {
                        const msg = data && data.detail ? data.detail : (txt ? txt.slice(0, 300) : 'Install failed');
                        throw new Error(msg);
                    }
                    const j = data || {};
                    setStatus('JAR installed at ' + (j.path || '(unknown)') + ' (' + ((j.size != null ? j.size : '?')) + ' bytes)');
                    const out = document.getElementById('out'); out.textContent = data ? JSON.stringify(j, null, 2) : (txt || 'OK');
                } catch (e) { setStatus('Install error: ' + e.message); }
            }

                function setStatus(msg) {
                    const s = document.getElementById('status');
                    s.textContent = msg;
                }

                async function registerUser() {
                    const u = document.getElementById('u_user').value.trim();
                    const p = document.getElementById('u_pass').value;
                    if (!u || !p) { setStatus('Fill username and password to register.'); return; }
                    setStatus('Registering…');
                    try {
                        const r = await fetch('/auth/register', {
                            method: 'POST', headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify({ username: u, password: p })
                        });
                        if (!r.ok) { const t=await r.text(); throw new Error(t); }
                        setStatus('Registered. Now login.');
                    } catch (e) { setStatus('Register error: ' + e.message); }
                }

                async function loginUser() {
                    const u = document.getElementById('l_user').value.trim();
                    const p = document.getElementById('l_pass').value;
                    if (!u || !p) { setStatus('Fill username and password to login.'); return; }
                    setStatus('Logging in…');
                    try {
                        const fd = new URLSearchParams(); fd.set('username', u); fd.set('password', p);
                        const r = await fetch('/auth/token', { method: 'POST', headers: { 'Content-Type': 'application/x-www-form-urlencoded' }, body: fd });
                        const j = await r.json();
                        if (!r.ok) throw new Error(j.detail || 'Login failed');
                        state.token = j.access_token; setStatus('Logged in. Token ready.');
                        document.getElementById('token_status').textContent = 'Authenticated';
                    } catch (e) { setStatus('Login error: ' + e.message); }
                }

                async function loginDev() {
                    document.getElementById('l_user').value = 'dev';
                    document.getElementById('l_pass').value = 'dev';
                    await loginUser();
                }

                async function saveAT() {
                    if (!state.token) { setStatus('Login first.'); return; }
                    const au = document.getElementById('at_user').value.trim();
                    const ap = document.getElementById('at_pass').value;
                    if (!au || !ap) { setStatus('Fill AT username and password.'); return; }
                    setStatus('Saving AT credentials…');
                    try {
                        const r = await fetch('/pt/secrets/at', {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json', 'Authorization': 'Bearer ' + state.token },
                            body: JSON.stringify({ username: au, password: ap })
                        });
                        const j = await r.json();
                        if (!r.ok) throw new Error(j.detail || 'Failed to save');
                        setStatus('AT credentials saved (encrypted).');
                    } catch (e) { setStatus('Save AT error: ' + e.message); }
                }

                function onFileChange(ev) { state.file = ev.target.files[0] || null; }

                async function presignUpload() {
                    if (!state.token) { setStatus('Login first.'); return; }
                    if (!state.file) { setStatus('Choose a file first.'); return; }
                    setStatus('Requesting presigned URL…');
                    try {
                        const r = await fetch('/pt/files/presign-upload', {
                            method: 'POST', headers: { 'Content-Type': 'application/json', 'Authorization': 'Bearer ' + state.token },
                            body: JSON.stringify({ filename: state.file.name, content_type: state.file.type || 'application/octet-stream' })
                        });
                        const j = await r.json();
                        if (!r.ok) throw new Error(j.detail || 'Failed to presign');
                        // PUT to S3 URL
                        setStatus('Uploading via presigned URL…');
                        const put = await fetch(j.url, { method: 'PUT', headers: j.headers || {}, body: state.file });
                        if (!put.ok && put.status !== 200 && put.status !== 201) throw new Error('PUT failed with status ' + put.status);
                        state.objectKey = j.object; setStatus('Uploaded. object_key=' + state.objectKey);
                        document.getElementById('object_key').textContent = state.objectKey;
                    } catch (e) { setStatus('Presign/Upload error: ' + e.message); }
                }

                async function submitFile() {
                    if (!state.token) { setStatus('Login first.'); return; }
                    if (!state.objectKey) { setStatus('Upload first to get object_key.'); return; }
                    setStatus('Submitting…');
                    try {
                        const r = await fetch('/pt/submit?object_key=' + encodeURIComponent(state.objectKey), {
                            method: 'POST', headers: { 'Authorization': 'Bearer ' + state.token }
                        });
                        const j = await r.json();
                        if (!r.ok) throw new Error(j.detail || 'Submit failed');
                        setStatus('Submit OK.');
                        const out = document.getElementById('out'); out.textContent = JSON.stringify(j, null, 2);
                    } catch (e) { setStatus('Submit error: ' + e.message); }
                }

                async function presignDownload() {
                    if (!state.token) { setStatus('Login first.'); return; }
                    const key = (document.getElementById('dl_key').value || '').trim();
                    if (!key) { setStatus('Provide an object_key.'); return; }
                    setStatus('Requesting download URL…');
                    try {
                        const r = await fetch('/pt/files/presign-download', {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json', 'Authorization': 'Bearer ' + state.token },
                            body: JSON.stringify({ object_key: key })
                        });
                        const j = await r.json();
                        if (!r.ok) throw new Error(j.detail || 'Failed to presign download');
                        document.getElementById('dl_url').textContent = j.url || '(no url)';
                        const out = document.getElementById('out'); out.textContent = JSON.stringify(j, null, 2);
                        setStatus('Download URL ready.');
                    } catch (e) { setStatus('Presign download error: ' + e.message); }
                }

                async function loadCredsStatus() {
                    if (!state.token) { setStatus('Login first.'); return; }
                    try {
                        const r = await fetch('/pt/secrets/at/status', { headers: { 'Authorization': 'Bearer ' + state.token } });
                        const j = await r.json();
                        document.getElementById('creds_user_mask').textContent = j.username_masked || '(none)';
                        document.getElementById('creds_updated').textContent = j.updated_at || '(unknown)';
                        setStatus(j.ok ? 'Credentials status loaded.' : 'No credentials saved.');
                    } catch (e) { setStatus('Load creds error: ' + e.message); }
                }

                async function saveAT2() {
                    if (!state.token) { setStatus('Login first.'); return; }
                    const au = document.getElementById('at_user2').value.trim();
                    const ap = document.getElementById('at_pass2').value;
                    if (!au || !ap) { setStatus('Fill AT username and password.'); return; }
                    setStatus('Saving AT credentials…');
                    try {
                        const r = await fetch('/pt/secrets/at', {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json', 'Authorization': 'Bearer ' + state.token },
                            body: JSON.stringify({ username: au, password: ap })
                        });
                        const j = await r.json();
                        if (!r.ok) throw new Error(j.detail || 'Failed to save creds');
                        setStatus('AT credentials saved.');
                        loadCredsStatus();
                    } catch (e) { setStatus('Save AT error: ' + e.message); }
                }

                async function analyzeAndSave() {
                    if (!state.token) { setStatus('Login first.'); return; }
                    const fileInput = document.getElementById('file');
                    if (!fileInput.files.length) { setStatus('Choose a SAFT XML file'); return; }
                    setStatus('Analyzing…');
                    try {
                        const f = fileInput.files[0];
                        const fd = new FormData(); fd.append('file', f);
                        const r = await fetch('/pt/analyze', { method: 'POST', headers: { 'Authorization': 'Bearer ' + state.token }, body: fd });
                        const txt = await r.text();
                        let data = null; try { data = txt ? JSON.parse(txt) : null; } catch(_){}
                        if (!r.ok) throw new Error((data && data.detail) || (txt ? txt.slice(0,300) : 'Analyze failed'));
                        const out = document.getElementById('out'); out.textContent = JSON.stringify(data, null, 2);
                        if (data.object_key) { state.objectKey = data.object_key; document.getElementById('object_key').textContent = state.objectKey; }
                        setStatus('Analysis saved.');
                    } catch (e) {
                        setStatus('Analyze error: ' + e.message);
                    }
                }

                async function saveNifEntry() {
                    if (!state.token) { setStatus('Login first.'); return; }
                    const ident = (document.getElementById('nif_ident').value || '').trim();
                    const pass = document.getElementById('nif_pass').value;
                    if (!ident || !pass) { setStatus('Preenche NIF e senha.'); return; }
                    setStatus('A guardar senha para NIF ' + ident + '…');
                    try {
                        const r = await fetch('/pt/secrets/at/entries', {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json', 'Authorization': 'Bearer ' + state.token },
                            body: JSON.stringify({ ident, password: pass })
                        });
                        const j = await r.json();
                        if (!r.ok) throw new Error(j.detail || 'Falha ao guardar');
                        setStatus('Senha guardada para NIF ' + ident + '.');
                        await loadNifEntries();
                    } catch (e) { setStatus('Erro a guardar NIF: ' + e.message); }
                }

                async function loadNifEntries() {
                    if (!state.token) { setStatus('Login first.'); return; }
                    setStatus('A carregar NIFs…');
                    try {
                        const r = await fetch('/pt/secrets/at/entries', { headers: { 'Authorization': 'Bearer ' + state.token } });
                        const j = await r.json();
                        if (!r.ok) throw new Error(j.detail || 'Falha ao listar');
                        const out = document.getElementById('nif_list');
                        out.textContent = JSON.stringify(j.items || [], null, 2);
                        setStatus('NIFs carregados.');
                    } catch (e) { setStatus('Erro a listar NIFs: ' + e.message); }
                }
    </script>
</head>
<body>
    <header>
        <h1>SAFT Doctor • Validator</h1>
        <p>Upload a SAFT XML to validate basic structure and header fields.</p>
    </header>
    <div class="tabs">
        <div class="tab active" data-tab="app" onclick="showTab('app')">Aplicação</div>
        <div class="tab" data-tab="config" onclick="showTab('config')">Configuração</div>
        <div class="tab" data-tab="creds" onclick="showTab('creds')">Credenciais</div>
    </div>

    <div id="panel-app" class="tabpanel active">
    <div class="card">
        <div class="row">
                    <input type="file" id="file" accept=".xml,text/xml" onchange="onFileChange(event)" />
            <button class="btn" id="btn" onclick="validate()">Validate</button>
            <button class="btn" onclick="validateWithJar()">Validate with JAR</button>
        </div>
        <div class="mt">
            <div>Comando (mascarado): <code id="cmd_mask">(n/a)</code></div>
            <pre id="out"></pre>
        </div>
    </div>

        <div class="card" style="margin-top:1rem;">
            <div class="log-header">
                <h3 style="margin:0;">Log</h3>
                <div class="log-actions">
                    <button class="btn" onclick="clearLog()">Clear log</button>
                </div>
            </div>
            <pre id="log" style="min-height:160px;" aria-label="Execution log"></pre>
        </div>

        <div class="card" style="margin-top:1rem;">
            <div class="row">
                <button class="btn" onclick="checkJavaVersion()">Java version</button>
                <button class="btn" onclick="checkJarStatus()">Check JAR status</button>
                <button class="btn" onclick="runJarCheck()">Run JAR check</button>
            </div>
        </div>

            <div class="card" style="margin-top:1rem;">
                <h3>Auth</h3>
                <div class="row mt">
                    <input placeholder="Register: username" id="u_user" />
                    <input placeholder="Register: password" id="u_pass" type="password" />
                    <button class="btn" onclick="registerUser()">Register</button>
                </div>
                <div class="row mt">
                    <input placeholder="Login: username" id="l_user" />
                    <input placeholder="Login: password" id="l_pass" type="password" />
                    <button class="btn" onclick="loginUser()">Login</button>
                    <button class="btn" onclick="loginDev()" title="Quick dev login">Login dev/dev</button>
                    <span id="token_status" class="ok" style="margin-left:.5rem;">Not authenticated</span>
                </div>
                <div class="row mt">
                    <button class="btn" onclick="(async()=>{ try { const r=await fetch('/auth/me',{ headers: state.token? { Authorization: 'Bearer '+state.token } : {} }); const t=await r.text(); setStatus('Auth self-test HTTP '+r.status+': '+t.slice(0,200)); } catch(e){ setStatus('Self-test error: '+e.message);} })()">Self-test</button>
                </div>
            </div>

            <div class="card" style="margin-top:1rem;">
                <h3>AT Secrets (requires login)</h3>
                <p>AT credentials are saved encrypted on the server only after login.</p>
                <div class="row mt">
                    <input placeholder="AT username" id="at_user" />
                    <input placeholder="AT password" id="at_pass" type="password" />
                    <button class="btn" onclick="saveAT()">Save AT</button>
                    <button class="btn" onclick="(async ()=>{ document.getElementById('at_user').value='teste'; document.getElementById('at_pass').value='segredo'; await saveAT(); })()">Guardar AT de teste</button>
                </div>
            </div>

            <div class="card" style="margin-top:1rem;">
                <h3>Upload & Submit (requires login)</h3>
                <div class="row mt">
                    <button class="btn" onclick="presignUpload()">Upload via Presign</button>
                    <span>object_key: <code id="object_key">(none)</code></span>
                </div>
                <div class="row mt">
                    <button class="btn" onclick="submitFile()">Submit</button>
                    <button class="btn" onclick="analyzeAndSave()">Analyze & save</button>
                </div>
            </div>

    </div> <!-- end panel-app -->

    <div id="panel-config" class="tabpanel">
        <div class="card">
            <h3>Instalar FACTEMICLI.jar (Configuração)</h3>
            <p class="note">
                Como instalar o ficheiro FACTEMICLI.jar no servidor:
            </p>
            <ol class="mt">
                <li>Carrega o JAR para o teu bucket Backblaze B2 <b>saftdoctor</b> sob o prefixo <code>pt/tools/FACTEMICLI.jar</code> (recomendado um único bucket com prefixos por país).</li>
                <li>Garante que a tua Application Key tem permissões de leitura no bucket: <b>readFiles</b> / <b>s3:GetObject</b> (e <b>putObject</b> se fores usar uploads).</li>
                <li>Configura as variáveis no Render (Serviço → Settings → Environment):
                    <ul>
                        <li><code>B2_BUCKET=saftdoctor</code></li>
                        <li><code>B2_REGION=eu-central-003</code></li>
                        <li><code>B2_ENDPOINT=https://s3.eu-central-003.backblazeb2.com</code></li>
                        <li><code>B2_KEY_ID</code> e <code>B2_APP_KEY</code> (com as permissões acima)</li>
                        <li><code>FACTEMICLI_JAR_PATH</code> (ex.: <code>/opt/factemi/FACTEMICLI.jar</code>)</li>
                    </ul>
                </li>
                <li>(Recomendado) Usa um <b>Persistent Disk</b> no Render montado em <code>/opt/factemi</code>, para o JAR persistir entre deployments.</li>
                <li>Depois de autenticado nesta página, usa o botão <b>Install JAR</b> abaixo para transferir do B2 diretamente para o caminho configurado.</li>
                <li>Evita usar <code>curl -L</code> com URLs presignados S3 (o redirect quebra a assinatura). Se precisares de um link temporário, usa "Presigned Download" nesta aba.</li>
                <li>Para atualizar o JAR no futuro, substitui o ficheiro no B2 (mesmo <code>object_key</code>) e clica novamente em <b>Install JAR</b>.</li>
            </ol>
            <h4 class="mt">Checklist pós-instalação</h4>
            <ol>
                <li>Clica em <b>Check JAR status</b> (separador Aplicação) — deve mostrar <code>ok:true</code> e <code>size</code> ~2.8 MB.</li>
                <li>Clica em <b>Run JAR check</b> — deve aparecer um pequeno <i>preview/usage</i> do JAR.</li>
                <li>Em <b>Auth</b>, faz <i>Register</i> e <i>Login</i> (se necessário) e confirma "Authenticated".</li>
                <li>Em <b>AT Secrets</b>, grava as credenciais da AT (ficam encriptadas no servidor).</li>
                <li>Em <b>Upload & Submit</b>, faz <i>Upload via Presign</i> (guarda o <code>object_key</code>) e depois <i>Submit</i>.</li>
                <li>Se o <i>Submit</i> falhar, lê a mensagem de erro (pode ser do JAR ou de credenciais AT). Ajusta e repete.</li>
            </ol>
            <h4 class="mt">Resolução de problemas</h4>
            <ul>
                <li><b>Access denied ao instalar</b>: verifica permissões da Application Key (readFiles/s3:GetObject) e se o objeto existe em <code>pt/tools/FACTEMICLI.jar</code>.</li>
                <li><b>Invalid or corrupt jarfile</b> após download manual: evita <code>-L</code> com presign; usa o botão <b>Install JAR</b> que usa o SDK (sem redirects).</li>
                <li><b>JWT inválido</b>: volta a fazer <i>Login</i> e tenta outra vez.</li>
                <li><b>Mongo indisponível</b>: /health/db deve ser <code>{ ok: true }</code>; se não, revê MONGO_URI/MONGO_DB e IP allowlist.</li>
            </ul>
            <h4 class="mt">Linha de comando (referência)</h4>
            <p>Usamos os campos do XML para preencher os parâmetros; só a senha AT vem do utilizador:</p>
            <pre>java -jar FACTEMICLI.jar -n &lt;TaxRegistrationNumber&gt; -p &lt;SENHA_AT&gt; -a &lt;FiscalYear&gt; -m &lt;MM_de_StartDate&gt; -op enviar -i @&lt;caminho_para_xml&gt;</pre>
            <div class="row mt">
                <input id="jar_key" placeholder="object_key (e.g. pt/tools/FACTEMICLI.jar)" value="pt/tools/FACTEMICLI.jar" />
                <button class="btn" onclick="installJar()">Install JAR</button>
            </div>
        </div>

        <div class="card" style="margin-top:1rem;">
            <h3>Presigned Download (opcional)</h3>
            <p>Podes gerar um URL temporário para descarregar o ficheiro diretamente no browser.</p>
            <div class="row mt">
                <input id="dl_key" placeholder="object_key (e.g. pt/tools/FACTEMICLI.jar)" value="pt/tools/FACTEMICLI.jar" />
                <button class="btn" onclick="presignDownload()">Get download URL</button>
            </div>
            <div class="mt">URL: <code id="dl_url">(none)</code></div>
        </div>
    </div>

    <div id="panel-creds" class="tabpanel">
        <div class="card">
            <h3>Credenciais AT</h3>
            <p>As credenciais são guardadas encriptadas no servidor. Mostramos apenas uma máscara do username.</p>
            <div class="row mt">
                <button class="btn" onclick="loadCredsStatus()">Atualizar estado</button>
                <span>Username (mask): <code id="creds_user_mask">(unknown)</code></span>
                <span>Atualizado em: <code id="creds_updated">(unknown)</code></span>
            </div>
        </div>
        <div class="card" style="margin-top:1rem;">
            <h3>Atualizar credenciais AT</h3>
            <div class="row mt">
                <input placeholder="AT username" id="at_user2" />
                <input placeholder="AT password" id="at_pass2" type="password" />
                <button class="btn" onclick="saveAT2()">Guardar</button>
            </div>
        </div>
        <div class="card" style="margin-top:1rem;">
            <h3>Senhas por NIF (recomendado)</h3>
            <p>Guarda a senha AT associada a cada NIF. A validação/submissão escolhe automaticamente pela NIF do XML.</p>
            <div class="row mt">
                <input placeholder="NIF (ident)" id="nif_ident" />
                <input placeholder="Senha AT" id="nif_pass" type="password" />
                <button class="btn" onclick="saveNifEntry()">Guardar NIF</button>
            </div>
            <div class="mt">
                <button class="btn" onclick="loadNifEntries()">Listar NIFs</button>
            </div>
            <div class="mt">
                <pre id="nif_list">(vazio)</pre>
            </div>
        </div>
    </div>

            <p id="status" class="mt"></p>
</body>
</html>
"""

@app.get('/ui', response_class=HTMLResponse, tags=['UI'])
def ui_page():
        return HTMLResponse(content=UI_HTML)

@app.post('/ui/validate', tags=['UI'])
async def ui_validate(file: UploadFile = File(...)):
        from core.saft_validator import parse_xml, validate_saft
        data = await file.read()
        try:
                root = parse_xml(data)
                issues, summary = validate_saft(root)
                status = 'ok' if not any(i['level'] == 'error' for i in issues) else 'errors'
                return JSONResponse({ 'status': status, 'summary': summary, 'issues': issues })
        except Exception as e:
                return JSONResponse({ 'status': 'error', 'message': str(e) }, status_code=400)
