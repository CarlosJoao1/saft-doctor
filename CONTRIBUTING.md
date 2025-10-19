# 🤝 Contribuindo para o SAFT Doctor

Obrigado pelo seu interesse em contribuir para o SAFT Doctor! Este documento orienta você sobre como contribuir efetivamente para o projeto.

## 📋 Índice

- [Código de Conduta](#código-de-conduta)
- [Como Contribuir](#como-contribuir)
- [Configuração do Ambiente](#configuração-do-ambiente)
- [Standards de Código](#standards-de-código)
- [Processo de Pull Request](#processo-de-pull-request)
- [Reportar Bugs](#reportar-bugs)
- [Sugerir Melhorias](#sugerir-melhorias)

## 📜 Código de Conduta

Este projeto adere ao [Contributor Covenant Code of Conduct](https://www.contributor-covenant.org/pt-br/version/2/1/code_of_conduct/). Ao participar, espera-se que você mantenha este código.

## 🚀 Como Contribuir

### Tipos de Contribuições

Aceitamos vários tipos de contribuições:

- 🐛 **Correção de bugs**
- ✨ **Novas funcionalidades**
- 📚 **Melhorias na documentação**
- 🧪 **Adição de testes**
- 🔧 **Refatoração de código**
- 🌍 **Suporte para novos países**

### Antes de Começar

1. Verifique se já existe uma [issue](https://github.com/seu-usuario/saft-doctor/issues) relacionada
2. Se não existir, crie uma issue descrevendo o problema ou melhoria
3. Aguarde feedback da equipe antes de começar a trabalhar

## ⚙️ Configuração do Ambiente

### Pré-requisitos

- Python 3.11+
- Docker e Docker Compose
- Git
- Conta Backblaze B2 (para testes completos)

### Setup Rápido

```bash
# Clone o repositório
git clone https://github.com/seu-usuario/saft-doctor.git
cd saft-doctor

# Execute o script de setup
chmod +x setup.sh
./setup.sh

# Ative o ambiente virtual
source venv/bin/activate  # Linux/Mac
# ou
venv\Scripts\activate     # Windows

# Execute os testes
cd services
python -m pytest ../tests/ -v
```

### Setup Manual

Se preferir configurar manualmente:

```bash
# Criar ambiente virtual
python -m venv venv
source venv/bin/activate

# Instalar dependências
pip install -r services/requirements.txt

# Configurar .env
cp .env.example .env
# Edite .env com suas configurações

# Iniciar serviços
docker-compose -f docker-compose.dev.yml up -d mongo redis

# Executar aplicação
cd services
uvicorn main:app --reload
```

## 📏 Standards de Código

### Estilo de Código

- **Formatação**: Usamos [Black](https://black.readthedocs.io/) para formatação automática
- **Imports**: Organizados com [isort](https://pycqa.github.io/isort/)
- **Linting**: [Flake8](https://flake8.pycqa.org/) para verificação de código
- **Tipo**: Anotações de tipo obrigatórias para funções públicas

### Executar Verificações

```bash
# Formatação
black services/ core/ saft-pt-doctor/

# Organizar imports
isort services/ core/ saft-pt-doctor/

# Linting
flake8 services/ core/ saft-pt-doctor/

# Verificação de segurança
bandit -r services/ core/ saft-pt-doctor/
```

### Estrutura de Código

```python
# Exemplo de função bem documentada
async def process_saft_file(
    file_path: str, 
    country: str, 
    user_credentials: dict
) -> dict:
    """
    Processa arquivo SAFT para submissão.
    
    Args:
        file_path: Caminho para o arquivo SAFT
        country: Código do país (pt, es, etc.)
        user_credentials: Credenciais do utilizador
        
    Returns:
        dict: Resultado do processamento
        
    Raises:
        ValueError: Se o arquivo for inválido
        HTTPException: Se a submissão falhar
    """
    logger.info("Processing SAFT file", extra={
        "file_path": file_path,
        "country": country,
        "user": user_credentials.get("username")
    })
    
    # Implementação...
```

### Logging

- Use logging estruturado com contexto
- Inclua `request_id` quando disponível
- Níveis apropriados: DEBUG, INFO, WARNING, ERROR
- Informações sensíveis devem ser mascaradas

```python
logger.info("User authentication successful", extra={
    "username": username,
    "country": country,
    "request_id": request.state.request_id
})
```

## 🔄 Processo de Pull Request

### 1. Preparação

```bash
# Crie uma branch a partir da main
git checkout main
git pull origin main
git checkout -b feature/sua-funcionalidade

# ou para bug fix
git checkout -b fix/correcao-do-bug
```

### 2. Desenvolvimento

- Faça commits pequenos e focados
- Use mensagens de commit descritivas
- Mantenha os testes atualizados

### 3. Antes de Submeter

```bash
# Execute todos os testes
python -m pytest tests/ -v

# Verifique o código
black --check services/ core/ saft-pt-doctor/
flake8 services/ core/ saft-pt-doctor/
bandit -r services/ core/ saft-pt-doctor/

# Execute verificação de segurança
safety check
```

### 4. Submissão

1. Push da sua branch
2. Abra um Pull Request no GitHub
3. Preencha o template de PR completamente
4. Aguarde review da equipe

### Template de PR

```markdown
## Descrição
Breve descrição das mudanças realizadas.

## Tipo de Mudança
- [ ] Bug fix (mudança que corrige um problema)
- [ ] Nova funcionalidade (mudança que adiciona funcionalidade)
- [ ] Breaking change (mudança que quebra compatibilidade)
- [ ] Documentação (mudança apenas na documentação)

## Como Foi Testado
Descreva os testes realizados para verificar as mudanças.

## Checklist
- [ ] Código segue os standards do projeto
- [ ] Testes passam localmente
- [ ] Documentação foi atualizada
- [ ] Changelog foi atualizado (se necessário)
```

## 🐛 Reportar Bugs

### Antes de Reportar

1. Verifique se o bug já foi reportado
2. Teste na versão mais recente
3. Colete informações sobre o ambiente

### Template de Bug Report

```markdown
**Descrição do Bug**
Descrição clara e concisa do problema.

**Reproduzir**
Passos para reproduzir:
1. Vá para '...'
2. Clique em '....'
3. Role para baixo até '....'
4. Veja o erro

**Comportamento Esperado**
Descrição clara do que deveria acontecer.

**Screenshots**
Se aplicável, adicione screenshots.

**Ambiente:**
- OS: [e.g. Ubuntu 20.04]
- Python: [e.g. 3.11.0]
- Docker: [e.g. 20.10.0]

**Logs**
```
Cole os logs relevantes aqui
```

**Contexto Adicional**
Qualquer outro contexto sobre o problema.
```

## 💡 Sugerir Melhorias

### Template de Feature Request

```markdown
**A sua sugestão está relacionada a um problema?**
Descrição clara do problema. Ex. "Fico frustrado quando [...]"

**Descreva a solução que gostaria**
Descrição clara e concisa da solução desejada.

**Descreva alternativas consideradas**
Descrição de soluções alternativas consideradas.

**Contexto Adicional**
Qualquer outro contexto ou screenshots sobre a sugestão.
```

## 🌍 Adicionando Suporte para Novos Países

### Estrutura Necessária

1. **Criar módulo do país**:
   ```
   saft-{código-país}-doctor/
   ├── routers_{código-país}.py
   ├── models_{código-país}.py
   └── submitter_{código-país}.py
   ```

2. **Implementar endpoints**:
   - Saúde específica do país
   - Configuração de credenciais
   - Upload e processamento
   - Submissão às autoridades

3. **Testes**:
   - Criar `test_{código-país}_flow.py`
   - Mockar serviços externos
   - Testar casos de erro

4. **Documentação**:
   - Atualizar README.md
   - Adicionar configuração específica
   - Documentar API endpoints

## 📞 Suporte

- **Issues**: [GitHub Issues](https://github.com/seu-usuario/saft-doctor/issues)
- **Discussões**: [GitHub Discussions](https://github.com/seu-usuario/saft-doctor/discussions)
- **Email**: support@saft-doctor.com

## 🏆 Reconhecimento

Contribuidores serão reconhecidos:
- No arquivo AUTHORS.md
- Nas release notes
- Na documentação

Obrigado por contribuir para o SAFT Doctor! 🎉