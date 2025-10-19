# Changelog

Todas as mudanças notáveis neste projeto serão documentadas neste arquivo.

O formato é baseado em [Keep a Changelog](https://keepachangelog.com/pt-BR/1.0.0/),
e este projeto adere ao [Semantic Versioning](https://semver.org/lang/pt-BR/).

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

### Melhorado
- README.md com documentação completa e estruturada
- Estrutura de testes com fixtures mais robustas
- Configuração de ambiente mais flexível
- Tratamento de erros com logging contextual
- Configuração Docker otimizada para desenvolvimento
- Documentação técnica e de contribuição

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