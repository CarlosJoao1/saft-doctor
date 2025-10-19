# 🏥 SAFT Doctor - Multi-Country Tax File Processor

> **Uma API moderna e escalável para processamento e submissão de arquivos SAFT (Standard Audit File for Tax purposes) às autoridades tributárias.**

![FastAPI](https://img.shields.io/badge/FastAPI-0.115.0-009688?style=flat&logo=fastapi)
![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=flat&logo=python)
![MongoDB](https://img.shields.io/badge/MongoDB-7.0-47A248?style=flat&logo=mongodb)
![Docker](https://img.shields.io/badge/Docker-Enabled-2496ED?style=flat&logo=docker)

## 🌍 Países Suportados

- 🇵🇹 **Portugal**: `/pt/*` - Totalmente implementado
- 🇪🇸 **Espanha**: `/es/*` - Em desenvolvimento
- 🇫🇷 **França**: `/fr/*` - Planeado
- 🇮🇹 **Itália**: `/it/*` - Planeado
- 🇩🇪 **Alemanha**: `/de/*` - Planeado

## ✨ Funcionalidades

- **🔐 Autenticação JWT** com suporte multi-país
- **📤 Upload Seguro** de arquivos SAFT
- **🚀 Submissão Automática** às autoridades tributárias
- **🔒 Armazenamento Encriptado** de credenciais
- **📊 Logging Estruturado** para monitorização
- **🐳 Containerização** com Docker
- **📈 Escalabilidade** preparada para crescimento

## 🏗️ Arquitetura

### Stack Tecnológico

```
├── FastAPI 0.115.0         # Framework web assíncrono
├── MongoDB 7.0             # Base de dados NoSQL
├── JWT Authentication      # Autenticação segura
├── Backblaze B2           # Armazenamento cloud
├── Docker                 # Containerização
└── Render.com            # Deployment
```

### Estrutura do Projeto

```
saft-doctor/
├── core/                  # Componentes fundamentais
│   ├── auth_repo.py      # Repositório de utilizadores
│   ├── auth_utils.py     # Utilitários de autenticação
│   ├── deps.py           # Dependências da aplicação
│   ├── logging_config.py # Configuração de logging
│   ├── middleware.py     # Middleware HTTP
│   ├── models.py         # Modelos Pydantic
│   ├── security.py       # Funções de segurança
│   ├── storage.py        # Gestão de armazenamento
│   └── submitter.py      # Submissão de arquivos
├── saft-pt-doctor/        # Implementação Portugal
│   ├── routers_pt.py     # Rotas específicas PT
│   └── factemi/          # CLI FACTEMI
├── services/              # Aplicação principal
│   ├── main.py           # Aplicação FastAPI
│   ├── requirements.txt  # Dependências Python
│   └── Dockerfile        # Container Docker
└── tests/                # Testes automatizados
    ├── conftest.py       # Configuração de testes
    ├── test_health.py    # Testes de saúde
    └── test_pt_flow.py   # Testes fluxo PT
```

## 🚀 Quick Start

### Pré-requisitos

- Python 3.11+
- Docker e Docker Compose
- MongoDB
- Conta Backblaze B2

### 1. Clonar o Repositório

```bash
git clone https://github.com/seu-usuario/saft-doctor.git
cd saft-doctor
```

### 2. Configurar Variáveis de Ambiente

Crie um arquivo `.env`:

```env
# Application
APP_ENV=dev
APP_PORT=8080
DEFAULT_COUNTRY=pt
SECRET_KEY=your-super-secret-key-here
MASTER_KEY=your-master-encryption-key-here
LOG_LEVEL=INFO

# Database
MONGO_URI=mongodb://localhost:27017
MONGO_DB=saft_doctor
MONGO_SCOPING=collection_prefix

# Storage (Backblaze B2)
B2_ENDPOINT=https://s3.eu-central-003.backblazeb2.com
B2_REGION=eu-central-003
B2_BUCKET=your-bucket-name
B2_KEY_ID=your-key-id
B2_APP_KEY=your-app-key

# FACTEMI CLI
FACTEMICLI_JAR_PATH=/opt/factemi/FACTEMICLI.jar
SUBMIT_TIMEOUT_MS=600000

# CORS
CORS_ORIGINS=http://localhost:3000,https://yourdomain.com
```

### 3. Executar com Docker

```bash
docker-compose up -d
```

A API estará disponível em `http://localhost:8080`

### 4. Verificar Saúde da API

```bash
curl http://localhost:8080/health
```

## 📚 Documentação da API

### Endpoints Principais

#### 🔐 Autenticação

- `POST /auth/register` - Registar novo utilizador
- `POST /auth/token` - Obter token de acesso

#### 🇵🇹 Portugal (`/pt/*`)

- `GET /pt/health` - Verificar saúde do serviço PT
- `POST /pt/secrets/at` - Guardar credenciais AT
- `POST /pt/files/upload` - Upload de arquivo SAFT
- `POST /pt/submit` - Submeter arquivo às autoridades

### Documentação Interativa

Aceda a `http://localhost:8080/docs` para explorar a API interativamente com Swagger UI.

## 🧪 Testes

### Executar Testes

```bash
# Instalar dependências de teste
pip install pytest pytest-asyncio httpx

# Executar todos os testes
pytest

# Executar com cobertura
pytest --cov=.
```

### Estrutura de Testes

- `test_health.py` - Testes de endpoints de saúde
- `test_pt_flow.py` - Testes do fluxo completo Portugal

## 🔧 Desenvolvimento

### Instalação Local

```bash
# Criar ambiente virtual
python -m venv venv
source venv/bin/activate  # Linux/Mac
# ou
venv\Scripts\activate     # Windows

# Instalar dependências
pip install -r services/requirements.txt

# Executar aplicação
cd services
uvicorn main:app --reload --host 0.0.0.0 --port 8080
```

### Adicionar Novo País

1. Criar pasta `saft-{código-país}-doctor/`
2. Implementar `routers_{código-país}.py`
3. Adicionar rota no `main.py`
4. Configurar integração específica do país

## 🚀 Deployment

### Render.com (Recomendado)

1. Faça fork do repositório
2. Configure as variáveis de ambiente no Render
3. O deployment é automático via `render.yaml`

### Docker Manual

```bash
# Build da imagem
docker build -t saft-doctor ./services

# Executar container
docker run -p 8080:8080 --env-file .env saft-doctor
```

## 📊 Monitoring & Logging

### Logging Estruturado

A aplicação usa logging estruturado JSON com os seguintes campos:

- `timestamp` - Timestamp UTC
- `level` - Nível do log
- `logger` - Nome do logger
- `message` - Mensagem
- `request_id` - ID único do request
- `user_id` - ID do utilizador (quando disponível)
- `country` - País do contexto

### Métricas

- Tempo de resposta por endpoint
- Taxa de sucesso/erro por país
- Volume de uploads por período

## 🔒 Segurança

- **Autenticação JWT** com expiração configurável
- **Encriptação de credenciais** sensíveis na base de dados
- **Validação rigorosa** de inputs
- **CORS configurável** por ambiente
- **Rate limiting** (planeado)

## 🤝 Contribuição

1. Fork o projeto
2. Crie uma branch para a feature (`git checkout -b feature/nova-funcionalidade`)
3. Commit as alterações (`git commit -am 'Adicionar nova funcionalidade'`)
4. Push para a branch (`git push origin feature/nova-funcionalidade`)
5. Abra um Pull Request

## 📝 Roadmap

- [ ] Implementação Espanha (`/es/*`)
- [ ] Rate limiting e throttling
- [ ] Cache Redis para performance
- [ ] Métricas Prometheus
- [ ] Testes end-to-end
- [ ] CI/CD pipeline
- [ ] Documentação técnica detalhada

## 📄 Licença

Este projeto está licenciado sob a MIT License - consulte o arquivo [LICENSE](LICENSE) para detalhes.

## 👥 Equipa

- **Desenvolvimento**: SAFT Doctor Team
- **Suporte**: support@saft-doctor.com

---

**💡 Dica**: Para questões técnicas ou sugestões, abra uma [issue](https://github.com/seu-usuario/saft-doctor/issues) no GitHub.
