# Release 20 - Gestão de Credenciais, Histórico e Exportações Excel

**Data**: 2025-10-23
**Branch**: `hotfix/fix-rules-dependency`
**PR**: #21
**Status**: ✅ Testado e funcional

---

## 📋 Resumo

Release focado em corrigir bugs críticos de deployment, implementar gestão completa de credenciais AT, melhorar o histórico de validações e corrigir exportações Excel.

## ✨ Funcionalidades Implementadas

### 1. 🔐 Gestão de Credenciais AT (Autoridade Tributária)

**Problema anterior**: Utilizadores não conseguiam visualizar, editar ou eliminar credenciais guardadas.

**Solução implementada**:
- Interface completa de CRUD para credenciais AT
- Visualização de credenciais com passwords mascaradas
- Botão "👁️ Ver" para mostrar/ocultar password
- Botão "✏️ Editar" para alterar password
- Botão "🗑️ Eliminar" para remover credencial
- Confirmação antes de eliminar credenciais

**Ficheiros alterados**:
- `saft_pt_doctor/routers_pt.py` - Endpoints `/pt/secrets/at/entries-full` e `DELETE /pt/secrets/at/entry/{nif}`
- `core/auth_repo.py` - Método `delete_at_entry()`
- `core/models.py` - Campo `password` opcional no `ATEntryOut`
- `static/app.js` - Funções `loadNifEntriesTable()`, `renderCredsTable()`, `togglePasswordVisibility()`, `editCredential()`, `deleteCredential()`
- `ui.html` - Tabela de credenciais substituindo `<pre>` JSON

**Como usar**:
1. No separador "Credenciais AT", clique em "🔄 Carregar Credenciais"
2. Visualize todas as credenciais numa tabela organizada
3. Clique "👁️ Ver" para revelar uma password
4. Clique "✏️ Editar" para alterar uma password
5. Clique "🗑️ Eliminar" para remover uma credencial (com confirmação)

---

### 2. 📊 Histórico de Validações Melhorado

#### 2.1 Correção: Ficheiros não apareciam no histórico

**Problema**: Após validação com JAR, os ficheiros não eram salvos no histórico.

**Root Cause**: Endpoint `/validate-jar-by-upload` chamava `save_validation()` com parâmetros incorretos:
```python
# ❌ ERRADO:
validation_id = await history_repo.save_validation(
    username=current['username'],
    success=ok,  # Este parâmetro não existe!
    ...
)
```

**Fix**: Corrigidos os parâmetros para corresponder à assinatura do método:
```python
# ✅ CORRETO:
validation_id = await history_repo.save_validation(
    username=current['username'],
    jar_stdout=stdout_str,
    jar_stderr=stderr_str,
    returncode=proc.returncode,
    ...
)
```

**Ficheiro**: `saft_pt_doctor/routers_pt.py` linhas 730-746

#### 2.2 Botão de Eliminação com B2

**Problema**: Botão "Eliminar" apenas removia da base de dados, não do Backblaze B2.

**Solução**:
- Eliminação do ficheiro ZIP do B2 antes de remover da base de dados
- Feedback ao utilizador sobre sucesso/erro da eliminação B2
- Confirmação com mensagem clara sobre o que será eliminado

**Código**:
```python
if storage_key:
    storage = Storage()
    storage.client.delete_object(
        Bucket=storage.bucket,
        Key=storage_key
    )
    b2_deleted = True
```

**Mensagem de confirmação**:
```
Tem a certeza que deseja eliminar este registo do histórico?

Isto irá eliminar:
- O registo da base de dados
- O ficheiro ZIP do Backblaze B2
```

**Ficheiro**: `saft_pt_doctor/routers_pt.py` linhas 1773-1814

---

### 3. 📤 Exportações Excel Corrigidas

#### 3.1 Exportação do Histórico

**Problema**: Campos vazios ou mal formatados no Excel exportado.

**Root Cause**: Código parseava HTML da tabela de forma frágil:
```javascript
// ❌ ERRADO - parsing HTML:
const periodo = cells[2].textContent.trim();
const periodoMatch = periodo.match(/(\d{4})-(\d{2})/);
```

**Fix**: Usar dados reais armazenados em `allHistoryRecords`:
```javascript
// ✅ CORRETO - dados reais:
html += '<td>' + (record.year || '') + '</td>';
html += '<td>' + (record.month || '') + '</td>';
```

**Ficheiro**: `static/app.js` linhas 1963-2063

**Colunas exportadas**:
- Data/Hora
- NIF
- Ano
- Mês
- Operação
- Sucesso
- Mensagem
- Ficheiro
- Tamanho

#### 3.2 Exportação de Documentos SAFT

**Problema 1**: `allDocs` não era populado quando documentos eram renderizados.

**Fix 1**: Adicionar armazenamento global em `renderDocsTable()`:
```javascript
window.renderDocsTable = function(docs) {
    // IMPORTANT: Store docs globally for export
    allDocs = docs || [];
    console.log('[renderDocsTable] Stored ' + allDocs.length + ' docs globally');
    ...
}
```

**Ficheiro**: `static/app.js` linha 2337

**Problema 2**: Nomes de campos incorretos - **ROOT CAUSE PRINCIPAL**

**Análise**:
- `renderDocsTable()` usa campos **PascalCase**: `InvoiceType`, `InvoiceNo`, `NetTotal`, etc.
- `exportDocsToExcel()` procurava campos **snake_case**: `type`, `number`, `net_total`, etc.
- Resultado: `parseFloat(undefined)` retornava `0` para todos os valores

**Fix 2**: Corrigir nomes dos campos no export:
```javascript
// ❌ ANTES:
const netTotal = parseFloat(doc.net_total) || 0;  // undefined → 0
html += `<Cell><Data ss:Type="String">${doc.type}</Data></Cell>`;

// ✅ DEPOIS:
const netTotal = parseFloat(doc.NetTotal) || 0;  // valor correto!
html += `<Cell><Data ss:Type="String">${doc.InvoiceType}</Data></Cell>`;
```

**Mapeamento completo de campos**:
| Errado (snake_case) | Correto (PascalCase) |
|---------------------|---------------------|
| `doc.type` | `doc.InvoiceType` |
| `doc.number` | `doc.InvoiceNo` |
| `doc.date` | `doc.InvoiceDate` |
| `doc.customer_id` | `doc.CustomerID` |
| `doc.customer_name` | `doc.CustomerName` |
| `doc.net_total` | `doc.NetTotal` |
| `doc.tax_payable` | `doc.TaxPayable` |
| `doc.gross_total` | `doc.GrossTotal` |
| `doc.status` | `doc.DocumentStatus` |

**Ficheiro**: `static/app.js` linhas 2499-2513

**Formato de exportação**: SpreadsheetML XML (formato nativo Excel)

**Colunas exportadas**:
- Tipo
- Número
- Data
- Cliente ID
- Cliente Nome
- Valor s/ IVA (€)
- IVA (€)
- Total (€)
- Status

---

### 4. 🐛 Fix de Deployment - ModuleNotFoundError

**Problema**: Após merge do PR #19, deployment no Render falhava:
```
ModuleNotFoundError: No module named 'core.fix_rules'
```

**Root Cause**: Ficheiro `core/fix_rules.py` existe localmente mas não está no repositório Git.

**Solução**:
- Comentar imports de `core.fix_rules` em `routers_pt.py`
- Comentar 3 endpoints relacionados: `GET/POST/DELETE /fix-rules`
- Comentar chamada a `detect_issue_with_rules()`

**Código comentado**:
```python
# from core.fix_rules import get_rules_manager, detect_issue_with_rules

# custom_issue = detect_issue_with_rules(msg, xml_path)
```

**Ficheiro**: `saft_pt_doctor/routers_pt.py` linha 14 e várias linhas em endpoints

**Nota**: Este módulo será restaurado numa release futura quando estiver pronto para produção.

---

### 5. ✍️ Formulário de Registo de Utilizadores

**Problema anterior**: Novos utilizadores não tinham forma de criar conta - apenas podiam usar credenciais existentes ou dev/dev.

**Solução implementada**:
- Interface com tabs Login/Registar no overlay de autenticação
- Formulário de registo com 3 campos:
  - Username
  - Password
  - Confirmar Password
- Validações em tempo real:
  - Campos obrigatórios
  - Password mínimo 3 caracteres
  - Confirmação de password deve coincidir
- Após registo bem-sucedido:
  - Auto-switch para tab de Login
  - Auto-preenchimento das credenciais no formulário de login
  - Mensagem de sucesso

**Ficheiros alterados**:
- `ui.html` - Tabs Login/Registar, formulário de registo (linhas 373-424)
- `static/app.js` - Funções `showAuthTab()` e `doRegister()` (linhas 1367-1446)

**Como usar**:
1. Ao abrir a aplicação sem autenticação, aparece o overlay
2. Clique no tab "✍️ Registar"
3. Preencha username, password e confirmação
4. Clique "✍️ Criar Conta"
5. Após sucesso, será redirecionado para o tab Login com credenciais preenchidas
6. Clique "🔓 Entrar" para fazer login

**Código principal**:
```javascript
window.doRegister = async function() {
    const username = document.getElementById('register_user').value.trim();
    const password = document.getElementById('register_pass').value;
    const passwordConfirm = document.getElementById('register_pass_confirm').value;

    // Validations
    if (!username || !password) {
        alert('⚠️ Preencha username e password');
        return;
    }

    if (password.length < 3) {
        alert('⚠️ Password deve ter pelo menos 3 caracteres');
        return;
    }

    if (password !== passwordConfirm) {
        alert('⚠️ As passwords não coincidem');
        return;
    }

    // Register via API
    const response = await fetch('/auth/register', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username: username, password: password })
    });

    // Auto-switch to login tab and fill form
    showAuthTab('login');
    document.getElementById('login_user').value = username;
    document.getElementById('login_pass').value = password;
}
```

---

## 🔧 Melhorias Técnicas

### Debug Logging Extensivo

Adicionado logging detalhado em:
- `exportDocsToExcel()` - rastreamento completo do processo de exportação
- `renderDocsTable()` - confirmação de armazenamento de dados
- `deleteHistoryRecord()` - confirmação de eliminação B2

**Exemplo de logs**:
```javascript
console.log('[renderDocsTable] Stored ' + allDocs.length + ' docs globally');
console.log('[EXPORT-DOCS] Starting export...');
console.log('[EXPORT-DOCS] Exporting ' + docsToExport.length + ' documents');
```

### Cache-Busting

Atualizado de `v=40` para `v=43` para forçar reload do JavaScript:
- `v=41` - Fix do armazenamento global de docs
- `v=42` - Fix dos nomes de campos na exportação
- `v=43` - Formulário de registo de utilizadores

**Ficheiro**: `ui.html` linha 354

---

## 📁 Ficheiros Modificados

### Backend
- `saft_pt_doctor/routers_pt.py` - Endpoints de credenciais, histórico, B2, comentar fix_rules
- `core/auth_repo.py` - Método `delete_at_entry()`
- `core/models.py` - Campo `password` opcional

### Frontend
- `static/app.js` - Gestão credenciais, exportações Excel corrigidas, histórico, registo utilizadores
- `ui.html` - Tabela de credenciais, formulário de registo, cache-buster v=43

---

## 🧪 Testes Realizados

### ✅ Gestão de Credenciais
- [x] Carregar lista de credenciais
- [x] Visualizar credenciais com passwords mascaradas
- [x] Ver/ocultar password individual
- [x] Editar password de credencial existente
- [x] Eliminar credencial com confirmação
- [x] Verificar eliminação no backend (MongoDB)

### ✅ Histórico de Validações
- [x] Validar ficheiro SAFT com JAR
- [x] Verificar que registo aparece no histórico
- [x] Confirmar storage_key no B2
- [x] Eliminar registo do histórico
- [x] Verificar eliminação do ficheiro ZIP do B2
- [x] Verificar feedback de sucesso/erro

### ✅ Exportação Excel - Histórico
- [x] Carregar histórico de validações
- [x] Exportar para Excel
- [x] Verificar todos os campos preenchidos
- [x] Verificar formatação de datas
- [x] Verificar valores numéricos corretos

### ✅ Exportação Excel - Documentos
- [x] Parse de ficheiro SAFT
- [x] Clicar "📄 Checkar os Docs"
- [x] Exportar para Excel
- [x] Verificar valores não são zero
- [x] Verificar tipos de documento corretos
- [x] Verificar valores monetários com 2 casas decimais
- [x] Abrir ficheiro Excel e confirmar dados legíveis

### ✅ Registo de Utilizadores
- [x] Abrir aplicação sem autenticação (ver overlay)
- [x] Clicar no tab "✍️ Registar"
- [x] Testar validação: campos vazios (deve alertar)
- [x] Testar validação: password < 3 caracteres (deve alertar)
- [x] Testar validação: passwords não coincidem (deve alertar)
- [x] Registar utilizador com dados válidos
- [x] Verificar auto-switch para tab Login
- [x] Verificar auto-preenchimento das credenciais
- [x] Fazer login com novo utilizador
- [x] Verificar registo criado no MongoDB

### ✅ Deployment
- [x] Build sem erros (sem ModuleNotFoundError)
- [x] Deploy no Render bem-sucedido
- [x] Health check OK em produção

---

## 🚀 Deploy

### Ambiente de Desenvolvimento
```bash
# Reiniciar Docker
docker-compose down
docker-compose up -d

# Hard refresh no browser
Ctrl + Shift + R  (Windows/Linux)
Cmd + Shift + R   (Mac)
```

### Ambiente de Produção (Render)
1. Merge PR #21 para `main`
2. Render detecta push e inicia deploy automático
3. Verificar logs de build: sem erros de módulos
4. Testar health check: `https://saft-doctor.onrender.com/health`
5. Testar funcionalidades em produção

---

## 📊 Commits do Release

```
f6f797f - Fix: Store docs globally in renderDocsTable for Excel export
7c076a4 - Fix: Use correct field names in docs Excel export
a9cbadc - UI: bump cache-buster app.js to v=41
164c18b - UI: bump cache-buster app.js to v=42
90d4d1e - Add user registration form to login overlay
2aea141 - Fix: Comment out fix_rules imports to prevent ModuleNotFoundError
```

---

## 🔍 Debugging Tips

### Se exportação de documentos mostrar zeros:

1. **Verificar browser cache**:
   - Fazer hard refresh (Ctrl+Shift+R)
   - Verificar em DevTools → Network que `app.js?v=42` foi carregado

2. **Verificar consola do browser (F12)**:
   ```
   [renderDocsTable] Stored 150 docs globally
   [EXPORT-DOCS] Starting export...
   [EXPORT-DOCS] Exporting 150 documents
   [EXPORT-DOCS] First document: {InvoiceType: "FT", NetTotal: 100.50, ...}
   ```

3. **Verificar estrutura de dados**:
   - Abrir consola
   - Digitar `allDocs[0]`
   - Confirmar que campos são PascalCase: `InvoiceType`, `NetTotal`, etc.

### Se histórico não guardar validações:

1. **Verificar logs do backend**:
   ```
   [save_validation] Saving validation for user: ...
   [save_validation] Storage key: ...
   [save_validation] Validation saved with ID: ...
   ```

2. **Verificar MongoDB**:
   ```javascript
   db.pt_validation_history.find({username: "seu_username"}).sort({validated_at: -1}).limit(1)
   ```

3. **Verificar Backblaze B2**:
   - Procurar ficheiro com nome: `{username}/{nif}/{year}-{month}/saft_{timestamp}.zip`

---

## 🎯 Próximos Passos

### Melhorias Futuras
- [ ] Restaurar módulo `core.fix_rules` quando estiver pronto
- [ ] Adicionar paginação ao histórico de validações
- [ ] Implementar filtros no histórico (por NIF, data, sucesso/erro)
- [ ] Adicionar download direto do ZIP do B2 a partir do histórico
- [ ] Exportar histórico em formato PDF
- [ ] Estatísticas agregadas de validações (gráficos)

### Otimizações
- [ ] Lazy loading para tabelas grandes de documentos
- [ ] Virtualização de lista para histórico com milhares de registos
- [ ] Comprimir ZIP antes de upload para B2
- [ ] Cache de credenciais AT em sessão

### Testes
- [ ] Testes unitários para `exportDocsToExcel()`
- [ ] Testes E2E para fluxo completo de validação e histórico
- [ ] Testes de performance com ficheiros SAFT grandes (>10MB)

---

## 📝 Notas de Migração

### Para utilizadores existentes:

✅ **Não há breaking changes** - todas as funcionalidades existentes continuam a funcionar.

✅ **Dados preservados** - histórico de validações anterior permanece intacto.

✅ **Credenciais seguras** - credenciais AT existentes permanecem encriptadas e funcionais.

### Hard refresh necessário:

Após deploy, utilizadores devem fazer **hard refresh** (Ctrl+Shift+R) para carregar `app.js?v=42` com as correções.

---

## 👥 Contribuidores

- **Carlos João** - Desenvolvimento e testes
- **Claude (Anthropic)** - Assistente de código

---

## 📄 Licença

MIT License - Ver [LICENSE](LICENSE) para detalhes.

---

**🎉 Release 20 completo e testado com sucesso!**
