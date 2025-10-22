# Manual de Utilizador
## SAFT Doctor - Validador Profissional de Ficheiros SAFT-T (PT)

---

**Versão**: 1.0 (Release 20)
**Data**: Outubro 2025
**URL da Aplicação**: [https://saft.aquinos.io](https://saft.aquinos.io)

---

## 📋 Índice

1. [Introdução](#introdução)
2. [Primeiros Passos](#primeiros-passos)
   - [Acesso à Aplicação](#acesso-à-aplicação)
   - [Registo de Utilizador](#registo-de-utilizador)
   - [Autenticação](#autenticação)
3. [Interface da Aplicação](#interface-da-aplicação)
4. [Funcionalidades Principais](#funcionalidades-principais)
   - [Validação de Ficheiros SAFT](#validação-de-ficheiros-saft)
   - [Análise de Documentos](#análise-de-documentos)
   - [Histórico de Validações](#histórico-de-validações)
   - [Gestão de Credenciais AT](#gestão-de-credenciais-at)
5. [Exportações](#exportações)
6. [Resolução de Problemas](#resolução-de-problemas)
7. [Boas Práticas](#boas-práticas)
8. [Suporte Técnico](#suporte-técnico)

---

## 📖 Introdução

Bem-vindo ao **SAFT Doctor**, uma aplicação web profissional desenvolvida para facilitar e automatizar a validação de ficheiros SAFT-T (Standard Audit File for Tax purposes) junto da Autoridade Tributária e Aduaneira Portuguesa.

### Porquê SAFT Doctor?

A validação de ficheiros SAFT é um processo crítico para empresas e profissionais de contabilidade. O SAFT Doctor foi criado para:

✅ **Simplificar** o processo de validação através de uma interface intuitiva
✅ **Automatizar** a comunicação com os sistemas da Autoridade Tributária
✅ **Centralizar** o histórico de validações num único local seguro
✅ **Agilizar** a análise e exportação de dados contabilísticos
✅ **Proteger** as suas credenciais com encriptação de grau empresarial

### Para Quem é Este Manual?

Este manual destina-se a profissionais com formação avançada em:
- Contabilidade e Fiscalidade
- Gestão Empresarial
- Tecnologias de Informação aplicadas à Contabilidade
- Auditoria e Consultoria Fiscal

### A Importância do Registo

> **💡 Nota Importante**
>
> Para usufruir de todas as funcionalidades do SAFT Doctor e manter um registo seguro e persistente das suas validações, **recomendamos vivamente que crie uma conta pessoal**.
>
> O registo é gratuito, rápido (menos de 1 minuto) e permite-lhe:
> - Guardar o histórico completo das suas validações
> - Armazenar credenciais AT de forma segura e encriptada
> - Exportar dados para Excel para análise posterior
> - Aceder ao serviço de qualquer dispositivo com as suas credenciais
> - Beneficiar de futuras funcionalidades premium

---

## 🚀 Primeiros Passos

### Acesso à Aplicação

#### Passo 1: Abrir o Navegador Web

A aplicação SAFT Doctor funciona em qualquer navegador moderno. Recomendamos:
- ✅ Google Chrome (versão 90+)
- ✅ Mozilla Firefox (versão 88+)
- ✅ Microsoft Edge (versão 90+)
- ✅ Safari (versão 14+)

#### Passo 2: Navegar para a URL

Digite na barra de endereços:

```
https://saft.aquinos.io
```

**📸 Imagem Sugerida**: Captura de ecrã da barra de endereços com a URL `https://saft.aquinos.io`

> **🔒 Segurança**
>
> Verifique sempre que o URL começa com `https://` (com o "s" de seguro) e que aparece um cadeado 🔒 na barra de endereços. Isto garante que a sua ligação está encriptada.

---

### Registo de Utilizador

Ao aceder pela primeira vez à aplicação, será apresentado um **overlay de autenticação**.

#### Passo 1: Aceder ao Formulário de Registo

**📸 Imagem Sugerida**: Overlay de autenticação com tabs "Login" e "Registar"

```
┌─────────────────────────────────────────┐
│     🔐 Autenticação                     │
├─────────────────────────────────────────┤
│                                         │
│  [ 🔓 Login ]  [ ✍️ Registar ]         │  ← Clique aqui
│                  ▲                      │
│                  │                      │
│                  └─── Tab de Registo   │
│                                         │
└─────────────────────────────────────────┘
```

1. Clique no tab **"✍️ Registar"** (canto superior direito do overlay)
2. O formulário de registo será apresentado

#### Passo 2: Preencher os Dados de Registo

**📸 Imagem Sugerida**: Formulário de registo preenchido com setas a indicar cada campo

```
┌─────────────────────────────────────────┐
│  Username                               │
│  ┌───────────────────────────────────┐  │ ← Escolha um nome único
│  │ joao.silva                        │  │   (letras, números, sem espaços)
│  └───────────────────────────────────┘  │
│                                         │
│  Password                               │
│  ┌───────────────────────────────────┐  │ ← Mínimo 3 caracteres
│  │ ••••••••                          │  │   (recomendado: 8+ chars)
│  └───────────────────────────────────┘  │
│                                         │
│  Confirmar Password                     │
│  ┌───────────────────────────────────┐  │ ← Repita a password exata
│  │ ••••••••                          │  │
│  └───────────────────────────────────┘  │
│                                         │
│        [ ✍️ Criar Conta ]               │ ← Clique para registar
│                                         │
└─────────────────────────────────────────┘
```

**Campos obrigatórios**:

| Campo | Descrição | Validação |
|-------|-----------|-----------|
| **Username** | Identificador único do utilizador | Alfanumérico, sem espaços |
| **Password** | Palavra-passe para acesso | Mínimo 3 caracteres |
| **Confirmar Password** | Repetição da password | Deve coincidir exatamente |

> **💡 Dica de Segurança**
>
> Embora o sistema aceite passwords com mínimo de 3 caracteres, **recomendamos vivamente** que utilize passwords com:
> - Pelo menos 8 caracteres
> - Mistura de letras maiúsculas e minúsculas
> - Números
> - Caracteres especiais (!, @, #, etc.)
>
> Exemplo de password forte: `Saft2025!@#`

#### Passo 3: Confirmar o Registo

Após preencher todos os campos:

1. Clique no botão **"✍️ Criar Conta"**
2. A aplicação validará os dados
3. Se tudo estiver correto, verá a mensagem:

```
┌─────────────────────────────────────────┐
│  ✅ Conta criada com sucesso!           │
│                                         │
│  Agora pode fazer login.                │
│                                         │
│              [ OK ]                     │
└─────────────────────────────────────────┘
```

4. Será automaticamente redirecionado para o **tab de Login**
5. As suas credenciais estarão **pré-preenchidas** para facilitar

**📸 Imagem Sugerida**: Mensagem de sucesso + tab Login com credenciais preenchidas

#### Validações do Formulário

A aplicação verifica em tempo real:

| Validação | Mensagem de Erro |
|-----------|------------------|
| Campos vazios | ⚠️ Preencha username e password |
| Password curta | ⚠️ Password deve ter pelo menos 3 caracteres |
| Passwords diferentes | ⚠️ As passwords não coincidem |
| Username duplicado | ❌ Erro ao registar: username já existe |

> **👤 Humanização**
>
> Compreendemos que criar mais uma conta pode parecer um passo extra desnecessário. No entanto, ao registar-se, está a criar um espaço pessoal e seguro onde todo o seu trabalho ficará guardado, protegido e acessível sempre que precisar. É como ter um gabinete digital exclusivo para as suas validações SAFT.

---

### Autenticação

#### Passo 1: Aceder ao Formulário de Login

Se acabou de se registar, as suas credenciais já estarão preenchidas. Caso contrário:

**📸 Imagem Sugerida**: Overlay de login com campos preenchidos

```
┌─────────────────────────────────────────┐
│     🔐 Autenticação                     │
├─────────────────────────────────────────┤
│                                         │
│  [ 🔓 Login ]  [ ✍️ Registar ]         │  ← Tab ativo
│    ▲                                    │
│    └─── Você está aqui                 │
│                                         │
│  Username                               │
│  ┌───────────────────────────────────┐  │
│  │ joao.silva                        │  │
│  └───────────────────────────────────┘  │
│                                         │
│  Password                               │
│  ┌───────────────────────────────────┐  │
│  │ ••••••••                          │  │
│  └───────────────────────────────────┘  │
│                                         │
│        [ 🔓 Entrar ]                    │ ← Clique aqui
│                                         │
│  Utilize dev/dev para acesso rápido     │ ← Apenas dev/teste
│                                         │
└─────────────────────────────────────────┘
```

#### Passo 2: Fazer Login

1. Preencha o **Username** e **Password**
2. Clique em **"🔓 Entrar"**
3. Se as credenciais estiverem corretas, o overlay desaparece
4. Será direcionado para a interface principal

**📸 Imagem Sugerida**: Transição do overlay para interface principal (antes/depois)

> **⚠️ Conta de Desenvolvimento**
>
> Existe uma conta de teste com credenciais `dev/dev` para demonstração rápida. **No entanto**, esta conta:
> - ❌ NÃO guarda dados permanentemente
> - ❌ É partilhada por todos os utilizadores de teste
> - ❌ NÃO deve ser usada para trabalho real
> - ❌ Pode ser limpa a qualquer momento
>
> **Para trabalho profissional, crie sempre a sua própria conta.**

#### Problemas de Autenticação

| Problema | Solução |
|----------|---------|
| ❌ Login error: Invalid credentials | Verifique username e password. Atenção a maiúsculas/minúsculas. |
| ❌ Login error: username not found | Utilizador não existe. Registe-se primeiro. |
| 🔄 A carregar indefinidamente | Verifique a sua ligação à Internet. Recarregue a página (F5). |
| 🔒 Esqueci a password | Contacte o suporte técnico para reset de password. |

---

## 🖥️ Interface da Aplicação

### Visão Geral

Após autenticação bem-sucedida, a interface principal é composta por:

**📸 Imagem Sugerida**: Interface completa anotada com números e setas

```
┌────────────────────────────────────────────────────────────┐
│  SAFT Doctor          👤 Username        🔧 Diag  🚪 Sair  │ ← 1. Barra de Navegação
├────────────────────────────────────────────────────────────┤
│                                                            │
│  [📄 Validação] [📋 Documentos] [📜 Histórico] [🔐 Creds] │ ← 2. Tabs Principais
│   ▲                                                        │
│   └─── Tab ativo                                          │
│                                                            │
│  ┌──────────────────────────────────────────────────────┐ │
│  │                                                      │ │ ← 3. Área de Trabalho
│  │  [Conteúdo do tab ativo]                            │ │    (muda conforme tab)
│  │                                                      │ │
│  └──────────────────────────────────────────────────────┘ │
│                                                            │
│  ┌──────────────────────────────────────────────────────┐ │
│  │  📊 Status: Pronto                                   │ │ ← 4. Barra de Status
│  └──────────────────────────────────────────────────────┘ │
│                                                            │
│  ┌──────────────────────────────────────────────────────┐ │
│  │  [Log de operações em tempo real...]                │ │ ← 5. Área de Log
│  └──────────────────────────────────────────────────────┘ │
└────────────────────────────────────────────────────────────┘
```

### Componentes da Interface

#### 1. Barra de Navegação Superior

| Elemento | Função |
|----------|--------|
| **SAFT Doctor** | Logótipo da aplicação (clique para recarregar) |
| **👤 [Username]** | Mostra o utilizador autenticado |
| **🔧 Diag** | Executa diagnósticos do sistema |
| **🚪 Sair** | Termina a sessão (logout) |

#### 2. Tabs Principais

| Tab | Ícone | Função |
|-----|-------|--------|
| **Validação** | 📄 | Upload e validação de ficheiros SAFT |
| **Documentos** | 📋 | Análise detalhada de documentos SAFT |
| **Histórico** | 📜 | Consulta de validações anteriores |
| **Credenciais AT** | 🔐 | Gestão de credenciais da Autoridade Tributária |

#### 3. Área de Trabalho

Espaço dinâmico que adapta o conteúdo ao tab selecionado.

#### 4. Barra de Status

Mostra informações sobre a operação atual:
- ✅ **Sucesso** (verde): Operação concluída com êxito
- ⚠️ **Aviso** (amarelo): Atenção necessária
- ❌ **Erro** (vermelho): Problema encontrado
- 🔄 **A processar** (azul): Operação em curso

#### 5. Área de Log

Registo em tempo real de todas as operações, útil para:
- Acompanhar progresso de validações
- Diagnosticar problemas
- Verificar comunicação com API

**📸 Imagem Sugerida**: Área de log com exemplos de mensagens

```
[2025-10-23 15:30:45] 🔄 Login rápido dev/dev...
[2025-10-23 15:30:46] ✅ Token obtido e validado
[2025-10-23 15:30:50] 📤 Upload ficheiro: SAFT_2024_10.xml (1.2 MB)
[2025-10-23 15:30:52] 🔍 Validação JAR iniciada...
[2025-10-23 15:31:05] ✅ Validação concluída: SEM ERROS
```

---

## 🔧 Funcionalidades Principais

### 📄 Validação de Ficheiros SAFT

Esta é a funcionalidade central do SAFT Doctor.

#### Objetivo

Validar ficheiros SAFT-T (PT) utilizando o validador oficial da Autoridade Tributária (FACTEMICLI.jar), com interface simplificada e armazenamento seguro.

#### Fluxo de Validação

**📸 Imagem Sugerida**: Diagrama de fluxo da validação

```
┌──────────────┐      ┌──────────────┐      ┌──────────────┐
│  Selecionar  │  ──► │   Upload +   │  ──► │  Validação   │
│   Ficheiro   │      │  Guardar B2  │      │  JAR AT      │
└──────────────┘      └──────────────┘      └──────────────┘
                                                    │
                                                    ▼
┌──────────────┐      ┌──────────────┐      ┌──────────────┐
│  Exportar    │  ◄── │  Consultar   │  ◄── │   Guardar    │
│  Resultado   │      │  Histórico   │      │  Histórico   │
└──────────────┘      └──────────────┘      └──────────────┘
```

#### Passo a Passo

##### 1. Selecionar o Tab "Validação"

Clique no tab **📄 Validação** na barra de tabs.

**📸 Imagem Sugerida**: Tab Validação selecionado

##### 2. Escolher o Ficheiro SAFT

```
┌────────────────────────────────────────────┐
│  📂 Escolher ficheiro XML                  │
│                                            │
│  ┌──────────────────────────────────────┐ │
│  │ SAFT_2024_10.xml                     │ │ ← Nome do ficheiro
│  │ 1.2 MB                               │ │ ← Tamanho
│  └──────────────────────────────────────┘ │
│                                            │
│  [ Procurar... ]                           │ ← Clique aqui
│                                            │
└────────────────────────────────────────────┘
```

1. Clique no botão **"Procurar..."**
2. Navegue até à localização do seu ficheiro SAFT
3. Selecione o ficheiro `.xml`
4. Clique **"Abrir"**

> **💡 Requisitos do Ficheiro**
>
> - Formato: XML (Standard Audit File for Tax)
> - Versão: SAFT-T PT (1.04_01)
> - Tamanho máximo: 100 MB (recomendado)
> - Extensão: `.xml`

##### 3. Preencher Dados da Validação

**📸 Imagem Sugerida**: Formulário de validação preenchido com anotações

```
┌────────────────────────────────────────────┐
│  NIF da Entidade                           │
│  ┌──────────────────────────────────────┐ │
│  │ 123456789                            │ │ ← NIF a validar
│  └──────────────────────────────────────┘ │
│                                            │
│  Ano Fiscal                                │
│  ┌──────────────────────────────────────┐ │
│  │ 2024                                 │ │ ← Ano (YYYY)
│  └──────────────────────────────────────┘ │
│                                            │
│  Mês                                       │
│  ┌──────────────────────────────────────┐ │
│  │ 10                                   │ │ ← Mês (1-12)
│  └──────────────────────────────────────┘ │
│                                            │
│  Tipo de Operação                          │
│  ┌──────────────────────────────────────┐ │
│  │ VALIDA ▼                             │ │ ← VALIDA/SUBMETE
│  └──────────────────────────────────────┘ │
│                                            │
└────────────────────────────────────────────┘
```

**Campos**:

| Campo | Descrição | Exemplo |
|-------|-----------|---------|
| **NIF** | Número de Identificação Fiscal da entidade | 123456789 |
| **Ano** | Ano fiscal do SAFT | 2024 |
| **Mês** | Mês do SAFT (1-12) | 10 |
| **Operação** | VALIDA (apenas valida) ou SUBMETE (valida e submete à AT) | VALIDA |

> **⚠️ Atenção**
>
> - **VALIDA**: Apenas valida o ficheiro, sem submeter à AT (recomendado para testes)
> - **SUBMETE**: Valida E submete oficialmente à Autoridade Tributária (irreversível)
>
> **Recomendação**: Use sempre VALIDA primeiro. Só use SUBMETE quando tiver certeza absoluta.

##### 4. Iniciar a Validação

**📸 Imagem Sugerida**: Botões de ação com destaque no "Validar Ficheiro"

```
┌────────────────────────────────────────────┐
│                                            │
│  [ 🔍 Validar Ficheiro ]  [ 📄 Docs ]     │
│         ▲                                  │
│         │                                  │
│         └─── Clique aqui para validar     │
│                                            │
└────────────────────────────────────────────┘
```

1. Clique no botão **"🔍 Validar Ficheiro"**
2. O ficheiro será enviado para validação
3. Acompanhe o progresso no **Log**:

```
[15:30:50] 📤 Upload ficheiro: SAFT_2024_10.xml (1.2 MB)
[15:30:51] ✅ Upload concluído
[15:30:51] 🔐 A desencriptar credenciais AT para NIF 123456789...
[15:30:52] ✅ Credenciais obtidas
[15:30:52] 🔍 Validação JAR iniciada (FACTEMICLI)...
[15:30:55] 📋 A processar ficheiro SAFT...
[15:31:00] 🔍 A validar estrutura XML...
[15:31:03] 🔍 A validar regras de negócio...
[15:31:05] ✅ Validação concluída: SEM ERROS
[15:31:05] 💾 A guardar no histórico...
[15:31:06] ✅ Guardado no histórico (ID: 67890abc)
```

##### 5. Interpretar o Resultado

**Cenário 1: Validação Bem-Sucedida ✅**

**📸 Imagem Sugerida**: Resultado de validação com sucesso

```
┌────────────────────────────────────────────────────────┐
│  📊 Resultado da Validação                             │
├────────────────────────────────────────────────────────┤
│                                                        │
│  ✅ VALIDAÇÃO CONCLUÍDA COM SUCESSO                    │
│                                                        │
│  NIF: 123456789                                        │
│  Período: Outubro 2024                                 │
│  Ficheiro: SAFT_2024_10.xml                            │
│  Tamanho: 1.2 MB                                       │
│                                                        │
│  📋 Estatísticas:                                      │
│  • Documentos: 450                                     │
│  • Clientes: 89                                        │
│  • Produtos: 234                                       │
│  • Total Faturação: € 125,450.00                       │
│                                                        │
│  ✅ Sem erros encontrados                              │
│  ✅ Ficheiro guardado no Backblaze B2                  │
│  ✅ Registo criado no histórico                        │
│                                                        │
└────────────────────────────────────────────────────────┘
```

**Cenário 2: Validação com Erros ❌**

**📸 Imagem Sugerida**: Resultado de validação com erros

```
┌────────────────────────────────────────────────────────┐
│  📊 Resultado da Validação                             │
├────────────────────────────────────────────────────────┤
│                                                        │
│  ❌ VALIDAÇÃO CONCLUÍDA COM ERROS                      │
│                                                        │
│  NIF: 123456789                                        │
│  Período: Outubro 2024                                 │
│                                                        │
│  ❌ 3 ERROS ENCONTRADOS:                               │
│                                                        │
│  1. Linha 1250: CustomerID inválido (vazio)            │
│  2. Linha 3402: TaxPayable não corresponde ao cálculo  │
│  3. Linha 5678: Data de documento superior à data do  │
│     sistema                                            │
│                                                        │
│  ⚠️ O ficheiro NÃO foi submetido à AT                  │
│  💡 Corrija os erros e tente novamente                 │
│                                                        │
└────────────────────────────────────────────────────────┘
```

> **📝 Nota Profissional**
>
> Erros de validação são comuns e fazem parte do processo. Cada erro identifica uma não-conformidade com as regras da AT. Anote os números de linha, corrija no seu software de contabilidade e volte a exportar o SAFT.

##### 6. Guardar/Exportar o Resultado

Após validação, pode:

1. **Ver no Histórico**: Tab **📜 Histórico** → listagem completa
2. **Exportar para Excel**: Tab **📜 Histórico** → botão **Exportar para Excel**
3. **Descarregar ZIP**: (funcionalidade futura)

---

### 📋 Análise de Documentos

Permite visualizar e exportar todos os documentos (faturas, notas de crédito, etc.) contidos num ficheiro SAFT.

#### Objetivo

Analisar em detalhe os documentos comerciais extraídos do SAFT, com possibilidade de filtragem e exportação para Excel.

#### Passo a Passo

##### 1. Selecionar o Tab "Documentos"

Clique no tab **📋 Documentos**.

**📸 Imagem Sugerida**: Tab Documentos selecionado

##### 2. Carregar o Ficheiro SAFT

Mesmo processo da validação:

1. Clique **"Procurar..."**
2. Selecione o ficheiro `.xml`
3. Clique **"📄 Checkar os Docs"**

**📸 Imagem Sugerida**: Botão "Checkar os Docs" destacado

```
┌────────────────────────────────────────────┐
│  📂 Ficheiro SAFT selecionado              │
│  SAFT_2024_10.xml (1.2 MB)                 │
│                                            │
│  [ 📄 Checkar os Docs ]                    │ ← Clique aqui
│         ▲                                  │
│         └─── Extrair documentos do SAFT   │
└────────────────────────────────────────────┘
```

##### 3. Visualizar a Tabela de Documentos

Após o processamento, aparece uma tabela com todos os documentos:

**📸 Imagem Sugerida**: Tabela de documentos com anotações

```
┌────────────────────────────────────────────────────────────────────────────────┐
│  📋 Documentos Extraídos: 450 documentos                                       │
├───┬──────┬─────────────┬────────────┬────────────┬──────────────┬──────────────┤
│ # │ Tipo │ Número      │ Data       │ Cliente    │ Valor s/ IVA │ Total        │
├───┼──────┼─────────────┼────────────┼────────────┼──────────────┼──────────────┤
│ 1 │ FT   │ FT 2024/001 │ 2024-10-01 │ CLI001     │ €    450.00  │ €    517.50  │
│ 2 │ FT   │ FT 2024/002 │ 2024-10-01 │ CLI003     │ €    890.00  │ €  1,023.70  │
│ 3 │ NC   │ NC 2024/001 │ 2024-10-02 │ CLI001     │ €   -120.00  │ €   -138.00  │
│...│ ...  │ ...         │ ...        │ ...        │ ...          │ ...          │
└───┴──────┴─────────────┴────────────┴────────────┴──────────────┴──────────────┘

[ 📊 Exportar para Excel ]  [ 🔍 Filtrar ]
```

**Tipos de Documento**:

| Código | Tipo | Descrição |
|--------|------|-----------|
| **FT** | Fatura | Fatura comercial normal |
| **FS** | Fatura Simplificada | Fatura simplificada |
| **FR** | Fatura-Recibo | Fatura com recibo incorporado |
| **NC** | Nota de Crédito | Anulação parcial ou total |
| **ND** | Nota de Débito | Acréscimo ao valor faturado |

##### 4. Filtrar Documentos

**📸 Imagem Sugerida**: Controlos de filtro

```
┌────────────────────────────────────────────┐
│  🔍 Filtros                                │
├────────────────────────────────────────────┤
│  Tipo:    [ Todos ▼ ]                      │
│  Status:  [ Todos ▼ ]                      │
│  Período: [ 01/10/2024 ] a [ 31/10/2024 ] │
│                                            │
│  [ Aplicar Filtros ]  [ Limpar ]           │
└────────────────────────────────────────────┘
```

Use os filtros para:
- Ver apenas Faturas (FT)
- Excluir documentos anulados
- Selecionar período específico

##### 5. Exportar para Excel

**📸 Imagem Sugerida**: Processo de exportação

1. Clique no botão **"📊 Exportar para Excel"**
2. O ficheiro será gerado e descarregado automaticamente
3. Nome do ficheiro: `documentos_saft_2024-10-23.xls`

**Conteúdo do Excel**:

| Coluna | Descrição |
|--------|-----------|
| Tipo | Tipo de documento (FT, NC, etc.) |
| Número | Número completo do documento |
| Data | Data de emissão |
| Cliente ID | Código do cliente |
| Cliente Nome | Nome do cliente |
| Valor s/ IVA (€) | Base tributável |
| IVA (€) | Montante de IVA |
| Total (€) | Valor total com IVA |
| Status | Normal / Anulado |

> **💼 Aplicação Profissional**
>
> A exportação para Excel permite-lhe:
> - Criar relatórios personalizados
> - Fazer análises com tabelas dinâmicas
> - Comparar períodos
> - Identificar padrões de faturação
> - Integrar com outras ferramentas de Business Intelligence

---

### 📜 Histórico de Validações

Consulte todas as validações realizadas, organizadas por data, NIF e período.

#### Objetivo

Manter um registo completo e auditável de todas as validações SAFT efetuadas, com possibilidade de consulta, exportação e eliminação.

#### Passo a Passo

##### 1. Aceder ao Histórico

Clique no tab **📜 Histórico**.

**📸 Imagem Sugerida**: Tab Histórico selecionado com tabela de registos

##### 2. Carregar o Histórico

**📸 Imagem Sugerida**: Botão "Carregar Histórico"

```
┌────────────────────────────────────────────┐
│  📜 Histórico de Validações                │
│                                            │
│  [ 🔄 Carregar Histórico ]                 │ ← Clique aqui
│         ▲                                  │
│         └─── Buscar registos da BD        │
└────────────────────────────────────────────┘
```

1. Clique em **"🔄 Carregar Histórico"**
2. Os registos serão carregados da base de dados
3. Apresentados em ordem cronológica inversa (mais recentes primeiro)

##### 3. Visualizar a Tabela de Histórico

**📸 Imagem Sugerida**: Tabela de histórico com anotações

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│  📜 Histórico de Validações (15 registos)                                           │
├──────────────────┬─────────┬──────┬─────┬─────────┬─────────┬──────────┬───────────┤
│ Data/Hora        │ NIF     │ Ano  │ Mês │ Operação│ Sucesso │ Ficheiro │ Ações     │
├──────────────────┼─────────┼──────┼─────┼─────────┼─────────┼──────────┼───────────┤
│ 2024-10-23 15:31 │ 1234567 │ 2024 │ 10  │ VALIDA  │ ✅ Sim  │ SAFT_... │ [📊][🗑️] │
│ 2024-10-22 14:20 │ 1234567 │ 2024 │ 09  │ VALIDA  │ ❌ Não  │ SAFT_... │ [📊][🗑️] │
│ 2024-10-21 10:15 │ 9876543 │ 2024 │ 09  │ SUBMETE │ ✅ Sim  │ SAFT_... │ [📊][🗑️] │
│ ...              │ ...     │ ...  │ ... │ ...     │ ...     │ ...      │ ...       │
└──────────────────┴─────────┴──────┴─────┴─────────┴─────────┴──────────┴───────────┘

[ 📊 Exportar para Excel ]
```

**Colunas**:

| Coluna | Descrição |
|--------|-----------|
| **Data/Hora** | Timestamp completo da validação |
| **NIF** | NIF da entidade validada |
| **Ano** | Ano fiscal |
| **Mês** | Mês fiscal |
| **Operação** | VALIDA ou SUBMETE |
| **Sucesso** | ✅ Sim (sem erros) ou ❌ Não (com erros) |
| **Ficheiro** | Nome do ficheiro SAFT |
| **Ações** | Botões de ação (ver detalhes, eliminar) |

##### 4. Ver Detalhes de uma Validação

Clique no botão **📊** na coluna "Ações" de um registo:

**📸 Imagem Sugerida**: Modal de detalhes de validação

```
┌─────────────────────────────────────────────────────────┐
│  📊 Detalhes da Validação                               │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  Data: 23 de Outubro de 2024, 15:31:05                 │
│  NIF: 123456789                                         │
│  Período: Outubro 2024                                  │
│  Operação: VALIDA                                       │
│  Resultado: ✅ Sucesso (sem erros)                      │
│                                                         │
│  📋 Ficheiro:                                           │
│  Nome: SAFT_2024_10.xml                                 │
│  Tamanho: 1.2 MB                                        │
│  Storage B2: users/joao.silva/123456789/2024-10/...    │
│                                                         │
│  📊 Estatísticas:                                       │
│  • Documentos: 450                                      │
│  • Clientes: 89                                         │
│  • Produtos: 234                                        │
│  • Total Faturação: € 125,450.00                        │
│                                                         │
│  📝 Saída do Validador JAR:                             │
│  ┌─────────────────────────────────────────────────┐   │
│  │ FACTEMICLI - Validador AT v2.0                  │   │
│  │ Ficheiro: SAFT_2024_10.xml                      │   │
│  │ Validação estrutural: OK                        │   │
│  │ Validação de negócio: OK                        │   │
│  │ Resultado: SEM ERROS                            │   │
│  └─────────────────────────────────────────────────┘   │
│                                                         │
│                        [ Fechar ]                       │
└─────────────────────────────────────────────────────────┘
```

##### 5. Eliminar um Registo

Para eliminar um registo do histórico:

**📸 Imagem Sugerida**: Confirmação de eliminação

1. Clique no botão **🗑️** na coluna "Ações"
2. Aparece uma confirmação:

```
┌─────────────────────────────────────────────┐
│  ⚠️ Confirmar Eliminação                    │
├─────────────────────────────────────────────┤
│                                             │
│  Tem a certeza que deseja eliminar este    │
│  registo do histórico?                      │
│                                             │
│  Isto irá eliminar:                         │
│  • O registo da base de dados               │
│  • O ficheiro ZIP do Backblaze B2           │
│                                             │
│  ⚠️ Esta ação é IRREVERSÍVEL                │
│                                             │
│     [ Cancelar ]     [ ✔️ Eliminar ]        │
└─────────────────────────────────────────────┘
```

3. Clique **"✔️ Eliminar"** para confirmar
4. O registo e ficheiro serão permanentemente eliminados

> **⚠️ Atenção Importante**
>
> A eliminação é permanente e não pode ser desfeita. Use esta função apenas quando:
> - O registo foi criado por erro
> - O ficheiro contém dados sensíveis que não devem ser mantidos
> - Está a fazer limpeza de registos antigos
>
> Recomendamos manter o histórico para fins de auditoria e rastreabilidade.

##### 6. Exportar Histórico para Excel

**📸 Imagem Sugerida**: Botão "Exportar para Excel" no histórico

Clique no botão **"📊 Exportar para Excel"** no topo da tabela.

**Conteúdo do Excel exportado**:

| Coluna | Descrição |
|--------|-----------|
| Data/Hora | Timestamp completo |
| NIF | NIF da entidade |
| Ano | Ano fiscal |
| Mês | Mês fiscal |
| Operação | VALIDA/SUBMETE |
| Sucesso | Sim/Não |
| Mensagem | Resumo do resultado |
| Ficheiro | Nome do ficheiro |
| Tamanho | Tamanho em bytes |

> **📊 Aplicação Prática**
>
> O histórico exportado permite:
> - Relatórios mensais de atividade
> - Auditoria de validações realizadas
> - Identificação de períodos com erros recorrentes
> - Comprovação de submissões à AT

---

### 🔐 Gestão de Credenciais AT

Guarde de forma segura e encriptada as credenciais de acesso ao Portal das Finanças.

#### Objetivo

Armazenar credenciais da Autoridade Tributária de forma encriptada para automatizar validações e submissões sem necessidade de inserção manual.

#### Segurança

🔒 **Encriptação de Grau Empresarial**

- As passwords são encriptadas usando **AES-256**
- Chave de encriptação armazenada em variável de ambiente (não no código)
- Desencriptação apenas no momento da utilização
- Nunca exibidas em logs ou mensagens de erro

#### Passo a Passo

##### 1. Aceder ao Tab "Credenciais AT"

Clique no tab **🔐 Credenciais AT**.

**📸 Imagem Sugerida**: Tab Credenciais AT selecionado

##### 2. Adicionar Nova Credencial

**📸 Imagem Sugerida**: Formulário de adicionar credencial

```
┌────────────────────────────────────────────┐
│  ➕ Adicionar Nova Credencial AT           │
├────────────────────────────────────────────┤
│                                            │
│  NIF / Username AT                         │
│  ┌──────────────────────────────────────┐ │
│  │ 123456789                            │ │ ← NIF da entidade
│  └──────────────────────────────────────┘ │
│                                            │
│  Password AT                               │
│  ┌──────────────────────────────────────┐ │
│  │ ••••••••••                           │ │ ← Password do Portal
│  └──────────────────────────────────────┘ │
│                                            │
│  [ ➕ Guardar Credencial ]                 │ ← Clique aqui
│                                            │
└────────────────────────────────────────────┘
```

1. Insira o **NIF** da entidade (serve como username no Portal das Finanças)
2. Insira a **Password** de acesso ao Portal das Finanças
3. Clique **"➕ Guardar Credencial"**

> **🔐 Segurança da Password**
>
> - A password é **imediatamente encriptada** antes de ser guardada
> - Nunca é armazenada em texto simples
> - Não aparece em logs ou mensagens de erro
> - Apenas o utilizador autenticado pode aceder às suas próprias credenciais

##### 3. Visualizar Credenciais Guardadas

Após adicionar credenciais, clique em **"🔄 Carregar Credenciais"**.

**📸 Imagem Sugerida**: Tabela de credenciais com passwords mascaradas

```
┌────────────────────────────────────────────────────────────────┐
│  🔐 Credenciais Guardadas (3 NIFs)                             │
├──────────────┬─────────────────────────┬───────────────────────┤
│ NIF          │ Password                │ Ações                 │
├──────────────┼─────────────────────────┼───────────────────────┤
│ 123456789    │ •••••••• [👁️ Ver]      │ [✏️ Editar] [🗑️]     │
│ 987654321    │ •••••••• [👁️ Ver]      │ [✏️ Editar] [🗑️]     │
│ 555444333    │ •••••••• [👁️ Ver]      │ [✏️ Editar] [🗑️]     │
└──────────────┴─────────────────────────┴───────────────────────┘
```

##### 4. Ver Password (Temporariamente)

Clique no botão **👁️ Ver** para revelar temporariamente a password:

**📸 Imagem Sugerida**: Password revelada

```
│ 123456789    │ MyP@ssw0rd! [👁️‍🗨️ Ocultar] │ [✏️ Editar] [🗑️] │
                  ▲
                  └─── Password visível
```

Clique novamente para voltar a mascarar: **👁️‍🗨️ Ocultar**

##### 5. Editar Password

**📸 Imagem Sugerida**: Modal de edição de password

1. Clique no botão **✏️ Editar**
2. Aparece um modal:

```
┌─────────────────────────────────────────────┐
│  ✏️ Editar Password para NIF 123456789      │
├─────────────────────────────────────────────┤
│                                             │
│  Nova Password                              │
│  ┌───────────────────────────────────────┐ │
│  │ ••••••••••                            │ │
│  └───────────────────────────────────────┘ │
│                                             │
│  Confirmar Password                         │
│  ┌───────────────────────────────────────┐ │
│  │ ••••••••••                            │ │
│  └───────────────────────────────────────┘ │
│                                             │
│     [ Cancelar ]     [ ✔️ Guardar ]         │
└─────────────────────────────────────────────┘
```

3. Insira a nova password (2 vezes para confirmar)
4. Clique **"✔️ Guardar"**

##### 6. Eliminar Credencial

**📸 Imagem Sugerida**: Confirmação de eliminação de credencial

1. Clique no botão **🗑️**
2. Confirme a eliminação:

```
┌─────────────────────────────────────────────┐
│  ⚠️ Confirmar Eliminação                    │
├─────────────────────────────────────────────┤
│                                             │
│  Tem a certeza que deseja eliminar a       │
│  credencial para o NIF 123456789?           │
│                                             │
│  ⚠️ Validações futuras para este NIF        │
│  necessitarão de nova credencial.           │
│                                             │
│     [ Cancelar ]     [ ✔️ Eliminar ]        │
└─────────────────────────────────────────────┘
```

3. Clique **"✔️ Eliminar"** para confirmar

> **💡 Quando Adicionar Credenciais?**
>
> - **Antes da primeira validação** de cada NIF
> - Quando alterar a password no Portal das Finanças
> - Ao trabalhar com múltiplas entidades (pode guardar várias)
>
> **Benefícios**:
> - Validações automáticas sem intervenção manual
> - Não precisa de lembrar passwords de múltiplos NIFs
> - Reduz erros de digitação
> - Acelera o processo de validação

---

## 📊 Exportações

O SAFT Doctor permite exportar dados em formato Excel para análise externa.

### Tipos de Exportação

| Exportação | Origem | Dados Exportados |
|------------|--------|------------------|
| **Histórico** | Tab Histórico | Lista completa de validações realizadas |
| **Documentos** | Tab Documentos | Lista detalhada de documentos extraídos do SAFT |

### Formato dos Ficheiros

- **Formato**: Excel (.xls)
- **Codificação**: UTF-8 com BOM (suporta caracteres portugueses)
- **Estrutura**: SpreadsheetML XML (compatível com Excel 2007+)
- **Nome**: `{tipo}_saft_{data}.xls` (ex: `historico_saft_2024-10-23.xls`)

### Como Utilizar os Ficheiros Exportados

**📸 Imagem Sugerida**: Excel aberto com dados exportados

#### 1. Abrir no Excel

Duplo-clique no ficheiro descarregado. Deve abrir diretamente no Excel.

#### 2. Tabelas Dinâmicas

Use Tabelas Dinâmicas para análises avançadas:

**Exemplo - Análise de Faturação por Tipo**:

```
┌────────────────┬────────────┬──────────────┐
│ Tipo Documento │ Quantidade │ Total (€)    │
├────────────────┼────────────┼──────────────┤
│ FT             │ 420        │ 120,450.00   │
│ FS             │ 25         │   3,200.00   │
│ NC             │ 5          │  -1,500.00   │
│ TOTAL          │ 450        │ 122,150.00   │
└────────────────┴────────────┴──────────────┘
```

**Passos**:
1. Selecione os dados
2. Menu **Inserir** → **Tabela Dinâmica**
3. Arraste campos para **Linhas**, **Valores**, etc.

#### 3. Gráficos

Crie gráficos para visualização:

**📸 Imagem Sugerida**: Gráfico de barras - Faturação por mês

- Gráfico de barras: Evolução mensal de faturação
- Gráfico circular: Distribuição por tipo de documento
- Gráfico de linhas: Tendência temporal

#### 4. Filtros Automáticos

Ative filtros para pesquisas rápidas:

1. Selecione cabeçalhos da tabela
2. Menu **Dados** → **Filtro**
3. Use setas ▼ nos cabeçalhos para filtrar

---

## 🔧 Resolução de Problemas

### Problemas Comuns e Soluções

#### 1. Não Consigo Fazer Login

**Sintomas**:
- ❌ Login error: Invalid credentials
- ❌ Login error: username not found

**Soluções**:

✅ **Verificar username e password**
   - Atenção a maiúsculas/minúsculas
   - Verifique se não há espaços extra

✅ **Criar conta se não existir**
   - Clique no tab "✍️ Registar"
   - Registe-se antes de tentar login

✅ **Reset de password**
   - Contacte suporte técnico se esqueceu password

#### 2. Validação Fica "A Processar" Indefinidamente

**Sintomas**:
- 🔄 A processar... (sem progresso)
- Log pára em determinado ponto

**Soluções**:

✅ **Verificar ligação à Internet**
   - Teste abrir outro website
   - Verifique firewall/antivírus

✅ **Tamanho do ficheiro**
   - Ficheiros > 50 MB podem demorar vários minutos
   - Aguarde pacientemente

✅ **Recarregar página**
   - Press **F5** ou **Ctrl + R**
   - Tente novamente

✅ **Verificar credenciais AT**
   - Tab **🔐 Credenciais AT**
   - Confirme que existem para o NIF usado

#### 3. Erro "Credenciais AT Não Encontradas"

**Sintomas**:
- ❌ Credenciais AT não encontradas para NIF 123456789

**Soluções**:

✅ **Adicionar credenciais**
   1. Vá ao tab **🔐 Credenciais AT**
   2. Adicione NIF e password
   3. Tente validar novamente

✅ **Verificar NIF correto**
   - O NIF no formulário de validação deve corresponder ao NIF das credenciais

#### 4. Exportação Excel com Zeros ou Vazio

**Sintomas**:
- Ficheiro Excel exporta com valores 0
- Colunas vazias

**Soluções**:

✅ **Hard Refresh do navegador**
   - Windows/Linux: **Ctrl + Shift + R**
   - Mac: **Cmd + Shift + R**
   - Isto garante que carrega a versão mais recente do código

✅ **Carregar documentos antes de exportar**
   - Tab Documentos: Clique **"📄 Checkar os Docs"**
   - Aguarde tabela aparecer
   - Só depois clique **"📊 Exportar para Excel"**

✅ **Carregar histórico antes de exportar**
   - Tab Histórico: Clique **"🔄 Carregar Histórico"**
   - Aguarde tabela aparecer
   - Só depois clique **"📊 Exportar para Excel"**

#### 5. Ficheiro SAFT Não Carrega

**Sintomas**:
- ❌ Erro ao processar ficheiro
- ❌ XML inválido

**Soluções**:

✅ **Verificar formato do ficheiro**
   - Deve ser `.xml` (não `.zip`, `.pdf`, etc.)
   - Abra em editor de texto: deve começar com `<?xml version="1.0"?>`

✅ **Validar estrutura XML**
   - Use validador XML online
   - Verifique se não está corrompido

✅ **Exportar novamente do software de contabilidade**
   - Pode haver erro na exportação original

#### 6. Histórico Não Mostra Validação Recente

**Sintomas**:
- Validação concluída mas não aparece no histórico

**Soluções**:

✅ **Recarregar histórico**
   - Clique **"🔄 Carregar Histórico"** novamente

✅ **Verificar se validação foi bem-sucedida**
   - Consulte o Log
   - Procure por: `✅ Guardado no histórico`

✅ **Verificar filtros**
   - Se houver filtros ativos, podem esconder o registo

#### 7. Overlay de Login Não Desaparece Após Login

**Sintomas**:
- Fiz login mas overlay continua visível

**Soluções**:

✅ **Recarregar página**
   - Press **F5**

✅ **Limpar cache do navegador**
   - Chrome: **Ctrl + Shift + Delete**
   - Limpar "Imagens e ficheiros em cache"

✅ **Tentar noutro navegador**
   - Use Chrome, Firefox ou Edge

### Obter Ajuda

Se nenhuma das soluções acima resolver o problema:

1. **Consulte os Logs** (área inferior da aplicação)
2. **Tire uma captura de ecrã** do erro
3. **Contacte o suporte técnico** (ver [Suporte Técnico](#suporte-técnico))

---

## ✅ Boas Práticas

### 1. Segurança

🔒 **Proteja as Suas Credenciais**

- Use passwords fortes (mínimo 8 caracteres, maiúsculas, minúsculas, números, símbolos)
- Não partilhe o seu username/password com terceiros
- Altere a password regularmente (a cada 3-6 meses)
- Termine sempre a sessão (botão **🚪 Sair**) ao acabar de trabalhar

🔐 **Credenciais AT**

- Só adicione credenciais AT de entidades que gere diretamente
- Elimine credenciais de clientes que já não trabalha
- Verifique regularmente se as passwords AT continuam válidas

### 2. Organização de Ficheiros

📁 **Nomenclatura de Ficheiros SAFT**

Use nomes descritivos e consistentes:

```
✅ BOM:  SAFT_NIF123456789_2024_10.xml
✅ BOM:  SAFT_EmpresaXPTO_Out2024.xml

❌ MAU: ficheiro.xml
❌ MAU: saft final (1) corrigido.xml
```

**Padrão recomendado**: `SAFT_{NIF}_{Ano}_{Mês}.xml`

### 3. Fluxo de Validação

📋 **Ordem Recomendada**

1. **Exportar SAFT** do software de contabilidade
2. **Validar localmente** (se possível) antes de submeter
3. **Usar operação VALIDA** no SAFT Doctor primeiro
4. **Corrigir erros** no software de contabilidade
5. **Re-validar** até obter 0 erros
6. **Só então usar SUBMETE** para submissão oficial

> **💡 Porquê este fluxo?**
>
> Usar VALIDA primeiro evita submissões com erros à AT, que podem:
> - Gerar multas ou avisos
> - Criar registos de submissões falhadas
> - Requerer correções e re-submissões (perda de tempo)

### 4. Gestão de Histórico

📜 **Manter Histórico Limpo**

- **Não elimine** registos de validações submetidas à AT (importantes para auditoria)
- **Elimine** apenas testes ou validações duplicadas
- **Exporte** periodicamente o histórico para Excel (backup)

### 5. Performance

⚡ **Otimizar Utilização**

- **Ficheiros grandes** (> 20 MB): Aguarde pacientemente (pode demorar 1-3 minutos)
- **Múltiplas validações**: Faça uma de cada vez (não abra múltiplos tabs)
- **Hard refresh** após atualizações: Garante que usa versão mais recente

### 6. Compatibilidade

🌐 **Navegadores e Dispositivos**

- **Desktop**: Experiência completa (recomendado)
- **Tablet**: Funcional mas menos confortável
- **Smartphone**: Não recomendado (ecrã pequeno)

**Navegadores testados**:
- ✅ Chrome 90+ (recomendado)
- ✅ Firefox 88+
- ✅ Edge 90+
- ✅ Safari 14+
- ❌ Internet Explorer (não suportado)

---

## 📞 Suporte Técnico

### Informações de Contacto

**URL da Aplicação**: [https://saft.aquinos.io](https://saft.aquinos.io)

**Email de Suporte**: support@aquinos.io
**Horário**: Segunda a Sexta, 9h00 - 18h00 (UTC)

### Ao Contactar o Suporte

Por favor forneça:

1. **Username** (para identificação)
2. **Descrição do problema** (clara e detalhada)
3. **Passos para reproduzir** o erro
4. **Capturas de ecrã** (se aplicável)
5. **Logs** da aplicação (copie da área de Log)

**Exemplo de mensagem de suporte eficaz**:

```
Assunto: Erro ao exportar histórico para Excel

Boa tarde,

Username: joao.silva
Problema: Ao tentar exportar o histórico para Excel, o ficheiro
descarrega mas todas as células aparecem com valor 0.

Passos seguidos:
1. Tab Histórico
2. Clique em "Carregar Histórico" (15 registos aparecem)
3. Clique em "Exportar para Excel"
4. Ficheiro descarrega: historico_saft_2024-10-23.xls
5. Ao abrir no Excel, todas as colunas numéricas têm 0

Já tentei:
- Hard refresh (Ctrl + Shift + R)
- Limpar cache do navegador
- Testar noutro navegador (Chrome e Firefox)

Em anexo: captura de ecrã do Excel com zeros.

Logs:
[2024-10-23 16:30:00] [EXPORT-HISTORY] Starting export...
[2024-10-23 16:30:00] [EXPORT-HISTORY] allHistoryRecords.length: 15
[2024-10-23 16:30:01] [EXPORT-HISTORY] Export completed

Aguardo orientações.

Cumprimentos,
João Silva
```

### FAQ Rápido

**P: A aplicação é gratuita?**
R: Sim, a aplicação SAFT Doctor é gratuita para todos os utilizadores registados.

**P: Os meus dados estão seguros?**
R: Sim. Todas as passwords são encriptadas com AES-256. A ligação é HTTPS (encriptada). Os ficheiros SAFT são armazenados em cloud segura (Backblaze B2) com acesso restrito.

**P: Posso usar a mesma conta em vários dispositivos?**
R: Sim. Faça login com as mesmas credenciais em qualquer dispositivo.

**P: Quantos NIFs posso gerir?**
R: Não há limite. Pode adicionar quantas credenciais AT quiser.

**P: O que acontece se esquecer a password?**
R: Contacte o suporte técnico para reset de password.

**P: Posso eliminar a minha conta?**
R: Sim. Contacte o suporte técnico para eliminação completa de dados (RGPD).

**P: A aplicação funciona offline?**
R: Não. Requer ligação à Internet para comunicar com a AT e guardar dados na cloud.

---

## 📚 Apêndice

### Glossário

| Termo | Definição |
|-------|-----------|
| **SAFT-T** | Standard Audit File for Tax purposes - Ficheiro standardizado de auditoria tributária |
| **AT** | Autoridade Tributária e Aduaneira |
| **NIF** | Número de Identificação Fiscal |
| **JAR** | Ficheiro executável Java (FACTEMICLI.jar é o validador oficial da AT) |
| **B2** | Backblaze B2 - Serviço de armazenamento cloud |
| **VALIDA** | Operação que apenas valida o ficheiro SAFT sem submeter à AT |
| **SUBMETE** | Operação que valida E submete oficialmente o ficheiro à AT |
| **FT** | Fatura |
| **FS** | Fatura Simplificada |
| **FR** | Fatura-Recibo |
| **NC** | Nota de Crédito |
| **ND** | Nota de Débito |
| **AES-256** | Advanced Encryption Standard com chave de 256 bits (encriptação forte) |

### Atalhos de Teclado

| Atalho | Função |
|--------|--------|
| **F5** | Recarregar página |
| **Ctrl + Shift + R** | Hard refresh (limpa cache) |
| **Ctrl + S** | Guardar (quando aplicável) |
| **Esc** | Fechar modais/overlays |
| **F12** | Abrir DevTools do navegador (debug avançado) |

### Códigos de Erro Comuns

| Código | Mensagem | Solução |
|--------|----------|---------|
| 401 | Unauthorized | Faça login novamente |
| 403 | Forbidden | Sem permissões (contacte suporte) |
| 404 | Not Found | Recurso não existe (recarregue página) |
| 500 | Internal Server Error | Erro do servidor (tente mais tarde ou contacte suporte) |

---

## 🙏 Nota Final

Obrigado por escolher o **SAFT Doctor** como ferramenta de validação de ficheiros SAFT.

Esta aplicação foi desenvolvida por profissionais para profissionais, com o objetivo de simplificar e humanizar um processo que tradicionalmente é técnico e complexo.

**O nosso compromisso**:

✅ Melhorar continuamente a aplicação com base no vosso feedback
✅ Manter os mais elevados padrões de segurança e privacidade
✅ Fornecer suporte técnico atento e eficaz
✅ Adicionar novas funcionalidades que tragam valor real ao vosso trabalho

**Ao registar-se e utilizar o SAFT Doctor**, está a juntar-se a uma comunidade de profissionais que valorizam:
- Eficiência
- Segurança
- Qualidade
- Inovação

Bem-vindo a bordo!

---

**Versão do Manual**: 1.0
**Data**: Outubro 2025
**Autor**: Equipa SAFT Doctor
**Website**: [https://saft.aquinos.io](https://saft.aquinos.io)
**Suporte**: support@aquinos.io

---

*Este documento está sujeito a atualizações. Consulte sempre a versão mais recente online.*
