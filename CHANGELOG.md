# Changelog

Todas as mudanças notáveis neste projeto serão documentadas neste arquivo.

O formato é baseado em [Keep a Changelog](https://keepachangelog.com/pt-BR/1.0.0/),
e este projeto adere ao [Semantic Versioning](https://semver.org/lang/pt-BR/).

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