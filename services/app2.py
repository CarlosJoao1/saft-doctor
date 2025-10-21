import os
from fastapi import FastAPI, Depends, HTTPException, UploadFile, File, Request, Response
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel, Field
from jose import jwt, JWTError

from core.logging_config import setup_logging, get_logger
from core.middleware import RequestLoggingMiddleware
from core.deps import get_db
from core.auth_repo import UsersRepo
from core.auth_utils import create_access_token, hash_password, verify_password

setup_logging(level=os.getenv('LOG_LEVEL', 'INFO'))
logger = get_logger(__name__)

SECRET_KEY = os.getenv('SECRET_KEY', 'change_me')
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

# Serve static files (JS/CSS)
try:
    static_dir = os.path.join(os.getcwd(), 'static')
    if os.path.isdir(static_dir):
        app.mount('/static', StaticFiles(directory=static_dir), name='static')
    else:
        logger.warning(f'Static directory not found at {static_dir}')
except Exception as e:
    logger.warning(f'Failed to mount /static: {e}')


class RegisterIn(BaseModel):
    username: str = Field(min_length=1)
    password: str = Field(min_length=1)


def country_from_request(request: Request) -> str:
    parts = [p for p in request.url.path.split('/') if p]
    if parts and parts[0] in {'pt', 'es', 'fr', 'it', 'de'}:
        return parts[0]
    return os.getenv('DEFAULT_COUNTRY', 'pt')


UI_HTML = """
<!doctype html>
<html><head><meta charset=\"utf-8\"><meta name=\"viewport\" content=\"width=device-width,initial-scale=1\"><title>SAFT Doctor • Validator</title>
<style>body{font-family:system-ui,-apple-system,Segoe UI,Roboto,sans-serif;margin:2rem}header{margin-bottom:1rem}.card{border:1px solid #e5e7eb;border-radius:8px;padding:1rem;max-width:760px}.row{display:flex;gap:1rem;align-items:center}.mt{margin-top:1rem}.btn{background:#111827;color:#fff;border:0;padding:.6rem 1rem;border-radius:6px;cursor:pointer}.btn:disabled{opacity:.5;cursor:not-allowed}pre{background:#0b1020;color:#e5e7eb;padding:1rem;border-radius:8px;overflow:auto}.log-header{display:flex;align-items:center;justify-content:space-between}.log-actions{display:flex;gap:.5rem}</style>
<script>const state={token:null,objectKey:null,file:null};function logLine(m){const e=document.getElementById('log');const t=new Date().toISOString();e.textContent+=`[${t}] ${m}\n`,e.scrollTop=e.scrollHeight}function clearLog(){document.getElementById('log').textContent=''}window.addEventListener('error',(e=>{try{setStatus('JS error: '+(e.message||'(no message)'))}catch(e){}})),window.addEventListener('unhandledrejection',(e=>{try{logLine('Unhandled rejection: '+(e.reason&&e.reason.message?e.reason.message:e.reason))}catch(e){}})),function(){const e=window.fetch;window.fetch=async function(t,n){try{const o='string'==typeof t?t:t&&t.url||'',s=n&&n.method||'GET';logLine(`[fetch] ${s} ${o}`)}catch(e){}const o=await e(t,n);try{logLine(`[fetch] -> ${o.status} ${o.statusText||''}`.trim())}catch(e){}return o}}(),window.addEventListener('DOMContentLoaded',(()=>{try{document.getElementById('js_ok').textContent='JS loaded'}catch(e){}try{logLine('[init] UI loaded')}catch(e){}}));async function validate(){const e=document.getElementById('file'),t=document.getElementById('out'),n=document.getElementById('btn');if(t.textContent='',!e.files.length)return void(t.textContent='Choose a SAFT XML file');const o=e.files[0],s=new FormData;s.append('file',o),n.disabled=!0,n.textContent='Validating…';try{const e=await fetch('/ui/validate',{method:'POST',body:s}),n=await e.json();t.textContent=JSON.stringify(n,null,2)}catch(e){t.textContent='Error: '+e}finally{n.disabled=!1,n.textContent='Validate'}}async function validateWithJar(){if(!state.token)return void setStatus('Login first.');const e=document.getElementById('file'),t=document.getElementById('out'),n=document.getElementById('cmd_mask');if(!e.files.length)return void setStatus('Choose a SAFT XML file');setStatus('Validating via FACTEMICLI.jar…'),logLine('Validate with JAR clicked. Preparing upload…');const o=e.files[0],s=new FormData;if(s.append('file',o),1)try{const e=await fetch('/pt/validate-jar?full=1',{method:'POST',headers:{Authorization:'Bearer '+state.token},body:s}),o=await e.text();let a=null;try{a=o?JSON.parse(o):null}catch(e){}if(t.textContent=a?JSON.stringify(a,null,2):o||'(no body)',a&&a.cmd_masked&&Array.isArray(a.cmd_masked))n.textContent=a.cmd_masked.join(' '),logLine('Command (masked): '+a.cmd_masked.join(' ')),void 0!==a.returncode&&null!==a.returncode&&logLine('Return code: '+a.returncode+(a.ok===!1?' (error)':'')),a.stderr&&function(e){const t=e.length>400?e.slice(0,400)+'…':e;t.trim()&&logLine('Stderr preview: '+t.split('\n').join(' | '))}(a.stderr);else n.textContent='(n/a)',logLine('No command returned by API.');setStatus(e.ok?'JAR validation done.':'JAR validation HTTP '+e.status)}catch(e){setStatus('JAR validation error: '+e.message),logLine('Error during JAR validation: '+e.message)}}async function checkJavaVersion(){const e=document.getElementById('out');e.textContent='Checking Java version…';try{const t=await fetch('/pt/java/version'),n=await t.json();e.textContent=JSON.stringify(n,null,2)}catch(t){e.textContent='Error: '+t}}async function checkJarStatus(){const e=document.getElementById('out');e.textContent='Checking JAR status…';try{const t=await fetch('/pt/jar/status'),n=await t.json();e.textContent=JSON.stringify(n,null,2)}catch(t){e.textContent='Error: '+t}}async function runJarCheck(){const e=document.getElementById('out');e.textContent='Running JAR check…';try{const t=await fetch('/pt/jar/run-check'),n=await t.json();e.textContent=JSON.stringify(n,null,2)}catch(t){e.textContent='Error: '+t}}async function pingApi(){setStatus('Pinging API…');try{const e=await fetch('/health'),t=await e.text();logLine(`/health -> ${e.status}`),logLine(`/health body: ${t.slice(0,200)}`);const n=await fetch('/health/db'),o=await n.text();logLine(`/health/db -> ${n.status}`),logLine(`/health/db body: ${o.slice(0,200)}`),setStatus('Ping done.')}catch(e){setStatus('Ping error: '+e.message),logLine('Ping error: '+e.message)}}async function diagAll(){logLine('Starting diagnostics…'),await pingApi(),await checkJavaVersion(),await checkJarStatus();try{if(state.token){const e=await fetch('/auth/me',{headers:{Authorization:'Bearer '+state.token}}),t=await e.text();logLine(`/auth/me -> ${e.status}`),logLine(`/auth/me body: ${t.slice(0,200)}`)}else logLine('No token set; skipping /auth/me')}catch(e){logLine('auth/me error: '+e.message)}logLine('Diagnostics finished.')}function setStatus(e){document.getElementById('status').textContent=e}async function registerUser(){const e=document.getElementById('u_user').value.trim(),t=document.getElementById('u_pass').value;if(!e||!t)return void setStatus('Fill username and password to register.');setStatus('Registering…');try{const n=await fetch('/auth/register',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({username:e,password:t})});if(!n.ok){const e=await n.text();throw new Error(e)}setStatus('Registered. Now login.')}catch(e){setStatus('Register error: '+e.message)}}async function loginUser(){const e=document.getElementById('l_user').value.trim(),t=document.getElementById('l_pass').value;if(!e||!t)return void setStatus('Fill username and password to login.');setStatus('Logging in…');try{const n=new URLSearchParams;n.set('username',e),n.set('password',t);const o=await fetch('/auth/token',{method:'POST',headers:{'Content-Type':'application/x-www-form-urlencoded'},body:n}),s=await o.json();if(!o.ok)throw new Error(s.detail||'Login failed');state.token=s.access_token,setStatus('Logged in. Token ready.'),document.getElementById('token_status').textContent='Authenticated'}catch(e){setStatus('Login error: '+e.message)}}async function loginDev(){try{document.getElementById('l_user').value='dev',document.getElementById('l_pass').value='dev',logLine('Login dev/dev clicked.'),setStatus('Logging in as dev/dev…'),await loginUser(),logLine('Login dev/dev finished. Token set: '+(state.token?'yes':'no'))}catch(e){logLine('Login dev/dev error: '+(e&&e.message?e.message:e)),setStatus('Login dev/dev error: '+(e&&e.message?e.message:e))}}async function saveAT(){if(!state.token)return void setStatus('Login first.');const e=document.getElementById('at_user').value.trim(),t=document.getElementById('at_pass').value;if(!e||!t)return void setStatus('Fill AT username and password.');setStatus('Saving AT credentials…');try{const n=await fetch('/pt/secrets/at',{method:'POST',headers:{'Content-Type':'application/json','Authorization':'Bearer '+state.token},body:JSON.stringify({username:e,password:t})}),o=await n.json();if(!n.ok)throw new Error(o.detail||'Failed to save');setStatus('AT credentials saved (encrypted).')}catch(e){setStatus('Save AT error: '+e.message)}}function onFileChange(e){state.file=e.target.files[0]||null}async function presignUpload(){if(!state.token)return void setStatus('Login first.');if(!state.file)return void setStatus('Choose a file first.');setStatus('Requesting presigned URL…');try{const e=await fetch('/pt/files/presign-upload',{method:'POST',headers:{'Content-Type':'application/json','Authorization':'Bearer '+state.token},body:JSON.stringify({filename:state.file.name,content_type:state.file.type||'application/octet-stream'})}),t=await e.json();if(!e.ok)throw new Error(t.detail||'Failed to presign');setStatus('Uploading via presigned URL…');const n=await fetch(t.url,{method:'PUT',headers:t.headers||{},body:state.file});if(!n.ok&&200!==n.status&&201!==n.status)throw new Error('PUT failed with status '+n.status);state.objectKey=t.object,setStatus('Uploaded. object_key='+state.objectKey),document.getElementById('object_key').textContent=state.objectKey}catch(e){setStatus('Presign/Upload error: '+e.message)}}async function submitFile(){if(!state.token)return void setStatus('Login first.');if(!state.objectKey)return void setStatus('Upload first to get object_key.');setStatus('Submitting…');try{const e=await fetch('/pt/submit?object_key='+encodeURIComponent(state.objectKey),{method:'POST',headers:{Authorization:'Bearer '+state.token}}),t=await e.json();if(!e.ok)throw new Error(t.detail||'Submit failed');setStatus('Submit OK.'),document.getElementById('out').textContent=JSON.stringify(t,null,2)}catch(e){setStatus('Submit error: '+e.message)}}async function presignDownload(){if(!state.token)return void setStatus('Login first.');const e=(document.getElementById('dl_key').value||'').trim();if(!e)return void setStatus('Provide an object_key.');setStatus('Requesting download URL…');try{const t=await fetch('/pt/files/presign-download',{method:'POST',headers:{'Content-Type':'application/json','Authorization':'Bearer '+state.token},body:JSON.stringify({object_key:e})}),n=await t.json();if(!t.ok)throw new Error(n.detail||'Failed to presign download');document.getElementById('dl_url').textContent=n.url||'(no url)',document.getElementById('out').textContent=JSON.stringify(n,null,2),setStatus('Download URL ready.')}catch(e){setStatus('Presign download error: '+e.message)}}async function loadCredsStatus(){if(!state.token)return void setStatus('Login first.');try{const e=await fetch('/pt/secrets/at/status',{headers:{Authorization:'Bearer '+state.token}}),t=await e.json();document.getElementById('creds_user_mask').textContent=t.username_masked||'(none)',document.getElementById('creds_updated').textContent=t.updated_at||'(unknown)',setStatus(t.ok?'Credentials status loaded.':'No credentials saved.')}catch(e){setStatus('Load creds error: '+e.message)}}async function saveAT2(){if(!state.token)return void setStatus('Login first.');const e=document.getElementById('at_user2').value.trim(),t=document.getElementById('at_pass2').value;if(!e||!t)return void setStatus('Fill AT username and password.');setStatus('Saving AT credentials…');try{const n=await fetch('/pt/secrets/at',{method:'POST',headers:{'Content-Type':'application/json','Authorization':'Bearer '+state.token},body:JSON.stringify({username:e,password:t})}),o=await n.json();if(!n.ok)throw new Error(o.detail||'Failed to save creds');setStatus('AT credentials saved.'),loadCredsStatus()}catch(e){setStatus('Save AT error: '+e.message)}}async function analyzeAndSave(){if(!state.token)return void setStatus('Login first.');const e=document.getElementById('file');if(!e.files.length)return void setStatus('Choose a SAFT XML file');setStatus('Analyzing…');try{const t=e.files[0],n=new FormData;n.append('file',t);const o=await fetch('/pt/analyze',{method:'POST',headers:{Authorization:'Bearer '+state.token},body:n}),s=await o.text();let a=null;try{a=s?JSON.parse(s):null}catch(e){}if(!o.ok)throw new Error(a&&a.detail||s?s.slice(0,300):'Analyze failed');if(document.getElementById('out').textContent=JSON.stringify(a,null,2),a.object_key&&(state.objectKey=a.object_key,document.getElementById('object_key').textContent=state.objectKey),setStatus('Analysis saved.'),0){} }catch(e){setStatus('Analyze error: '+e.message)}}async function saveNifEntry(){if(!state.token)return void setStatus('Login first.');const e=(document.getElementById('nif_ident').value||'').trim(),t=document.getElementById('nif_pass').value;if(!e||!t)return void setStatus('Preenche NIF e senha.');setStatus('A guardar senha para NIF '+e+'…');try{const n=await fetch('/pt/secrets/at/entries',{method:'POST',headers:{'Content-Type':'application/json','Authorization':'Bearer '+state.token},body:JSON.stringify({ident:e,password:t})}),o=await n.json();if(!n.ok)throw new Error(o.detail||'Falha ao guardar');setStatus('Senha guardada para NIF '+e+'.'),await loadNifEntries()}catch(e){setStatus('Erro a guardar NIF: '+e.message)}}async function loadNifEntries(){if(!state.token)return void setStatus('Login first.');setStatus('A carregar NIFs…');try{const e=await fetch('/pt/secrets/at/entries',{headers:{Authorization:'Bearer '+state.token}}),t=await e.json();if(!e.ok)throw new Error(t.detail||'Falha ao listar');document.getElementById('nif_list').textContent=JSON.stringify(t.items||[],null,2),setStatus('NIFs carregados.')}catch(e){setStatus('Erro a listar NIFs: '+e.message)}}</script>
</head><body>
  <header>
    <h1>SAFT Doctor • Validator <small style=\"font-weight:400;color:#6b7280\">diag-2025-10-20-3</small></h1>
    <div style=\"font-size:.9rem;color:#6b7280\">Marker: DIAGNOSTICS-ENABLED</div>
    <p>Upload a SAFT XML to validate basic structure and header fields.</p>
  </header>
  <div class=\"card\">
    <div class=\"row\"><input type=\"file\" id=\"file\" accept=\".xml,text/xml\" onchange=\"onFileChange(event)\" />
      <button class=\"btn\" id=\"btn\" onclick=\"validate()\">Validate</button>
      <button class=\"btn\" onclick=\"validateWithJar()\">Validate with JAR</button>
    </div>
    <div class=\"mt\"><div>Estado JS: <code id=\"js_ok\">(loading…)</code></div>
      <div>Comando (mascarado): <code id=\"cmd_mask\">(n/a)</code></div>
      <pre id=\"out\"></pre></div>
  </div>
  <div class=\"card\" style=\"margin-top:1rem;\"><div class=\"log-header\"><h3 style=\"margin:0;\">Log</h3><div class=\"log-actions\"><button class=\"btn\" onclick=\"clearLog()\">Clear log</button></div></div><pre id=\"log\" style=\"min-height:160px;\" aria-label=\"Execution log\"></pre></div>
  <div class=\"card\" style=\"margin-top:1rem;\"><div class=\"row\"><button class=\"btn\" onclick=\"checkJavaVersion()\">Java version</button><button class=\"btn\" onclick=\"checkJarStatus()\">Check JAR status</button><button class=\"btn\" onclick=\"runJarCheck()\">Run JAR check</button><button class=\"btn\" onclick=\"pingApi()\">Ping API</button><button class=\"btn\" onclick=\"diagAll()\">Diagnostics</button></div></div>
  <div class=\"card\" style=\"margin-top:1rem;\"><h3>Auth</h3><div class=\"row mt\"><input placeholder=\"Register: username\" id=\"u_user\" /><input placeholder=\"Register: password\" id=\"u_pass\" type=\"password\" /><button class=\"btn\" onclick=\"registerUser()\">Register</button></div><div class=\"row mt\"><input placeholder=\"Login: username\" id=\"l_user\" /><input placeholder=\"Login: password\" id=\"l_pass\" type=\"password\" /><button class=\"btn\" onclick=\"loginUser()\">Login</button><button class=\"btn\" onclick=\"loginDev()\" title=\"Quick dev login\">Login dev/dev</button><span id=\"token_status\" class=\"ok\" style=\"margin-left:.5rem;\">Not authenticated</span></div><div class=\"row mt\"><button class=\"btn\" onclick=\"(async()=>{ try { const r=await fetch('/auth/me',{ headers: state.token? { Authorization: 'Bearer '+state.token } : {} }); const t=await r.text(); setStatus('Auth self-test HTTP '+r.status+': '+t.slice(0,200)); } catch(e){ setStatus('Self-test error: '+e.message);} })()\">Self-test</button></div></div>
  <div class=\"card\" style=\"margin-top:1rem;\"><h3>AT Secrets (requires login)</h3><p>AT credentials are saved encrypted on the server only after login.</p><div class=\"row mt\"><input placeholder=\"AT username\" id=\"at_user\" /><input placeholder=\"AT password\" id=\"at_pass\" type=\"password\" /><button class=\"btn\" onclick=\"saveAT()\">Save AT</button></div></div>
  <div class=\"card\" style=\"margin-top:1rem;\"><h3>Upload & Submit (requires login)</h3><div class=\"row mt\"><button class=\"btn\" onclick=\"presignUpload()\">Upload via Presign</button><span>object_key: <code id=\"object_key\">(none)</code></span></div><div class=\"row mt\"><button class=\"btn\" onclick=\"submitFile()\">Submit</button><button class=\"btn\" onclick=\"analyzeAndSave()\">Analyze & save</button></div></div>
  <div class=\"card\" style=\"margin-top:1rem;\"><h3>Presigned Download (opcional)</h3><div class=\"row mt\"><input id=\"dl_key\" placeholder=\"object_key (e.g. pt/tools/FACTEMICLI.jar)\" value=\"pt/tools/FACTEMICLI.jar\" /><button class=\"btn\" onclick=\"presignDownload()\">Get download URL</button></div><div class=\"mt\">URL: <code id=\"dl_url\">(none)</code></div></div>
  <div class=\"card\" style=\"margin-top:1rem;\"><h3>Credenciais AT</h3><div class=\"row mt\"><button class=\"btn\" onclick=\"loadCredsStatus()\">Atualizar estado</button><span>Username (mask): <code id=\"creds_user_mask\">(unknown)</code></span><span>Atualizado em: <code id=\"creds_updated\">(unknown)</code></span></div></div>
  <div class=\"card\" style=\"margin-top:1rem;\"><h3>Atualizar credenciais AT</h3><div class=\"row mt\"><input placeholder=\"AT username\" id=\"at_user2\" /><input placeholder=\"AT password\" id=\"at_pass2\" type=\"password\" /><button class=\"btn\" onclick=\"saveAT2()\">Guardar</button></div></div>
  <div class=\"card\" style=\"margin-top:1rem;\"><h3>Senhas por NIF (recomendado)</h3><div class=\"row mt\"><input placeholder=\"NIF (ident)\" id=\"nif_ident\" /><input placeholder=\"Senha AT\" id=\"nif_pass\" type=\"password\" /><button class=\"btn\" onclick=\"saveNifEntry()\">Guardar NIF</button></div><div class=\"mt\"><button class=\"btn\" onclick=\"loadNifEntries()\">Listar NIFs</button></div><div class=\"mt\"><pre id=\"nif_list\">(vazio)</pre></div></div>
  <p id=\"status\" class=\"mt\"></p>
</body></html>
"""


@app.get('/', response_class=HTMLResponse)
def root_ui():
    try:
        with open(os.path.join(os.getcwd(), 'ui.html'), 'r', encoding='utf-8') as f:
            html = f.read()
        return HTMLResponse(content=html, headers={'Cache-Control': 'no-store'})
    except Exception:
        return HTMLResponse(content=UI_HTML, headers={'Cache-Control': 'no-store'})


@app.get('/ui', response_class=HTMLResponse)
def ui_page():
    try:
        with open(os.path.join(os.getcwd(), 'ui.html'), 'r', encoding='utf-8') as f:
            html = f.read()
        return HTMLResponse(content=html, headers={'Cache-Control': 'no-store'})
    except Exception:
        return HTMLResponse(content=UI_HTML, headers={'Cache-Control': 'no-store'})


@app.get('/ui/check')
def ui_check():
    return JSONResponse({ 'ui_version': '2', 'diagnostics_enabled': True }, headers={'Cache-Control': 'no-store'})


@app.get('/favicon.ico', include_in_schema=False)
def favicon_ico():
    return Response(status_code=204)


@app.get('/health')
def health():
    return { 'status': 'ok', 'env': os.getenv('APP_ENV','dev') }


@app.get('/health/db')
async def health_db(db=Depends(get_db)):
    try:
        await db.command('ping')
        return { 'ok': True }
    except Exception as e:
        return { 'ok': False, 'error': str(e) }


@app.post('/auth/register')
async def register(user: RegisterIn, request: Request, db=Depends(get_db)):
    country = country_from_request(request)
    repo = UsersRepo(db, country)
    try:
        if await repo.exists(user.username):
            raise HTTPException(status_code=400, detail='Username already exists')
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=503, detail='Database unavailable (exists check).')
    created = await repo.create(user.username, hash_password(user.password))
    return { 'id': str(created['_id']), 'username': created['username'], 'country': country }


@app.post('/auth/token')
async def login(form_data: OAuth2PasswordRequestForm = Depends(), request: Request = None, db=Depends(get_db)):
    country = country_from_request(request)
    repo = UsersRepo(db, country)
    u = await repo.get(form_data.username)
    if not u or not verify_password(form_data.password, u['password_hash']):
        raise HTTPException(status_code=400, detail='Incorrect username or password')
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
    u = await UsersRepo(db, country).get(username)
    if not u:
        raise HTTPException(status_code=401, detail='User not found')
    return { 'username': username, 'country': country }


@app.get('/auth/me')
async def auth_me(current=Depends(get_current_user)):
    return current


from saft_pt_doctor.routers_pt import router as router_pt
app.include_router(router_pt, prefix='/pt')


@app.post('/ui/validate')
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
