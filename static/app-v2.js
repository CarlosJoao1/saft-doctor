// SAFT Doctor - UI Logic v2 (UX Professional)
// Global state
window.state = { token: null, objectKey: null, file: null };

// Utilities
window.setStatus = function(msg, type = 'info') {
    const s = document.getElementById('status');
    if (!s) return;
    s.textContent = msg;
    // Optional: add color based on type
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

window.clearLog = function() {
    const el = document.getElementById('log');
    if (el) el.textContent = '(log vazio)';
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

    // Auto-login dev/dev if no token
    try {
        if (!state.token) {
            logLine('Auto-login dev/dev...');
            setTimeout(() => loginDev(), 500);
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
    setStatus('🚀 A validar via FACTEMICLI.jar...', 'info');
    logLine('Validação JAR iniciada...');
    const f = fI.files[0];
    const fd = new FormData();
    fd.append('file', f);
    try {
        const r = await fetch('/pt/validate-jar?full=1', {
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

        if (data && data.cmd_masked && Array.isArray(data.cmd_masked)) {
            cmdEl.textContent = data.cmd_masked.join(' ');
            logLine('Comando: ' + data.cmd_masked.join(' '));
            if (data.returncode !== undefined && data.returncode !== null) {
                logLine('Return code: ' + data.returncode);
            }
            if (data.stdout) {
                const preview = (data.stdout.length > 400 ? data.stdout.slice(0, 400) + '…' : data.stdout);
                if (preview.trim()) logLine('Stdout: ' + preview.split('\n').join(' | '));
            }
            if (data.stderr) {
                const preview = (data.stderr.length > 400 ? data.stderr.slice(0, 400) + '…' : data.stderr);
                if (preview.trim()) logLine('Stderr: ' + preview.split('\n').join(' | '));
            }

            // Friendly summary
            const all = ((data.stdout || '') + '\n' + (data.stderr || '')).toLowerCase();
            let sev = 'ok',
                msg = 'Validação concluída.';
            if (/parametro .*n[aã]o conhecido|parametros dispon[ií]veis|usage/.test(all)) {
                sev = 'error';
                msg = 'Execução JAR incorreta (parâmetros).';
            } else if (data.returncode !== 0) {
                sev = 'error';
                msg = 'Return code diferente de 0.';
            } else if (/(erro|error|inv[aá]lid|falh[ao])/i.test(all)) {
                sev = 'warning';
                msg = 'Foram detetadas mensagens de erro/aviso no output.';
            }
            const human = sev === 'ok' ? '✅ OK' : (sev === 'warning' ? '⚠️ Com avisos' : '❌ Com erros');
            setStatus('Validação JAR: ' + human + (msg ? ' – ' + msg : ''), sev === 'ok' ? 'success' : sev === 'warning' ? 'warning' : 'error');
            logLine('Resumo: ' + human + (msg ? ' – ' + msg : ''));
        } else {
            cmdEl.textContent = '(nenhum comando executado)';
            logLine('Sem comando retornado pela API');
        }
    } catch (e) {
        setStatus('❌ Erro na validação JAR: ' + e.message, 'error');
        logLine('Erro validação JAR: ' + e.message);
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
    const u = document.getElementById('l_user').value.trim();
    const p = document.getElementById('l_pass').value;
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
        setStatus('✅ Login efetuado com sucesso', 'success');
        const badge = document.getElementById('token_status');
        if (badge) {
            badge.textContent = 'Autenticado ✓';
            badge.className = 'badge badge-success';
        }
        logLine('Login OK');
    } catch (e) {
        setStatus('❌ Erro no login: ' + e.message, 'error');
        logLine('Login error: ' + e.message);
    }
};

window.loginDev = async function() {
    try {
        document.getElementById('l_user').value = 'dev';
        document.getElementById('l_pass').value = 'dev';
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
