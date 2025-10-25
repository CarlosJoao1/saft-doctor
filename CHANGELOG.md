# Changelog

Todas as mudanças notáveis neste projeto serão documentadas neste arquivo.

O formato é baseado em [Keep a Changelog](https://keepachangelog.com/pt-BR/1.0.0/),
e este projeto adere ao [Semantic Versioning](https://semver.org/lang/pt-BR/).

## [Release 21] - 2025-10-25

### Adicionado
- 🔐 **Sistema completo de recuperação de password**
  - Endpoint `POST /auth/password-reset/request` para solicitar reset de password
  - Endpoint `POST /auth/password-reset/confirm` para confirmar e criar nova password
  - Endpoint `GET /auth/check-reset-token` para validar tokens de reset
  - Integração com ServerSMTP.com para envio de emails
  - Templates HTML profissionais para emails de recuperação
  - Tokens SHA-256 com expiração de 1 hora e uso único
  - Campo email opcional no registo de utilizadores
  - Link "Esqueceu a password?" no formulário de login
  - Formulário de reset de password com deteção automática de token no URL
  - Confirmação por email após alteração bem-sucedida

- 💬 **Widget de ajuda interativo (Bot Fase 1)**
  - Botão flutuante de ajuda no canto inferior direito
  - Centro de ajuda com FAQ abrangente organizado por secções:
    * 🔐 Autenticação (login, registo, recuperação de password)
    * 📄 Validação de ficheiros SAFT
    * 🔑 Gestão de credenciais AT
    * 🚀 Processo de submissão
    * 📊 Histórico de validações
    * 📑 Visualização de documentos
    * ⚠️ Resolução de problemas comuns
  - Sistema de pesquisa/filtro de conteúdos de ajuda
  - Items expandíveis/colapsáveis estilo acordeão
  - Design responsivo para mobile
  - Zero dependências externas
  - Link para suporte técnico por email

- 📧 **Serviço de email (sysadmin-only)**
  - Módulo `core/email_service.py` para envio de emails via SMTP
  - Configuração centralizada via variáveis de ambiente (sysadmin)
  - Suporte para ServerSMTP.com com TLS
  - Templates HTML responsivos e profissionais
  - Fallback para texto plano quando HTML não disponível

- 📚 **Documentação técnica**
  - Documento `docs/SISTEMA-PASSWORD-RESET-E-BOT.md` (1.247 linhas)
  - Diagramas de fluxo ASCII do processo de reset
  - Análise de 4 opções de bot/chatbot com custos
  - Guia de configuração SMTP para sysadmin
  - Considerações de segurança e melhores práticas

### Melhorado
- 🚀 **Cache-busting**
  - Atualizado de v=43 para v=44
  - Garante carregamento da versão mais recente do JavaScript

- 🔐 **Segurança de passwords**
  - Tokens nunca armazenados em texto plano (SHA-256)
  - Tokens de uso único marcados como usados após reset
  - Não revela se username existe (proteção contra enumeração)
  - Validação de expiração de tokens (1 hora)

- 🎨 **UI/UX**
  - Formulário de password reset integrado no overlay de login
  - Deteção automática de token de reset no URL
  - Feedback visual claro em todos os passos do processo
  - Widget de ajuda sempre acessível mas não intrusivo

- 📊 **Diagnósticos do sistema**
  - Melhorado endpoint `/diagnostics` com mais informações:
    * Versão Python e plataforma
    * Contagem de CPUs
    * Espaço em disco (total/usado/livre)
    * Socket MongoDB connectivity check
    * Verificações mais robustas do B2 (head_bucket)

### Técnico
- **Novos módulos** (criados em sessão anterior):
  - `core/email_service.py` - Serviço de envio de emails
  - `core/password_reset_repo.py` - Gestão de tokens de reset
  - `docs/SISTEMA-PASSWORD-RESET-E-BOT.md` - Documentação completa

- **Ficheiros modificados**:
  - `services/main.py` - Endpoints password reset, diagnostics melhorado
  - `core/models.py` - Modelos PasswordReset* (sessão anterior)
  - `core/auth_repo.py` - Métodos update_password(), update_email() (sessão anterior)
  - `static/app.js` - Funções password reset, help widget
  - `ui.html` - Formulários reset, help widget HTML/CSS, cache-buster v=44

- **Commits principais**:
  - `1028b69` - Feature: Add password reset system and help widget (Release 21)

- **Variáveis de ambiente** (sysadmin):
  ```env
  # SMTP Configuration (System-wide)
  SMTP_HOST=mail.serversmtp.com
  SMTP_PORT=587
  SMTP_USER=your-smtp-username
  SMTP_PASSWORD=your-smtp-password
  SMTP_FROM_EMAIL=noreply@saft.aquinos.io
  APP_URL=https://saft.aquinos.io
  ```

- **Documentação**: Ver [docs/SISTEMA-PASSWORD-RESET-E-BOT.md](docs/SISTEMA-PASSWORD-RESET-E-BOT.md) para detalhes completos

## [Release 20] - 2025-10-23

### Adicionado
- 🔐 **Gestão completa de credenciais AT**
  - Interface CRUD para credenciais da Autoridade Tributária
  - Visualização de credenciais com passwords mascaradas
  - Botões para ver/ocultar, editar e eliminar credenciais
  - Endpoint `GET /pt/secrets/at/entries-full` para listar credenciais com passwords
  - Endpoint `DELETE /pt/secrets/at/entry/{nif}` para eliminar credenciais
  - Método `delete_at_entry()` no `auth_repo.py`
  - Campo `password` opcional no modelo `ATEntryOut`

- 📊 **Melhorias no histórico de validações**
  - Botão "Eliminar" para remover registos do histórico
  - Eliminação automática de ficheiros ZIP do Backblaze B2 ao eliminar histórico
  - Confirmação clara antes de eliminar (BD + B2)
  - Feedback de sucesso/erro na eliminação B2

- 📤 **Exportações Excel corrigidas e melhoradas**
  - Botão "Exportar para Excel" no separador Histórico
  - Formato SpreadsheetML XML para melhor compatibilidade
  - Logging extensivo de debug para troubleshooting

- ✍️ **Formulário de registo de utilizadores**
  - Interface com tabs Login/Registar no overlay de autenticação
  - Formulário de registo com username, password e confirmação
  - Validação de password (mínimo 3 caracteres, confirmação obrigatória)
  - Auto-preenchimento do formulário de login após registo
  - Feedback visual de sucesso/erro

### Corrigido
- 🐛 **Fix crítico: Validações não apareciam no histórico**
  - Root cause: parâmetros incorretos na chamada a `save_validation()`
  - Corrigido para usar `jar_stdout`, `jar_stderr`, `returncode` em vez de `success`
  - Ficheiros agora salvos corretamente no histórico e B2

- 📊 **Fix crítico: Exportação Excel de documentos mostrava zeros**
  - Root cause #1: `renderDocsTable()` não armazenava docs em `allDocs` global
  - Root cause #2: nomes de campos incorretos (snake_case vs PascalCase)
  - Corrigido `exportDocsToExcel()` para usar `InvoiceType`, `NetTotal`, etc.
  - Valores monetários agora exportam corretamente

- 📈 **Fix: Exportação Excel do histórico com campos vazios**
  - Substituído parsing frágil de HTML por acesso direto a `allHistoryRecords`
  - Todos os campos agora exportam corretamente (data, NIF, ano, mês, etc.)

- 🚀 **Fix de deployment: ModuleNotFoundError**
  - Comentados imports de `core.fix_rules` (módulo não está no repositório)
  - Comentados 3 endpoints relacionados: `GET/POST/DELETE /fix-rules`
  - Deploy no Render agora funciona sem erros

### Melhorado
- 🎨 **UI de credenciais**
  - Substituída visualização JSON por tabela organizada
  - Botões de ação intuitivos (ver, editar, eliminar)
  - Feedback visual para ações (loading, sucesso, erro)

- 🔐 **UI de autenticação**
  - Overlay de login dividido em tabs Login/Registar
  - Interface mais intuitiva para novos utilizadores
  - Validações em tempo real

- 🔍 **Debug e logging**
  - Logging extensivo em `exportDocsToExcel()` para troubleshooting
  - Logs de confirmação em `renderDocsTable()` e `deleteHistoryRecord()`
  - Mensagens de erro mais descritivas

- 🚀 **Cache-busting**
  - Atualizado de v=40 para v=43
  - Garante que utilizadores carregam versão mais recente do JavaScript

### Técnico
- **Ficheiros modificados**:
  - `saft_pt_doctor/routers_pt.py` - Endpoints credenciais, histórico, B2, fix_rules
  - `core/auth_repo.py` - Método `delete_at_entry()`
  - `core/models.py` - Campo `password` opcional
  - `static/app.js` - Gestão credenciais, exportações Excel, histórico, registo
  - `ui.html` - Tabela credenciais, formulário registo, cache-buster v=43

- **Commits principais**:
  - `f6f797f` - Store docs globally in renderDocsTable
  - `7c076a4` - Use correct field names in docs Excel export
  - `164c18b` - Cache-buster v=42
  - `90d4d1e` - Add user registration form
  - `2aea141` - Comment out fix_rules imports

- **Pull Request**: #21
- **Documentação**: Ver [RELEASE-20.md](RELEASE-20.md) para detalhes completos

## [Não Lançado]

### Adicionado
- Sistema de logging estruturado com formato JSON
- Middleware de logging de requests com IDs únicos e métricas de tempo
- Documentação abrangente da API com Swagger UI melhorado
- Descrições detalhadas para todos os endpoints
- Validação robusta de configuração em ambiente de produção
- Sistema de CI/CD com GitHub Actions
- Testes automatizados expandidos com múltiplos cenários
- Docker Compose para desenvolvimento com MongoDB e Redis
- Script de setup automatizado para desenvolvimento (`setup.sh`)
- Suporte para CORS configurável por ambiente
- Estrutura preparada para cache Redis (futuro)
- Arquivo .gitignore abrangente
- Pipeline de segurança com Bandit e Safety
- Build multi-arquitetura (amd64/arm64)
- Templates GitHub para Issues (Bug Report, Feature Request)
- Template de Pull Request
- Guia GETTING_STARTED.md com instruções completas
- Script PowerShell para facilitar push inicial (`push-to-github.ps1`)

### Melhorado
- README.md com documentação completa e estruturada
- Estrutura de testes com fixtures mais robustas
- Configuração de ambiente mais flexível
- Tratamento de erros com logging contextual
- Configuração Docker otimizada para desenvolvimento
- Documentação técnica e de contribuição

### Corrigido
- Configuração do Render.com para deployment correto
- Caminho do Dockerfile e contexto de build no render.yaml
- URL do repositório no render.yaml

### Segurança
- Validação de SECRET_KEY em ambiente de produção
- Logging de tentativas de autenticação falhadas
- Headers de segurança melhorados

## [0.2.0] - 2024-XX-XX

### Adicionado
- API multi-país com suporte para Portugal
- Sistema de autenticação JWT
- Upload e armazenamento de arquivos SAFT
- Integração com FACTEMI para submissão
- Armazenamento encriptado de credenciais AT
- Suporte para Backblaze B2 storage
- Containerização com Docker
- Testes automatizados básicos

### Funcionalidades
- Registro e login de utilizadores
- Gestão de credenciais das autoridades tributárias
- Upload de arquivos XML SAFT
- Submissão automática às autoridades portuguesas
- Healthcheck endpoints

### Infraestrutura
- MongoDB para persistência
- FastAPI como framework web
- Estrutura modular e escalável
- Configuração via variáveis de ambiente

## [0.1.0] - 2024-XX-XX

### Adicionado
- Estrutura inicial do projeto
- Configuração básica da aplicação
- Endpoints fundamentais

---

## Tipos de Mudanças

- **Adicionado** para novas funcionalidades
- **Melhorado** para mudanças em funcionalidades existentes
- **Obsoleto** para funcionalidades que serão removidas
- **Removido** para funcionalidades removidas
- **Corrigido** para correções de bugs
- **Segurança** para vulnerabilidades corrigidas