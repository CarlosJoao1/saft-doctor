import os
from fastapi import FastAPI, Depends, HTTPException, UploadFile, File, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel, Field
from typing import Optional
from jose import jwt, JWTError

from core.logging_config import setup_logging, get_logger
from core.middleware import RequestLoggingMiddleware
from core.deps import get_db
from core.auth_repo import UsersRepo
from core.auth_utils import create_access_token, hash_password, verify_password


# Setup logging and app
setup_logging(level=os.getenv('LOG_LEVEL', 'INFO'))
logger = get_logger(__name__)

# Normalize SECRET_KEY to avoid accidental spaces in environment vars
SECRET_KEY = (os.getenv('SECRET_KEY', 'change_me') or 'change_me').strip()
ALGORITHM = 'HS256'
oauth2_scheme = OAuth2PasswordBearer(tokenUrl='/auth/token')

app = FastAPI(title='SAFT Doctor (multi-country)', version='0.2.0')
app.add_middleware(RequestLoggingMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv('CORS_ORIGINS', '*').split(','),
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)

@app.on_event('startup')
async def startup_cleanup():
    """Cleanup old upload chunks on startup and log environment."""
    import glob
    import time
    UPLOAD_ROOT = os.getenv('UPLOAD_ROOT', '/var/saft/uploads')
    print(f"[STARTUP] UPLOAD_ROOT={UPLOAD_ROOT}")
    try:
        os.makedirs(UPLOAD_ROOT, mode=0o755, exist_ok=True)
        print(f"[STARTUP] Upload directory ready: {UPLOAD_ROOT}")
    except Exception as e:
        print(f"[STARTUP] ERRO ao criar UPLOAD_ROOT: {e}")
    # Cleanup old files (>1 hour)
    try:
        now = time.time()
        pattern = os.path.join(UPLOAD_ROOT, '*')
        removed = 0
        for fpath in glob.glob(pattern):
            try:
                if os.path.isfile(fpath) and (now - os.path.getmtime(fpath)) > 3600:
                    os.remove(fpath)
                    removed += 1
            except Exception:
                pass
        if removed > 0:
            print(f"[STARTUP] Limpeza: removidos {removed} ficheiros antigos de upload")
    except Exception as e:
        print(f"[STARTUP] Erro na limpeza de uploads: {e}")


class RegisterIn(BaseModel):
    username: str = Field(min_length=1)
    password: str = Field(min_length=1)
    email: Optional[str] = None  # Optional email for password reset


def country_from_request(request: Request) -> str:
    parts = [p for p in request.url.path.split('/') if p]
    if parts and parts[0] in {'pt', 'es', 'fr', 'it', 'de'}:
        return parts[0]
    return os.getenv('DEFAULT_COUNTRY', 'pt')


UI_HTML = """
<!doctype html>
<html lang=\"en\">
<head>
  <meta charset=\"utf-8\" />
  <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\" />
  <title>SAFT Doctor • Validator</title>
  <style>
    body{font-family:system-ui,-apple-system,Segoe UI,Roboto,sans-serif;margin:2rem}
    header{margin-bottom:1rem}
    .card{border:1px solid #e5e7eb;border-radius:8px;padding:1rem;max-width:760px}
    .row{display:flex;gap:1rem;align-items:center}
    .mt{margin-top:1rem}
    .btn{background:#111827;color:#fff;border:0;padding:.6rem 1rem;border-radius:6px;cursor:pointer}
    .btn:disabled{opacity:.5;cursor:not-allowed}
    pre{background:#0b1020;color:#e5e7eb;padding:1rem;border-radius:8px;overflow:auto}
    .log-header{display:flex;align-items:center;justify-content:space-between}
    .log-actions{display:flex;gap:.5rem}
  </style>
  <script>
    const state={token:null,objectKey:null,file:null};
    function logLine(m){const el=document.getElementById('log');const ts=new Date().toISOString();el.textContent+=`[${ts}] ${m}\n`;el.scrollTop=el.scrollHeight}
    function clearLog(){const el=document.getElementById('log');el.textContent=''}
    window.addEventListener('error',e=>{try{setStatus('JS error: '+(e.message||'(no message)'))}catch(_){}});
    window.addEventListener('unhandledrejection',e=>{try{logLine('Unhandled rejection: '+(e.reason&&e.reason.message?e.reason.message:e.reason))}catch(_){}});
    (function(){const orig=window.fetch;window.fetch=async function(i,n){try{const u=typeof i==='string'?i:(i&&i.url)||'';const m=(n&&n.method)||'GET';logLine(`[fetch] ${m} ${u}`)}catch(_){}const r=await orig(i,n);try{logLine(`[fetch] -> ${r.status} ${r.statusText||''}`.trim())}catch(_){}return r};})();
    window.addEventListener('DOMContentLoaded',()=>{try{document.getElementById('js_ok').textContent='JS loaded'}catch(_){};try{logLine('[init] UI loaded')}catch(_){}});

    async function validate(){const fI=document.getElementById('file');const out=document.getElementById('out');const btn=document.getElementById('btn');out.textContent='';if(!fI.files.length){out.textContent='Choose a SAFT XML file';return}const f=fI.files[0];const fd=new FormData();fd.append('file',f);btn.disabled=true;btn.textContent='Validating…';try{const r=await fetch('/ui/validate',{method:'POST',body:fd});const j=await r.json();out.textContent=JSON.stringify(j,null,2)}catch(e){out.textContent='Error: '+e}finally{btn.disabled=false;btn.textContent='Validate'}}

    async function validateWithJar(){if(!state.token){setStatus('Login first.');return}const fI=document.getElementById('file');const out=document.getElementById('out');const cmdEl=document.getElementById('cmd_mask');if(!fI.files.length){setStatus('Choose a SAFT XML file');return}setStatus('Validating via FACTEMICLI.jar…');logLine('Validate with JAR clicked. Preparing upload…');const f=fI.files[0];const fd=new FormData();fd.append('file',f);try{const r=await fetch('/pt/validate-jar?full=1',{method:'POST',headers:{'Authorization':'Bearer '+state.token},body:fd});const txt=await r.text();let data=null;try{data=txt?JSON.parse(txt):null}catch(_){}out.textContent=data?JSON.stringify(data,null,2):(txt||'(no body)');if(data&&data.cmd_masked&&Array.isArray(data.cmd_masked)){cmdEl.textContent=data.cmd_masked.join(' ');logLine('Command (masked): '+data.cmd_masked.join(' '));if(typeof data.returncode!=='undefined'&&data.returncode!==null)logLine('Return code: '+data.returncode+(data.ok===false?' (error)':''));if(data.stderr){const preview=(data.stderr.length>400?data.stderr.slice(0,400)+'…':data.stderr);if(preview.trim())logLine('Stderr preview: '+preview.split('\n').join(' | '))}}else{cmdEl.textContent='(n/a)';logLine('No command returned by API.')}setStatus(r.ok?'JAR validation done.':('JAR validation HTTP '+r.status))}catch(e){setStatus('JAR validation error: '+e.message);logLine('Error during JAR validation: '+e.message)}}

    async function checkJavaVersion(){const out=document.getElementById('out');out.textContent='Checking Java version…';try{const r=await fetch('/pt/java/version');const j=await r.json();out.textContent=JSON.stringify(j,null,2)}catch(e){out.textContent='Error: '+e}}
    async function checkJarStatus(){const out=document.getElementById('out');out.textContent='Checking JAR status…';try{const r=await fetch('/pt/jar/status');const j=await r.json();out.textContent=JSON.stringify(j,null,2)}catch(e){out.textContent='Error: '+e}}
    async function runJarCheck(){const out=document.getElementById('out');out.textContent='Running JAR check…';try{const r=await fetch('/pt/jar/run-check');const j=await r.json();out.textContent=JSON.stringify(j,null,2)}catch(e){out.textContent='Error: '+e}}
    async function pingApi(){setStatus('Pinging API…');try{const r1=await fetch('/health');const t1=await r1.text();logLine(`/health -> ${r1.status}`);logLine(`/health body: ${t1.slice(0,200)}`);const r2=await fetch('/health/db');const t2=await r2.text();logLine(`/health/db -> ${r2.status}`);logLine(`/health/db body: ${t2.slice(0,200)}`);setStatus('Ping done.')}catch(e){setStatus('Ping error: '+e.message);logLine('Ping error: '+e.message)}}
    async function diagAll(){logLine('Starting diagnostics…');await pingApi();await checkJavaVersion();await checkJarStatus();try{if(state.token){const r=await fetch('/auth/me',{headers:{'Authorization':'Bearer '+state.token}});const t=await r.text();logLine(`/auth/me -> ${r.status}`);logLine(`/auth/me body: ${t.slice(0,200)}`)}else{logLine('No token set; skipping /auth/me')}}catch(e){logLine('auth/me error: '+e.message)}logLine('Diagnostics finished.')}

    function setStatus(m){document.getElementById('status').textContent=m}
    async function registerUser(){const u=document.getElementById('u_user').value.trim();const p=document.getElementById('u_pass').value;if(!u||!p){setStatus('Fill username and password to register.');return}setStatus('Registering…');try{const r=await fetch('/auth/register',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({username:u,password:p})});if(!r.ok){const t=await r.text();throw new Error(t)}setStatus('Registered. Now login.')}catch(e){setStatus('Register error: '+e.message)}}
    async function loginUser(){const u=document.getElementById('l_user').value.trim();const p=document.getElementById('l_pass').value;if(!u||!p){setStatus('Fill username and password to login.');return}setStatus('Logging in…');try{const fd=new URLSearchParams();fd.set('username',u);fd.set('password',p);const r=await fetch('/auth/token',{method:'POST',headers:{'Content-Type':'application/x-www-form-urlencoded'},body:fd});const j=await r.json();if(!r.ok)throw new Error(j.detail||'Login failed');state.token=j.access_token;setStatus('Logged in. Token ready.');document.getElementById('token_status').textContent='Authenticated'}catch(e){setStatus('Login error: '+e.message)}}
    async function loginDev(){try{document.getElementById('l_user').value='dev';document.getElementById('l_pass').value='dev';logLine('Login dev/dev clicked.');setStatus('Logging in as dev/dev…');await loginUser();logLine('Login dev/dev finished. Token set: '+(state.token?'yes':'no'))}catch(e){logLine('Login dev/dev error: '+(e&&e.message?e.message:e));setStatus('Login dev/dev error: '+(e&&e.message?e.message:e))}}
    async function saveAT(){if(!state.token){setStatus('Login first.');return}const au=document.getElementById('at_user').value.trim();const ap=document.getElementById('at_pass').value;if(!au||!ap){setStatus('Fill AT username and password.');return}setStatus('Saving AT credentials…');try{const r=await fetch('/pt/secrets/at',{method:'POST',headers:{'Content-Type':'application/json','Authorization':'Bearer '+state.token},body:JSON.stringify({username:au,password:ap})});const j=await r.json();if(!r.ok)throw new Error(j.detail||'Failed to save');setStatus('AT credentials saved (encrypted).')}catch(e){setStatus('Save AT error: '+e.message)}}
    function onFileChange(ev){state.file=ev.target.files[0]||null}
    async function presignUpload(){if(!state.token){setStatus('Login first.');return}if(!state.file){setStatus('Choose a file first.');return}setStatus('Requesting presigned URL…');try{const r=await fetch('/pt/files/presign-upload',{method:'POST',headers:{'Content-Type':'application/json','Authorization':'Bearer '+state.token},body:JSON.stringify({filename:state.file.name,content_type:state.file.type||'application/octet-stream'})});const j=await r.json();if(!r.ok)throw new Error(j.detail||'Failed to presign');setStatus('Uploading via presigned URL…');const put=await fetch(j.url,{method:'PUT',headers:j.headers||{},body:state.file});if(!put.ok&&put.status!==200&&put.status!==201)throw new Error('PUT failed with status '+put.status);state.objectKey=j.object;setStatus('Uploaded. object_key='+state.objectKey);document.getElementById('object_key').textContent=state.objectKey}catch(e){setStatus('Presign/Upload error: '+e.message)}}
    async function submitFile(){if(!state.token){setStatus('Login first.');return}if(!state.objectKey){setStatus('Upload first to get object_key.');return}setStatus('Submitting…');try{const r=await fetch('/pt/submit?object_key='+encodeURIComponent(state.objectKey),{method:'POST',headers:{'Authorization':'Bearer '+state.token}});const j=await r.json();if(!r.ok)throw new Error(j.detail||'Submit failed');setStatus('Submit OK.');document.getElementById('out').textContent=JSON.stringify(j,null,2)}catch(e){setStatus('Submit error: '+e.message)}}
    async function presignDownload(){if(!state.token){setStatus('Login first.');return}const key=(document.getElementById('dl_key').value||'').trim();if(!key){setStatus('Provide an object_key.');return}setStatus('Requesting download URL…');try{const r=await fetch('/pt/files/presign-download',{method:'POST',headers:{'Content-Type':'application/json','Authorization':'Bearer '+state.token},body:JSON.stringify({object_key:key})});const j=await r.json();if(!r.ok)throw new Error(j.detail||'Failed to presign download');document.getElementById('dl_url').textContent=j.url||'(no url)';document.getElementById('out').textContent=JSON.stringify(j,null,2);setStatus('Download URL ready.')}catch(e){setStatus('Presign download error: '+e.message)}}
    async function loadCredsStatus(){if(!state.token){setStatus('Login first.');return}try{const r=await fetch('/pt/secrets/at/status',{headers:{'Authorization':'Bearer '+state.token}});const j=await r.json();document.getElementById('creds_user_mask').textContent=j.username_masked||'(none)';document.getElementById('creds_updated').textContent=j.updated_at||'(unknown)';setStatus(j.ok?'Credentials status loaded.':'No credentials saved.')}catch(e){setStatus('Load creds error: '+e.message)}}
    async function saveAT2(){if(!state.token){setStatus('Login first.');return}const au=document.getElementById('at_user2').value.trim();const ap=document.getElementById('at_pass2').value;if(!au||!ap){setStatus('Fill AT username and password.');return}setStatus('Saving AT credentials…');try{const r=await fetch('/pt/secrets/at',{method:'POST',headers:{'Content-Type':'application/json','Authorization':'Bearer '+state.token},body:JSON.stringify({username:au,password:ap})});const j=await r.json();if(!r.ok)throw new Error(j.detail||'Failed to save creds');setStatus('AT credentials saved.');loadCredsStatus()}catch(e){setStatus('Save AT error: '+e.message)}}
    async function analyzeAndSave(){if(!state.token){setStatus('Login first.');return}const fI=document.getElementById('file');if(!fI.files.length){setStatus('Choose a SAFT XML file');return}setStatus('Analyzing…');try{const f=fI.files[0];const fd=new FormData();fd.append('file',f);const r=await fetch('/pt/analyze',{method:'POST',headers:{'Authorization':'Bearer '+state.token},body:fd});const txt=await r.text();let data=null;try{data=txt?JSON.parse(txt):null}catch(_){}if(!r.ok)throw new Error((data&&data.detail)||(txt?txt.slice(0,300):'Analyze failed'));document.getElementById('out').textContent=JSON.stringify(data,null,2);if(data.object_key){state.objectKey=data.object_key;document.getElementById('object_key').textContent=state.objectKey}setStatus('Analysis saved.')}catch(e){setStatus('Analyze error: '+e.message)}}
    async function saveNifEntry(){if(!state.token){setStatus('Login first.');return}const ident=(document.getElementById('nif_ident').value||'').trim();const pass=document.getElementById('nif_pass').value;if(!ident||!pass){setStatus('Preenche NIF e senha.');return}setStatus('A guardar senha para NIF '+ident+'…');try{const r=await fetch('/pt/secrets/at/entries',{method:'POST',headers:{'Content-Type':'application/json','Authorization':'Bearer '+state.token},body:JSON.stringify({ident,password:pass})});const j=await r.json();if(!r.ok)throw new Error(j.detail||'Falha ao guardar');setStatus('Senha guardada para NIF '+ident+'.');await loadNifEntries()}catch(e){setStatus('Erro a guardar NIF: '+e.message)}}
    async function loadNifEntries(){if(!state.token){setStatus('Login first.');return}setStatus('A carregar NIFs…');try{const r=await fetch('/pt/secrets/at/entries',{headers:{'Authorization':'Bearer '+state.token}});const j=await r.json();if(!r.ok)throw new Error(j.detail||'Falha ao listar');document.getElementById('nif_list').textContent=JSON.stringify(j.items||[],null,2);setStatus('NIFs carregados.')}catch(e){setStatus('Erro a listar NIFs: '+e.message)}}
  </script>
</head>
<body>
  <header>
    <h1>SAFT Doctor • Validator <small style=\"font-weight:400;color:#6b7280\">diag-2025-10-20-3</small></h1>
    <div style=\"font-size:.9rem;color:#6b7280\">Marker: DIAGNOSTICS-ENABLED</div>
    <p>Upload a SAFT XML to validate basic structure and header fields.</p>
  </header>
  <div class=\"card\">
    <div class=\"row\">
      <input type=\"file\" id=\"file\" accept=\".xml,text/xml\" onchange=\"onFileChange(event)\" />
      <button class=\"btn\" id=\"btn\" onclick=\"validate()\">Validate</button>
      <button class=\"btn\" onclick=\"validateWithJar()\">Validate with JAR</button>
    </div>
    <div class=\"mt\">
      <div>Estado JS: <code id=\"js_ok\">(loading…)</code></div>
      <div>Comando (mascarado): <code id=\"cmd_mask\">(n/a)</code></div>
      <pre id=\"out\"></pre>
    </div>
  </div>

  <div class=\"card\" style=\"margin-top:1rem;\">
    <div class=\"log-header\">
      <h3 style=\"margin:0;\">Log</h3>
      <div class=\"log-actions\"><button class=\"btn\" onclick=\"clearLog()\">Clear log</button></div>
    </div>
    <pre id=\"log\" style=\"min-height:160px;\" aria-label=\"Execution log\"></pre>
  </div>

  <div class=\"card\" style=\"margin-top:1rem;\">
    <div class=\"row\">
      <button class=\"btn\" onclick=\"checkJavaVersion()\">Java version</button>
      <button class=\"btn\" onclick=\"checkJarStatus()\">Check JAR status</button>
      <button class=\"btn\" onclick=\"runJarCheck()\">Run JAR check</button>
      <button class=\"btn\" onclick=\"pingApi()\">Ping API</button>
      <button class=\"btn\" onclick=\"diagAll()\">Diagnostics</button>
    </div>
  </div>

  <div class=\"card\" style=\"margin-top:1rem;\">
    <h3>Auth</h3>
    <div class=\"row mt\">
      <input placeholder=\"Register: username\" id=\"u_user\" />
      <input placeholder=\"Register: password\" id=\"u_pass\" type=\"password\" />
      <button class=\"btn\" onclick=\"registerUser()\">Register</button>
    </div>
    <div class=\"row mt\">
      <input placeholder=\"Login: username\" id=\"l_user\" />
      <input placeholder=\"Login: password\" id=\"l_pass\" type=\"password\" />
      <button class=\"btn\" onclick=\"loginUser()\">Login</button>
      <button class=\"btn\" onclick=\"loginDev()\" title=\"Quick dev login\">Login dev/dev</button>
      <span id=\"token_status\" class=\"ok\" style=\"margin-left:.5rem;\">Not authenticated</span>
    </div>
    <div class=\"row mt\">
      <button class=\"btn\" onclick=\"(async()=>{ try { const r=await fetch('/auth/me',{ headers: state.token? { Authorization: 'Bearer '+state.token } : {} }); const t=await r.text(); setStatus('Auth self-test HTTP '+r.status+': '+t.slice(0,200)); } catch(e){ setStatus('Self-test error: '+e.message);} })()\">Self-test</button>
    </div>
  </div>

  <div class=\"card\" style=\"margin-top:1rem;\"><h3>AT Secrets (requires login)</h3><p>AT credentials are saved encrypted on the server only after login.</p><div class=\"row mt\"><input placeholder=\"AT username\" id=\"at_user\" /><input placeholder=\"AT password\" id=\"at_pass\" type=\"password\" /><button class=\"btn\" onclick=\"saveAT()\">Save AT</button><button class=\"btn\" onclick=\"(async ()=>{ document.getElementById('at_user').value='teste'; document.getElementById('at_pass').value='segredo'; await saveAT(); })()\">Guardar AT de teste</button></div></div>

  <div class=\"card\" style=\"margin-top:1rem;\"><h3>Upload & Submit (requires login)</h3><div class=\"row mt\"><button class=\"btn\" onclick=\"presignUpload()\">Upload via Presign</button><span>object_key: <code id=\"object_key\">(none)</code></span></div><div class=\"row mt\"><button class=\"btn\" onclick=\"submitFile()\">Submit</button><button class=\"btn\" onclick=\"analyzeAndSave()\">Analyze & save</button></div></div>

  <div class=\"card\" style=\"margin-top:1rem;\"><h3>Presigned Download (opcional)</h3><div class=\"row mt\"><input id=\"dl_key\" placeholder=\"object_key (e.g. pt/tools/FACTEMICLI.jar)\" value=\"pt/tools/FACTEMICLI.jar\" /><button class=\"btn\" onclick=\"presignDownload()\">Get download URL</button></div><div class=\"mt\">URL: <code id=\"dl_url\">(none)</code></div></div>

  <div class=\"card\" style=\"margin-top:1rem;\"><h3>Credenciais AT</h3><div class=\"row mt\"><button class=\"btn\" onclick=\"loadCredsStatus()\">Atualizar estado</button><span>Username (mask): <code id=\"creds_user_mask\">(unknown)</code></span><span>Atualizado em: <code id=\"creds_updated\">(unknown)</code></span></div></div>

  <div class=\"card\" style=\"margin-top:1rem;\"><h3>Atualizar credenciais AT</h3><div class=\"row mt\"><input placeholder=\"AT username\" id=\"at_user2\" /><input placeholder=\"AT password\" id=\"at_pass2\" type=\"password\" /><button class=\"btn\" onclick=\"saveAT2()\">Guardar</button></div></div>

  <div class=\"card\" style=\"margin-top:1rem;\"><h3>Senhas por NIF (recomendado)</h3><p>Guarda a senha AT associada a cada NIF. A validação/submissão escolhe automaticamente pela NIF do XML.</p><div class=\"row mt\"><input placeholder=\"NIF (ident)\" id=\"nif_ident\" /><input placeholder=\"Senha AT\" id=\"nif_pass\" type=\"password\" /><button class=\"btn\" onclick=\"saveNifEntry()\">Guardar NIF</button></div><div class=\"mt\"><button class=\"btn\" onclick=\"loadNifEntries()\">Listar NIFs</button></div><div class=\"mt\"><pre id=\"nif_list\">(vazio)</pre></div></div>

  <p id=\"status\" class=\"mt\"></p>
</body>
</html>
"""


@app.get('/', response_class=HTMLResponse, tags=['UI'])
def root_ui():
    return HTMLResponse(content=UI_HTML, headers={'Cache-Control': 'no-store'})


@app.get('/ui', response_class=HTMLResponse, tags=['UI'])
def ui_page():
    return HTMLResponse(content=UI_HTML, headers={'Cache-Control': 'no-store'})


@app.get('/ui/check', tags=['UI'])
def ui_check():
    try:
        uri = os.getenv('MONGO_URI') or 'mongodb://mongo:27017'
        if '://' in uri and '@' in uri:
            scheme, rest = uri.split('://', 1)
            if '@' in rest and ':' in rest.split('@', 1)[0]:
                creds, host = rest.split('@', 1)
                user = creds.split(':', 1)[0]
                uri = f"{scheme}://{user}:***@{host}"
            else:
                uri = f"{scheme}://***"
    except Exception:
        pass
    return JSONResponse({
        'ui_version': 'diag-2025-10-20-3',
        'diagnostics_enabled': True,
        'has_ping_button': ('Ping API' in UI_HTML),
        'env': os.getenv('APP_ENV', 'dev'),
        'mongo': {
            'uri': uri,
            'db': os.getenv('MONGO_DB', 'saft_doctor'),
            'scoping': os.getenv('MONGO_SCOPING', 'collection_prefix')
        }
    }, headers={'Cache-Control': 'no-store'})


@app.get('/info', tags=['Health'])
def api_info():
    return { 'name': 'SAFT Doctor API', 'status': 'ok', 'env': os.getenv('APP_ENV','dev') }


@app.get('/health', tags=['Health'])
def health():
    return { 'status': 'ok', 'env': os.getenv('APP_ENV','dev') }


@app.get('/health/db', tags=['Health'])
async def health_db(db=Depends(get_db)):
    try:
        await db.command('ping')
        return { 'ok': True }
    except Exception as e:
        return { 'ok': False, 'error': str(e) }


@app.get('/diag', tags=['Health'])
async def diagnostics(request: Request, db=Depends(get_db)):
    """Deep diagnostics for environment and dependencies.
    Returns JSON with checks for:
    - env/keys
    - MongoDB connectivity
    - Upload root directory writability
    - Java availability and JAR presence
    - B2 (S3) client configuration and basic connectivity
    """
    import time, tempfile, asyncio, os, os.path, socket, sys, platform, shutil
    from core.storage import Storage

    now = time.time()
    app_env = os.getenv('APP_ENV', 'dev')
    upload_root = os.getenv('UPLOAD_ROOT', '/var/saft/uploads')
    jar_path = os.getenv('FACTEMICLI_JAR_PATH', '/opt/factemi/FACTEMICLI.jar')

    # ENV / SECRET
    env_info = {
        'env': app_env,
        'hostname': socket.gethostname(),
        'secret_key_set': (SECRET_KEY != 'change_me'),
        'secret_key_len': len(SECRET_KEY) if isinstance(SECRET_KEY, str) else None,
        'secret_key_default': (SECRET_KEY == 'change_me'),
        'app_port': os.getenv('APP_PORT'),
        'default_country': os.getenv('DEFAULT_COUNTRY','pt'),
        'cors_origins': os.getenv('CORS_ORIGINS','*'),
        'upload_chunk_size': int(os.getenv('UPLOAD_CHUNK_SIZE', str(5*1024*1024))),
        'factemiclI_timeout': int(os.getenv('FACTEMICLI_TIMEOUT','300')),
        'python': sys.version,
        'platform': platform.platform(),
        'cpu_count': os.cpu_count(),
    }

    # DB
    db_info = { 'ok': False }
    try:
        await db.command('ping')
        db_info.update({
            'ok': True,
            'uri': os.getenv('MONGO_URI') or 'mongodb://mongo:27017',
            'db': os.getenv('MONGO_DB','saft_doctor'),
            'scoping': os.getenv('MONGO_SCOPING','collection_prefix')
        })
    except Exception as e:
        db_info.update({ 'ok': False, 'error': str(e) })

    # Upload root
    upload_info = { 'path': upload_root, 'ok': False }
    try:
        os.makedirs(upload_root, mode=0o755, exist_ok=True)
        test_path = os.path.join(upload_root, f'.diag_{int(now)}.tmp')
        with open(test_path, 'w', encoding='utf-8') as f:
            f.write('ok')
        os.remove(test_path)
        total, used, free = shutil.disk_usage(upload_root)
        upload_info.update({ 'ok': True, 'writable': True, 'disk': { 'total': total, 'used': used, 'free': free } })
    except Exception as e:
        upload_info.update({ 'ok': False, 'writable': False, 'error': str(e) })

    # Java
    java_info = { 'ok': False }
    try:
        proc = await asyncio.create_subprocess_exec(
            'java','-version', stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
        )
        try:
            out, err = await asyncio.wait_for(proc.communicate(), timeout=5)
        except asyncio.TimeoutError:
            proc.kill(); out, err = b'', b'timeout'
        java_info.update({
            'ok': (proc.returncode == 0 or proc.returncode is not None),
            'returncode': proc.returncode,
            'stdout': (out.decode() if out else ''),
            'stderr': (err.decode() if err else ''),
        })
    except Exception as e:
        java_info.update({ 'ok': False, 'error': str(e) })

    # JAR
    jar_info = {
        'path': jar_path,
        'exists': os.path.isfile(jar_path),
        'size': None
    }
    try:
        if jar_info['exists']:
            jar_info['size'] = os.path.getsize(jar_path)
    except Exception:
        pass

    # B2 / S3 client
    b2_info = {
        'endpoint': os.getenv('B2_ENDPOINT'),
        'region': os.getenv('B2_REGION'),
        'bucket': os.getenv('B2_BUCKET'),
        'key_id_set': bool(os.getenv('B2_KEY_ID')),
        'app_key_set': bool(os.getenv('B2_APP_KEY')),
        'ok': False
    }
    try:
        storage = Storage()
        # Try head_bucket first (requires permission), else report error
        def _try_checks():
            try:
                storage.client.head_bucket(Bucket=storage.bucket)
                # Optionally try a very light list (may still fail on perms)
                try:
                    storage.client.list_objects_v2(Bucket=storage.bucket, MaxKeys=1)
                except Exception:
                    pass
                return True, None
            except Exception as ex:
                return False, str(ex)
        ok, err = await asyncio.to_thread(_try_checks)
        b2_info['ok'] = ok
        if not ok:
            b2_info['error'] = err
    except Exception as e:
        b2_info.update({ 'ok': False, 'error': str(e) })

    # Mongo socket connectivity (best-effort)
    mongo_sock = { 'ok': False }
    try:
        uri = os.getenv('MONGO_URI') or 'mongodb://mongo:27017'
        from urllib.parse import urlparse
        p = urlparse(uri)
        host = p.hostname or 'mongo'
        port = p.port or 27017
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(3.0)
        try:
            sock.connect((host, port))
            mongo_sock.update({ 'ok': True, 'host': host, 'port': port })
        finally:
            try: sock.close()
            except Exception: pass
    except Exception as e:
        mongo_sock.update({ 'ok': False, 'error': str(e) })

    return {
        'ok': (env_info['secret_key_set'] and db_info.get('ok') and upload_info.get('ok')),
        'env': env_info,
        'db': db_info,
        'db_socket': mongo_sock,
        'upload': upload_info,
        'java': java_info,
        'jar': jar_info,
        'b2': b2_info,
        'time': int(now)
    }


@app.post('/auth/register', tags=['Authentication'])
async def register(user: RegisterIn, request: Request, db=Depends(get_db)):
    country = country_from_request(request)
    repo = UsersRepo(db, country)
    try:
        if await repo.exists(user.username):
            raise HTTPException(status_code=400, detail='Username already exists')
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Registration exists check failed", extra={'error': str(e)})
        raise HTTPException(status_code=503, detail='Database unavailable (exists check).')
    try:
        pwd_hash = hash_password(user.password)
    except Exception as e:
        logger.error("Password hashing failed", extra={'error': str(e)})
        raise HTTPException(status_code=500, detail=f"Server crypto error while hashing password: {e.__class__.__name__}")
    try:
        created = await repo.create(user.username, pwd_hash, user.email)
        return { 'id': str(created['_id']), 'username': created['username'], 'country': country }
    except Exception as e:
        logger.error("Registration failed at create", extra={'error': str(e)})
        raise HTTPException(status_code=503, detail='Database unavailable (create).')


@app.post('/auth/token', tags=['Authentication'])
async def login(form_data: OAuth2PasswordRequestForm = Depends(), request: Request = None, db=Depends(get_db)):
    country = country_from_request(request)
    repo = UsersRepo(db, country)
    try:
        u = await repo.get(form_data.username)
    except Exception as e:
        logger.error("Login failed at get(user)", extra={'error': str(e)})
        raise HTTPException(status_code=503, detail='Database unavailable (get user).')
    try:
        if not u or not verify_password(form_data.password, u['password_hash']):
            raise HTTPException(status_code=400, detail='Incorrect username or password')
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Password verification failed", extra={'error': str(e)})
        raise HTTPException(status_code=500, detail='Server crypto error while verifying password.')
    token = create_access_token({'sub': form_data.username, 'cty': country})
    return { 'access_token': token, 'token_type': 'bearer' }


async def get_current_user(request: Request, token: str = Depends(oauth2_scheme), db=Depends(get_db)):
    country = country_from_request(request)
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get('sub')
        if not username:
            raise HTTPException(status_code=401, detail='Invalid token')
    except JWTError:
        raise HTTPException(status_code=401, detail='Invalid token')
    repo = UsersRepo(db, country)
    u = await repo.get(username)
    if not u:
        raise HTTPException(status_code=401, detail='User not found')
    return { 'username': username, 'country': country }


@app.get('/auth/me', tags=['Authentication'])
async def auth_me(current=Depends(get_current_user)):
    return current


@app.get('/auth/profile', tags=['Authentication'])
async def get_profile(current=Depends(get_current_user), db=Depends(get_db)):
    """
    Get current user's profile including email
    """
    username = current['username']
    country = current.get('country', 'pt')
    repo = UsersRepo(db, country)

    try:
        user = await repo.get(username)
        if not user:
            raise HTTPException(status_code=404, detail='User not found')

        email_value = user.get('email')
        logger.info(f"Profile loaded for {username}: email={'set' if email_value else 'not set'}")

        return {
            'username': user['username'],
            'email': email_value if email_value else None,
            'country': country
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting profile: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail='Error getting profile')


@app.post('/auth/profile/email', tags=['Authentication'])
async def update_profile_email(email: str, current=Depends(get_current_user), db=Depends(get_db)):
    """
    Update current user's email address
    """
    username = current['username']
    country = current.get('country', 'pt')
    repo = UsersRepo(db, country)

    try:
        # Validate email format (basic validation)
        if email and '@' not in email:
            raise HTTPException(status_code=400, detail='Email inválido')

        # Update email
        await repo.update_email(username, email)

        logger.info(f"✅ Email updated for user {username}")

        return {
            'ok': True,
            'message': 'Email atualizado com sucesso',
            'email': email
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating email: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail='Erro ao atualizar email')


# Password Reset Endpoints
from core.models import PasswordResetRequestIn, PasswordResetRequestOut, PasswordResetConfirmIn, PasswordResetConfirmOut
from core.password_reset_repo import PasswordResetRepo
from core.email_service import get_email_service

@app.post('/auth/password-reset/request', tags=['Authentication'], response_model=PasswordResetRequestOut)
async def request_password_reset(data: PasswordResetRequestIn, request: Request, db=Depends(get_db)):
    """
    Request password reset - sends email with reset token

    Security: Always returns success even if username doesn't exist (prevents user enumeration)
    """
    country = country_from_request(request)
    repo = UsersRepo(db, country)
    reset_repo = PasswordResetRepo(db)
    email_service = get_email_service()

    try:
        # Get user
        user = await repo.get(data.username)

        if not user:
            # Security: Don't reveal if username exists
            logger.info(f"Password reset requested for non-existent user: {data.username}")
            return PasswordResetRequestOut(
                ok=True,
                message="Se o username existir e tiver email configurado, receberá um email com instruções."
            )

        # Check if user has email
        user_email = user.get('email')
        if not user_email:
            logger.warning(f"User {data.username} has no email configured")
            return PasswordResetRequestOut(
                ok=False,
                message="Este utilizador não tem email configurado. Por favor, faça login e adicione um email no seu Perfil (botão ⚙️ Perfil na barra superior)."
            )

        # Generate reset token
        reset_token = await reset_repo.create_reset_token(data.username, user_email)

        # Send email
        if email_service.is_configured():
            email_sent = email_service.send_password_reset_email(
                to_email=user_email,
                username=data.username,
                reset_token=reset_token
            )

            if email_sent:
                logger.info(f"✅ Password reset email sent to {user_email} for user {data.username}")
                return PasswordResetRequestOut(
                    ok=True,
                    message=f"Email enviado para {user_email}. Verifique a sua caixa de entrada e spam."
                )
            else:
                logger.error(f"❌ Failed to send password reset email to {user_email}")
                return PasswordResetRequestOut(
                    ok=False,
                    message="Erro ao enviar email. Contacte o suporte técnico."
                )
        else:
            logger.error("❌ SMTP not configured. Cannot send password reset email.")
            return PasswordResetRequestOut(
                ok=False,
                message="Serviço de email não configurado. Contacte o administrador do sistema."
            )

    except Exception as e:
        logger.error(f"Error in password reset request: {e}", exc_info=True)
        return PasswordResetRequestOut(
            ok=False,
            message="Erro ao processar pedido. Tente novamente mais tarde."
        )


@app.post('/auth/password-reset/confirm', tags=['Authentication'], response_model=PasswordResetConfirmOut)
async def confirm_password_reset(data: PasswordResetConfirmIn, request: Request, db=Depends(get_db)):
    """
    Confirm password reset with token and set new password
    """
    country = country_from_request(request)
    repo = UsersRepo(db, country)
    reset_repo = PasswordResetRepo(db)
    email_service = get_email_service()

    try:
        # Validate token
        token_doc = await reset_repo.validate_token(data.token)

        if not token_doc:
            logger.warning(f"Invalid or expired password reset token")
            return PasswordResetConfirmOut(
                ok=False,
                message="Link de recuperação inválido ou expirado. Solicite um novo link."
            )

        username = token_doc['username']
        user_email = token_doc['email']

        # Validate new password
        if len(data.new_password) < 3:
            return PasswordResetConfirmOut(
                ok=False,
                message="Password deve ter pelo menos 3 caracteres."
            )

        # Hash new password
        from core.security import hash_password
        new_hash = hash_password(data.new_password)

        # Update password in database
        await repo.update_password(username, new_hash)

        # Mark token as used
        await reset_repo.mark_token_used(data.token)

        logger.info(f"✅ Password reset successful for user {username}")

        # Send confirmation email
        if email_service.is_configured():
            email_service.send_password_changed_notification(user_email, username)

        return PasswordResetConfirmOut(
            ok=True,
            message="Password alterada com sucesso! Já pode fazer login com a nova password."
        )

    except Exception as e:
        logger.error(f"Error in password reset confirm: {e}", exc_info=True)
        return PasswordResetConfirmOut(
            ok=False,
            message="Erro ao alterar password. Tente novamente."
        )


@app.get('/auth/check-reset-token', tags=['Authentication'])
async def check_reset_token(token: str, db=Depends(get_db)):
    """
    Check if a password reset token is valid (for frontend validation)
    """
    reset_repo = PasswordResetRepo(db)

    try:
        token_doc = await reset_repo.validate_token(token)

        if token_doc:
            return {
                'ok': True,
                'valid': True,
                'username': token_doc['username']
            }
        else:
            return {
                'ok': True,
                'valid': False,
                'reason': 'Token inválido ou expirado'
            }

    except Exception as e:
        logger.error(f"Error checking reset token: {e}")
        return {
            'ok': False,
            'valid': False,
            'reason': 'Erro ao validar token'
        }


# PT router
from saft_pt_doctor.routers_pt import router as router_pt
app.include_router(router_pt, prefix='/pt')


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
import os
from fastapi import FastAPI, Depends, HTTPException, UploadFile, File, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from jose import jwt, JWTError
from pydantic import BaseModel, Field

from core.deps import get_db
from core.auth_utils import create_access_token, hash_password, verify_password
from core.auth_repo import UsersRepo
from core.logging_config import setup_logging, get_logger
from core.middleware import RequestLoggingMiddleware


# -----------------------------------------------------------------------------
# App setup
# -----------------------------------------------------------------------------
setup_logging(level=os.getenv('LOG_LEVEL', 'INFO'))
logger = get_logger(__name__)

SECRET_KEY = os.getenv('SECRET_KEY', 'change_me')
ALGORITHM = 'HS256'

oauth2_scheme = OAuth2PasswordBearer(tokenUrl='/auth/token')

app = FastAPI(
    title='SAFT Doctor (multi-country)',
    version='0.2.0',
    description='API multi-país para processamento e submissão de arquivos SAFT.'
)

app.add_middleware(RequestLoggingMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv('CORS_ORIGINS', '*').split(','),
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*']
)

try:
    app.mount('/static', StaticFiles(directory='static'), name='static')
except Exception:
    pass


# -----------------------------------------------------------------------------
# Helper models and functions
# -----------------------------------------------------------------------------
class RegisterIn(BaseModel):
    username: str = Field(min_length=1)
    password: str = Field(min_length=1)
    email: Optional[str] = None  # Optional email for password reset


def country_from_request(request: Request) -> str:
    parts = [p for p in request.url.path.split('/') if p]
    if parts and parts[0] in {'pt', 'es', 'fr', 'it', 'de'}:
        return parts[0]
    return os.getenv('DEFAULT_COUNTRY', 'pt')


# -----------------------------------------------------------------------------
# Inline UI (single page) - diagnostics-enabled
# -----------------------------------------------------------------------------
UI_HTML = """
<!doctype html>
<html lang=\"en\">
<head>
  <meta charset=\"utf-8\" />
  <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\" />
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
    .note { background: #fff7ed; border: 1px solid #fed7aa; color: #7c2d12; padding: .8rem; border-radius: 8px; }
    .log-header { display:flex; align-items:center; justify-content: space-between; }
    .log-actions { display:flex; gap:.5rem; }
  </style>
  <script>
    const state = { token: null, objectKey: null, file: null };
    function logLine(msg) {
      const el = document.getElementById('log');
      const ts = new Date().toISOString();
      el.textContent += `[${ts}] ${msg}\\n`;
      el.scrollTop = el.scrollHeight;
    }
    function clearLog(){ const el=document.getElementById('log'); el.textContent=''; }
    window.addEventListener('error', (e) => { try { setStatus('JS error: ' + (e.message || '(no message)')); } catch(_){} });
    window.addEventListener('unhandledrejection', (e) => { try { logLine('Unhandled rejection: ' + (e.reason && e.reason.message ? e.reason.message : e.reason)); } catch(_){} });
    (function(){
      const orig = window.fetch;
      window.fetch = async function(input, init){
        try {
          const url = (typeof input === 'string') ? input : (input && input.url) || '';
          const method = (init && init.method) || 'GET';
          logLine(`[fetch] ${method} ${url}`);
        } catch(_){}
        const res = await orig(input, init);
        try { logLine(`[fetch] -> ${res.status} ${res.statusText || ''}`.trim()); } catch(_){}
        return res;
      };
    })();
    window.addEventListener('DOMContentLoaded', () => {
      try { document.getElementById('js_ok').textContent = 'JS loaded'; } catch(_){}
      try { logLine('[init] UI loaded'); } catch(_){}
    });

    async function validate(){
      const fileInput = document.getElementById('file');
      const out = document.getElementById('out');
      const btn = document.getElementById('btn');
      out.textContent = '';
      if (!fileInput.files.length) { out.textContent='Choose a SAFT XML file'; return; }
      const f = fileInput.files[0];
      const fd = new FormData(); fd.append('file', f);
      btn.disabled = true; btn.textContent = 'Validating…';
      try {
        const r = await fetch('/ui/validate', { method:'POST', body: fd });
        const j = await r.json();
        out.textContent = JSON.stringify(j, null, 2);
      } catch(e){ out.textContent = 'Error: ' + e; }
      finally { btn.disabled=false; btn.textContent='Validate'; }
    }

    async function validateWithJar(){
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
        const r = await fetch('/pt/validate-jar?full=1', { method:'POST', headers: { 'Authorization': 'Bearer ' + state.token }, body: fd });
        const txt = await r.text();
        let data = null; try { data = txt ? JSON.parse(txt) : null; } catch(_){}
        out.textContent = data ? JSON.stringify(data, null, 2) : (txt || '(no body)');
        if (data && data.cmd_masked && Array.isArray(data.cmd_masked)){
          cmdEl.textContent = data.cmd_masked.join(' ');
          logLine('Command (masked): ' + data.cmd_masked.join(' '));
          if (typeof data.returncode !== 'undefined' && data.returncode !== null) logLine('Return code: ' + data.returncode + (data.ok === false ? ' (error)' : ''));
          if (data.stderr){
            const preview = (data.stderr.length > 400 ? data.stderr.slice(0,400) + '…' : data.stderr);
            if (preview.trim()) logLine('Stderr preview: ' + preview.split('\\n').join(' | '));
          }
        } else {
          cmdEl.textContent='(n/a)'; logLine('No command returned by API.');
        }
        setStatus(r.ok ? 'JAR validation done.' : ('JAR validation HTTP ' + r.status));
      } catch(e){ setStatus('JAR validation error: ' + e.message); logLine('Error during JAR validation: ' + e.message); }
    }

    async function checkJarStatus(){
      const out = document.getElementById('out'); out.textContent='Checking JAR status…';
      try { const r=await fetch('/pt/jar/status'); const j=await r.json(); out.textContent=JSON.stringify(j,null,2); }
      catch(e){ out.textContent='Error: ' + e; }
    }

    async function runJarCheck(){
      const out = document.getElementById('out'); out.textContent='Running JAR check…';
      try { const r=await fetch('/pt/jar/run-check'); const j=await r.json(); out.textContent=JSON.stringify(j,null,2); }
      catch(e){ out.textContent='Error: ' + e; }
    }

    async function pingApi(){
      setStatus('Pinging API…');
      try {
        const r1 = await fetch('/health'); const t1 = await r1.text();
        logLine(`/health -> ${r1.status}`); logLine(`/health body: ${t1.slice(0,200)}`);
        const r2 = await fetch('/health/db'); const t2 = await r2.text();
        logLine(`/health/db -> ${r2.status}`); logLine(`/health/db body: ${t2.slice(0,200)}`);
        setStatus('Ping done.');
      } catch(e){ setStatus('Ping error: ' + e.message); logLine('Ping error: ' + e.message); }
    }

    async function diagAll(){
      logLine('Starting diagnostics…');
      await pingApi();
      await checkJavaVersion();
      await checkJarStatus();
      try {
        if (state.token) {
          const r = await fetch('/auth/me', { headers: { 'Authorization': 'Bearer ' + state.token } });
          const t = await r.text();
          logLine(`/auth/me -> ${r.status}`); logLine(`/auth/me body: ${t.slice(0,200)}`);
        } else { logLine('No token set; skipping /auth/me'); }
      } catch(e){ logLine('auth/me error: ' + e.message); }
      logLine('Diagnostics finished.');
    }

    async function checkJavaVersion(){
      const out = document.getElementById('out'); out.textContent='Checking Java version…';
      try { const r=await fetch('/pt/java/version'); const j=await r.json(); out.textContent=JSON.stringify(j,null,2); }
      catch(e){ out.textContent='Error: ' + e; }
    }

    async function installJar(){
      if (!state.token) { setStatus('Login first.'); return; }
      const key = (document.getElementById('jar_key').value || '').trim();
      if (!key) { setStatus('Provide an object_key.'); return; }
      setStatus('Installing JAR…');
      try {
        const r = await fetch('/pt/jar/install', { method:'POST', headers: { 'Content-Type': 'application/json', 'Authorization': 'Bearer ' + state.token }, body: JSON.stringify({ object_key: key }) });
        const txt = await r.text(); let data=null; try { data = txt ? JSON.parse(txt) : null; } catch(_){}
        if (!r.ok) { const msg = data && data.detail ? data.detail : (txt ? txt.slice(0,300) : 'Install failed'); throw new Error(msg); }
        const j = data || {}; setStatus('JAR installed at ' + (j.path || '(unknown)') + ' (' + ((j.size != null ? j.size : '?')) + ' bytes)');
        const out = document.getElementById('out'); out.textContent = data ? JSON.stringify(j, null, 2) : (txt || 'OK');
      } catch(e){ setStatus('Install error: ' + e.message); }
    }

    function setStatus(msg){ const s=document.getElementById('status'); s.textContent=msg; }

    async function registerUser(){
      const u = document.getElementById('u_user').value.trim();
      const p = document.getElementById('u_pass').value;
      if (!u || !p) { setStatus('Fill username and password to register.'); return; }
      setStatus('Registering…');
      try {
        const r = await fetch('/auth/register', { method:'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ username: u, password: p }) });
        if (!r.ok) { const t=await r.text(); throw new Error(t); }
        setStatus('Registered. Now login.');
      } catch(e){ setStatus('Register error: ' + e.message); }
    }

    async function loginUser(){
      const u = document.getElementById('l_user').value.trim();
      const p = document.getElementById('l_pass').value;
      if (!u || !p) { setStatus('Fill username and password to login.'); return; }
      setStatus('Logging in…');
      try {
        const fd = new URLSearchParams(); fd.set('username', u); fd.set('password', p);
        const r = await fetch('/auth/token', { method: 'POST', headers: { 'Content-Type': 'application/x-www-form-urlencoded' }, body: fd });
        const j = await r.json(); if (!r.ok) throw new Error(j.detail || 'Login failed');
        state.token = j.access_token; setStatus('Logged in. Token ready.');
        document.getElementById('token_status').textContent = 'Authenticated';
      } catch(e){ setStatus('Login error: ' + e.message); }
    }

    async function loginDev(){
      try {
        document.getElementById('l_user').value = 'dev';
        document.getElementById('l_pass').value = 'dev';
        logLine('Login dev/dev clicked.'); setStatus('Logging in as dev/dev…');
        await loginUser();
        logLine('Login dev/dev finished. Token set: ' + (state.token ? 'yes' : 'no'));
      } catch(e){ logLine('Login dev/dev error: ' + (e && e.message ? e.message : e)); setStatus('Login dev/dev error: ' + (e && e.message ? e.message : e)); }
    }

    async function saveAT(){
      if (!state.token) { setStatus('Login first.'); return; }
      const au = document.getElementById('at_user').value.trim();
      const ap = document.getElementById('at_pass').value;
      if (!au || !ap) { setStatus('Fill AT username and password.'); return; }
      setStatus('Saving AT credentials…');
      try {
        const r = await fetch('/pt/secrets/at', { method:'POST', headers: { 'Content-Type': 'application/json', 'Authorization': 'Bearer ' + state.token }, body: JSON.stringify({ username: au, password: ap }) });
        const j = await r.json(); if (!r.ok) throw new Error(j.detail || 'Failed to save');
        setStatus('AT credentials saved (encrypted).');
      } catch(e){ setStatus('Save AT error: ' + e.message); }
    }

    function onFileChange(ev){ state.file = ev.target.files[0] || null; }

    async function presignUpload(){
      if (!state.token) { setStatus('Login first.'); return; }
      if (!state.file) { setStatus('Choose a file first.'); return; }
      setStatus('Requesting presigned URL…');
      try {
        const r = await fetch('/pt/files/presign-upload', { method:'POST', headers: { 'Content-Type': 'application/json', 'Authorization': 'Bearer ' + state.token }, body: JSON.stringify({ filename: state.file.name, content_type: state.file.type || 'application/octet-stream' }) });
        const j = await r.json(); if (!r.ok) throw new Error(j.detail || 'Failed to presign');
        setStatus('Uploading via presigned URL…');
        const put = await fetch(j.url, { method:'PUT', headers: j.headers || {}, body: state.file });
        if (!put.ok && put.status !== 200 && put.status !== 201) throw new Error('PUT failed with status ' + put.status);
        state.objectKey = j.object; setStatus('Uploaded. object_key=' + state.objectKey);
        document.getElementById('object_key').textContent = state.objectKey;
      } catch(e){ setStatus('Presign/Upload error: ' + e.message); }
    }

    async function submitFile(){
      if (!state.token) { setStatus('Login first.'); return; }
      if (!state.objectKey) { setStatus('Upload first to get object_key.'); return; }
      setStatus('Submitting…');
      try {
        const r = await fetch('/pt/submit?object_key=' + encodeURIComponent(state.objectKey), { method:'POST', headers: { 'Authorization': 'Bearer ' + state.token } });
        const j = await r.json(); if (!r.ok) throw new Error(j.detail || 'Submit failed');
        setStatus('Submit OK.');
        const out = document.getElementById('out'); out.textContent = JSON.stringify(j, null, 2);
      } catch(e){ setStatus('Submit error: ' + e.message); }
    }

    async function presignDownload(){
      if (!state.token) { setStatus('Login first.'); return; }
      const key = (document.getElementById('dl_key').value || '').trim();
      if (!key) { setStatus('Provide an object_key.'); return; }
      setStatus('Requesting download URL…');
      try {
        const r = await fetch('/pt/files/presign-download', { method:'POST', headers: { 'Content-Type': 'application/json', 'Authorization': 'Bearer ' + state.token }, body: JSON.stringify({ object_key: key }) });
        const j = await r.json(); if (!r.ok) throw new Error(j.detail || 'Failed to presign download');
        document.getElementById('dl_url').textContent = j.url || '(no url)';
        const out = document.getElementById('out'); out.textContent = JSON.stringify(j, null, 2);
        setStatus('Download URL ready.');
      } catch(e){ setStatus('Presign download error: ' + e.message); }
    }

    async function loadCredsStatus(){
      if (!state.token) { setStatus('Login first.'); return; }
      try {
        const r = await fetch('/pt/secrets/at/status', { headers: { 'Authorization': 'Bearer ' + state.token } });
        const j = await r.json();
        document.getElementById('creds_user_mask').textContent = j.username_masked || '(none)';
        document.getElementById('creds_updated').textContent = j.updated_at || '(unknown)';
        setStatus(j.ok ? 'Credentials status loaded.' : 'No credentials saved.');
      } catch(e){ setStatus('Load creds error: ' + e.message); }
    }

    async function saveAT2(){
      if (!state.token) { setStatus('Login first.'); return; }
      const au = document.getElementById('at_user2').value.trim();
      const ap = document.getElementById('at_pass2').value;
      if (!au || !ap) { setStatus('Fill AT username and password.'); return; }
      setStatus('Saving AT credentials…');
      try {
        const r = await fetch('/pt/secrets/at', { method:'POST', headers: { 'Content-Type': 'application/json', 'Authorization': 'Bearer ' + state.token }, body: JSON.stringify({ username: au, password: ap }) });
        const j = await r.json(); if (!r.ok) throw new Error(j.detail || 'Failed to save creds');
        setStatus('AT credentials saved.');
        loadCredsStatus();
      } catch(e){ setStatus('Save AT error: ' + e.message); }
    }

    async function analyzeAndSave(){
      if (!state.token) { setStatus('Login first.'); return; }
      const fileInput = document.getElementById('file');
      if (!fileInput.files.length) { setStatus('Choose a SAFT XML file'); return; }
      setStatus('Analyzing…');
      try {
        const f = fileInput.files[0];
        const fd = new FormData(); fd.append('file', f);
        const r = await fetch('/pt/analyze', { method:'POST', headers: { 'Authorization': 'Bearer ' + state.token }, body: fd });
        const txt = await r.text(); let data=null; try { data = txt ? JSON.parse(txt) : null; } catch(_){}
        if (!r.ok) throw new Error((data && data.detail) || (txt ? txt.slice(0,300) : 'Analyze failed'));
        const out = document.getElementById('out'); out.textContent = JSON.stringify(data, null, 2);
        if (data.object_key) { state.objectKey = data.object_key; document.getElementById('object_key').textContent = state.objectKey; }
        setStatus('Analysis saved.');
      } catch(e){ setStatus('Analyze error: ' + e.message); }
    }

    async function saveNifEntry(){
      if (!state.token) { setStatus('Login first.'); return; }
      const ident = (document.getElementById('nif_ident').value || '').trim();
      const pass = document.getElementById('nif_pass').value;
      if (!ident || !pass) { setStatus('Preenche NIF e senha.'); return; }
      setStatus('A guardar senha para NIF ' + ident + '…');
      try {
        const r = await fetch('/pt/secrets/at/entries', { method:'POST', headers: { 'Content-Type': 'application/json', 'Authorization': 'Bearer ' + state.token }, body: JSON.stringify({ ident, password: pass }) });
        const j = await r.json(); if (!r.ok) throw new Error(j.detail || 'Falha ao guardar');
        setStatus('Senha guardada para NIF ' + ident + '.');
        await loadNifEntries();
      } catch(e){ setStatus('Erro a guardar NIF: ' + e.message); }
    }

    async function loadNifEntries(){
      if (!state.token) { setStatus('Login first.'); return; }
      setStatus('A carregar NIFs…');
      try {
        const r = await fetch('/pt/secrets/at/entries', { headers: { 'Authorization': 'Bearer ' + state.token } });
        const j = await r.json(); if (!r.ok) throw new Error(j.detail || 'Falha ao listar');
        const out = document.getElementById('nif_list'); out.textContent = JSON.stringify(j.items || [], null, 2);
        setStatus('NIFs carregados.');
      } catch(e){ setStatus('Erro a listar NIFs: ' + e.message); }
    }
  </script>
</head>
<body>
  <header>
    <h1>SAFT Doctor • Validator <small style=\"font-weight:400;color:#6b7280\">diag-2025-10-20-3</small></h1>
    <div style=\"font-size:.9rem;color:#6b7280\">Marker: DIAGNOSTICS-ENABLED</div>
    <p>Upload a SAFT XML to validate basic structure and header fields.</p>
  </header>
  <div class=\"card\">
    <div class=\"row\">
      <input type=\"file\" id=\"file\" accept=\".xml,text/xml\" onchange=\"onFileChange(event)\" />
      <button class=\"btn\" id=\"btn\" onclick=\"validate()\">Validate</button>
      <button class=\"btn\" onclick=\"validateWithJar()\">Validate with JAR</button>
    </div>
    <div class=\"mt\">
      <div>Estado JS: <code id=\"js_ok\">(loading…)</code></div>
      <div>Comando (mascarado): <code id=\"cmd_mask\">(n/a)</code></div>
      <pre id=\"out\"></pre>
    </div>
  </div>

  <div class=\"card\" style=\"margin-top:1rem;\">
    <div class=\"log-header\">
      <h3 style=\"margin:0;\">Log</h3>
      <div class=\"log-actions\">
        <button class=\"btn\" onclick=\"clearLog()\">Clear log</button>
      </div>
    </div>
    <pre id=\"log\" style=\"min-height:160px;\" aria-label=\"Execution log\"></pre>
  </div>

  <div class=\"card\" style=\"margin-top:1rem;\">
    <div class=\"row\">
      <button class=\"btn\" onclick=\"checkJavaVersion()\">Java version</button>
      <button class=\"btn\" onclick=\"checkJarStatus()\">Check JAR status</button>
      <button class=\"btn\" onclick=\"runJarCheck()\">Run JAR check</button>
      <button class=\"btn\" onclick=\"pingApi()\">Ping API</button>
      <button class=\"btn\" onclick=\"diagAll()\">Diagnostics</button>
    </div>
  </div>

  <div class=\"card\" style=\"margin-top:1rem;\">
    <h3>Auth</h3>
    <div class=\"row mt\">
      <input placeholder=\"Register: username\" id=\"u_user\" />
      <input placeholder=\"Register: password\" id=\"u_pass\" type=\"password\" />
      <button class=\"btn\" onclick=\"registerUser()\">Register</button>
    </div>
    <div class=\"row mt\">
      <input placeholder=\"Login: username\" id=\"l_user\" />
      <input placeholder=\"Login: password\" id=\"l_pass\" type=\"password\" />
      <button class=\"btn\" onclick=\"loginUser()\">Login</button>
      <button class=\"btn\" onclick=\"loginDev()\" title=\"Quick dev login\">Login dev/dev</button>
      <span id=\"token_status\" class=\"ok\" style=\"margin-left:.5rem;\">Not authenticated</span>
    </div>
    <div class=\"row mt\">
      <button class=\"btn\" onclick=\"(async()=>{ try { const r=await fetch('/auth/me',{ headers: state.token? { Authorization: 'Bearer '+state.token } : {} }); const t=await r.text(); setStatus('Auth self-test HTTP '+r.status+': '+t.slice(0,200)); } catch(e){ setStatus('Self-test error: '+e.message);} })()\">Self-test</button>
    </div>
  </div>

  <div class=\"card\" style=\"margin-top:1rem;\">
    <h3>AT Secrets (requires login)</h3>
    <p>AT credentials are saved encrypted on the server only after login.</p>
    <div class=\"row mt\">
      <input placeholder=\"AT username\" id=\"at_user\" />
      <input placeholder=\"AT password\" id=\"at_pass\" type=\"password\" />
      <button class=\"btn\" onclick=\"saveAT()\">Save AT</button>
      <button class=\"btn\" onclick=\"(async ()=>{ document.getElementById('at_user').value='teste'; document.getElementById('at_pass').value='segredo'; await saveAT(); })()\">Guardar AT de teste</button>
    </div>
  </div>

  <div class=\"card\" style=\"margin-top:1rem;\">
    <h3>Upload & Submit (requires login)</h3>
    <div class=\"row mt\">
      <button class=\"btn\" onclick=\"presignUpload()\">Upload via Presign</button>
      <span>object_key: <code id=\"object_key\">(none)</code></span>
    </div>
    <div class=\"row mt\">
      <button class=\"btn\" onclick=\"submitFile()\">Submit</button>
      <button class=\"btn\" onclick=\"analyzeAndSave()\">Analyze & save</button>
    </div>
  </div>

  <div class=\"card\" style=\"margin-top:1rem;\">
    <h3>Instalar FACTEMICLI.jar (Configuração)</h3>
    <p class=\"note\">Como instalar o ficheiro FACTEMICLI.jar no servidor:</p>
    <ol class=\"mt\">
      <li>Carrega o JAR para o teu bucket Backblaze B2 <b>saftdoctor</b> sob o prefixo <code>pt/tools/FACTEMICLI.jar</code>.</li>
      <li>Garante permissões de leitura: <b>readFiles</b> / <b>s3:GetObject</b> (e <b>putObject</b> se fores usar uploads).</li>
      <li>Configura variáveis no Render: <code>B2_BUCKET</code>, <code>B2_REGION</code>, <code>B2_ENDPOINT</code>, <code>B2_KEY_ID</code>, <code>B2_APP_KEY</code>, <code>FACTEMICLI_JAR_PATH</code>.</li>
      <li>(Recomendado) Usa um <b>Persistent Disk</b> montado em <code>/opt/factemi</code>.</li>
      <li>Depois de autenticado, usa <b>Install JAR</b> para transferir do B2 para o caminho configurado.</li>
      <li>Evita <code>curl -L</code> com presign. Para link temporário, usa \"Presigned Download\" abaixo.</li>
    </ol>
    <div class=\"row mt\">
      <input id=\"jar_key\" placeholder=\"object_key (e.g. pt/tools/FACTEMICLI.jar)\" value=\"pt/tools/FACTEMICLI.jar\" />
      <button class=\"btn\" onclick=\"installJar()\">Install JAR</button>
    </div>
  </div>

  <div class=\"card\" style=\"margin-top:1rem;\">
    <h3>Presigned Download (opcional)</h3>
    <p>Podes gerar um URL temporário para descarregar o ficheiro diretamente no browser.</p>
    <div class=\"row mt\">
      <input id=\"dl_key\" placeholder=\"object_key (e.g. pt/tools/FACTEMICLI.jar)\" value=\"pt/tools/FACTEMICLI.jar\" />
      <button class=\"btn\" onclick=\"presignDownload()\">Get download URL</button>
    </div>
    <div class=\"mt\">URL: <code id=\"dl_url\">(none)</code></div>
  </div>

  <div class=\"card\" style=\"margin-top:1rem;\">
    <h3>Credenciais AT</h3>
    <p>As credenciais são guardadas encriptadas no servidor. Mostramos apenas uma máscara do username.</p>
    <div class=\"row mt\">
      <button class=\"btn\" onclick=\"loadCredsStatus()\">Atualizar estado</button>
      <span>Username (mask): <code id=\"creds_user_mask\">(unknown)</code></span>
      <span>Atualizado em: <code id=\"creds_updated\">(unknown)</code></span>
    </div>
  </div>

  <div class=\"card\" style=\"margin-top:1rem;\">
    <h3>Atualizar credenciais AT</h3>
    <div class=\"row mt\">
      <input placeholder=\"AT username\" id=\"at_user2\" />
      <input placeholder=\"AT password\" id=\"at_pass2\" type=\"password\" />
      <button class=\"btn\" onclick=\"saveAT2()\">Guardar</button>
    </div>
  </div>

  <div class=\"card\" style=\"margin-top:1rem;\">
    <h3>Senhas por NIF (recomendado)</h3>
    <p>Guarda a senha AT associada a cada NIF. A validação/submissão escolhe automaticamente pela NIF do XML.</p>
    <div class=\"row mt\">
      <input placeholder=\"NIF (ident)\" id=\"nif_ident\" />
      <input placeholder=\"Senha AT\" id=\"nif_pass\" type=\"password\" />
      <button class=\"btn\" onclick=\"saveNifEntry()\">Guardar NIF</button>
    </div>
    <div class=\"mt\">
      <button class=\"btn\" onclick=\"loadNifEntries()\">Listar NIFs</button>
    </div>
    <div class=\"mt\">
      <pre id=\"nif_list\">(vazio)</pre>
    </div>
  </div>

  <p id=\"status\" class=\"mt\"></p>
</body>
</html>
"""


# -----------------------------------------------------------------------------
# Routes: UI and health
# -----------------------------------------------------------------------------
@app.get('/', response_class=HTMLResponse, tags=['UI'])
def root_ui():
    return HTMLResponse(content=UI_HTML, headers={'Cache-Control': 'no-store'})


@app.get('/ui', response_class=HTMLResponse, tags=['UI'])
def ui_page():
    return HTMLResponse(content=UI_HTML, headers={'Cache-Control': 'no-store'})


@app.get('/ui/check', tags=['UI'], summary='UI diagnostics')
def ui_check():
    try:
        uri = os.getenv('MONGO_URI') or 'mongodb://mongo:27017'
        if '://' in uri and '@' in uri:
            scheme, rest = uri.split('://', 1)
            if '@' in rest and ':' in rest.split('@', 1)[0]:
                creds, host = rest.split('@', 1)
                user = creds.split(':', 1)[0]
                uri = f"{scheme}://{user}:***@{host}"
            else:
                uri = f"{scheme}://***"
    except Exception:
        pass
    return JSONResponse({
        'ui_version': 'diag-2025-10-20-3',
        'diagnostics_enabled': True,
        'has_ping_button': ('Ping API' in UI_HTML),
        'env': os.getenv('APP_ENV', 'dev'),
        'mongo': {
            'uri': uri,
            'db': os.getenv('MONGO_DB', 'saft_doctor'),
            'scoping': os.getenv('MONGO_SCOPING', 'collection_prefix')
        }
    }, headers={'Cache-Control': 'no-store'})


@app.get('/info', tags=['Health'])
def api_info():
    return { 'name': 'SAFT Doctor API', 'status': 'ok', 'env': os.getenv('APP_ENV','dev'), 'docs': '/docs', 'openapi': '/openapi.json', 'health': '/health', 'countries': ['pt'] }


@app.get('/health', tags=['Health'])
def health():
    env = os.getenv('APP_ENV','dev')
    logger.info(f"Health check requested - Environment: {env}")
    return { 'status': 'ok', 'env': env }


@app.get('/health/db', tags=['Health'])
async def health_db(db=Depends(get_db)):
    try:
        await db.command('ping')
        return { 'ok': True }
    except Exception as e:
        return { 'ok': False, 'error': str(e) }


# -----------------------------------------------------------------------------
# Auth endpoints
# -----------------------------------------------------------------------------
@app.post('/auth/register', tags=['Authentication'])
async def register(user: RegisterIn, request: Request, db=Depends(get_db)):
    country = country_from_request(request)
    repo = UsersRepo(db, country)
    try:
        if await repo.exists(user.username):
            raise HTTPException(status_code=400, detail='Username already exists')
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Registration 'exists' check failed", extra={'error': str(e)})
        raise HTTPException(status_code=503, detail='Database unavailable (exists check).')
    try:
        pwd_hash = hash_password(user.password)
    except Exception as e:
        logger.error("Password hashing failed", extra={'error': str(e)})
        raise HTTPException(status_code=500, detail=f"Server crypto error while hashing password: {e.__class__.__name__}")
    try:
        created = await repo.create(user.username, pwd_hash, user.email)
        return { 'id': str(created['_id']), 'username': created['username'], 'country': country }
    except Exception as e:
        logger.error("Registration failed at create", extra={'error': str(e)})
        raise HTTPException(status_code=503, detail='Database unavailable (create).')


@app.post('/auth/token', tags=['Authentication'])
async def login(form_data: OAuth2PasswordRequestForm = Depends(), request: Request = None, db=Depends(get_db)):
    country = country_from_request(request)
    repo = UsersRepo(db, country)
    try:
        u = await repo.get(form_data.username)
    except Exception as e:
        logger.error("Login failed at get(user)", extra={'error': str(e)})
        raise HTTPException(status_code=503, detail='Database unavailable (get user).')
    try:
        if not u or not verify_password(form_data.password, u['password_hash']):
            raise HTTPException(status_code=400, detail='Incorrect username or password')
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Password verification failed", extra={'error': str(e)})
        raise HTTPException(status_code=500, detail='Server crypto error while verifying password.')
    token = create_access_token({'sub': form_data.username, 'cty': country})
    return { 'access_token': token, 'token_type': 'bearer' }


async def get_current_user(request: Request, token: str = Depends(oauth2_scheme), db=Depends(get_db)):
    country = country_from_request(request)
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get('sub')
        if not username:
            raise HTTPException(status_code=401, detail='Invalid token')
    except JWTError:
        raise HTTPException(status_code=401, detail='Invalid token')
    repo = UsersRepo(db, country)
    u = await repo.get(username)
    if not u:
        raise HTTPException(status_code=401, detail='User not found')
    return { 'username': username, 'country': country }


@app.get('/auth/me', tags=['Authentication'])
async def auth_me(current=Depends(get_current_user)):
    return current


@app.get('/auth/profile', tags=['Authentication'])
async def get_profile(current=Depends(get_current_user), db=Depends(get_db)):
    """
    Get current user's profile including email
    """
    username = current['username']
    country = current.get('country', 'pt')
    repo = UsersRepo(db, country)

    try:
        user = await repo.get(username)
        if not user:
            raise HTTPException(status_code=404, detail='User not found')

        email_value = user.get('email')
        logger.info(f"Profile loaded for {username}: email={'set' if email_value else 'not set'}")

        return {
            'username': user['username'],
            'email': email_value if email_value else None,
            'country': country
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting profile: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail='Error getting profile')


@app.post('/auth/profile/email', tags=['Authentication'])
async def update_profile_email(email: str, current=Depends(get_current_user), db=Depends(get_db)):
    """
    Update current user's email address
    """
    username = current['username']
    country = current.get('country', 'pt')
    repo = UsersRepo(db, country)

    try:
        # Validate email format (basic validation)
        if email and '@' not in email:
            raise HTTPException(status_code=400, detail='Email inválido')

        # Update email
        await repo.update_email(username, email)

        logger.info(f"✅ Email updated for user {username}")

        return {
            'ok': True,
            'message': 'Email atualizado com sucesso',
            'email': email
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating email: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail='Erro ao atualizar email')


# -----------------------------------------------------------------------------
# Include PT router
# -----------------------------------------------------------------------------
from saft_pt_doctor.routers_pt import router as router_pt
app.include_router(router_pt, prefix='/pt')


# -----------------------------------------------------------------------------
# UI validate endpoint (basic client-side check)
# -----------------------------------------------------------------------------
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


# -----------------------------------------------------------------------------
# Include PT router
# -----------------------------------------------------------------------------
from saft_pt_doctor.routers_pt import router as router_pt
app.include_router(router_pt, prefix='/pt')


# -----------------------------------------------------------------------------
# UI validate endpoint (basic client-side check)
# -----------------------------------------------------------------------------
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

# UI diagnostics/version marker (hardcoded in HTML to avoid string formatting issues)

# Validate critical configuration (log error but do not crash app)
if SECRET_KEY == 'change_me' and os.getenv('APP_ENV') == 'prod':
    logger.error("SECRET_KEY is using default value in production. Set SECRET_KEY in environment.")

app = FastAPI(
    title='SAFT Doctor (multi-country)', 
    version='0.2.0',
    description="""
    API multi-país para processamento e submissão de arquivos SAFT (Standard Audit File for Tax purposes).
    
    """
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
                try { setStatus('JS error: ' + (e.message || '(no message)')); } catch(_){ }
            });
            window.addEventListener('unhandledrejection', (e) => {
                try { logLine('Unhandled rejection: ' + (e.reason && e.reason.message ? e.reason.message : e.reason)); } catch(_){ }
            });
            // Minimal network tracer for fetch
            (function(){
                const orig = window.fetch;
                window.fetch = async function(input, init){
                    try {
                        const url = (typeof input === 'string') ? input : (input && input.url) || '';
                        const method = (init && init.method) || 'GET';
                        logLine(`[fetch] ${method} ${url}`);
                    } catch(_){ }
                    const res = await orig(input, init);
                    try { logLine(`[fetch] -> ${res.status} ${res.statusText || ''}`.trim()); } catch(_){ }
                    return res;
                };
            })();
            // Mark JS as loaded when DOM is ready
            window.addEventListener('DOMContentLoaded', () => {
                try { document.getElementById('js_ok').textContent = 'JS loaded'; } catch(_){ }
                try { logLine('[init] UI loaded'); } catch(_){ }
            });

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
                            // Use split/join instead of regex replace to avoid parsing issues
                            if (preview.trim()) logLine('Stderr preview: ' + preview.split('\n').join(' | '));
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

            async function pingApi() {
                setStatus('Pinging API…');
                try {
                    const r1 = await fetch('/health');
                    const t1 = await r1.text();
                    logLine(`/health -> ${r1.status}`);
                    logLine(`/health body: ${t1.slice(0, 200)}`);
                    const r2 = await fetch('/health/db');
                    const t2 = await r2.text();
                    logLine(`/health/db -> ${r2.status}`);
                    logLine(`/health/db body: ${t2.slice(0, 200)}`);
                    setStatus('Ping done.');
                } catch (e) {
                    setStatus('Ping error: ' + e.message);
                    logLine('Ping error: ' + e.message);
                }
            }

            async function diagAll() {
                logLine('Starting diagnostics…');
                await pingApi();
                await checkJavaVersion();
                await checkJarStatus();
                try {
                    if (state.token) {
                        const r = await fetch('/auth/me', { headers: { 'Authorization': 'Bearer ' + state.token } });
                        const t = await r.text();
                        logLine(`/auth/me -> ${r.status}`);
                        logLine(`/auth/me body: ${t.slice(0, 200)}`);
                    } else {
                        logLine('No token set; skipping /auth/me');
                    }
                } catch (e) { logLine('auth/me error: ' + e.message); }
                logLine('Diagnostics finished.');
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
                try {
                    document.getElementById('l_user').value = 'dev';
                    document.getElementById('l_pass').value = 'dev';
                    logLine('Login dev/dev clicked.');
                    setStatus('Logging in as dev/dev…');
                    await loginUser();
                    logLine('Login dev/dev finished. Token set: ' + (state.token ? 'yes' : 'no'));
                } catch (e) {
                    logLine('Login dev/dev error: ' + (e && e.message ? e.message : e));
                    setStatus('Login dev/dev error: ' + (e && e.message ? e.message : e));
                }
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
                    let data = null; try { data = txt ? JSON.parse(txt) : null; } catch(_){ }
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
            <h1>SAFT Doctor • Validator <small style="font-weight:400;color:#6b7280">diag-2025-10-20-3</small></h1>
            <div style="font-size:.9rem;color:#6b7280">Marker: DIAGNOSTICS-ENABLED</div>
            <p>Upload a SAFT XML to validate basic structure and header fields.</p>
        </header>

        <div class="card">
            <div class="row">
                <input type="file" id="file" accept=".xml,text/xml" onchange="onFileChange(event)" />
                <button class="btn" id="btn" onclick="validate()">Validate</button>
                <button class="btn" onclick="validateWithJar()">Validate with JAR</button>
            </div>
            <div class="mt">
                <div>Estado JS: <code id="js_ok">(loading…)</code></div>
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
                <button class="btn" onclick="pingApi()">Ping API</button>
                <button class="btn" onclick="diagAll()">Diagnostics</button>
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

        <div class="card" style="margin-top:1rem;">
            <h3>Instalar FACTEMICLI.jar (Configuração)</h3>
            <p class="note">Como instalar o ficheiro FACTEMICLI.jar no servidor:</p>
            <ol class="mt">
                <li>Carrega o JAR para o teu bucket Backblaze B2 <b>saftdoctor</b> sob o prefixo <code>pt/tools/FACTEMICLI.jar</code>.</li>
                <li>Garante permissões de leitura: <b>readFiles</b> / <b>s3:GetObject</b> (e <b>putObject</b> se fores usar uploads).</li>
                <li>Configura variáveis no Render: <code>B2_BUCKET</code>, <code>B2_REGION</code>, <code>B2_ENDPOINT</code>, <code>B2_KEY_ID</code>, <code>B2_APP_KEY</code>, <code>FACTEMICLI_JAR_PATH</code>.</li>
                <li>(Recomendado) Usa um <b>Persistent Disk</b> montado em <code>/opt/factemi</code>.</li>
                <li>Depois de autenticado, usa <b>Install JAR</b> para transferir do B2 para o caminho configurado.</li>
                <li>Evita <code>curl -L</code> com presign. Para link temporário, usa "Presigned Download" abaixo.</li>
            </ol>
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

        <div class="card" style="margin-top:1rem;">
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

        <p id="status" class="mt"></p>
    </body>
    </html>
    """
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
"""
    
    
"""
</head>
<body>
    <header>
        <h1>SAFT Doctor • Validator <small style="font-weight:400;color:#6b7280">diag-2025-10-20-3</small></h1>
        <div style="font-size:.9rem;color:#6b7280">Marker: DIAGNOSTICS-ENABLED</div>
        <p>Upload a SAFT XML to validate basic structure and header fields.</p>
    </header>
    <div class="card">
        <div class="row">
                    <input type="file" id="file" accept=".xml,text/xml" onchange="onFileChange(event)" />
            <button class="btn" id="btn" onclick="validate()">Validate</button>
            <button class="btn" onclick="validateWithJar()">Validate with JAR</button>
        </div>
        <div class="mt">
            <div>Estado JS: <code id="js_ok">(loading…)</code></div>
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
                <button class="btn" onclick="pingApi()">Ping API</button>
                <button class="btn" onclick="diagAll()">Diagnostics</button>
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
    # Avoid stale cache if user accesses /ui directly
    return HTMLResponse(content=UI_HTML, headers={'Cache-Control': 'no-store'})

@app.get('/ui/check', tags=['UI'], summary='UI diagnostics')
def ui_check():
    # Basic diagnostics to verify updated UI is served
    try:
        uri = os.getenv('MONGO_URI') or 'mongodb://mongo:27017'
        # sanitize user:pass
        if '://' in uri and '@' in uri:
            scheme, rest = uri.split('://', 1)
            if '@' in rest and ':' in rest.split('@', 1)[0]:
                creds, host = rest.split('@', 1)
                user = creds.split(':', 1)[0]
                uri = f"{scheme}://{user}:***@{host}"
            else:
                uri = f"{scheme}://***"
    except Exception:
        pass
    return JSONResponse({
        'ui_version': 'diag-2025-10-20-3',
        'diagnostics_enabled': True,
        'has_ping_button': ('Ping API' in UI_HTML),
        'env': os.getenv('APP_ENV', 'dev'),
        'mongo': {
            'uri': uri,
            'db': os.getenv('MONGO_DB', 'saft_doctor'),
            'scoping': os.getenv('MONGO_SCOPING', 'collection_prefix')
        }
    }, headers={'Cache-Control': 'no-store'})

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
