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

oauth2_scheme = OAuth2PasswordBearer(tokenUrl='/auth/token')

@app.get('/', tags=['Health'], summary='API Root')
def root():
    """Root endpoint with quick links and status."""
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

@app.post('/auth/register', tags=['Authentication'], summary="Register User")
async def register(user: dict, request: Request, db=Depends(get_db)):
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
        "username": user.get('username'),
        "country": country
    })
    
    if await repo.exists(user['username']): 
        logger.warning("Registration failed - username already exists", extra={
            "username": user.get('username'),
            "country": country
        })
        raise HTTPException(status_code=400, detail='Username already exists')
    
    created=await repo.create(user['username'], hash_password(user['password']))
    
    logger.info("User registered successfully", extra={
        "user_id": str(created['_id']),
        "username": created['username'],
        "country": country
    })
    
    return {'id':str(created['_id']),'username':created['username'],'country':country}

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
    
    u=await repo.get(form_data.username)
    if not u or not verify_password(form_data.password, u['password_hash']): 
        logger.warning("Login failed - invalid credentials", extra={
            "username": form_data.username,
            "country": country
        })
        raise HTTPException(status_code=400, detail='Incorrect username or password')
    
    token=create_access_token({'sub':form_data.username,'cty':country})
    
    logger.info("Login successful", extra={
        "username": form_data.username,
        "country": country
    })
    
    return {'access_token':token,'token_type':'bearer'}

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
    </style>
    <script>
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
    </script>
</head>
<body>
    <header>
        <h1>SAFT Doctor • Validator</h1>
        <p>Upload a SAFT XML to validate basic structure and header fields.</p>
    </header>
    <div class="card">
        <div class="row">
            <input type="file" id="file" accept=".xml,text/xml" />
            <button class="btn" id="btn" onclick="validate()">Validate</button>
        </div>
        <div class="mt">
            <pre id="out"></pre>
        </div>
    </div>
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
