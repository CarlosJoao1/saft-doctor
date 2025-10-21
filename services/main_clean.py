from services.app2 import app  # re-export clean app for tests
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
    allow_headers=['*']
)
try:
    app.mount('/static', StaticFiles(directory='static'), name='static')
except Exception:
    pass


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
<html><head><meta charset='utf-8'/><meta name='viewport' content='width=device-width, initial-scale=1'/>
<title>SAFT Doctor • Validator</title>
<style>body{font-family:system-ui,-apple-system,Segoe UI,Roboto,sans-serif;margin:2rem}.card{border:1px solid #e5e7eb;border-radius:8px;padding:1rem;max-width:760px}.row{display:flex;gap:1rem;align-items:center}.mt{margin-top:1rem}.btn{background:#111827;color:#fff;border:0;padding:.6rem 1rem;border-radius:6px;cursor:pointer}.btn:disabled{opacity:.5;cursor:not-allowed}pre{background:#0b1020;color:#e5e7eb;padding:1rem;border-radius:8px;overflow:auto}</style>
<script>
const state={token:null,objectKey:null,file:null};function logLine(m){const l=document.getElementById('log');l.textContent+=`[${new Date().toISOString()}] ${m}\n`;l.scrollTop=l.scrollHeight}
function setStatus(m){const s=document.getElementById('status');if(s)s.textContent=m}
window.addEventListener('DOMContentLoaded',()=>{const ok=document.getElementById('js_ok');if(ok)ok.textContent='JS loaded'})
async function validate(){const fi=document.getElementById('file'),out=document.getElementById('out'),btn=document.getElementById('btn');out.textContent='';if(!fi.files.length){out.textContent='Choose a SAFT XML file';return}const f=fi.files[0],fd=new FormData();fd.append('file',f);btn.disabled=true;btn.textContent='Validating…';try{const r=await fetch('/ui/validate',{method:'POST',body:fd});const j=await r.json();out.textContent=JSON.stringify(j,null,2)}catch(e){out.textContent='Error: '+e}finally{btn.disabled=false;btn.textContent='Validate'}}
async function validateWithJar(){if(!state.token){setStatus('Login first.');return}const fi=document.getElementById('file'),out=document.getElementById('out'),cmd=document.getElementById('cmd_mask');if(!fi.files.length){setStatus('Choose a SAFT XML file');return}setStatus('Validating via FACTEMICLI.jar…');const f=fi.files[0],fd=new FormData();fd.append('file',f);try{const r=await fetch('/pt/validate-jar?full=1',{method:'POST',headers:{Authorization:'Bearer '+state.token},body:fd});const t=await r.text();let d=null;try{d=t?JSON.parse(t):null}catch(_){}out.textContent=d?JSON.stringify(d,null,2):(t||'(no body)');if(d&&Array.isArray(d.cmd_masked)){cmd.textContent=d.cmd_masked.join(' ');if(typeof d.returncode!=='undefined'&&d.returncode!==null)logLine('Return code: '+d.returncode+(d.ok===false?' (error)':''));if(d.stderr){const p=(d.stderr.length>400?d.stderr.slice(0,400)+'…':d.stderr);if(p.trim())logLine('Stderr preview: '+p.split('\n').join(' | '))}}else{cmd.textContent='(n/a)'}setStatus(r.ok?'JAR validation done.':'JAR validation HTTP '+r.status)}catch(e){setStatus('JAR validation error: '+e.message)}}
</script></head>
<body>
<header><h1>SAFT Doctor • Validator <small style='font-weight:400;color:#6b7280'>diag-2025-10-20-3</small></h1><div style='font-size:.9rem;color:#6b7280'>Marker: DIAGNOSTICS-ENABLED</div></header>
<div class='card'><div class='row'>
<input type='file' id='file' accept='.xml,text/xml'/>
<button class='btn' id='btn' onclick='validate()'>Validate</button>
<button class='btn' onclick='validateWithJar()'>Validate with JAR</button>
</div>
<div class='mt'><div>Estado JS: <code id='js_ok'>(loading…)</code></div><div>Comando (mascarado): <code id='cmd_mask'>(n/a)</code></div><pre id='out'></pre></div>
</div>
<div class='card' style='margin-top:1rem;'><h3>Log</h3><pre id='log' style='min-height:160px;'></pre></div>
<p id='status' class='mt'></p>
</body></html>
"""


@app.get('/', response_class=HTMLResponse, tags=['UI'])
def root_ui():
    return HTMLResponse(content=UI_HTML, headers={'Cache-Control': 'no-store'})


@app.get('/ui', response_class=HTMLResponse, tags=['UI'])
def ui_page():
    return HTMLResponse(content=UI_HTML, headers={'Cache-Control': 'no-store'})


@app.get('/ui/check', tags=['UI'])
def ui_check():
    return {'ui_version': 'diag-2025-10-20-3', 'diagnostics_enabled': True}


@app.get('/health', tags=['Health'])
def health():
    return {'status': 'ok'}


@app.get('/health/db', tags=['Health'])
async def health_db(db=Depends(get_db)):
    try:
        await db.command('ping')
        return {'ok': True}
    except Exception as e:
        return {'ok': False, 'error': str(e)}


@app.post('/auth/register', tags=['Authentication'])
async def register(user: RegisterIn, request: Request, db=Depends(get_db)):
    country = country_from_request(request)
    repo = UsersRepo(db, country)
    if await repo.exists(user.username):
        raise HTTPException(status_code=400, detail='Username already exists')
    created = await repo.create(user.username, hash_password(user.password))
    return { 'id': str(created.get('_id','1')), 'username': created['username'], 'country': country }


@app.post('/auth/token', tags=['Authentication'])
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
    repo = UsersRepo(db, country)
    u = await repo.get(username)
    if not u:
        raise HTTPException(status_code=401, detail='User not found')
    return { 'username': username, 'country': country }


@app.get('/auth/me', tags=['Authentication'])
async def auth_me(current=Depends(get_current_user)):
    return current


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
