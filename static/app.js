// SAFT Doctor - UI Logic v2 (UX Professional)
// Global state
window.state = { token: null, objectKey: null, file: null, username: null };

// Load token from localStorage on startup
try {
    const saved = localStorage.getItem('saft_token');
    const savedUser = localStorage.getItem('saft_username');
    if (saved) {
        window.state.token = saved;
        window.state.username = savedUser || 'Utilizador';
    }
} catch (_) {}

// Utilities
window.setStatus = function(msg, type = 'info') {
    const s = document.getElementById('status');
    if (!s) return;
    s.textContent = msg;
    s.style.color = type === 'error' ? 'var(--error)' : type === 'success' ? 'var(--success)' : 'var(--text-secondary)';
};

window.logLine = function(msg) {
    const el = document.getElementById('log');
    if (!el) return;
    const ts = new Date().toISOString().split('T')[1].split('.')[0]; // HH:MM:SS
    const isEmpty = !el.textContent || el.textContent === '(log vazio)';
    el.textContent = (isEmpty ? '' : el.textContent) + `[${ts}] ${msg}\n`;
    el.scrollTop = el.scrollHeight;
};

// Upload direto para B2 usando URL presignado
window.presignUpload = async function() {
    if (!state.token) {
        setStatus('⚠️ Faça login primeiro', 'error');
        return;
    }
    const fI = document.getElementById('file');
    if (!fI.files.length) {
        setStatus('⚠️ Escolha um ficheiro XML primeiro', 'error');
        return;
    }
    const f = fI.files[0];
    setStatus('☁️ A gerar URL presignada…', 'info');
    logLine('Solicitar presign-upload…');
    try {
        const res = await fetch('/pt/files/presign-upload', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': 'Bearer ' + state.token
            },
            body: JSON.stringify({ filename: f.name, content_type: f.type || 'application/octet-stream' })
        });
        const j = await res.json();
        if (!res.ok) throw new Error(j.detail || 'Falha ao gerar URL presignada');

        setStatus('📤 A enviar ficheiro para o B2…', 'info');
        const put = await fetch(j.url, { method: 'PUT', headers: j.headers || {}, body: f });
        if (!put.ok && put.status !== 200 && put.status !== 201) {
            throw new Error('PUT falhou com status ' + put.status);
        }

        state.objectKey = j.object;
        const okEl = document.getElementById('object_key');
        if (okEl) okEl.textContent = state.objectKey;
        setStatus('✅ Upload concluído. object_key definido.', 'success');
        logLine('Upload presign: OK → ' + state.objectKey);
    } catch (e) {
        setStatus('❌ Erro no upload presignado: ' + e.message, 'error');
        logLine('Erro presign-upload: ' + e.message);
    }
};

window.clearLog = function() {
    const el = document.getElementById('log');
    if (el) el.textContent = '(log vazio)';
};

// Upload direto para B2 usando URL presignado
window.presignUpload = async function() {
    if (!state.token) { setStatus('⚠️ Faça login primeiro', 'error'); return; }
    const fI = document.getElementById('file');
    if (!fI.files.length) { setStatus('⚠️ Escolha um ficheiro XML primeiro', 'error'); return; }
    const f = fI.files[0];
    setStatus('☁️ A gerar URL presignada…', 'info');
    logLine('Solicitar presign-upload…');
        const btnB2 = document.getElementById('btn-b2');
        const btnJar = document.getElementById('btn-jar');
        const btnBasic = document.getElementById('btn-validate');
    try {
        const res = await fetch('/pt/files/presign-upload', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json', 'Authorization': 'Bearer ' + state.token },
            body: JSON.stringify({ filename: f.name, content_type: f.type || 'application/octet-stream' })
        });
        const j = await res.json();
        if (!res.ok) throw new Error(j.detail || 'Falha ao gerar URL presignada');
        setStatus('📤 A enviar ficheiro para o B2…', 'info');
        if (btnB2) btnB2.disabled = true;
        if (btnJar) btnJar.disabled = true;
        if (btnBasic) btnBasic.disabled = true;
        const prog = document.getElementById('upload-progress');
        const progBar = document.getElementById('upload-progress-bar');
        const progText = document.getElementById('upload-progress-text');
        if (prog) prog.style.display = '';
        if (progBar) progBar.style.width = '0%';
        if (progText) progText.textContent = '0%';

        await new Promise((resolve, reject) => {
            const xhr = new XMLHttpRequest();
            xhr.open('PUT', j.url, true);
            const headers = j.headers || {};
            for (const k in headers) {
                try { xhr.setRequestHeader(k, headers[k]); } catch(e) {}
            }
            xhr.upload.onprogress = (e) => {
                if (e.lengthComputable && progBar && progText) {
                    const pct = Math.round((e.loaded / e.total) * 100);
                    progBar.style.width = pct + '%';
                    progText.textContent = pct + '%';
                } else if (progText) {
                    progText.textContent = 'a enviar…';
                }
            };
            xhr.onerror = () => reject(new Error('Erro de rede no upload'));
            xhr.onabort = () => reject(new Error('Upload cancelado'));
            xhr.onload = () => {
                if (xhr.status === 200 || xhr.status === 201) resolve(); else reject(new Error('PUT falhou com status ' + xhr.status));
            };
            xhr.send(f);
        });
        state.objectKey = j.object;
    const okEl = document.getElementById('object_key');
    if (okEl) okEl.textContent = state.objectKey;
    state.lastFilename = f.name;
    const okName = document.getElementById('object_key_name');
    if (okName) okName.textContent = state.lastFilename;
        setStatus('✅ Upload concluído. object_key definido.', 'success');
        logLine('Upload presign: OK → ' + state.objectKey);
            if (btnB2) btnB2.disabled = false;
            if (btnJar) btnJar.disabled = false;
            if (btnBasic) btnBasic.disabled = false;
    } catch (e) {
        setStatus('❌ Erro no upload presignado: ' + e.message, 'error');
        logLine('Erro presign-upload: ' + e.message);
            if (btnB2) btnB2.disabled = false;
            if (btnJar) btnJar.disabled = false;
            if (btnBasic) btnBasic.disabled = false;
    }
};

// Validação inteligente: usa B2 se disponível; senão, faz upload via Presign e depois valida do B2
window.validateSmart = async function() {
    if (!state.token) { setStatus('⚠️ Faça login primeiro', 'error'); return; }
    // Se já temos object_key, validar do B2 diretamente
    if (state.objectKey) {
        return await validateFromB2();
    }
    // Caso contrário, faça upload chunked para o servidor e valide
    const btnValidar = document.getElementById('btn-validate');
    const btnJar = document.getElementById('btn-jar');
    const btnB2 = document.getElementById('btn-b2');
    try {
        const fI = document.getElementById('file');
        if (!fI.files.length) { setStatus('⚠️ Escolha um ficheiro XML primeiro', 'error'); return; }
        const f = fI.files[0];
        // Bloqueia botões durante upload
        if (btnValidar) btnValidar.disabled = true;
        if (btnJar) btnJar.disabled = true;
        if (btnB2) btnB2.disabled = true;
        // Iniciar progress bar
        const prog = document.getElementById('upload-progress');
        const progBar = document.getElementById('upload-progress-bar');
        const progText = document.getElementById('upload-progress-text');
        if (prog) prog.style.display = 'block';
        if (progBar) progBar.style.width = '0%';
        if (progText) progText.textContent = '0%';
        logLine('📤 Iniciando upload segmentado...');
        setStatus('📤 A enviar ficheiro em chunks...', 'info');
        // start
        const startRes = await fetch('/pt/upload/start', {
            method: 'POST', headers: { 'Content-Type': 'application/json', 'Authorization': 'Bearer ' + state.token },
            body: JSON.stringify({ filename: f.name, size: f.size })
        });
        if (!startRes.ok) {
            const errText = await startRes.text();
            throw new Error(`Falha no upload/start (${startRes.status}): ${errText}`);
        }
        const start = await startRes.json();
        if (!start.upload_id) throw new Error('Sem upload_id na resposta');
        const uploadId = start.upload_id;
        const chunkSize = start.chunk_size || (5 * 1024 * 1024);
        logLine(`✅ Upload iniciado: id=${uploadId}, chunk=${Math.round(chunkSize/1024)}KB`);
        let sent = 0; let index = 0;
        const totalChunks = Math.ceil(f.size / chunkSize);
        while (sent < f.size) {
            const slice = f.slice(sent, Math.min(sent + chunkSize, f.size));
            const buf = await slice.arrayBuffer();
            logLine(`📦 Enviando chunk ${index+1}/${totalChunks} (${Math.round(slice.size/1024)}KB)...`);
            const putRes = await fetch(`/pt/upload/chunk?upload_id=${uploadId}&index=${index}`, {
                method: 'PUT', headers: { 'Authorization': 'Bearer ' + state.token }, body: buf
            });
            if (!putRes.ok) {
                const errText = await putRes.text();
                throw new Error(`Falha no chunk ${index} (${putRes.status}): ${errText}`);
            }
            sent += slice.size; index++;
            const pct = Math.round((sent / f.size) * 100);
            if (progBar) progBar.style.width = pct + '%';
            if (progText) progText.textContent = pct + '%';
        }
        logLine(`✅ Upload 100% completo (${totalChunks} chunks)`);
        const finishRes = await fetch('/pt/upload/finish', {
            method: 'POST', headers: { 'Content-Type': 'application/json', 'Authorization': 'Bearer ' + state.token },
            body: JSON.stringify({ upload_id: uploadId })
        });
        if (!finishRes.ok) {
            const errText = await finishRes.text();
            throw new Error(`Falha no upload/finish (${finishRes.status}): ${errText}`);
        }
        logLine('🔍 A validar ficheiro no servidor...');
        setStatus('🔍 A validar ficheiro...', 'info');
        // validate via upload
        const vres = await fetch(`/pt/validate-jar-by-upload?upload_id=${uploadId}&operation=validar&full=1`, { headers: { 'Authorization': 'Bearer ' + state.token }, method: 'POST' });
        const txt = await vres.text();
        let data = null;
        try { data = txt ? JSON.parse(txt) : null; } catch(_e){ /* ignore */ }
        const out = document.getElementById('out');
        if (out) out.textContent = data ? JSON.stringify(data, null, 2) : (txt || '(sem resposta)');
        const cmdEl = document.getElementById('cmd_mask');
        if (data?.cmd_masked?.join) cmdEl.textContent = data.cmd_masked.join(' ');
        if (vres.ok) {
            logLine('✅ Validação concluída com sucesso.');
            setStatus('✅ Validação concluída (upload chunked).', 'success');
        } else {
            logLine('❌ Validação falhou: ' + (data?.error || vres.statusText));
            setStatus('❌ Erro na validação', 'error');
        }
    } catch (e) {
        setStatus('❌ Erro na validação por upload: ' + e.message, 'error');
        logLine('❌ Erro validação upload: ' + e.message);
    } finally {
        // Desbloqueia botões
        if (btnValidar) btnValidar.disabled = false;
        if (btnJar) btnJar.disabled = false;
        if (btnB2) btnB2.disabled = false;
    }
};

window.updateNavbar = function() {
    const usernameEl = document.getElementById('navbar-username');
    const logoutBtn = document.getElementById('btn-logout');
    const overlay = document.getElementById('login-overlay');
    
    if (window.state.token) {
        if (usernameEl) usernameEl.textContent = window.state.username || 'Utilizador';
        if (logoutBtn) logoutBtn.style.display = 'block';
        if (overlay) overlay.classList.add('hidden');
    } else {
        if (usernameEl) usernameEl.textContent = 'Não autenticado';
        if (logoutBtn) logoutBtn.style.display = 'none';
        if (overlay) overlay.classList.remove('hidden');
    }
};

window.logout = function() {
    try {
        localStorage.removeItem('saft_token');
        localStorage.removeItem('saft_username');
    } catch (_) {}
    window.state.token = null;
    window.state.username = null;
    updateNavbar();
    setStatus('Sessão terminada', 'info');
    logLine('Logout efetuado');
};

// Fetch tracer with improved logging
(function() {
    const orig = window.fetch;
    window.fetch = async function(input, init) {
        try {
            const url = (typeof input === 'string') ? input : (input && input.url) || '';
            const method = (init && init.method) || 'GET';
            logLine(`→ ${method} ${url}`);
        } catch (_) {}
        const res = await orig(input, init);
        try {
            logLine(`← ${res.status} ${res.statusText || ''}`.trim());
        } catch (_) {}
        return res;
    };
})();

// DOM ready
window.addEventListener('DOMContentLoaded', () => {
    // Update navbar with current token state
    updateNavbar();
    
    // Heartbeat toggle
    try {
        const hb = document.getElementById('hb');
        if (hb) {
            try { localStorage.removeItem('hb'); } catch (_) {} // cleanup old key
            const saved = localStorage.getItem('hb_enabled') === '1';
            hb.checked = !!saved;
            if (hb.checked) {
                window._hbId = window.enableHeartbeat(5000);
            }
            hb.addEventListener('change', () => {
                if (hb.checked) {
                    localStorage.setItem('hb_enabled', '1');
                    if (!window._hbId) window._hbId = window.enableHeartbeat(5000);
                    setStatus('Auto-reload ativado', 'success');
                } else {
                    localStorage.removeItem('hb_enabled');
                    if (window._hbId) {
                        clearInterval(window._hbId);
                        window._hbId = null;
                    }
                    setStatus('Auto-reload desativado', 'info');
                }
            });
        }
    } catch (_) {}

    // Auto-login dev/dev se não tiver token
    try {
        if (!state.token) {
            logLine('Sem token guardado, a efetuar auto-login dev/dev...');
            setTimeout(() => doLogin(), 500);
        } else {
            logLine('Token carregado do localStorage');
            setStatus('Bem-vindo de volta, ' + (state.username || 'Utilizador'), 'success');
        }
    } catch (_) {}
});

// Heartbeat
window.enableHeartbeat = function(intervalMs = 5000) {
    let hadError = false,
        lastVersion = '2';
    async function tick() {
        try {
            const r = await fetch('/ui/check', { cache: 'no-store' });
            if (!r.ok) throw new Error('HTTP ' + r.status);
            const j = await r.json();
            const v = (j && j.ui_version) || null;
            if (hadError || (v && v !== lastVersion)) {
                logLine('Backend reiniciado, a recarregar UI...');
                location.reload();
                return;
            }
            hadError = false;
        } catch (e) {
            hadError = true;
        }
    }
    return setInterval(tick, intervalMs);
};

// Tabs
window.showTab = function(id) {
    document.querySelectorAll('.tab').forEach(el => el.classList.remove('active'));
    document.querySelectorAll('.tabpanel').forEach(el => el.classList.remove('active'));
    const btn = document.querySelector(`[data-tab="${id}"]`);
    const panel = document.getElementById(`panel-${id}`);
    if (btn && panel) {
        btn.classList.add('active');
        panel.classList.add('active');
    }
};

// Validation actions
window.validate = async function() {
    const fI = document.getElementById('file');
    const out = document.getElementById('out');
    const btn = document.getElementById('btn');
    out.textContent = '';
    if (!fI.files.length) {
        out.textContent = '⚠️ Escolha um ficheiro XML primeiro';
        setStatus('Nenhum ficheiro selecionado', 'error');
        return;
    }
    const f = fI.files[0];
    const fd = new FormData();
    fd.append('file', f);
    btn.disabled = true;
    btn.innerHTML = '<span>⏳</span> A validar...';
    logLine('Validação básica iniciada...');
    try {
        const r = await fetch('/ui/validate', { method: 'POST', body: fd });
        const j = await r.json();
        out.textContent = JSON.stringify(j, null, 2);
        setStatus('Validação básica concluída', 'success');
        logLine('Validação básica: OK');
    } catch (e) {
        out.textContent = '❌ Erro: ' + e;
        setStatus('Erro na validação: ' + e.message, 'error');
        logLine('Erro validação básica: ' + e.message);
    } finally {
        btn.disabled = false;
        btn.innerHTML = '<span>✓</span> Validação básica';
    }
};

window.validateWithJar = async function() {
    if (!state.token) {
        setStatus('⚠️ Faça login primeiro', 'error');
        return;
    }
    const fI = document.getElementById('file');
    const out = document.getElementById('out');
    const cmdEl = document.getElementById('cmd_mask');
    
    if (!fI.files.length) {
        setStatus('⚠️ Escolha um ficheiro XML primeiro', 'error');
        return;
    }
    
    // Esconder fase 2 (envio) quando inicia nova validação
    const submitPhase = document.getElementById('submit-phase');
    if (submitPhase) submitPhase.style.display = 'none';
    
    setStatus(`🔍 A validar ficheiro via FACTEMICLI.jar...`, 'info');
    logLine('========================================');
    logLine(`� VALIDAÇÃO JAR - Operação: VALIDAR`);
    logLine('========================================');
    const f = fI.files[0];
    const fd = new FormData();
    fd.append('file', f);
    
    // Sempre usa operação 'validar' (fase 1)
    const url = `/pt/validate-jar?full=1&operation=validar`;
    
    try {
        const r = await fetch(url, {
            method: 'POST',
            headers: { 'Authorization': 'Bearer ' + state.token },
            body: fd
        });
        const txt = await r.text();
        let data = null;
        try {
            data = txt ? JSON.parse(txt) : null;
        } catch (_) {}
        out.textContent = data ? JSON.stringify(data, null, 2) : (txt || '(sem resposta)');

        // Timeout feedback
        if (data && data.timeout) {
            setStatus('⏳ Validation timed out. Aumente FACTEMICLI_TIMEOUT no servidor (ex.: 600–1200s).', 'warning');
            logLine('⏳ Timeout: aumente FACTEMICLI_TIMEOUT no backend.');
        }

        if (data && data.cmd_masked && Array.isArray(data.cmd_masked)) {
            cmdEl.textContent = data.cmd_masked.join(' ');
            logLine('📋 Comando executado:');
            logLine('   ' + data.cmd_masked.join(' '));
            logLine('');
            
            if (data.returncode !== undefined && data.returncode !== null) {
                logLine('📊 Return code: ' + data.returncode);
            }
            
            // Mostrar stdout completo
            if (data.stdout && data.stdout.trim()) {
                logLine('');
                logLine('✅ STDOUT (saída padrão):');
                logLine('----------------------------------------');
                const lines = data.stdout.split('\n');
                lines.forEach(line => {
                    if (line.trim()) logLine('   ' + line);
                });
                logLine('----------------------------------------');
            }
            
            // Mostrar stderr completo
            if (data.stderr && data.stderr.trim()) {
                logLine('');
                logLine('⚠️ STDERR (erros/avisos):');
                logLine('----------------------------------------');
                const lines = data.stderr.split('\n');
                lines.forEach(line => {
                    if (line.trim()) logLine('   ' + line);
                });
                logLine('----------------------------------------');
            }

            // Detecção de sucesso na validação
            const allOutput = ((data.stdout || '') + '\n' + (data.stderr || ''));
            const validationSuccess = /validado com sucesso|response code="200"/i.test(allOutput);
            
            // Friendly summary
            let sev = 'ok',
                msg = 'Execução concluída.';
            if (/parametro .*n[aã]o conhecido|parametros dispon[ií]veis|usage/.test(allOutput.toLowerCase())) {
                sev = 'error';
                msg = 'Execução JAR incorreta (parâmetros inválidos).';
            } else if (data.returncode !== 0) {
                sev = 'error';
                msg = 'Return code diferente de 0.';
            } else if (/(erro|error|inv[aá]lid|falh[ao])/i.test(allOutput) && !validationSuccess) {
                sev = 'warning';
                msg = 'Foram detetadas mensagens de erro/aviso no output.';
            }
            
            const human = sev === 'ok' ? '✅ OK' : (sev === 'warning' ? '⚠️ Com avisos' : '❌ Com erros');
            logLine('');
            logLine('🏁 RESUMO: ' + human + (msg ? ' – ' + msg : ''));
            
            // Se validação bem-sucedida, mostrar fase 2 (enviar)
            if (validationSuccess && data.returncode === 0) {
                logLine('');
                logLine('✨ FICHEIRO PRONTO PARA ENVIO À AT!');
                logLine('   Clique no botão "2. Enviar à Autoridade Tributária" para submeter.');
                if (submitPhase) submitPhase.style.display = 'block';
            }
            
            logLine('========================================');
            setStatus(`Validação: ` + human + (msg ? ' – ' + msg : ''), sev === 'ok' ? 'success' : sev === 'warning' ? 'warning' : 'error');
        } else {
            cmdEl.textContent = '(nenhum comando executado)';
            logLine('⚠️ Sem comando retornado pela API');
        }
    } catch (e) {
        setStatus('❌ Erro na validação JAR: ' + e.message, 'error');
        logLine('❌ ERRO: ' + e.message);
        logLine('========================================');
    }
};

// Validar ficheiro diretamente do B2 (usa state.objectKey)
window.validateFromB2 = async function() {
    if (!state.token) {
        setStatus('⚠️ Faça login primeiro', 'error');
        return;
    }
    if (!state.objectKey) {
        setStatus('⚠️ Faça upload via Presign para obter object_key', 'error');
        return;
    }
    const out = document.getElementById('out');
    const cmdEl = document.getElementById('cmd_mask');
    const submitPhase = document.getElementById('submit-phase');
    if (submitPhase) submitPhase.style.display = 'none';

    const fname = state.lastFilename || '(desconhecido)';
    const key = state.objectKey || '(sem object_key)';
    setStatus(`☁️ A validar do B2: ${fname} (${key})`, 'info');
    logLine('========================================');
    logLine(`☁️ VALIDAÇÃO DO B2 - Operação: VALIDAR → ${fname} (${key})`);
    logLine('========================================');
    try {
        const r = await fetch('/pt/validate-jar-by-key?full=1&operation=validar', {
            method: 'POST',
            headers: {
                'Authorization': 'Bearer ' + state.token,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ object_key: state.objectKey })
        });
        const txt = await r.text();
        let data = null;
        try { data = txt ? JSON.parse(txt) : null; } catch(_) {}
        out.textContent = data ? JSON.stringify(data, null, 2) : (txt || '(sem resposta)');

        if (data && data.timeout) {
            setStatus('⏳ Validation timed out. Aumente FACTEMICLI_TIMEOUT no servidor (ex.: 600–1200s).', 'warning');
            logLine('⏳ Timeout: aumente FACTEMICLI_TIMEOUT no backend.');
        }

        if (data && data.cmd_masked && Array.isArray(data.cmd_masked)) {
            cmdEl.textContent = data.cmd_masked.join(' ');
            logLine('📋 Comando executado:');
            logLine('   ' + data.cmd_masked.join(' '));

            if (data.returncode !== undefined && data.returncode !== null) {
                logLine('📊 Return code: ' + data.returncode);
            }

            const allOutput = ((data.stdout || '') + '\n' + (data.stderr || ''));
            const validationSuccess = /validado com sucesso|response code="200"/i.test(allOutput);

            let sev = 'ok', msg = 'Execução concluída.';
            if (/parametro .*n[aã]o conhecido|parametros dispon[ií]veis|usage/.test(allOutput.toLowerCase())) { sev = 'error'; msg = 'Execução JAR incorreta (parâmetros).'; }
            else if (data.returncode !== 0) { sev = 'error'; msg = 'Return code diferente de 0.'; }
            else if (/(erro|error|inv[aá]lid|falh[ao])/i.test(allOutput) && !validationSuccess) { sev = 'warning'; msg = 'Mensagens de erro/aviso no output.'; }

            const human = sev === 'ok' ? '✅ OK' : (sev === 'warning' ? '⚠️ Com avisos' : '❌ Com erros');
            logLine('');
            logLine('🏁 RESUMO: ' + human + (msg ? ' – ' + msg : ''));
            if (validationSuccess && data.returncode === 0) {
                if (submitPhase) submitPhase.style.display = 'block';
            }
            setStatus('Validação (B2): ' + human + (msg ? ' – ' + msg : ''), sev === 'ok' ? 'success' : sev === 'warning' ? 'warning' : 'error');
        } else {
            cmdEl.textContent = '(nenhum comando executado)';
            logLine('⚠️ Sem comando retornado pela API');
        }
    } catch (e) {
        setStatus('❌ Erro na validação (B2): ' + e.message, 'error');
        logLine('❌ ERRO (B2): ' + e.message);
    }
};

// Nova função: Enviar ficheiro à AT (Fase 2)
window.submitToAT = async function() {
    if (!state.token) {
        setStatus('⚠️ Faça login primeiro', 'error');
        return;
    }
    const fI = document.getElementById('file');
    const out = document.getElementById('out');
    const cmdEl = document.getElementById('cmd_mask');
    
    if (!fI.files.length) {
        setStatus('⚠️ Escolha um ficheiro XML primeiro', 'error');
        return;
    }
    
    setStatus(`📨 A enviar ficheiro à AT via FACTEMICLI.jar...`, 'info');
    logLine('========================================');
    logLine(`📨 ENVIO À AT - Operação: ENVIAR`);
    logLine('========================================');
    const f = fI.files[0];
    const fd = new FormData();
    fd.append('file', f);
    
    // Usa operação 'enviar' (fase 2)
    const url = `/pt/validate-jar?full=1&operation=enviar`;
    
    try {
        const r = await fetch(url, {
            method: 'POST',
            headers: { 'Authorization': 'Bearer ' + state.token },
            body: fd
        });
        const txt = await r.text();
        let data = null;
        try {
            data = txt ? JSON.parse(txt) : null;
        } catch (_) {}
        out.textContent = data ? JSON.stringify(data, null, 2) : (txt || '(sem resposta)');

        if (data && data.timeout) {
            setStatus('⏳ Validation timed out. Aumente FACTEMICLI_TIMEOUT no servidor (ex.: 600–1200s).', 'warning');
            logLine('⏳ Timeout: aumente FACTEMICLI_TIMEOUT no backend.');
        }

        if (data && data.cmd_masked && Array.isArray(data.cmd_masked)) {
            cmdEl.textContent = data.cmd_masked.join(' ');
            logLine('📋 Comando executado:');
            logLine('   ' + data.cmd_masked.join(' '));
            logLine('');
            
            if (data.returncode !== undefined && data.returncode !== null) {
                logLine('📊 Return code: ' + data.returncode);
            }
            
            // Mostrar stdout completo
            if (data.stdout && data.stdout.trim()) {
                logLine('');
                logLine('✅ STDOUT (saída padrão):');
                logLine('----------------------------------------');
                const lines = data.stdout.split('\n');
                lines.forEach(line => {
                    if (line.trim()) logLine('   ' + line);
                });
                logLine('----------------------------------------');
            }
            
            // Mostrar stderr completo
            if (data.stderr && data.stderr.trim()) {
                logLine('');
                logLine('⚠️ STDERR (erros/avisos):');
                logLine('----------------------------------------');
                const lines = data.stderr.split('\n');
                lines.forEach(line => {
                    if (line.trim()) logLine('   ' + line);
                });
                logLine('----------------------------------------');
            }

            // Friendly summary
            const allOutput = ((data.stdout || '') + '\n' + (data.stderr || ''));
            let sev = 'ok',
                msg = 'Envio concluído.';
            
            if (/parametro .*n[aã]o conhecido|parametros dispon[ií]veis|usage/.test(allOutput.toLowerCase())) {
                sev = 'error';
                msg = 'Execução JAR incorreta (parâmetros inválidos).';
            } else if (!data.ok && /no at password/i.test(data.error || '')) {
                sev = 'error';
                msg = 'Credenciais AT não encontradas. Guarde NIF e senha na aba Credenciais.';
            } else if (data.returncode !== 0) {
                sev = 'error';
                msg = 'Return code diferente de 0.';
            } else if (/(erro|error|inv[aá]lid|falh[ao])/i.test(allOutput)) {
                sev = 'warning';
                msg = 'Foram detetadas mensagens de erro/aviso no output.';
            }
            
            const human = sev === 'ok' ? '✅ OK' : (sev === 'warning' ? '⚠️ Com avisos' : '❌ Com erros');
            logLine('');
            logLine('🏁 RESUMO: ' + human + (msg ? ' – ' + msg : ''));
            logLine('========================================');
            setStatus(`Envio à AT: ` + human + (msg ? ' – ' + msg : ''), sev === 'ok' ? 'success' : sev === 'warning' ? 'warning' : 'error');
        } else {
            cmdEl.textContent = '(nenhum comando executado)';
            logLine('⚠️ Sem comando retornado pela API');
            if (data && data.error) {
                logLine('❌ ERRO: ' + data.error);
                setStatus('❌ ' + data.error, 'error');
            }
        }
    } catch (e) {
        setStatus('❌ Erro no envio à AT: ' + e.message, 'error');
        logLine('❌ ERRO: ' + e.message);
        logLine('========================================');
    }
};

window.previewJarCommand = async function(operation) {
    if (!state.token) {
        setStatus('⚠️ Faça login primeiro', 'error');
        return;
    }
    const fI = document.getElementById('file');
    const out = document.getElementById('out');
    const cmdEl = document.getElementById('cmd_mask');
    
    // Usa o parâmetro passado ou default 'validar'
    const op = operation || 'validar';
    
    if (!fI.files.length) {
        setStatus('⚠️ Escolha um ficheiro XML primeiro', 'error');
        return;
    }
    
    setStatus('👁️ A gerar preview do comando...', 'info');
    logLine('📋 PREVIEW DO COMANDO - Operação: ' + op.toUpperCase());
    const f = fI.files[0];
    const fd = new FormData();
    fd.append('file', f);
    
    const url = `/pt/validate-jar?full=1&operation=${encodeURIComponent(op)}&dry_run=1`;
    
    try {
        const r = await fetch(url, {
            method: 'POST',
            headers: { 'Authorization': 'Bearer ' + state.token },
            body: fd
        });
        const txt = await r.text();
        let data = null;
        try {
            data = txt ? JSON.parse(txt) : null;
        } catch (_) {}
        
        if (data && data.cmd_masked && Array.isArray(data.cmd_masked)) {
            const cmdStr = data.cmd_masked.join(' ');
            cmdEl.textContent = cmdStr;
            out.textContent = 'PREVIEW DO COMANDO:\n\n' + cmdStr + '\n\n' + JSON.stringify(data, null, 2);
            logLine('Comando que será executado:');
            logLine('   ' + cmdStr);
            setStatus('✅ Preview gerado - comando mostrado acima', 'success');
        } else {
            out.textContent = data ? JSON.stringify(data, null, 2) : (txt || '(sem resposta)');
            setStatus('⚠️ Não foi possível gerar preview', 'warning');
        }
    } catch (e) {
        setStatus('❌ Erro no preview: ' + e.message, 'error');
        logLine('Erro preview: ' + e.message);
    }
};

window.checkJavaVersion = async function() {
    const out = document.getElementById('out');
    out.textContent = '⏳ A verificar versão Java...';
    logLine('Check Java version...');
    try {
        const r = await fetch('/pt/java/version');
        const j = await r.json();
        out.textContent = JSON.stringify(j, null, 2);
        setStatus('Java version verificada', 'success');
    } catch (e) {
        out.textContent = '❌ Erro: ' + e;
        setStatus('Erro ao verificar Java', 'error');
    }
};

window.checkJarStatus = async function() {
    const out = document.getElementById('out');
    out.textContent = '⏳ A verificar status do JAR...';
    logLine('Check JAR status...');
    try {
        const r = await fetch('/pt/jar/status');
        const j = await r.json();
        out.textContent = JSON.stringify(j, null, 2);
        setStatus('JAR status verificado', 'success');
    } catch (e) {
        out.textContent = '❌ Erro: ' + e;
        setStatus('Erro ao verificar JAR', 'error');
    }
};

window.runJarCheck = async function() {
    const out = document.getElementById('out');
    out.textContent = '⏳ A executar JAR check...';
    logLine('Run JAR check...');
    try {
        const r = await fetch('/pt/jar/run-check');
        const j = await r.json();
        out.textContent = JSON.stringify(j, null, 2);
        setStatus('JAR check executado', 'success');
    } catch (e) {
        out.textContent = '❌ Erro: ' + e;
        setStatus('Erro ao executar JAR check', 'error');
    }
};

window.installJar = async function() {
    if (!state.token) {
        setStatus('⚠️ Faça login primeiro', 'error');
        return;
    }
    const key = (document.getElementById('jar_key').value || '').trim();
    if (!key) {
        setStatus('⚠️ Forneça um object_key', 'error');
        return;
    }
    setStatus('📥 A instalar JAR...', 'info');
    logLine('Instalar JAR: ' + key);
    try {
        const r = await fetch('/pt/jar/install', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': 'Bearer ' + state.token
            },
            body: JSON.stringify({ object_key: key })
        });
        const txt = await r.text();
        let data = null;
        try {
            data = txt ? JSON.parse(txt) : null;
        } catch (_) {}
        if (!r.ok) {
            const msg = (data && data.detail) ? data.detail : (txt ? txt.slice(0, 300) : 'Instalação falhou');
            throw new Error(msg);
        }
        const j = data || {};
        setStatus('✅ JAR instalado: ' + (j.path || '(desconhecido)') + ' (' + ((j.size != null ? j.size : '?')) + ' bytes)', 'success');
        const out = document.getElementById('out');
        out.textContent = data ? JSON.stringify(j, null, 2) : (txt || 'OK');
        logLine('JAR instalado com sucesso');
    } catch (e) {
        setStatus('❌ Erro ao instalar JAR: ' + e.message, 'error');
        logLine('Erro instalar JAR: ' + e.message);
    }
};

window.loginUser = async function() {
    const u = document.getElementById('login_user').value.trim();
    const p = document.getElementById('login_pass').value;
    if (!u || !p) {
        setStatus('⚠️ Preencha username e password', 'error');
        return;
    }
    setStatus('🔓 A fazer login...', 'info');
    logLine('Login: ' + u);
    try {
        const fd = new URLSearchParams();
        fd.set('username', u);
        fd.set('password', p);
        const r = await fetch('/auth/token', {
            method: 'POST',
            headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
            body: fd
        });
        const j = await r.json();
        if (!r.ok) throw new Error(j.detail || 'Login falhou');
        state.token = j.access_token;
        state.username = u;
        
        // Guardar no localStorage
        try {
            localStorage.setItem('saft_token', state.token);
            localStorage.setItem('saft_username', state.username);
        } catch (_) {}
        
        updateNavbar();
        setStatus('✅ Login efetuado: ' + u, 'success');
        logLine('Login OK: ' + u);
    } catch (e) {
        setStatus('❌ Erro no login: ' + e.message, 'error');
        logLine('Login error: ' + e.message);
    }
};

window.doLogin = async function() {
    await loginUser();
};

window.loginDev = async function() {
    try {
        document.getElementById('login_user').value = 'dev';
        document.getElementById('login_pass').value = 'dev';
        logLine('Login rápido dev/dev...');
        setStatus('🔓 Login rápido (dev/dev)...', 'info');
        await loginUser();
    } catch (e) {
        logLine('Login dev/dev error: ' + (e && e.message ? e.message : e));
        setStatus('❌ Erro login dev/dev: ' + (e && e.message ? e.message : e), 'error');
    }
};

window.onFileChange = function(ev) {
    state.file = ev.target.files[0] || null;
    if (state.file) {
        logLine('Ficheiro selecionado: ' + state.file.name + ' (' + (state.file.size / 1024).toFixed(1) + ' KB)');
        setStatus('Ficheiro carregado: ' + state.file.name, 'success');
    }
};

window.loadCredsStatus = async function() {
    if (!state.token) {
        setStatus('⚠️ Faça login primeiro', 'error');
        return;
    }
    setStatus('🔄 A carregar estado das credenciais...', 'info');
    logLine('Carregar estado credenciais...');
    try {
        const r = await fetch('/pt/secrets/at/status', {
            headers: { 'Authorization': 'Bearer ' + state.token }
        });
        const j = await r.json();
        document.getElementById('creds_user_mask').textContent = j.username_masked || '(nenhum)';
        document.getElementById('creds_updated').textContent = j.updated_at || '(desconhecido)';
        setStatus(j.ok ? '✅ Estado das credenciais carregado' : '⚠️ Sem credenciais guardadas', j.ok ? 'success' : 'warning');
        logLine('Estado credenciais: ' + (j.ok ? 'OK' : 'sem credenciais'));
    } catch (e) {
        setStatus('❌ Erro ao carregar credenciais: ' + e.message, 'error');
        logLine('Erro load creds: ' + e.message);
    }
};

// Run deep diagnostics against /diag
window.diagConnections = async function() {
    setStatus('🔎 A correr diagnóstico (/diag)...', 'info');
    logLine('Executar /diag');
    try {
        const r = await fetch('/diag');
        const txt = await r.text();
        let data = null;
        try { data = txt ? JSON.parse(txt) : null; } catch (_) {}
        const out = document.getElementById('out');
        if (out) out.textContent = data ? JSON.stringify(data, null, 2) : (txt || '(sem resposta)');
        if (r.ok && data) {
            const ok = data.ok;
            setStatus(ok ? '✅ Diagnóstico OK' : '⚠️ Diagnóstico com avisos/erros', ok ? 'success' : 'warning');
        } else {
            setStatus('⚠️ Diagnóstico retornou erro HTTP ' + r.status, 'warning');
        }
    } catch (e) {
        setStatus('❌ Erro no diagnóstico: ' + e.message, 'error');
        logLine('Diag erro: ' + e.message);
    }
};

window.saveNifEntry = async function() {
    if (!state.token) {
        setStatus('⚠️ Faça login primeiro', 'error');
        return;
    }
    const ident = (document.getElementById('nif_ident').value || '').trim();
    const pass = document.getElementById('nif_pass').value;
    if (!ident || !pass) {
        setStatus('⚠️ Preencha NIF e senha', 'error');
        return;
    }
    setStatus('💾 A guardar senha para NIF ' + ident + '...', 'info');
    logLine('Guardar NIF: ' + ident);
    try {
        const r = await fetch('/pt/secrets/at/entries', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': 'Bearer ' + state.token
            },
            body: JSON.stringify({ ident, password: pass })
        });
        const j = await r.json();
        if (!r.ok) throw new Error(j.detail || 'Falha ao guardar');
        setStatus('✅ Senha guardada para NIF ' + ident, 'success');
        logLine('NIF guardado: ' + ident);
        // Clear inputs
        document.getElementById('nif_ident').value = '';
        document.getElementById('nif_pass').value = '';
        await loadNifEntries();
    } catch (e) {
        setStatus('❌ Erro ao guardar NIF: ' + e.message, 'error');
        logLine('Erro guardar NIF: ' + e.message);
    }
};

window.loadNifEntries = async function() {
    if (!state.token) {
        setStatus('⚠️ Faça login primeiro', 'error');
        return;
    }
    setStatus('📋 A carregar NIFs...', 'info');
    logLine('Listar NIFs...');
    try {
        const r = await fetch('/pt/secrets/at/entries', {
            headers: { 'Authorization': 'Bearer ' + state.token }
        });
        const j = await r.json();
        if (!r.ok) throw new Error(j.detail || 'Falha ao listar');
        const out = document.getElementById('nif_list');
        if (j.items && j.items.length > 0) {
            out.textContent = JSON.stringify(j.items, null, 2);
            setStatus('✅ ' + j.items.length + ' NIF(s) carregado(s)', 'success');
            logLine('NIFs carregados: ' + j.items.length);
        } else {
            out.textContent = '(nenhum NIF guardado)';
            setStatus('⚠️ Nenhum NIF guardado', 'warning');
            logLine('Nenhum NIF guardado');
        }
    } catch (e) {
        setStatus('❌ Erro ao listar NIFs: ' + e.message, 'error');
        logLine('Erro listar NIFs: ' + e.message);
    }
};

window.presignDownload = async function() {
    if (!state.token) {
        setStatus('⚠️ Faça login primeiro', 'error');
        return;
    }
    const key = (document.getElementById('dl_key').value || '').trim();
    if (!key) {
        setStatus('⚠️ Forneça um object_key', 'error');
        return;
    }
    setStatus('🔗 A gerar URL de download...', 'info');
    logLine('Presign download: ' + key);
    try {
        const r = await fetch('/pt/files/presign-download', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': 'Bearer ' + state.token
            },
            body: JSON.stringify({ object_key: key })
        });
        const j = await r.json();
        if (!r.ok) throw new Error(j.detail || 'Falha ao gerar URL');
        document.getElementById('dl_url').textContent = j.url || '(sem URL)';
        const out = document.getElementById('out');
        out.textContent = JSON.stringify(j, null, 2);
        setStatus('✅ URL de download gerado', 'success');
        logLine('URL gerado');
    } catch (e) {
        setStatus('❌ Erro ao gerar URL: ' + e.message, 'error');
        logLine('Erro presign download: ' + e.message);
    }
};

// ============================================
// VALIDATION HISTORY FUNCTIONS
// ============================================

// History state
window.historyState = {
    currentPage: 0,
    limit: 20,
    filters: { nif: '', year: '', month: '' }
};

window.loadHistory = async function(skip = 0) {
    if (!state.token) {
        showHistoryError('⚠️ Faça login primeiro');
        return;
    }
    
    const loading = document.getElementById('history-loading');
    const empty = document.getElementById('history-empty');
    const results = document.getElementById('history-results');
    const error = document.getElementById('history-error');
    
    // Show loading state
    loading.style.display = 'block';
    empty.style.display = 'none';
    results.style.display = 'none';
    error.style.display = 'none';
    
    try {
        // Build query params
        const params = new URLSearchParams({
            limit: historyState.limit.toString(),
            skip: skip.toString()
        });
        
        if (historyState.filters.nif) params.append('nif', historyState.filters.nif);
        if (historyState.filters.year) params.append('year', historyState.filters.year);
        if (historyState.filters.month) params.append('month', historyState.filters.month);
        
        const response = await fetch(`/pt/validation-history?${params}`, {
            headers: { 'Authorization': 'Bearer ' + state.token }
        });
        
        if (!response.ok) {
            throw new Error('Erro ao carregar histórico');
        }
        
        const data = await response.json();
        
        loading.style.display = 'none';
        
        if (!data.records || data.records.length === 0) {
            empty.style.display = 'block';
            return;
        }
        
        // Populate table
        renderHistoryTable(data.records);
        updateHistoryPagination(data);
        
        results.style.display = 'block';
        
    } catch (err) {
        loading.style.display = 'none';
        showHistoryError('❌ Erro ao carregar histórico: ' + err.message);
    }
};

window.renderHistoryTable = function(records) {
    const tbody = document.getElementById('history-table-body');
    tbody.innerHTML = '';
    
    records.forEach(record => {
        const row = document.createElement('tr');
        row.style.borderBottom = '1px solid var(--border)';
        
        // Format date
        const date = new Date(record.validated_at);
        const dateStr = date.toLocaleString('pt-PT', {
            day: '2-digit',
            month: '2-digit',
            year: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        });
        
        // Get statistics
        const stats = record.statistics || {};
        const faturas = stats.total_faturas || 0;
        const creditos = stats.total_creditos || 0;
        const debitos = stats.total_debitos || 0;
        
        // Operation badge
        const opBadge = record.operation === 'enviar' 
            ? '<span style="background:#28a745; color:white; padding:2px 8px; border-radius:4px; font-size:0.75rem;">📨 Enviar</span>'
            : '<span style="background:#007bff; color:white; padding:2px 8px; border-radius:4px; font-size:0.75rem;">🔍 Validar</span>';
        
        // Success indicator
        const successIcon = record.success ? '✅' : '⚠️';
        
        row.innerHTML = `
            <td style="padding: 0.75rem;">${successIcon} ${dateStr}</td>
            <td style="padding: 0.75rem; font-family: monospace;">${record.nif}</td>
            <td style="padding: 0.75rem; text-align: center;">${record.year}/${record.month}</td>
            <td style="padding: 0.75rem;">${opBadge}</td>
            <td style="padding: 0.75rem; text-align: right;">${faturas.toLocaleString('pt-PT')}</td>
            <td style="padding: 0.75rem; text-align: right;">${creditos.toLocaleString('pt-PT', {minimumFractionDigits: 2})}</td>
            <td style="padding: 0.75rem; text-align: right;">${debitos.toLocaleString('pt-PT', {minimumFractionDigits: 2})}</td>
            <td style="padding: 0.75rem; text-align: center;">
                ${record.storage_key ? `<button class="btn btn-secondary btn-sm" onclick="downloadArchive('${record.storage_key}', '${record.file_info?.name || 'arquivo.xml'}')">📥 Download ZIP</button>` : '<span style="color: var(--text-secondary);">-</span>'}
            </td>
        `;
        
        tbody.appendChild(row);
    });
};

window.updateHistoryPagination = function(data) {
    const info = document.getElementById('history-info');
    const prevBtn = document.getElementById('history-prev');
    const nextBtn = document.getElementById('history-next');
    
    const start = data.skip + 1;
    const end = data.skip + data.records.length;
    const total = data.total;
    
    info.textContent = `Mostrar ${start}-${end} de ${total} registos`;
    
    // Update buttons
    prevBtn.disabled = data.skip === 0;
    nextBtn.disabled = !data.has_more;
    
    historyState.currentPage = Math.floor(data.skip / historyState.limit);
};

window.historyPrevPage = function() {
    const skip = Math.max(0, historyState.currentPage * historyState.limit - historyState.limit);
    loadHistory(skip);
};

window.historyNextPage = function() {
    const skip = (historyState.currentPage + 1) * historyState.limit;
    loadHistory(skip);
};

window.filterHistory = function() {
    const nifInput = document.getElementById('history-filter-nif');
    const yearInput = document.getElementById('history-filter-year');
    const monthInput = document.getElementById('history-filter-month');
    
    historyState.filters.nif = nifInput ? nifInput.value.trim() : '';
    historyState.filters.year = yearInput ? yearInput.value.trim() : '';
    historyState.filters.month = monthInput ? monthInput.value.trim() : '';
    historyState.currentPage = 0;
    
    loadHistory(0);
};

window.downloadArchive = async function(storageKey, originalName) {
    if (!state.token) {
        alert('⚠️ Faça login primeiro');
        return;
    }
    
    try {
        // Generate presigned download URL
        const response = await fetch('/pt/files/presign-download', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': 'Bearer ' + state.token
            },
            body: JSON.stringify({ object_key: storageKey })
        });
        
        if (!response.ok) {
            throw new Error('Erro ao gerar URL de download');
        }
        
        const data = await response.json();
        
        if (data.url) {
            // Open download in new window/tab
            window.open(data.url, '_blank');
            logLine(`✅ Download iniciado: ${originalName}`);
        } else {
            throw new Error('URL não disponível');
        }
        
    } catch (err) {
        alert('❌ Erro ao fazer download: ' + err.message);
        logLine(`❌ Erro download: ${err.message}`);
    }
};

window.showHistoryError = function(message) {
    const error = document.getElementById('history-error');
    const loading = document.getElementById('history-loading');
    const empty = document.getElementById('history-empty');
    const results = document.getElementById('history-results');
    
    loading.style.display = 'none';
    empty.style.display = 'none';
    results.style.display = 'none';
    error.style.display = 'block';
    error.textContent = message;
};

// Auto-load history when switching to history tab
document.addEventListener('DOMContentLoaded', function() {
    const historyTab = document.querySelector('[data-tab="history"]');
    if (historyTab) {
        historyTab.addEventListener('click', function() {
            // Small delay to ensure tab is visible
            setTimeout(() => loadHistory(0), 100);
        });
    }
});

