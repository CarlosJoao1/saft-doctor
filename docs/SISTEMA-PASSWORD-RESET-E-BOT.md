# Sistema de Password Reset e Bot - SAFT Doctor

## 📋 Visão Geral

Documento de design técnico para o sistema de recuperação de password via email e exploração de integração de bot/chatbot na aplicação SAFT Doctor.

---

## 🔐 Sistema de Password Reset

### Objetivo

Permitir que utilizadores recuperem o acesso à sua conta quando esquecem a password, usando o email como método de verificação.

### Fluxo Completo

```
┌─────────────────────────────────────────────────────────────────┐
│                    FLUXO DE PASSWORD RESET                      │
└─────────────────────────────────────────────────────────────────┘

1. SOLICITAÇÃO
   ┌─────────────┐
   │ Utilizador  │
   │ esqueceu    │
   │ password    │
   └──────┬──────┘
          │
          ▼
   ┌─────────────────────────────┐
   │ Clica "Esqueci password"    │
   │ no overlay de login         │
   └──────┬──────────────────────┘
          │
          ▼
   ┌─────────────────────────────┐
   │ Insere username             │
   │ (não precisa de email,      │
   │  está na BD)                │
   └──────┬──────────────────────┘
          │
          ▼
   ┌─────────────────────────────┐
   │ POST /auth/password-reset   │
   │ {username: "joao"}          │
   └──────┬──────────────────────┘
          │
          ▼

2. GERAÇÃO DE TOKEN
   ┌─────────────────────────────┐
   │ Backend procura user na BD  │
   │ Valida que existe           │
   └──────┬──────────────────────┘
          │
          ▼
   ┌─────────────────────────────┐
   │ Gera token seguro           │
   │ (secrets.token_urlsafe(32)) │
   └──────┬──────────────────────┘
          │
          ▼
   ┌─────────────────────────────┐
   │ Hash token (SHA-256)        │
   │ Guarda hash na BD           │
   │ Expira em 1 hora            │
   └──────┬──────────────────────┘
          │
          ▼

3. ENVIO DE EMAIL
   ┌─────────────────────────────┐
   │ Envia email via SMTP        │
   │ (ServerSMTP.com)            │
   │                             │
   │ Para: user.email@...        │
   │ Link: saft.aquinos.io       │
   │       ?reset_token=ABC123   │
   └──────┬──────────────────────┘
          │
          ▼
   ┌─────────────────────────────┐
   │ ✅ Mensagem ao utilizador:  │
   │ "Email enviado! Verifique   │
   │  a sua caixa de entrada"    │
   └─────────────────────────────┘

4. UTILIZADOR RECEBE EMAIL
   ┌─────────────────────────────┐
   │ 📧 Email bonito (HTML)      │
   │ Template profissional       │
   │ Botão "Recuperar Password"  │
   └──────┬──────────────────────┘
          │
          ▼
   ┌─────────────────────────────┐
   │ Utilizador clica no link    │
   │ Abre: saft.aquinos.io       │
   │       ?reset_token=ABC123   │
   └──────┬──────────────────────┘
          │
          ▼

5. VALIDAÇÃO DO TOKEN
   ┌─────────────────────────────┐
   │ Frontend deteta parâmetro   │
   │ reset_token no URL          │
   └──────┬──────────────────────┘
          │
          ▼
   ┌─────────────────────────────┐
   │ Mostra overlay especial:    │
   │ "Criar Nova Password"       │
   │                             │
   │ [Nova Password    ]         │
   │ [Confirmar        ]         │
   │ [Guardar]                   │
   └──────┬──────────────────────┘
          │
          ▼
   ┌─────────────────────────────┐
   │ POST /auth/password-reset   │
   │      /confirm               │
   │ {                           │
   │   token: "ABC123",          │
   │   new_password: "..."       │
   │ }                           │
   └──────┬──────────────────────┘
          │
          ▼

6. ATUALIZAÇÃO DA PASSWORD
   ┌─────────────────────────────┐
   │ Backend valida token:       │
   │ - Existe?                   │
   │ - Não expirou?              │
   │ - Não foi usado?            │
   └──────┬──────────────────────┘
          │
          ▼
   ┌─────────────────────────────┐
   │ Hash nova password          │
   │ (bcrypt)                    │
   └──────┬──────────────────────┘
          │
          ▼
   ┌─────────────────────────────┐
   │ Atualiza na BD:             │
   │ - password_hash             │
   │ - password_updated_at       │
   └──────┬──────────────────────┘
          │
          ▼
   ┌─────────────────────────────┐
   │ Marca token como usado      │
   └──────┬──────────────────────┘
          │
          ▼
   ┌─────────────────────────────┐
   │ Envia email de confirmação: │
   │ "Password alterada!"        │
   └──────┬──────────────────────┘
          │
          ▼
   ┌─────────────────────────────┐
   │ ✅ Redireciona para login   │
   │ "Password alterada! Faça    │
   │  login com nova password"   │
   └─────────────────────────────┘
```

### Componentes Técnicos

#### 1. Email Service (`core/email_service.py`)

**Responsabilidade**: Enviar emails via ServerSMTP.com

**Configuração (sysadmin apenas)**:
```env
SMTP_HOST=mail.serversmtp.com
SMTP_PORT=587
SMTP_USER=your_username
SMTP_PASSWORD=your_password
SMTP_FROM_EMAIL=noreply@saft.aquinos.io
SMTP_FROM_NAME=SAFT Doctor
APP_URL=https://saft.aquinos.io
```

**Métodos**:
- `send_password_reset_email(email, username, token)` → Email com link de reset
- `send_password_changed_notification(email, username)` → Email de confirmação

#### 2. Password Reset Repository (`core/password_reset_repo.py`)

**Responsabilidade**: Gerir tokens de reset na MongoDB

**Coleção**: `password_reset_tokens`

**Documento**:
```json
{
  "username": "joao.silva",
  "email": "joao@example.com",
  "token_hash": "sha256_hash_do_token",
  "created_at": "2025-10-23T01:30:00Z",
  "expires_at": "2025-10-23T02:30:00Z",
  "used": false,
  "used_at": null
}
```

**Métodos**:
- `create_reset_token(username, email)` → Cria token, retorna plaintext (só 1x)
- `validate_token(token)` → Valida se token existe e é válido
- `mark_token_used(token)` → Marca como usado (não pode reutilizar)
- `delete_expired_tokens()` → Limpeza automática

#### 3. Auth Repository (`core/auth_repo.py`)

**Novos métodos**:
- `update_password(username, new_hash)` → Atualiza password
- `update_email(username, email)` → Atualiza email

#### 4. Modelos (`core/models.py`)

**Novos modelos**:
```python
class PasswordResetRequestIn(BaseModel):
    username: str

class PasswordResetRequestOut(BaseModel):
    ok: bool
    message: str

class PasswordResetConfirmIn(BaseModel):
    token: str
    new_password: str

class PasswordResetConfirmOut(BaseModel):
    ok: bool
    message: str
```

#### 5. Endpoints (main.py ou routers)

**POST /auth/password-reset/request**
- Input: `{username: "joao"}`
- Ação:
  1. Procurar user na BD
  2. Se não existe: retornar ok=true (segurança: não revelar se username existe)
  3. Se existe e TEM email: criar token, enviar email
  4. Se existe mas SEM email: retornar mensagem "Configure email primeiro"
- Output: `{ok: true, message: "Se o username existir, receberá um email"}`

**POST /auth/password-reset/confirm**
- Input: `{token: "ABC123", new_password: "new_pass"}`
- Ação:
  1. Validar token (existe? não expirou? não usado?)
  2. Hash nova password
  3. Atualizar password na BD
  4. Marcar token como usado
  5. Enviar email de confirmação
- Output: `{ok: true, message: "Password alterada com sucesso!"}`

**GET /auth/check-reset-token?token=ABC123**
- Input: Query param `token`
- Ação: Validar se token é válido (para frontend saber se deve mostrar form)
- Output: `{ok: true, valid: true}` ou `{ok: true, valid: false, reason: "expired"}`

#### 6. Frontend (static/app.js + ui.html)

**Overlay de Login - Adicionar link**:
```html
<div id="login-form">
    ...
    <a href="#" onclick="showPasswordResetForm()">Esqueceu a password?</a>
</div>
```

**Form de Password Reset**:
```html
<div id="password-reset-form" style="display: none;">
    <h3>Recuperar Password</h3>
    <input type="text" id="reset_username" placeholder="Username">
    <button onclick="requestPasswordReset()">Enviar Email</button>
</div>
```

**Overlay de Nova Password** (quando URL tem ?reset_token=):
```html
<div id="new-password-overlay">
    <h3>Criar Nova Password</h3>
    <input type="password" id="new_password" placeholder="Nova password">
    <input type="password" id="new_password_confirm" placeholder="Confirmar">
    <button onclick="confirmPasswordReset()">Guardar Password</button>
</div>
```

**JavaScript**:
```javascript
// Detetar token no URL ao carregar página
window.addEventListener('DOMContentLoaded', () => {
    const urlParams = new URLSearchParams(window.location.search);
    const resetToken = urlParams.get('reset_token');

    if (resetToken) {
        showNewPasswordOverlay(resetToken);
    }
});

async function requestPasswordReset() {
    const username = document.getElementById('reset_username').value;

    const response = await fetch('/auth/password-reset/request', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({username})
    });

    const data = await response.json();
    alert(data.message);
}

async function confirmPasswordReset(token) {
    const newPassword = document.getElementById('new_password').value;
    const confirm = document.getElementById('new_password_confirm').value;

    if (newPassword !== confirm) {
        alert('Passwords não coincidem');
        return;
    }

    const response = await fetch('/auth/password-reset/confirm', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({token, new_password: newPassword})
    });

    const data = await response.json();

    if (data.ok) {
        alert('Password alterada! Faça login.');
        window.location.href = '/';  // Remove token do URL
    } else {
        alert('Erro: ' + data.message);
    }
}
```

### Segurança

#### ✅ Boas Práticas Implementadas

1. **Token nunca guardado em plaintext**: Apenas hash SHA-256 na BD
2. **Token único e aleatório**: `secrets.token_urlsafe(32)` = 256 bits
3. **Expiração curta**: 1 hora (configur configurável)
4. **Token uso único**: Marcado como `used=true` após utilização
5. **Não revelar se username existe**: Sempre retorna "Email enviado se username existir"
6. **Password hash**: Bcrypt com salt automático
7. **HTTPS obrigatório**: Links no email usam https://
8. **Email de notificação**: Avisa quando password foi alterada (detetar uso não autorizado)

#### ⚠️ Considerações

- **Rate limiting**: Implementar limite de pedidos (ex: 3 pedidos/hora por IP)
- **CAPTCHA**: Considerar para evitar spam
- **2FA** (futuro): Opção de autenticação em dois fatores

---

## 🤖 Sistema de Bot / Chatbot

### Opções Exploradas

#### Opção 1: Bot de Ajuda Contextual (Simple Widget)

**Tipo**: Widget de ajuda com FAQ e guias rápidos

**Tecnologia**: JavaScript puro, sem backend extra

**Funcionalidades**:
- ❓ FAQ com perguntas frequentes
- 📚 Links para secções do manual
- 💬 Dicas contextuais baseadas no tab ativo
- 🔍 Pesquisa de ajuda

**Vantagens**:
- ✅ Simples de implementar
- ✅ Sem custos adicionais
- ✅ Offline-first (não depende de API externa)

**Desvantagens**:
- ❌ Não é "inteligente" (respostas pré-definidas)
- ❌ Não aprende com interações

**Implementação**:
```html
<!-- Widget de ajuda fixo no canto inferior direito -->
<div id="help-widget" class="help-widget">
    <button onclick="toggleHelpWidget()">
        💬 Ajuda
    </button>

    <div id="help-content" style="display: none;">
        <h3>Como posso ajudar?</h3>

        <div class="help-category">
            <h4>📄 Validação de Ficheiros</h4>
            <ul>
                <li><a href="#" onclick="showHelp('upload')">Como fazer upload?</a></li>
                <li><a href="#" onclick="showHelp('errors')">O que significam os erros?</a></li>
            </ul>
        </div>

        <div class="help-category">
            <h4>🔐 Credenciais AT</h4>
            <ul>
                <li><a href="#" onclick="showHelp('add-creds')">Como adicionar credenciais?</a></li>
                <li><a href="#" onclick="showHelp('security')">As minhas credenciais estão seguras?</a></li>
            </ul>
        </div>

        <input type="text" placeholder="🔍 Pesquisar ajuda..." onkeyup="searchHelp(this.value)">
    </div>
</div>
```

#### Opção 2: ChatBot com IA (GPT-4 / Claude)

**Tipo**: Chatbot inteligente com processamento de linguagem natural

**Tecnologias**:
- OpenAI GPT-4 API
- Anthropic Claude API
- Google Gemini API

**Funcionalidades**:
- 💬 Conversação natural em Português
- 🧠 Entende contexto da aplicação
- 📖 Conhece manual de utilizador
- 🔧 Pode sugerir soluções para erros SAFT
- 📊 Explica estatísticas e resultados

**Vantagens**:
- ✅ Experiência de utilizador superior
- ✅ Aprende com manual (RAG - Retrieval Augmented Generation)
- ✅ Respostas personalizadas

**Desvantagens**:
- ❌ Custo de API (pago)
- ❌ Requer backend para API keys
- ❌ Latência (chamadas à API)

**Implementação** (conceito):
```python
# Backend endpoint
@app.post('/chat/message')
async def chat_message(message: str, current_user: dict = Depends(get_current_user)):
    # Context: user, current tab, last operations
    context = f"""
    Você é um assistente do SAFT Doctor, aplicação de validação SAFT-T portuguesa.

    Utilizador: {current_user['username']}

    Manual de utilizador (resumo):
    - Validação de ficheiros SAFT
    - Análise de documentos
    - Histórico de validações
    - Gestão de credenciais AT

    Mensagem do utilizador: {message}
    """

    # Chamar API (exemplo com OpenAI)
    response = await openai.ChatCompletion.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": context},
            {"role": "user", "content": message}
        ]
    )

    return {"reply": response.choices[0].message.content}
```

```javascript
// Frontend chat UI
async function sendChatMessage(message) {
    const response = await fetch('/chat/message', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'Authorization': 'Bearer ' + token
        },
        body: JSON.stringify({message})
    });

    const data = await response.json();
    displayChatMessage('bot', data.reply);
}
```

#### Opção 3: Bot Híbrido (Recomendado)

**Conceito**: Combinar FAQ local com IA para casos complexos

**Funcionamento**:
1. Utilizador faz pergunta
2. Tentar responder com FAQ local (instant, grátis)
3. Se não encontrar resposta → Enviar para IA (custo, mas melhor UX)

**Vantagens**:
- ✅ Maioria das perguntas respondidas gratuitamente
- ✅ Casos complexos tratados pela IA
- ✅ Controlo de custos

#### Opção 4: Bot via Email (Inovador)

**Conceito**: Utilizadores enviam dúvidas por email, recebem respostas automáticas

**Tecnologia**:
- Email parsing (receber emails em support@saft.aquinos.io)
- IA processa pergunta
- Responde automaticamente

**Vantagens**:
- ✅ Assíncrono (não precisa de resposta imediata)
- ✅ Utilizadores já conhecem email
- ✅ Histórico de conversas no email

**Desvantagens**:
- ❌ Menos imediato que chat

---

## 📊 Recomendações

### Para Password Reset: ✅ IMPLEMENTAR

**Prioridade**: ALTA

**Motivo**:
- Funcionalidade essencial
- Melhora UX significativamente
- Reduz carga de suporte (menos "esqueci password")

**Próximos passos**:
1. ✅ Criar `email_service.py` (feito)
2. ✅ Criar `password_reset_repo.py` (feito)
3. ⏳ Adicionar endpoints em `main.py`
4. ⏳ Adicionar UI no `ui.html` e `app.js`
5. ⏳ Configurar SMTP no `.env` (sysadmin)
6. ⏳ Testar fluxo completo

### Para Bot: 🤔 AVALIAR

**Opções recomendadas por ordem**:

1. **Fase 1 - Widget de Ajuda Simples** (implementar JÁ)
   - Custo: ZERO
   - Tempo: 2-4 horas
   - Impacto: Médio
   - Acção: Criar widget com FAQ baseada no manual

2. **Fase 2 - Chat com IA** (avaliar após Fase 1)
   - Custo: ~€50-200/mês (depende do uso)
   - Tempo: 1-2 dias
   - Impacto: Alto
   - Acção: Testar com OpenAI GPT-4 ou Claude
   - Condição: Se widget simples não for suficiente

3. **Fase 3 - Híbrido** (ideal a longo prazo)
   - Custo: Variável (só IA quando necessário)
   - Tempo: 3-5 dias
   - Impacto: Muito Alto
   - Acção: FAQ local + fallback para IA

---

## 🛠️ Configuração SMTP (Sysadmin)

### ServerSMTP.com Setup

1. **Criar conta** em https://serversmtp.com/
2. **Obter credenciais**:
   - SMTP Host: `mail.serversmtp.com`
   - Port: `587` (TLS)
   - Username: (fornecido por ServerSMTP)
   - Password: (fornecido por ServerSMTP)

3. **Configurar DNS** (se usar domínio próprio):
   - SPF record
   - DKIM record
   - MX record (opcional, se receber emails)

4. **Adicionar ao `.env`**:
```env
# Email Service (ServerSMTP.com) - SYSADMIN ONLY
SMTP_HOST=mail.serversmtp.com
SMTP_PORT=587
SMTP_USER=your_serversmtp_username
SMTP_PASSWORD=your_serversmtp_password
SMTP_FROM_EMAIL=noreply@saft.aquinos.io
SMTP_FROM_NAME=SAFT Doctor
APP_URL=https://saft.aquinos.io
```

5. **Testar** (Python):
```python
from core.email_service import get_email_service

email_service = get_email_service()
success = email_service.send_email(
    to_email='test@example.com',
    subject='Teste SMTP',
    html_body='<h1>Funciona!</h1>',
    text_body='Funciona!'
)

print('✅ Email sent!' if success else '❌ Failed')
```

---

## 📝 Tarefas Pendentes

### Password Reset
- [ ] Adicionar endpoints em `main.py` ou `services/main.py`
- [ ] Atualizar `ui.html` com link "Esqueceu password?"
- [ ] Adicionar forms de reset no `ui.html`
- [ ] Implementar JavaScript em `app.js`
- [ ] Configurar SMTP (sysadmin)
- [ ] Testar fluxo completo
- [ ] Documentar no manual de utilizador
- [ ] Adicionar ao CHANGELOG

### Bot (Fase 1 - Widget Simples)
- [ ] Criar componente `help-widget` em `ui.html`
- [ ] Extrair FAQ do manual para JSON
- [ ] Implementar pesquisa de ajuda
- [ ] Adicionar dicas contextuais
- [ ] Estilizar widget (CSS)
- [ ] Testar em diferentes ecrãs

### Bot (Fase 2 - IA) - OPCIONAL
- [ ] Avaliar APIs (OpenAI vs Claude vs Gemini)
- [ ] Estimar custos mensais
- [ ] Criar endpoint `/chat/message`
- [ ] Integrar com API escolhida
- [ ] Adicionar rate limiting
- [ ] Testar qualidade das respostas
- [ ] Decisão: Implementar ou não?

---

**Autor**: Sistema SAFT Doctor
**Data**: 2025-10-23
**Versão**: 1.0
