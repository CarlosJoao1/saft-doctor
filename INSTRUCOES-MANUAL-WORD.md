# Instruções: Criar Manual de Utilizador em Word com Imagens

Este documento explica como criar o manual de utilizador em formato Word (.docx) com capturas de ecrã reais da aplicação.

## 📋 Pré-requisitos

- Microsoft Word (2016 ou superior)
- Aplicação SAFT Doctor a correr (local ou https://saft.aquinos.io)
- Ferramenta de captura de ecrã (Windows: Snipping Tool / Snip & Sketch)

---

## 🎯 Método Rápido: Converter Markdown para Word

### Opção A: Usando Pandoc (Linha de Comando)

1. **Instalar Pandoc**:
   - Descarregar de: https://pandoc.org/installing.html
   - Windows: Descarregar .msi e instalar

2. **Converter ficheiro**:
   ```bash
   cd C:\Python\scripts\Pessoal\saft-doctor
   pandoc MANUAL-UTILIZADOR.md -o MANUAL-UTILIZADOR.docx --toc --toc-depth=2
   ```

3. **Resultado**: Ficheiro `MANUAL-UTILIZADOR.docx` criado

### Opção B: Usando Conversor Online

1. Ir a: https://cloudconvert.com/md-to-docx
2. Upload: `MANUAL-UTILIZADOR.md`
3. Converter
4. Descarregar `MANUAL-UTILIZADOR.docx`

### Opção C: Abrir diretamente no Word

1. Abrir Microsoft Word
2. File → Open
3. Selecionar `MANUAL-UTILIZADOR.md`
4. Word converte automaticamente
5. Save As → `.docx`

---

## 📸 Capturar Imagens da Aplicação

### Preparação

1. **Iniciar aplicação local**:
   ```bash
   docker-compose up -d
   ```
   Ou aceder a: https://saft.aquinos.io

2. **Abrir ferramenta de captura**:
   - Windows 10/11: `Win + Shift + S`
   - Ou: Procurar "Snipping Tool"

3. **Criar pasta para imagens**:
   ```
   C:\Python\scripts\Pessoal\saft-doctor\docs\images\
   ```

### Lista de Capturas Necessárias

#### 1. Autenticação e Registo

**Imagem 1.1**: `01-login-overlay.png`
- **Quando**: Abrir aplicação sem estar autenticado
- **O que mostrar**: Overlay de autenticação com tab Login ativo
- **Anotar**: Seta a apontar para tab "Registar"

**Imagem 1.2**: `02-register-form.png`
- **Quando**: Clicar no tab "✍️ Registar"
- **O que mostrar**: Formulário de registo vazio
- **Anotar**:
  - Seta no campo Username
  - Seta no campo Password
  - Seta no campo Confirmar Password
  - Seta no botão "Criar Conta"

**Imagem 1.3**: `03-register-filled.png`
- **Quando**: Preencher formulário com dados exemplo
- **O que mostrar**: Formulário preenchido (username: joao.silva)
- **Dados exemplo**:
  - Username: joao.silva
  - Password: ••••••••
  - Confirmar: ••••••••

**Imagem 1.4**: `04-register-success.png`
- **Quando**: Após registar com sucesso
- **O que mostrar**: Alert de sucesso + tab Login com credenciais preenchidas

**Imagem 1.5**: `05-login-form.png`
- **Quando**: Tab Login ativo
- **O que mostrar**: Formulário de login com credenciais preenchidas

#### 2. Interface Principal

**Imagem 2.1**: `06-interface-overview.png`
- **Quando**: Após login bem-sucedido
- **O que mostrar**: Interface completa
- **Anotar**:
  - Caixa vermelha: Barra de navegação superior
  - Caixa azul: Tabs principais
  - Caixa verde: Área de trabalho
  - Caixa amarela: Barra de status
  - Caixa roxa: Área de log

**Imagem 2.2**: `07-navbar.png`
- **Quando**: Zoom na barra superior
- **O que mostrar**: Logo, username, botões Diag e Sair
- **Anotar**: Setas em cada elemento com descrição

**Imagem 2.3**: `08-tabs.png`
- **Quando**: Zoom nos tabs
- **O que mostrar**: 4 tabs (Validação, Documentos, Histórico, Credenciais)
- **Anotar**: Seta a indicar tab ativo

#### 3. Validação de Ficheiros SAFT

**Imagem 3.1**: `09-validation-tab.png`
- **Quando**: Tab Validação selecionado
- **O que mostrar**: Formulário de validação vazio

**Imagem 3.2**: `10-file-selected.png`
- **Quando**: Após selecionar ficheiro SAFT
- **O que mostrar**: Nome do ficheiro e tamanho
- **Anotar**: Seta no botão "Procurar"

**Imagem 3.3**: `11-validation-form-filled.png`
- **Quando**: Formulário de validação preenchido
- **O que mostrar**:
  - Ficheiro: SAFT_2024_10.xml
  - NIF: 123456789
  - Ano: 2024
  - Mês: 10
  - Operação: VALIDA
- **Anotar**: Setas em cada campo

**Imagem 3.4**: `12-validation-in-progress.png`
- **Quando**: Durante validação (clicar "Validar Ficheiro")
- **O que mostrar**: Log com mensagens de progresso
- **Anotar**: Highlight nas mensagens do log

**Imagem 3.5**: `13-validation-success.png`
- **Quando**: Validação concluída com sucesso
- **O que mostrar**: Resultado no formato JSON + log com ✅
- **Anotar**: Highlight na mensagem "SEM ERROS"

**Imagem 3.6**: `14-validation-errors.png`
- **Quando**: Validação com erros (usar ficheiro com erros)
- **O que mostrar**: Resultado com lista de erros
- **Anotar**: Highlight nos erros

#### 4. Análise de Documentos

**Imagem 4.1**: `15-documents-tab.png`
- **Quando**: Tab Documentos selecionado
- **O que mostrar**: Formulário de upload

**Imagem 4.2**: `16-documents-button.png`
- **Quando**: Ficheiro selecionado
- **O que mostrar**: Botão "📄 Checkar os Docs" destacado
- **Anotar**: Seta no botão

**Imagem 4.3**: `17-documents-table.png`
- **Quando**: Após processar SAFT
- **O que mostrar**: Tabela completa de documentos (450 docs)
- **Anotar**:
  - Caixa nas colunas (Tipo, Número, Data, Cliente, Valores)
  - Seta no botão "Exportar para Excel"

**Imagem 4.4**: `18-documents-detail.png`
- **Quando**: Zoom numa linha da tabela
- **O que mostrar**: Detalhe de 3-4 documentos
- **Anotar**: Tipos diferentes (FT, NC, ND)

**Imagem 4.5**: `19-excel-docs.png`
- **Quando**: Após exportar, abrir Excel
- **O que mostrar**: Ficheiro Excel com documentos exportados
- **Anotar**: Dados reais visíveis

#### 5. Histórico de Validações

**Imagem 5.1**: `20-history-tab.png`
- **Quando**: Tab Histórico selecionado
- **O que mostrar**: Botão "Carregar Histórico"

**Imagem 5.2**: `21-history-table.png`
- **Quando**: Histórico carregado
- **O que mostrar**: Tabela com 10-15 registos
- **Anotar**:
  - Setas nas colunas (Data, NIF, Ano, Mês, Sucesso)
  - Setas nos botões de ação (📊, 🗑️)

**Imagem 5.3**: `22-history-detail.png`
- **Quando**: Clicar no botão 📊 de um registo
- **O que mostrar**: Modal com detalhes da validação
- **Anotar**: Informações principais

**Imagem 5.4**: `23-history-delete.png`
- **Quando**: Clicar no botão 🗑️
- **O que mostrar**: Confirmação de eliminação
- **Anotar**: Texto explicativo sobre B2

**Imagem 5.5**: `24-excel-history.png`
- **Quando**: Após exportar histórico
- **O que mostrar**: Excel com histórico exportado

#### 6. Gestão de Credenciais AT

**Imagem 6.1**: `25-credentials-tab.png`
- **Quando**: Tab Credenciais AT selecionado
- **O que mostrar**: Formulário de adicionar credencial

**Imagem 6.2**: `26-credentials-form.png`
- **Quando**: Formulário preenchido
- **O que mostrar**:
  - NIF: 123456789
  - Password: ••••••••
- **Anotar**: Setas nos campos

**Imagem 6.3**: `27-credentials-table.png`
- **Quando**: Após "Carregar Credenciais"
- **O que mostrar**: Tabela com 3 NIFs guardados
- **Anotar**:
  - Passwords mascaradas (•••••)
  - Botões (👁️ Ver, ✏️ Editar, 🗑️)

**Imagem 6.4**: `28-credentials-reveal.png`
- **Quando**: Clicar em "👁️ Ver"
- **O que mostrar**: Password revelada temporariamente
- **Anotar**: Botão mudou para "Ocultar"

**Imagem 6.5**: `29-credentials-edit.png`
- **Quando**: Clicar em "✏️ Editar"
- **O que mostrar**: Modal de edição de password

**Imagem 6.6**: `30-credentials-delete.png`
- **Quando**: Clicar em "🗑️"
- **O que mostrar**: Confirmação de eliminação

#### 7. Extras

**Imagem 7.1**: `31-log-area.png`
- **Quando**: Durante operação qualquer
- **O que mostrar**: Área de log com mensagens diversas
- **Anotar**: Diferentes tipos de mensagens (✅, ❌, 🔄, 📤)

**Imagem 7.2**: `32-status-bar.png`
- **Quando**: Durante operação
- **O que mostrar**: Barra de status com mensagem
- **Anotar**: Estados diferentes (sucesso, erro, aviso)

**Imagem 7.3**: `33-browser-url.png`
- **Quando**: Zoom na barra de endereços
- **O que mostrar**: https://saft.aquinos.io com cadeado 🔒

---

## 🖼️ Anotar Imagens (Adicionar Setas e Textos)

### Ferramentas Recomendadas

**Windows**:
- **Snagit** (pago, muito completo)
- **Greenshot** (grátis, open-source)
- **ShareX** (grátis, open-source)
- **Paint** (básico, já incluído no Windows)

**Online**:
- **Canva** (https://canva.com) - grátis
- **Photopea** (https://photopea.com) - grátis, clone do Photoshop

### Como Anotar no Greenshot

1. **Instalar Greenshot**:
   - Download: https://getgreenshot.org/downloads/
   - Instalar

2. **Capturar e anotar**:
   - Tecla: `Print Screen`
   - Selecionar área
   - Abre editor automático

3. **Adicionar setas**:
   - Botão: "Draw arrow"
   - Cor: Vermelho (#FF0000)
   - Espessura: 3px
   - Desenhar seta

4. **Adicionar texto**:
   - Botão: "Add text"
   - Font: Arial, tamanho 14
   - Cor: Vermelho ou Azul
   - Escrever texto explicativo

5. **Adicionar caixas/highlights**:
   - Botão: "Draw rectangle"
   - Cor: Vermelho ou Amarelo
   - Fill: None (só contorno)
   - Desenhar ao redor do elemento

6. **Guardar**:
   - File → Save As
   - Formato: PNG
   - Nome: Conforme lista acima

### Como Anotar no Paint (básico)

1. **Abrir imagem no Paint**:
   - Botão direito na imagem → Abrir com → Paint

2. **Adicionar setas**:
   - Home → Shapes → Arrow
   - Escolher "Outline" (sem fill)
   - Cor: Vermelho
   - Desenhar

3. **Adicionar texto**:
   - Home → Text (A)
   - Clicar na imagem
   - Escrever texto
   - Font: Arial, tamanho 14

4. **Guardar**:
   - File → Save As → PNG

---

## 📄 Inserir Imagens no Manual Word

### Passo a Passo

1. **Abrir MANUAL-UTILIZADOR.docx** no Word

2. **Procurar placeholders**:
   - Procurar por: `📸 Imagem Sugerida:`
   - Shortcut: `Ctrl + F`

3. **Para cada placeholder**:

   **Antes** (Markdown):
   ```
   **📸 Imagem Sugerida**: Overlay de autenticação com tabs Login/Registar
   ```

   **Depois** (Word):
   ```
   [Eliminar linha do placeholder]
   [Inserir imagem: 01-login-overlay.png]
   [Adicionar legenda abaixo: "Figura 1.1 - Overlay de autenticação"]
   ```

4. **Inserir imagem no Word**:
   - Posicionar cursor onde quer a imagem
   - Insert → Pictures → This Device
   - Selecionar imagem (ex: `01-login-overlay.png`)
   - Ajustar tamanho: Clicar na imagem → cantos → arrastar
   - Alinhamento: Center

5. **Adicionar legenda**:
   - Clicar na imagem
   - References → Insert Caption
   - Label: "Figura"
   - Position: Below selected item
   - Caption: "Figura 1.1 - Overlay de autenticação"

6. **Formatar imagem**:
   - Clicar na imagem
   - Picture Format → Wrap Text → "Square" ou "Top and Bottom"
   - Ajustar margens se necessário

### Numeração de Figuras

| Secção | Figuras | Range |
|--------|---------|-------|
| 1. Autenticação | 5 imagens | Figura 1.1 - 1.5 |
| 2. Interface | 3 imagens | Figura 2.1 - 2.3 |
| 3. Validação | 6 imagens | Figura 3.1 - 3.6 |
| 4. Documentos | 5 imagens | Figura 4.1 - 4.5 |
| 5. Histórico | 5 imagens | Figura 5.1 - 5.5 |
| 6. Credenciais | 6 imagens | Figura 6.1 - 6.6 |
| 7. Extras | 3 imagens | Figura 7.1 - 7.3 |
| **TOTAL** | **33 imagens** | |

---

## 🎨 Formatação Final do Word

### Estilos Recomendados

**Título (H1)**:
- Font: Calibri (Body), 24pt, Bold
- Color: RGB(37, 99, 235) - Azul
- Spacing: Before 12pt, After 6pt

**Subtítulo (H2)**:
- Font: Calibri (Body), 18pt, Bold
- Color: RGB(37, 99, 235)
- Spacing: Before 12pt, After 6pt

**Subtítulo (H3)**:
- Font: Calibri (Body), 14pt, Bold
- Color: RGB(71, 85, 105) - Cinza escuro
- Spacing: Before 6pt, After 3pt

**Corpo de Texto**:
- Font: Calibri (Body), 11pt
- Line spacing: 1.15
- Alignment: Justified

**Código/Exemplo**:
- Font: Consolas, 10pt
- Background: Cinza claro RGB(248, 250, 252)
- Border: 1pt cinza

**Notas/Avisos**:
- Background: Amarelo claro RGB(254, 252, 232)
- Border left: 4pt amarelo RGB(245, 158, 11)
- Padding: 10pt

### Índice Automático

1. **Criar índice**:
   - Posicionar cursor no início (após capa)
   - References → Table of Contents
   - Escolher estilo "Automatic Table 1"

2. **Atualizar índice**:
   - Clicar no índice
   - Update Table
   - "Update entire table"

### Cabeçalho e Rodapé

**Cabeçalho**:
- Logo SAFT Doctor (se tiver)
- Texto: "Manual de Utilizador - SAFT Doctor"
- Alinhamento: Centro

**Rodapé**:
- Esquerda: "Versão 1.0 - Outubro 2025"
- Centro: "Confidencial"
- Direita: Número de página

---

## ✅ Checklist Final

Antes de considerar o manual completo:

- [ ] Todas as 33 imagens capturadas
- [ ] Todas as imagens anotadas com setas/textos
- [ ] Todas as imagens inseridas no Word
- [ ] Todas as legendas adicionadas
- [ ] Índice gerado e atualizado
- [ ] Cabeçalho e rodapé configurados
- [ ] Numeração de páginas correta
- [ ] Tabelas formatadas
- [ ] Notas/avisos destacados
- [ ] Revisão ortográfica (F7)
- [ ] Links funcionais (testar Ctrl+Clique)
- [ ] Exportar para PDF (File → Export → Create PDF)

---

## 📤 Distribuição

### Formatos a Criar

1. **MANUAL-UTILIZADOR.docx** (editável)
   - Para clientes que querem personalizar

2. **MANUAL-UTILIZADOR.pdf** (final)
   - File → Export → Create PDF/XPS
   - Optimize for: Standard (publishing online and printing)

3. **MANUAL-UTILIZADOR-IMPRESSO.pdf** (impressão)
   - File → Print → Microsoft Print to PDF
   - Settings: High quality

### Metadados do Documento

Antes de distribuir, preencher:

1. **File → Info → Properties**:
   - Title: Manual de Utilizador - SAFT Doctor
   - Subject: Guia completo de utilização da aplicação SAFT Doctor
   - Author: Equipa SAFT Doctor
   - Company: Aquinos
   - Keywords: SAFT, Autoridade Tributária, Validação, Portugal, Contabilidade
   - Comments: Manual para utilizadores com formação avançada

---

## 🆘 Resolução de Problemas

### Imagem muito grande no Word

**Solução**:
- Clicar na imagem
- Picture Format → Size
- Width: Max 16cm (para página A4)
- Manter aspecto ratio ativado

### Imagem pixelizada/desfocada

**Solução**:
- Capturar novamente em resolução maior
- Ou: File → Options → Advanced → "Do not compress images in file"

### Setas/anotações não ficam boas

**Solução**:
- Usar Greenshot ou Snagit (melhores ferramentas)
- Praticar algumas capturas primeiro
- Manter consistência (mesma cor, espessura)

### Muitas imagens tornam ficheiro Word muito grande

**Solução**:
- Comprimir imagens:
  - Selecionar imagem → Picture Format → Compress Pictures
  - Resolution: 150 ppi (adequado para ecrã)
  - "Delete cropped areas of pictures" ✓

---

## 📞 Suporte

Se tiveres dúvidas durante o processo, podes:
- Consultar tutoriais do Greenshot: https://getgreenshot.org/help/
- Ver exemplos de manuais técnicos em: https://techwhirl.com/
- Pedir ajuda à comunidade: https://stackoverflow.com/

---

**Boa sorte com a criação do manual! 📚✨**
