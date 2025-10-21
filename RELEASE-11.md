# Release 11

Melhorias de robustez e produção

- Async I/O para upload de chunks (não bloqueia event loop)
- Logs stdout detalhados para Render ([UPLOAD], [VALIDATE], [STARTUP])
- Cleanup automático de uploads antigos (>1h) no startup
- Progress bar sempre visível com logs por chunk
- Bloqueio de botões durante upload/validação
- Mensagens de erro detalhadas (status + corpo)
- UPLOAD_ROOT criado automaticamente com permissões

Data: 2025-10-21
