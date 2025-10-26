// SAFT Doctor - UI Logic v2 (UX Professional)
// Global state
window.state = { token: null, objectKey: null, file: null, username: null };

// Load token from localStorage on startup
try {
    const saved = localStorage.getItem('saft_token');
    const savedUser = localStorage.getItem('saft_username');
    const savedRole = localStorage.getItem('saft_role');
    console.log('[DEBUG] Startup: Loading token from localStorage');
    console.log('[DEBUG] Startup: Token found?', !!saved);
    console.log('[DEBUG] Startup: Token length:', saved?.length);
    console.log('[DEBUG] Startup: Token preview:', saved?.substring(0, 50));
    console.log('[DEBUG] Startup: Username:', savedUser);
    console.log('[DEBUG] Startup: Role:', savedRole);

    if (saved) {
        window.state.token = saved;
        window.state.username = savedUser || 'Utilizador';
        window.state.role = savedRole || 'user';
        console.log('[DEBUG] Startup: Token loaded into state');
    } else {
        console.log('[DEBUG] Startup: NO TOKEN in localStorage, user needs to login');
    }
} catch (err) {
    console.error('[DEBUG] Startup: Error loading from localStorage:', err);
}

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
    console.log('[DEBUG] validateSmart: state.token exists?', !!state.token);
    console.log('[DEBUG] validateSmart: state.token (first 50 chars):', state.token?.substring(0, 50));

    if (!state.token) {
        console.error('[DEBUG] validateSmart: NO TOKEN! User needs to login');
        setStatus('⚠️ Faça login primeiro', 'error');
        return;
    }

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

        console.log('[DEBUG] validateSmart: Sending upload/start request with token');

        // start
        const startRes = await fetch('/pt/upload/start', {
            method: 'POST', headers: { 'Content-Type': 'application/json', 'Authorization': 'Bearer ' + state.token },
            body: JSON.stringify({ filename: f.name, size: f.size })
        });

        console.log('[DEBUG] validateSmart: upload/start response status:', startRes.status);

        if (!startRes.ok) {
            const errText = await startRes.text();
            console.error('[DEBUG] validateSmart: upload/start FAILED:', errText);
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
        // Store last upload id for fixes
        window.state.lastUploadId = uploadId;

        // DEBUG: Log validation response
        console.log('================================================================================');
        console.log('[DEBUG] validateSmart: Validation response received');
        console.log('  data.ok:', data?.ok);
        console.log('  data.returncode:', data?.returncode);
        console.log('  data.issues:', data?.issues);
        console.log('  data.issues length:', data?.issues?.length);
        console.log('  Full data:', data);
        console.log('================================================================================');

        try {
            if (data && Array.isArray(data.issues) && data.issues.length > 0) {
                console.log('[DEBUG] validateSmart: Showing popup with', data.issues.length, 'issues');
                window.showIssuesPopup(data.issues);
            } else {
                console.log('[DEBUG] validateSmart: No issues to show (ok=' + data?.ok + ')');
            }
        } catch(err) {
            console.error('[DEBUG] validateSmart: Error showing popup:', err);
        }
        // Append detailed JAR results to execution log
        try {
            if (data) {
                if (Array.isArray(data.cmd_masked)) {
                    logLine('cmd: ' + data.cmd_masked.join(' '));
                }
                if (typeof data.returncode !== 'undefined') {
                    logLine('returncode: ' + data.returncode);
                }
                const logPreview = (label, content) => {
                    if (!content) return;
                    const lines = String(content).split(/\r?\n/);
                    const maxLines = 200; // avoid flooding log
                    const slice = lines.slice(0, maxLines);
                    for (const ln of slice) logLine(label + ': ' + ln);
                    if (lines.length > maxLines) logLine(label + ': ... [truncated]');
                };
                if (data.stdout) logPreview('stdout', data.stdout);
                if (data.stderr) logPreview('stderr', data.stderr);
            } else if (txt) {
                logLine('raw: ' + (txt.length > 2000 ? (txt.slice(0,2000)+'... [truncated]') : txt));
            }
        } catch(_) {}
        if (data && data.ok) {
            logLine('✅ Validação concluída com sucesso.');
            setStatus('✅ Validação concluída (upload chunked).', 'success');

            // Log B2 storage info if available
            if (data.save_error) {
                logLine('⚠️ AVISO: Erro ao guardar no histórico');
                logLine(`   Erro: ${data.save_error}`);
                console.error('[SAVE] Error saving to B2/history:', data.save_error);
            } else if (data.storage_key) {
                logLine('💾 Ficheiro guardado no histórico');
                logLine(`   Storage key: ${data.storage_key}`);
                if (data.validation_id) {
                    logLine(`   Validation ID: ${data.validation_id}`);
                }
            } else {
                logLine('⚠️ AVISO: Ficheiro NÃO foi guardado no histórico (sem storage_key)');
                console.warn('[SAVE] No storage_key in response - file was not saved');
            }

            // Mostrar botão de enviar
            const submitPhase = document.getElementById('submit-phase');
            if (submitPhase) {
                submitPhase.style.display = 'block';
                logLine('');
                logLine('✨ FICHEIRO PRONTO PARA ENVIO À AT!');
                logLine('   Clique no botão "2. Enviar à Autoridade Tributária" para submeter.');
                logLine('   Ou vá ao separador "📜 Histórico" para ver validações anteriores.');
            }
        } else {
            logLine('❌ Validação falhou: ' + (data?.error || vres.statusText));
            setStatus('❌ Erro na validação', 'error');

            // Esconder botão de enviar
            const submitPhase = document.getElementById('submit-phase');
            if (submitPhase) submitPhase.style.display = 'none';
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

// Popup to show structured issues and suggestions
window.showIssuesPopup = function(issues) {
    console.log('================================================================================');
    console.log('[DEBUG] *** showIssuesPopup CALLED ***');
    console.log('[DEBUG] Number of issues:', issues?.length);
    console.log('[DEBUG] Issues array:', issues);

    // Log details of each issue
    if (issues && issues.length > 0) {
        issues.forEach((issue, idx) => {
            console.log(`[DEBUG] Issue ${idx}:`, {
                code: issue.code,
                message: issue.message?.substring(0, 100),
                hasSuggestion: !!issue.suggestion,
                hasSuggestions: !!issue.suggestions,
                suggestionsCount: issue.suggestions?.length || 0,
                location: issue.location
            });
        });
    }
    console.log('================================================================================');

    // Create overlay
    const overlay = document.createElement('div');
    overlay.style.position = 'fixed';
    overlay.style.inset = '0';
    overlay.style.background = 'rgba(0,0,0,0.5)';
    overlay.style.zIndex = '9999';
    // Modal
    const modal = document.createElement('div');
    modal.style.position = 'absolute';
    modal.style.top = '50%';
    modal.style.left = '50%';
    modal.style.transform = 'translate(-50%, -50%)';
    modal.style.background = '#fff';
    modal.style.color = '#111';
    modal.style.borderRadius = '8px';
    modal.style.maxWidth = '900px';
    modal.style.width = '90%';
    modal.style.maxHeight = '80%';
    modal.style.overflow = 'auto';
    modal.style.boxShadow = '0 10px 30px rgba(0,0,0,0.3)';
    modal.style.padding = '16px';

    const title = document.createElement('div');
    title.innerHTML = '<h2 style="margin:0 0 8px 0;">Erros detetados</h2><div style="color:#555;margin-bottom:8px;">Sugestões automáticas quando possível</div>';
    modal.appendChild(title);

    const list = document.createElement('div');
    issues.forEach((it, idx) => {
        const card = document.createElement('div');
        card.style.border = '1px solid #e5e7eb';
        card.style.borderRadius = '6px';
        card.style.padding = '10px';
        card.style.marginBottom = '8px';
        const code = (it.code || 'JAR_ERROR');
        const msg = (it.message || '').toString();
        const loc = it.location || {};
        const cid = it.customer_id || '';
        const suggestion = it.suggestion || null;
        const suggestions = it.suggestions || null; // Array of multiple suggestions
        const line = (loc.line != null ? `L${loc.line}` : '(linha desconhecida)');
        const ctx = loc.context ? `<pre style="white-space:pre-wrap;background:#f8fafc;border-radius:6px;padding:8px;">${loc.context}</pre>` : '';

        // Handle single suggestion (backwards compatible)
        let sugHtml = suggestion ? `<div style="margin-top:6px;"><b>Sugestão:</b> substituir por <code>${suggestion}</code>${cid?` no cliente <code>${cid}</code>`:''}</div>` : '';

        // JAR_ERROR with no suggestion - show "Create Rule" button
        if (code === 'JAR_ERROR' && !suggestion && !suggestions) {
            sugHtml = `<div style="margin-top:8px;"><button class="btn btn-sm" onclick="window.showCreateRuleModal(${idx}, '${encodeURIComponent(msg)}')">📝 Criar regra para este erro</button></div>`;
        }

        // Handle multiple suggestions
        if (suggestions && Array.isArray(suggestions) && suggestions.length > 0) {
            sugHtml = '<div style="margin-top:8px;"><b>Opções de correção:</b></div>';
            sugHtml += '<div style="margin-top:4px;">';
            suggestions.forEach((sug, sidx) => {
                const radioId = `sug-${idx}-${sidx}`;
                const checked = sidx === 0 ? 'checked' : ''; // Select first option by default
                sugHtml += `
                    <div style="margin:4px 0;">
                        <label style="display:flex;align-items:start;cursor:pointer;">
                            <input type="radio" name="suggestion-${idx}" id="${radioId}" value="${sidx}" ${checked} style="margin-top:4px;margin-right:8px;">
                            <div>
                                <div style="font-weight:500;">${sug.label}</div>
                                <div style="font-size:0.9em;color:#666;">Reason: ${sug.reason}</div>
                                <div style="font-size:0.9em;color:#666;">Code: <code>${sug.code}</code></div>
                            </div>
                        </label>
                    </div>
                `;
            });
            sugHtml += '</div>';
            // Store selected suggestion index in card dataset
            card.dataset.selectedSuggestionIndex = '0';
            card.querySelectorAll = () => card.getElementsByTagName('*');
            setTimeout(() => {
                const radios = card.querySelectorAll(`input[name="suggestion-${idx}"]`);
                for (let radio of radios) {
                    radio.addEventListener('change', (e) => {
                        card.dataset.selectedSuggestionIndex = e.target.value;
                    });
                }
            }, 100);
        }

        card.innerHTML = `
            <div style="font-weight:600;">${idx+1}. ${code}</div>
            <div style="color:#222;margin-top:4px;">${msg}</div>
            <div style="color:#666;margin-top:4px;">${line}</div>
            ${ctx}
            ${sugHtml}
        `;

        // Re-attach event listeners after innerHTML (since innerHTML destroys them)
        if (suggestions && Array.isArray(suggestions) && suggestions.length > 0) {
            card.dataset.selectedSuggestionIndex = '0';
            setTimeout(() => {
                const radios = card.querySelectorAll(`input[name="suggestion-${idx}"]`);
                for (let radio of radios) {
                    radio.addEventListener('change', (e) => {
                        card.dataset.selectedSuggestionIndex = e.target.value;
                    });
                }
            }, 50);
        }

        list.appendChild(card);
    });
    modal.appendChild(list);

    const actions = document.createElement('div');
    actions.style.display = 'flex';
    actions.style.justifyContent = 'flex-end';
    actions.style.gap = '8px';
    actions.style.marginTop = '8px';

    const applyBtn = document.createElement('button');
    applyBtn.className = 'btn';
    applyBtn.textContent = 'Aplicar sugestões e revalidar';
    applyBtn.onclick = async () => {
        console.log('[DEBUG] ========================================');
        console.log('[DEBUG] Apply button clicked!');
        console.log('[DEBUG] ========================================');
        try {
            const uploadId = (window.state && window.state.lastUploadId) || null;
            console.log('[DEBUG] uploadId:', uploadId);
            if (!uploadId) { alert('Sem upload_id disponível'); return; }

            // Prepare fixes: handle both single suggestion and multiple suggestions
            const fixes = [];
            const cards = list.querySelectorAll('div[style*="border"]');
            console.log('[DEBUG] Found', cards.length, 'cards');
            console.log('[DEBUG] Processing', issues.length, 'issues');

            issues.forEach((it, idx) => {
                console.log(`[DEBUG] Issue ${idx}:`, it.code, 'has suggestion?', !!it.suggestion, 'has suggestions?', !!it.suggestions);

                if (it.suggestion) {
                    // Single suggestion (backwards compatible)
                    fixes.push(it);
                    console.log(`[DEBUG] Added single suggestion fix for issue ${idx}`);
                } else if (it.suggestions && Array.isArray(it.suggestions) && it.suggestions.length > 0) {
                    // Multiple suggestions - get selected option
                    const card = cards[idx];
                    const selectedIdx = parseInt(card?.dataset?.selectedSuggestionIndex || '0');
                    const selectedSug = it.suggestions[selectedIdx];
                    console.log(`[DEBUG] Issue ${idx}: selected index=${selectedIdx}, suggestion:`, selectedSug);
                    // Create fix object with selected suggestion
                    fixes.push({
                        ...it,
                        selected_suggestion: selectedSug
                    });
                    console.log(`[DEBUG] Added multi-suggestion fix for issue ${idx}`);
                } else {
                    console.log(`[DEBUG] Issue ${idx}: No fixable suggestions`);
                }
            });

            console.log('[DEBUG] Total fixes prepared:', fixes.length);
            if (fixes.length === 0) {
                console.log('[DEBUG] No fixes to apply, showing alert');
                alert('Sem sugestões automáticas a aplicar');
                return;
            }

            console.log('[DEBUG] About to send fixes to backend...');
            setStatus('🔧 A aplicar sugestões...', 'info');
            logLine(`[APPLY] A aplicar ${fixes.length} sugestões...`);
            const r = await fetch('/pt/upload/apply-fixes-and-validate', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': 'Bearer ' + (window.state && window.state.token ? window.state.token : '')
                },
                body: JSON.stringify({ upload_id: uploadId, fixes })
            });
            const txt = await r.text();
            console.log('[DEBUG] apply-fixes response status:', r.status);
            console.log('[DEBUG] apply-fixes response text length:', txt.length);

            let data = null;
            try {
                data = txt ? JSON.parse(txt) : null;
                console.log('[DEBUG] apply-fixes parsed data:', data);
            } catch(parseErr) {
                console.error('[DEBUG] Error parsing response:', parseErr);
                console.error('[DEBUG] Response text:', txt);
            }

            const out = document.getElementById('out');
            if (out) out.textContent = data ? JSON.stringify(data, null, 2) : (txt || '(sem resposta)');

            console.log('[DEBUG] About to close overlay...');
            // IMPORTANT: Close current popup FIRST, then show new one
            try {
                if (overlay && overlay.parentNode) {
                    document.body.removeChild(overlay);
                    console.log('[DEBUG] Overlay removed successfully');
                }
            } catch (removeErr) {
                console.error('[DEBUG] Error removing overlay:', removeErr);
            }

            console.log('[DEBUG] Checking response: data.issues?', data?.issues?.length, 'data.ok?', data?.ok);
            // Check response and show appropriate feedback
            if (data && Array.isArray(data.issues) && data.issues.length > 0) {
                // Show new issues in NEW popup
                console.log('[DEBUG] Showing new popup with', data.issues.length, 'issues');
                setStatus(`🔧 ${data.applied || 0} correções aplicadas. ${data.issues.length} erros restantes.`, 'info');
                logLine(`🔧 ${data.applied || 0} correções aplicadas. ${data.issues.length} erros restantes.`);
                window.showIssuesPopup(data.issues);
            } else if (data && data.ok) {
                console.log('[DEBUG] No more errors! File is ready.');
                setStatus('✅ Sem erros após correções! Ficheiro pronto.', 'success');
                logLine('✅ Sem erros após correções! Ficheiro pronto para enviar.');
                // Show submit button
                const submitPhase = document.getElementById('submit-phase');
                if (submitPhase) submitPhase.style.display = 'block';
            } else {
                console.log('[DEBUG] Unexpected response state');
                console.log('[DEBUG] data:', data);
                setStatus('⚠️ Verifique resultado após correções', 'warning');
                logLine('⚠️ Resposta inesperada após correções. Verifique o output.');
            }
        } catch (e) {
            console.error('[DEBUG] Error applying fixes:', e);
            alert('Erro a aplicar sugestões: ' + e.message);
            // Try to close popup on error
            try {
                if (overlay && overlay.parentNode) {
                    document.body.removeChild(overlay);
                }
            } catch(_) {}
        }
    };
    actions.appendChild(applyBtn);

    // "Apply All Automatically" button - loops until no more fixable errors
    const applyAllBtn = document.createElement('button');
    applyAllBtn.className = 'btn btn-warning';
    applyAllBtn.textContent = '🔁 Aplicar TUDO Automaticamente';
    applyAllBtn.title = 'Aplica todas as correções repetidamente até não haver mais erros';
    applyAllBtn.onclick = async () => {
        console.log('[DEBUG] Auto-fix button clicked!');
        const uploadId = (window.state && window.state.lastUploadId) || null;
        if (!uploadId) {
            alert('Sem upload_id disponível');
            return;
        }

        // Close current popup
        console.log('[DEBUG] Closing issues popup...');
        document.body.removeChild(overlay);

        // Create custom confirmation modal instead of using browser confirm()
        console.log('[DEBUG] Creating confirmation modal...');
        const confirmOverlay = document.createElement('div');
        confirmOverlay.style.position = 'fixed';
        confirmOverlay.style.inset = '0';
        confirmOverlay.style.background = 'rgba(0,0,0,0.6)';
        confirmOverlay.style.zIndex = '10000';
        confirmOverlay.style.display = 'flex';
        confirmOverlay.style.alignItems = 'center';
        confirmOverlay.style.justifyContent = 'center';

        const confirmModal = document.createElement('div');
        confirmModal.style.background = '#fff';
        confirmModal.style.color = '#111';
        confirmModal.style.borderRadius = '8px';
        confirmModal.style.padding = '24px';
        confirmModal.style.maxWidth = '500px';
        confirmModal.style.boxShadow = '0 10px 30px rgba(0,0,0,0.3)';

        confirmModal.innerHTML = `
            <h3 style="margin:0 0 16px 0;">🔁 Auto-Fix Automático</h3>
            <p style="margin:0 0 16px 0;">Após corrigir todos os erros automaticamente, deseja <strong>ENVIAR</strong> o ficheiro para a AT?</p>
            <div style="display:flex;gap:8px;justify-content:flex-end;">
                <button id="confirm-no" class="btn btn-secondary">Não - Apenas Corrigir</button>
                <button id="confirm-yes" class="btn" style="background:#28a745;border-color:#28a745;">Sim - Corrigir + Enviar</button>
            </div>
        `;

        confirmOverlay.appendChild(confirmModal);
        document.body.appendChild(confirmOverlay);

        console.log('[DEBUG] Confirmation modal added to DOM');

        // Handle button clicks
        document.getElementById('confirm-yes').onclick = () => {
            console.log('[DEBUG] User selected: YES (fix + submit)');
            document.body.removeChild(confirmOverlay);
            window.autoFixLoop(uploadId, 20, true);
        };

        document.getElementById('confirm-no').onclick = () => {
            console.log('[DEBUG] User selected: NO (fix only)');
            document.body.removeChild(confirmOverlay);
            window.autoFixLoop(uploadId, 20, false);
        };
    };
    actions.appendChild(applyAllBtn);

    const closeBtn = document.createElement('button');
    closeBtn.className = 'btn';
    closeBtn.textContent = 'Fechar';
    closeBtn.onclick = () => document.body.removeChild(overlay);
    actions.appendChild(closeBtn);
    modal.appendChild(actions);

    overlay.appendChild(modal);
    overlay.addEventListener('click', (e) => { if (e.target === overlay) document.body.removeChild(overlay); });
    document.body.appendChild(overlay);

    console.log('[DEBUG] showIssuesPopup: Popup added to DOM, z-index=9999');
};

window.updateNavbar = function() {
    const usernameEl = document.getElementById('navbar-username');
    const logoutBtn = document.getElementById('btn-logout');
    const profileBtn = document.getElementById('btn-profile');
    const adminTab = document.getElementById('admin-tab');
    const overlay = document.getElementById('login-overlay');

    if (window.state.token) {
        if (usernameEl) usernameEl.textContent = window.state.username || 'Utilizador';
        if (logoutBtn) logoutBtn.style.display = 'block';
        if (profileBtn) profileBtn.style.display = 'block';
        if (overlay) overlay.classList.add('hidden');

        // Show Admin tab only for sysadmin
        if (adminTab) {
            adminTab.style.display = (window.state.role === 'sysadmin') ? 'inline-block' : 'none';
            console.log('[DEBUG] updateNavbar: Admin tab visible:', window.state.role === 'sysadmin');
        }
    } else {
        if (usernameEl) usernameEl.textContent = 'Não autenticado';
        if (logoutBtn) logoutBtn.style.display = 'none';
        if (profileBtn) profileBtn.style.display = 'none';
        if (adminTab) adminTab.style.display = 'none';
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
window.submitToAT = async function(uploadId) {
    if (!state.token) {
        setStatus('⚠️ Faça login primeiro', 'error');
        return;
    }
    const fI = document.getElementById('file');
    const out = document.getElementById('out');
    const cmdEl = document.getElementById('cmd_mask');

    // Check if we have an upload_id (from chunked upload) or need to use direct file upload
    const useUploadId = uploadId || (window.state && window.state.lastUploadId);

    setStatus(`📨 A enviar ficheiro à AT via FACTEMICLI.jar...`, 'info');
    logLine('========================================');
    logLine(`📨 ENVIO À AT - Operação: ENVIAR`);
    logLine('========================================');

    let url, fetchOptions;

    if (useUploadId) {
        // Use chunked upload endpoint
        logLine(`[SUBMIT] Usando upload_id: ${useUploadId}`);
        url = `/pt/validate-jar-by-upload?upload_id=${useUploadId}&operation=enviar&full=1`;
        fetchOptions = {
            method: 'POST',
            headers: { 'Authorization': 'Bearer ' + state.token }
        };
    } else {
        // Fallback to direct file upload
        if (!fI.files.length) {
            setStatus('⚠️ Escolha um ficheiro XML primeiro', 'error');
            return;
        }
        logLine(`[SUBMIT] Usando upload direto do ficheiro`);
        const f = fI.files[0];
        const fd = new FormData();
        fd.append('file', f);
        url = `/pt/validate-jar?full=1&operation=enviar`;
        fetchOptions = {
            method: 'POST',
            headers: { 'Authorization': 'Bearer ' + state.token },
            body: fd
        };
    }

    try {
        const r = await fetch(url, fetchOptions);
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

        console.log('[DEBUG] loginUser: Token received, length:', state.token?.length);
        console.log('[DEBUG] loginUser: Token preview:', state.token?.substring(0, 50));

        // Guardar no localStorage
        try {
            localStorage.setItem('saft_token', state.token);
            localStorage.setItem('saft_username', state.username);
            console.log('[DEBUG] loginUser: Token saved to localStorage');
        } catch (err) {
            console.error('[DEBUG] loginUser: Failed to save to localStorage:', err);
        }

        // Fetch user role
        try {
            const meResponse = await fetch('/auth/me', {
                headers: { 'Authorization': 'Bearer ' + state.token }
            });
            if (meResponse.ok) {
                const meData = await meResponse.json();
                state.role = meData.role || 'user';
                localStorage.setItem('saft_role', state.role);
                console.log('[DEBUG] loginUser: User role:', state.role);
            }
        } catch (err) {
            console.error('[DEBUG] loginUser: Failed to fetch role:', err);
            state.role = 'user'; // Default to user
        }

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

// Switch between login, register, and password-reset tabs
window.showAuthTab = function(tab) {
    const loginForm = document.getElementById('login-form');
    const registerForm = document.getElementById('register-form');
    const passwordResetForm = document.getElementById('password-reset-form');
    const loginTabBtn = document.getElementById('login-tab-btn');
    const registerTabBtn = document.getElementById('register-tab-btn');

    // Hide all forms
    loginForm.style.display = 'none';
    registerForm.style.display = 'none';
    passwordResetForm.style.display = 'none';

    if (tab === 'login') {
        loginForm.style.display = 'block';
        loginTabBtn.style.background = '';
        registerTabBtn.style.background = 'var(--text-secondary)';
    } else if (tab === 'register') {
        registerForm.style.display = 'block';
        loginTabBtn.style.background = 'var(--text-secondary)';
        registerTabBtn.style.background = '';
    } else if (tab === 'password-reset') {
        passwordResetForm.style.display = 'block';
        loginTabBtn.style.background = 'var(--text-secondary)';
        registerTabBtn.style.background = 'var(--text-secondary)';
    }
};

// Register new user
window.doRegister = async function() {
    const username = document.getElementById('register_user').value.trim();
    const email = document.getElementById('register_email').value.trim();
    const password = document.getElementById('register_pass').value;
    const passwordConfirm = document.getElementById('register_pass_confirm').value;

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

    setStatus('✍️ A registar utilizador...', 'info');
    logLine('Registar utilizador: ' + username);

    try {
        const payload = { username: username, password: password };
        if (email) {
            payload.email = email;
        }

        const response = await fetch('/auth/register', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.detail || 'Erro ao registar');
        }

        setStatus('✅ Conta criada com sucesso!', 'success');
        logLine('✅ Utilizador registado: ' + username + (email ? ' (email: ' + email + ')' : ''));

        // Clear form
        document.getElementById('register_user').value = '';
        document.getElementById('register_email').value = '';
        document.getElementById('register_pass').value = '';
        document.getElementById('register_pass_confirm').value = '';

        // Switch to login tab
        showAuthTab('login');

        // Fill login form with new credentials
        document.getElementById('login_user').value = username;
        document.getElementById('login_pass').value = password;

        alert('✅ Conta criada com sucesso!\n\nAgora pode fazer login.');

    } catch (e) {
        setStatus('❌ Erro ao registar: ' + e.message, 'error');
        logLine('❌ Erro ao registar: ' + e.message);
        alert('❌ Erro ao registar:\n\n' + e.message);
    }
};

// Password Reset Functions

// Request password reset
window.requestPasswordReset = async function() {
    const username = document.getElementById('reset_username').value.trim();

    if (!username) {
        alert('⚠️ Preencha o username');
        return;
    }

    setStatus('📧 A enviar email de recuperação...', 'info');
    logLine('Password reset solicitado para: ' + username);

    try {
        const response = await fetch('/auth/password-reset/request', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username: username })
        });

        const data = await response.json();

        if (data.ok) {
            setStatus('✅ ' + data.message, 'success');
            logLine('✅ ' + data.message);
            alert('✅ ' + data.message);

            // Clear form and go back to login
            document.getElementById('reset_username').value = '';
            showAuthTab('login');
        } else {
            setStatus('❌ ' + data.message, 'error');
            logLine('❌ ' + data.message);
            alert('❌ ' + data.message);
        }

    } catch (e) {
        setStatus('❌ Erro ao solicitar reset: ' + e.message, 'error');
        logLine('❌ Erro: ' + e.message);
        alert('❌ Erro ao solicitar reset:\n\n' + e.message);
    }
};

// Confirm password reset (when URL has reset_token)
window.confirmPasswordReset = async function() {
    const newPassword = document.getElementById('new_password').value;
    const newPasswordConfirm = document.getElementById('new_password_confirm').value;

    if (!newPassword) {
        alert('⚠️ Preencha a nova password');
        return;
    }

    if (newPassword.length < 3) {
        alert('⚠️ Password deve ter pelo menos 3 caracteres');
        return;
    }

    if (newPassword !== newPasswordConfirm) {
        alert('⚠️ As passwords não coincidem');
        return;
    }

    // Get token from URL
    const urlParams = new URLSearchParams(window.location.search);
    const resetToken = urlParams.get('reset_token');

    if (!resetToken) {
        alert('❌ Token de reset não encontrado no URL');
        return;
    }

    setStatus('🔐 A alterar password...', 'info');
    logLine('A confirmar reset de password...');

    try {
        const response = await fetch('/auth/password-reset/confirm', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                token: resetToken,
                new_password: newPassword
            })
        });

        const data = await response.json();

        if (data.ok) {
            setStatus('✅ ' + data.message, 'success');
            logLine('✅ ' + data.message);

            // Clear form
            document.getElementById('new_password').value = '';
            document.getElementById('new_password_confirm').value = '';

            alert('✅ ' + data.message);

            // Remove token from URL and reload
            window.location.href = window.location.pathname;

        } else {
            setStatus('❌ ' + data.message, 'error');
            logLine('❌ ' + data.message);
            alert('❌ ' + data.message);
        }

    } catch (e) {
        setStatus('❌ Erro ao alterar password: ' + e.message, 'error');
        logLine('❌ Erro: ' + e.message);
        alert('❌ Erro ao alterar password:\n\n' + e.message);
    }
};

// Check if URL has reset_token on page load
window.addEventListener('DOMContentLoaded', function() {
    const urlParams = new URLSearchParams(window.location.search);
    const resetToken = urlParams.get('reset_token');

    if (resetToken) {
        console.log('[PASSWORD-RESET] Reset token detected in URL');
        logLine('🔐 Link de recuperação de password detectado');

        // Validate token first
        fetch('/auth/check-reset-token?token=' + encodeURIComponent(resetToken))
            .then(response => response.json())
            .then(data => {
                if (data.valid) {
                    console.log('[PASSWORD-RESET] Token is valid for user:', data.username);
                    logLine('✅ Link válido. Username: ' + data.username);

                    // Hide all auth forms
                    document.getElementById('login-form').style.display = 'none';
                    document.getElementById('register-form').style.display = 'none';
                    document.getElementById('password-reset-form').style.display = 'none';

                    // Show new password form
                    document.getElementById('new-password-form').style.display = 'block';

                    // Show login overlay
                    document.getElementById('login-overlay').style.display = 'flex';

                    setStatus('🔐 Crie uma nova password', 'info');
                } else {
                    console.log('[PASSWORD-RESET] Token is invalid:', data.reason);
                    logLine('❌ Link inválido: ' + data.reason);
                    alert('❌ Link de recuperação inválido ou expirado.\n\nSolicite um novo link.');

                    // Remove token from URL
                    window.location.href = window.location.pathname;
                }
            })
            .catch(error => {
                console.error('[PASSWORD-RESET] Error validating token:', error);
                logLine('❌ Erro ao validar link de recuperação');
                alert('❌ Erro ao validar link de recuperação');
            });
    }
});

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

// ============================================================================
// HELP WIDGET FUNCTIONS
// ============================================================================

/**
 * Toggle help widget panel visibility
 */
window.toggleHelpWidget = function() {
    const panel = document.getElementById('help-widget-panel');
    if (panel) {
        panel.classList.toggle('open');

        // Clear search when closing
        if (!panel.classList.contains('open')) {
            const searchInput = document.getElementById('help-search');
            if (searchInput) {
                searchInput.value = '';
                filterHelpItems();
            }
        }
    }
};

/**
 * Toggle individual help item (expand/collapse)
 */
window.toggleHelpItem = function(element) {
    element.classList.toggle('expanded');
};

/**
 * Filter help items based on search input
 */
window.filterHelpItems = function() {
    const searchInput = document.getElementById('help-search');
    const searchTerm = searchInput ? searchInput.value.toLowerCase() : '';
    const helpItems = document.querySelectorAll('.help-item');
    const helpSections = document.querySelectorAll('.help-section');

    if (!searchTerm) {
        // Show all items and sections
        helpItems.forEach(item => {
            item.style.display = 'block';
            item.classList.remove('expanded');
        });
        helpSections.forEach(section => {
            section.style.display = 'block';
        });
        return;
    }

    // Track which sections have visible items
    const sectionsWithResults = new Set();

    helpItems.forEach(item => {
        const question = item.querySelector('.help-item-question');
        const answer = item.querySelector('.help-item-answer');

        if (!question || !answer) return;

        const questionText = question.textContent.toLowerCase();
        const answerText = answer.textContent.toLowerCase();

        if (questionText.includes(searchTerm) || answerText.includes(searchTerm)) {
            item.style.display = 'block';
            item.classList.add('expanded'); // Auto-expand matching items

            // Mark parent section as having results
            const parentSection = item.closest('.help-section');
            if (parentSection) {
                sectionsWithResults.add(parentSection);
            }
        } else {
            item.style.display = 'none';
            item.classList.remove('expanded');
        }
    });

    // Show/hide sections based on whether they have visible items
    helpSections.forEach(section => {
        if (sectionsWithResults.has(section)) {
            section.style.display = 'block';
        } else {
            section.style.display = 'none';
        }
    });
};

// ============================================================================
// USER PROFILE FUNCTIONS
// ============================================================================

/**
 * Show profile modal and load current user data
 */
window.showProfileModal = async function() {
    const overlay = document.getElementById('profile-overlay');
    if (!overlay) {
        console.error('[PROFILE] Overlay element not found');
        return;
    }

    // Check if user is logged in
    if (!window.state || !window.state.token) {
        console.error('[PROFILE] No token found in state');
        alert('❌ Sessão expirada. Por favor, faça login novamente.');
        logout();
        return;
    }

    console.log('[PROFILE] Opening modal, token length:', window.state.token.length);

    // Show modal
    overlay.style.display = 'flex';

    // Load profile data
    try {
        const response = await fetch('/auth/profile', {
            method: 'GET',
            headers: {
                'Authorization': 'Bearer ' + window.state.token
            }
        });

        console.log('[PROFILE] Response status:', response.status);

        if (!response.ok) {
            const errorData = await response.json().catch(() => ({}));
            const errorMsg = errorData.detail || errorData.message || `HTTP ${response.status}`;
            console.error('[PROFILE] Request failed:', errorMsg);
            throw new Error(errorMsg);
        }

        const data = await response.json();
        console.log('[PROFILE] Profile data received:', { username: data.username, hasEmail: !!data.email });

        // Fill form
        document.getElementById('profile-username').value = data.username || '';
        document.getElementById('profile-email').value = data.email || '';

        logLine('📋 Perfil carregado: ' + data.username);
    } catch (e) {
        console.error('[PROFILE] Error loading profile:', e);
        alert('❌ Erro ao carregar perfil:\n\n' + e.message);
        // Close modal on error
        overlay.style.display = 'none';
    }
};

/**
 * Close profile modal
 */
window.closeProfileModal = function() {
    const overlay = document.getElementById('profile-overlay');
    if (overlay) {
        overlay.style.display = 'none';
    }
};

/**
 * Update user email
 */
window.updateProfileEmail = async function() {
    const email = document.getElementById('profile-email').value.trim();

    // Validate email
    if (email && !email.includes('@')) {
        alert('⚠️ Email inválido. Deve conter @');
        return;
    }

    setStatus('💾 A guardar email...', 'info');
    logLine('Atualizando email: ' + email);

    try {
        const response = await fetch('/auth/profile/email?email=' + encodeURIComponent(email), {
            method: 'POST',
            headers: {
                'Authorization': 'Bearer ' + state.token
            }
        });

        const data = await response.json();

        if (response.ok && data.ok) {
            setStatus('✅ ' + data.message, 'success');
            alert('✅ ' + data.message);
            logLine('✅ Email atualizado com sucesso');
            closeProfileModal();
        } else {
            const errorMsg = data.detail || data.message || 'Erro desconhecido';
            setStatus('❌ ' + errorMsg, 'error');
            alert('❌ ' + errorMsg);
            logLine('❌ Erro ao atualizar email: ' + errorMsg);
        }
    } catch (e) {
        setStatus('❌ Erro ao atualizar email: ' + e.message, 'error');
        alert('❌ Erro ao atualizar email:\n\n' + e.message);
        logLine('❌ Erro: ' + e.message);
    }
};

// ============================================================================
// SMTP CONFIGURATION FUNCTIONS (Sysadmin only)
// ============================================================================

window.loadSmtpConfig = async function() {
    if (!state.token) {
        alert('❌ Faça login primeiro');
        return;
    }

    setStatus('🔄 A carregar configuração SMTP...', 'info');

    try {
        const response = await fetch('/admin/smtp/config', {
            headers: { 'Authorization': 'Bearer ' + state.token }
        });

        if (!response.ok) {
            const errorData = await response.json().catch(() => ({}));
            throw new Error(errorData.detail || 'Erro ao carregar configuração');
        }

        const config = await response.json();

        document.getElementById('smtp-host').value = config.smtp_host || '';
        document.getElementById('smtp-port').value = config.smtp_port || 587;
        document.getElementById('smtp-user').value = config.smtp_user || '';
        document.getElementById('smtp-password').value = config.smtp_password === '***' ? '' : config.smtp_password;
        document.getElementById('smtp-from-email').value = config.from_email || '';
        document.getElementById('smtp-from-name').value = config.from_name || '';
        document.getElementById('smtp-app-url').value = config.app_url || '';

        document.getElementById('smtp-source-text').textContent = config.source === 'database' ? 'Base de Dados' : 'Variáveis de Ambiente';
        document.getElementById('smtp-config-source').style.display = 'block';

        setStatus('✅ Configuração SMTP carregada', 'success');
        logLine('SMTP config loaded from: ' + config.source);
    } catch (e) {
        setStatus('❌ ' + e.message, 'error');
        alert('❌ ' + e.message);
    }
};

window.saveSmtpConfig = async function() {
    if (!state.token) {
        alert('❌ Faça login primeiro');
        return;
    }

    const smtpHost = document.getElementById('smtp-host').value.trim();
    const smtpPort = parseInt(document.getElementById('smtp-port').value);
    const smtpUser = document.getElementById('smtp-user').value.trim();
    const smtpPassword = document.getElementById('smtp-password').value;
    const fromEmail = document.getElementById('smtp-from-email').value.trim();
    const fromName = document.getElementById('smtp-from-name').value.trim();
    const appUrl = document.getElementById('smtp-app-url').value.trim();

    if (!smtpHost || !smtpUser || !smtpPassword || !fromEmail || !appUrl) {
        alert('⚠️ Preencha todos os campos obrigatórios (incluindo URL da Aplicação)');
        return;
    }

    if (!appUrl.startsWith('http://') && !appUrl.startsWith('https://')) {
        alert('⚠️ URL da Aplicação deve começar com http:// ou https://');
        return;
    }

    setStatus('💾 A guardar configuração SMTP...', 'info');

    try {
        const params = new URLSearchParams({
            smtp_host: smtpHost,
            smtp_port: smtpPort,
            smtp_user: smtpUser,
            smtp_password: smtpPassword,
            from_email: fromEmail,
            from_name: fromName,
            app_url: appUrl
        });

        const response = await fetch('/admin/smtp/config?' + params.toString(), {
            method: 'POST',
            headers: { 'Authorization': 'Bearer ' + state.token }
        });

        const data = await response.json();

        if (response.ok && data.ok) {
            setStatus('✅ ' + data.message, 'success');
            alert('✅ ' + data.message);
            logLine('✅ SMTP config saved');
            loadSmtpConfig(); // Reload to show updated source
        } else {
            throw new Error(data.detail || data.message || 'Erro desconhecido');
        }
    } catch (e) {
        setStatus('❌ ' + e.message, 'error');
        alert('❌ Erro ao guardar: ' + e.message);
    }
};

window.deleteSmtpConfig = async function() {
    if (!confirm('⚠️ Eliminar configuração SMTP da base de dados?\n\nO sistema voltará a usar variáveis de ambiente.')) {
        return;
    }

    setStatus('🗑️ A eliminar configuração SMTP...', 'info');

    try {
        const response = await fetch('/admin/smtp/config', {
            method: 'DELETE',
            headers: { 'Authorization': 'Bearer ' + state.token }
        });

        const data = await response.json();

        if (response.ok && data.ok) {
            setStatus('✅ ' + data.message, 'success');
            alert('✅ ' + data.message);
            logLine('SMTP config deleted, reverted to env vars');
            loadSmtpConfig(); // Reload to show env var config
        } else {
            throw new Error(data.detail || data.message || 'Erro desconhecido');
        }
    } catch (e) {
        setStatus('❌ ' + e.message, 'error');
        alert('❌ Erro ao eliminar: ' + e.message);
    }
};

window.testSmtpConfig = async function() {
    if (!state.token) {
        alert('❌ Faça login primeiro');
        return;
    }

    const testEmail = document.getElementById('smtp-test-email').value.trim();

    if (!testEmail || !testEmail.includes('@')) {
        alert('⚠️ Preencha um email válido para teste');
        return;
    }

    setStatus('📧 A enviar email de teste...', 'info');
    logLine('Sending test email to: ' + testEmail);

    try {
        const params = new URLSearchParams({ test_email: testEmail });

        const response = await fetch('/admin/smtp/test?' + params.toString(), {
            method: 'POST',
            headers: { 'Authorization': 'Bearer ' + state.token }
        });

        const data = await response.json();

        if (response.ok && data.ok) {
            setStatus(data.message, 'success');
            alert(data.message);
            logLine('✅ Test email sent successfully');
        } else {
            setStatus(data.message, 'error');
            alert(data.message);
            logLine('❌ Test email failed: ' + data.message);
        }
    } catch (e) {
        setStatus('❌ Erro ao enviar email de teste: ' + e.message, 'error');
        alert('❌ Erro ao enviar email de teste:\n\n' + e.message);
        logLine('❌ Error: ' + e.message);
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

window.loadNifEntriesTable = async function() {
    if (!state.token) {
        alert('Faça login primeiro');
        return;
    }

    const loading = document.getElementById('creds-loading');
    const empty = document.getElementById('creds-empty');
    const results = document.getElementById('creds-results');

    loading.style.display = 'block';
    empty.style.display = 'none';
    results.style.display = 'none';

    try {
        const response = await fetch('/pt/secrets/at/entries-full', {
            headers: { 'Authorization': 'Bearer ' + state.token }
        });

        if (!response.ok) {
            throw new Error('Erro ao carregar credenciais');
        }

        const data = await response.json();
        loading.style.display = 'none';

        if (!data.items || data.items.length === 0) {
            empty.style.display = 'block';
            return;
        }

        renderCredsTable(data.items);
        results.style.display = 'block';

    } catch (err) {
        loading.style.display = 'none';
        alert('❌ Erro ao carregar credenciais: ' + err.message);
    }
};

window.renderCredsTable = function(items) {
    const tbody = document.getElementById('creds-table-body');
    tbody.innerHTML = '';

    items.forEach(item => {
        const row = document.createElement('tr');
        row.style.borderBottom = '1px solid var(--border)';

        const updatedDate = item.updated_at ? new Date(item.updated_at).toLocaleString('pt-PT', {
            day: '2-digit',
            month: '2-digit',
            year: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        }) : '-';

        row.innerHTML = `
            <td style="padding: 0.75rem; font-family: monospace;">${item.ident}</td>
            <td style="padding: 0.75rem;">
                <input type="password" value="${item.password}" readonly
                       style="width: 100%; padding: 0.25rem; border: 1px solid var(--border); border-radius: 4px;"
                       id="pass-${item.ident}">
            </td>
            <td style="padding: 0.75rem;">${updatedDate}</td>
            <td style="padding: 0.75rem; text-align: center;">
                <div style="display: flex; gap: 4px; justify-content: center;">
                    <button class="btn btn-secondary btn-sm" onclick="togglePasswordVisibility('${item.ident}')">👁️ Ver</button>
                    <button class="btn btn-sm" style="background:#ffc107;border-color:#ffc107;color:#000;" onclick="editCredential('${item.ident}')">✏️ Editar</button>
                    <button class="btn btn-sm" style="background:#dc3545;border-color:#dc3545;color:white;" onclick="deleteCredential('${item.ident}')">🗑️ Eliminar</button>
                </div>
            </td>
        `;

        tbody.appendChild(row);
    });
};

window.togglePasswordVisibility = function(nif) {
    const input = document.getElementById(`pass-${nif}`);
    if (input.type === 'password') {
        input.type = 'text';
    } else {
        input.type = 'password';
    }
};

window.editCredential = function(nif) {
    const input = document.getElementById(`pass-${nif}`);
    const newPassword = prompt('Nova password AT para NIF ' + nif + ':', input.value);

    if (newPassword && newPassword.trim()) {
        document.getElementById('nif_ident').value = nif;
        document.getElementById('nif_pass').value = newPassword.trim();
        saveNifEntry();
    }
};

window.deleteCredential = async function(nif) {
    if (!confirm(`Tem a certeza que deseja eliminar as credenciais do NIF ${nif}?`)) {
        return;
    }

    try {
        const response = await fetch('/pt/secrets/at/entry/' + encodeURIComponent(nif), {
            method: 'DELETE',
            headers: { 'Authorization': 'Bearer ' + state.token }
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.detail || 'Erro ao eliminar');
        }

        logLine(`✅ Credencial eliminada: NIF ${nif}`);
        loadNifEntriesTable();

    } catch (err) {
        alert('❌ Erro ao eliminar credencial: ' + err.message);
    }
};

window.deleteHistoryRecord = async function(recordId) {
    if (!confirm('Tem a certeza que deseja eliminar este registo do histórico?\n\nIsto irá eliminar:\n- O registo da base de dados\n- O ficheiro ZIP do Backblaze B2')) {
        return;
    }

    try {
        const response = await fetch('/pt/validation-history/' + recordId, {
            method: 'DELETE',
            headers: { 'Authorization': 'Bearer ' + state.token }
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.detail || 'Erro ao eliminar');
        }

        // Check if B2 deletion was successful
        if (data.b2_deleted) {
            logLine(`✅ Registo eliminado do histórico (incluindo ficheiro B2)`);
        } else if (data.b2_warning) {
            logLine(`⚠️ Registo eliminado mas aviso B2: ${data.b2_warning}`);
            alert(`⚠️ Aviso:\n${data.b2_warning}`);
        } else {
            logLine(`✅ Registo eliminado do histórico (sem ficheiro B2 associado)`);
        }

        loadHistory(0);

    } catch (err) {
        alert('❌ Erro ao eliminar registo: ' + err.message);
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

        console.log('[HISTORY] Response data:', data);
        logLine(`[HISTORY] Recebidos ${data.records?.length || 0} registos (total: ${data.total || 0})`);

        loading.style.display = 'none';

        if (!data.records || data.records.length === 0) {
            logLine('[HISTORY] Nenhum registo encontrado');
            empty.style.display = 'block';
            return;
        }

        // Populate table
        logLine(`[HISTORY] A renderizar tabela com ${data.records.length} registos`);
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

    // Store records globally for export
    allHistoryRecords = records;

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
                ${record.storage_key ? `
                    <div style="display: flex; gap: 4px; justify-content: center; flex-wrap: wrap;">
                        <button class="btn btn-secondary btn-sm" onclick="downloadArchive('${record.storage_key}', '${record.file_info?.name || 'arquivo.xml'}')">📥 Download ZIP</button>
                        <button class="btn btn-info btn-sm" onclick="analyzeHistoryDocs('${record.storage_key}')">📊 Análise Dados</button>
                        <button class="btn btn-sm" style="background:#dc3545;border-color:#dc3545;color:white;" onclick="deleteHistoryRecord('${record._id}')">🗑️ Eliminar</button>
                    </div>
                ` : `<button class="btn btn-sm" style="background:#dc3545;border-color:#dc3545;color:white;" onclick="deleteHistoryRecord('${record._id}')">🗑️ Eliminar</button>`}
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

window.analyzeHistoryDocs = async function(storageKey) {
    if (!state.token) {
        alert('⚠️ Faça login primeiro');
        return;
    }

    try {
        // Switch to docs tab
        showTab('docs');

        // Show loading
        document.getElementById('docs-loading').style.display = 'block';
        document.getElementById('docs-table-body').innerHTML = '';
        document.getElementById('docs-stats').style.display = 'none';

        setStatus('📄 A carregar documentos do histórico...', 'info');
        logLine(`[DOCS-HISTORY] A carregar documentos do storage_key: ${storageKey}`);

        // Fetch documents from storage
        const res = await fetch('/pt/history/extract-documents', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': 'Bearer ' + state.token
            },
            body: JSON.stringify({ storage_key: storageKey })
        });

        const data = await res.json();

        if (data.ok && data.documents) {
            allDocs = data.documents;
            logLine(`[DOCS-HISTORY] Encontrados ${allDocs.length} documentos`);
            setStatus(`✅ ${allDocs.length} documentos carregados do histórico`, 'success');

            // Show stats
            updateDocsStats();

            // Render table
            renderDocsTable(allDocs);
        } else {
            logLine('[DOCS-HISTORY] ❌ Erro: ' + (data.error || 'Erro desconhecido'));
            setStatus('❌ Erro ao carregar documentos', 'error');
            document.getElementById('docs-table-body').innerHTML = `
                <tr><td colspan="10" style="padding:2rem; text-align:center; color:#ef4444;">
                    ❌ Erro: ${data.error || data.detail || 'Erro desconhecido'}
                </td></tr>
            `;
        }
    } catch (e) {
        logLine('[DOCS-HISTORY] ❌ Exceção: ' + e.message);
        setStatus('❌ Erro ao carregar documentos', 'error');
        document.getElementById('docs-table-body').innerHTML = `
            <tr><td colspan="10" style="padding:2rem; text-align:center; color:#ef4444;">
                ❌ Erro: ${e.message}
            </td></tr>
        `;
    } finally {
        document.getElementById('docs-loading').style.display = 'none';
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

window.exportHistoryToExcel = function() {
    // Use stored records data instead of parsing HTML
    if (!allHistoryRecords || allHistoryRecords.length === 0) {
        alert('Nenhum registo de histórico para exportar.\n\nCarregue o histórico primeiro.');
        return;
    }

    // Create HTML table for Excel
    let html = '<html xmlns:o="urn:schemas-microsoft-com:office:office" xmlns:x="urn:schemas-microsoft-com:office:excel" xmlns="http://www.w3.org/TR/REC-html40">';
    html += '<head><!--[if gte mso 9]><xml><x:ExcelWorkbook><x:ExcelWorksheets><x:ExcelWorksheet>';
    html += '<x:Name>Histórico Validações</x:Name>';
    html += '<x:WorksheetOptions><x:DisplayGridlines/></x:WorksheetOptions></x:ExcelWorksheet>';
    html += '</x:ExcelWorksheets></x:ExcelWorkbook></xml><![endif]-->';
    html += '<meta http-equiv="content-type" content="text/plain; charset=UTF-8"/>';
    html += '</head><body>';
    html += '<table border="1">';

    // Header
    html += '<thead><tr style="background-color: #f1f5f9; font-weight: bold;">';
    html += '<th>Data/Hora</th>';
    html += '<th>NIF</th>';
    html += '<th>Ano</th>';
    html += '<th>Mês</th>';
    html += '<th>Operação</th>';
    html += '<th>Sucesso</th>';
    html += '<th>Faturas</th>';
    html += '<th>Créditos (€)</th>';
    html += '<th>Débitos (€)</th>';
    html += '<th>Ficheiro</th>';
    html += '</tr></thead>';

    // Body - use actual data from records
    html += '<tbody>';
    allHistoryRecords.forEach(record => {
        html += '<tr>';

        // Data/Hora
        const date = new Date(record.validated_at);
        const dateStr = date.toLocaleString('pt-PT', {
            day: '2-digit',
            month: '2-digit',
            year: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        });
        html += '<td>' + dateStr + '</td>';

        // NIF
        html += '<td>' + (record.nif || '') + '</td>';

        // Ano
        html += '<td>' + (record.year || '') + '</td>';

        // Mês
        html += '<td>' + (record.month || '') + '</td>';

        // Operação
        html += '<td>' + (record.operation || '') + '</td>';

        // Sucesso
        html += '<td>' + (record.success ? 'Sim' : 'Não') + '</td>';

        // Statistics
        const stats = record.statistics || {};
        const faturas = stats.total_faturas || 0;
        const creditos = stats.total_creditos || 0;
        const debitos = stats.total_debitos || 0;

        // Faturas
        html += '<td>' + faturas + '</td>';

        // Créditos (€)
        html += '<td style="mso-number-format:\\"0\\.00\\"">' + creditos.toFixed(2) + '</td>';

        // Débitos (€)
        html += '<td style="mso-number-format:\\"0\\.00\\"">' + debitos.toFixed(2) + '</td>';

        // Ficheiro (nome do ficheiro original)
        const filename = record.file_info?.name || record.storage_key || '';
        html += '<td>' + filename + '</td>';

        html += '</tr>';
    });
    html += '</tbody></table></body></html>';

    // Create blob and download
    const blob = new Blob(['\ufeff', html], {
        type: 'application/vnd.ms-excel'
    });

    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'historico_validacoes_' + new Date().toISOString().slice(0,10) + '.xls';
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    window.URL.revokeObjectURL(url);

    logLine('[HISTORY] Exportado para Excel: ' + allHistoryRecords.length + ' registos');
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

// ==================== Create Custom Fix Rule Modal ====================
window.showCreateRuleModal = function(errorIndex, encodedMessage) {
    const errorMessage = decodeURIComponent(encodedMessage);

    // Create overlay
    const overlay = document.createElement('div');
    overlay.style.position = 'fixed';
    overlay.style.inset = '0';
    overlay.style.background = 'rgba(0,0,0,0.5)';
    overlay.style.zIndex = '10000';

    // Modal
    const modal = document.createElement('div');
    modal.style.position = 'absolute';
    modal.style.top = '50%';
    modal.style.left = '50%';
    modal.style.transform = 'translate(-50%, -50%)';
    modal.style.background = '#fff';
    modal.style.color = '#111';
    modal.style.borderRadius = '8px';
    modal.style.maxWidth = '800px';
    modal.style.width = '90%';
    modal.style.maxHeight = '80%';
    modal.style.overflow = 'auto';
    modal.style.boxShadow = '0 10px 30px rgba(0,0,0,0.3)';
    modal.style.padding = '20px';

    modal.innerHTML = `
        <h2 style="margin:0 0 16px 0;">Criar Regra Personalizada</h2>

        <div style="margin-bottom:12px;">
            <label style="display:block;font-weight:500;margin-bottom:4px;">ID da Regra:</label>
            <input type="text" id="rule-id" placeholder="ex: my_custom_rule" style="width:100%;padding:8px;border:1px solid #ddd;border-radius:4px;">
        </div>

        <div style="margin-bottom:12px;">
            <label style="display:block;font-weight:500;margin-bottom:4px;">Nome:</label>
            <input type="text" id="rule-name" placeholder="ex: Corrigir erro XYZ" style="width:100%;padding:8px;border:1px solid #ddd;border-radius:4px;">
        </div>

        <div style="margin-bottom:12px;">
            <label style="display:block;font-weight:500;margin-bottom:4px;">Código do Erro:</label>
            <input type="text" id="rule-code" placeholder="ex: MY_ERROR" style="width:100%;padding:8px;border:1px solid #ddd;border-radius:4px;">
        </div>

        <div style="margin-bottom:12px;">
            <label style="display:block;font-weight:500;margin-bottom:4px;">Mensagem de Erro Original:</label>
            <textarea id="rule-error-msg" readonly style="width:100%;padding:8px;border:1px solid #ddd;border-radius:4px;background:#f5f5f5;font-family:monospace;font-size:12px;height:80px;">${errorMessage}</textarea>
        </div>

        <div style="margin-bottom:12px;">
            <label style="display:block;font-weight:500;margin-bottom:4px;">Padrão Regex (use named groups como (?P<line>\\d+)):</label>
            <input type="text" id="rule-pattern" placeholder="ex: Linha:\\s*(?P<line>\\d+).*?MeuErro" style="width:100%;padding:8px;border:1px solid #ddd;border-radius:4px;font-family:monospace;font-size:12px;">
            <small style="color:#666;">Dica: Use (?P<line>\\d+) para capturar número da linha, (?P<val>...) para valores</small>
        </div>

        <div style="margin-bottom:16px;">
            <label style="display:block;font-weight:500;margin-bottom:8px;">Sugestões de Correção:</label>
            <div id="suggestions-container">
                <div style="display:flex;gap:8px;margin-bottom:8px;">
                    <input type="text" class="sug-label" placeholder="Label (ex: M16 - Artigo 14º)" style="flex:2;padding:6px;border:1px solid #ddd;border-radius:4px;">
                    <input type="text" class="sug-reason" placeholder="Reason" style="flex:2;padding:6px;border:1px solid #ddd;border-radius:4px;">
                    <input type="text" class="sug-code" placeholder="Code (ex: M16)" style="flex:1;padding:6px;border:1px solid #ddd;border-radius:4px;">
                </div>
            </div>
            <button class="btn btn-sm" onclick="window.addSuggestionRow()">+ Adicionar Sugestão</button>
        </div>

        <div style="display:flex;justify-content:flex-end;gap:8px;margin-top:16px;">
            <button class="btn btn-secondary" onclick="document.body.removeChild(this.closest('[style*=\\'position: fixed\\']'))">Cancelar</button>
            <button class="btn" onclick="window.saveCustomRule()">💾 Guardar Regra</button>
        </div>
    `;

    overlay.appendChild(modal);
    document.body.appendChild(overlay);
};

window.addSuggestionRow = function() {
    const container = document.getElementById('suggestions-container');
    const row = document.createElement('div');
    row.style.display = 'flex';
    row.style.gap = '8px';
    row.style.marginBottom = '8px';
    row.innerHTML = `
        <input type="text" class="sug-label" placeholder="Label" style="flex:2;padding:6px;border:1px solid #ddd;border-radius:4px;">
        <input type="text" class="sug-reason" placeholder="Reason" style="flex:2;padding:6px;border:1px solid #ddd;border-radius:4px;">
        <input type="text" class="sug-code" placeholder="Code" style="flex:1;padding:6px;border:1px solid #ddd;border-radius:4px;">
        <button class="btn btn-sm" onclick="this.parentElement.remove()">✖</button>
    `;
    container.appendChild(row);
};

// ==================== Check Documents ====================
let allDocs = []; // Store all documents globally for filtering
let allHistoryRecords = []; // Store history records globally for export

window.checkDocs = async function() {
    let uploadId = (window.state && window.state.lastUploadId) || null;

    // If no upload ID, check if file is selected and upload it first
    if (!uploadId) {
        const fileInput = document.getElementById('file');
        const file = fileInput && fileInput.files && fileInput.files[0];

        if (!file) {
            alert('Por favor, selecione um ficheiro SAFT primeiro');
            return;
        }

        // File is selected but not uploaded - perform automatic upload
        logLine('[DOCS] Ficheiro seleccionado mas não carregado. A fazer upload automático...');
        setStatus('📤 A fazer upload do ficheiro...', 'info');

        try {
            // Perform chunked upload (same as validateSmart)
            const startRes = await fetch('/pt/upload/start', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': 'Bearer ' + (window.state && window.state.token ? window.state.token : '')
                },
                body: JSON.stringify({ filename: file.name, size: file.size })
            });

            if (!startRes.ok) {
                const errText = await startRes.text();
                throw new Error(`Falha no upload/start (${startRes.status}): ${errText}`);
            }

            const start = await startRes.json();
            if (!start.upload_id) throw new Error('Sem upload_id na resposta');

            uploadId = start.upload_id;
            const chunkSize = start.chunk_size || (5 * 1024 * 1024);
            logLine(`[DOCS] Upload iniciado: id=${uploadId}, chunk=${Math.round(chunkSize/1024)}KB`);

            let sent = 0;
            let index = 0;
            const totalChunks = Math.ceil(file.size / chunkSize);

            // Upload chunks
            while (sent < file.size) {
                const slice = file.slice(sent, Math.min(sent + chunkSize, file.size));
                const buf = await slice.arrayBuffer();

                const putRes = await fetch(`/pt/upload/chunk?upload_id=${uploadId}&index=${index}`, {
                    method: 'PUT',
                    headers: { 'Authorization': 'Bearer ' + (window.state && window.state.token ? window.state.token : '') },
                    body: buf
                });

                if (!putRes.ok) {
                    const errText = await putRes.text();
                    throw new Error(`Falha no chunk ${index} (${putRes.status}): ${errText}`);
                }

                sent += slice.size;
                index++;
                const pct = Math.round((sent / file.size) * 100);
                setStatus(`📤 A fazer upload... ${pct}%`, 'info');
            }

            logLine(`[DOCS] Upload 100% completo (${totalChunks} chunks)`);

            // Finalize upload
            const finishRes = await fetch('/pt/upload/finish', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': 'Bearer ' + (window.state && window.state.token ? window.state.token : '')
                },
                body: JSON.stringify({ upload_id: uploadId })
            });

            if (!finishRes.ok) {
                const errText = await finishRes.text();
                throw new Error(`Falha no upload/finish (${finishRes.status}): ${errText}`);
            }

            // Store upload ID
            if (!window.state) window.state = {};
            window.state.lastUploadId = uploadId;

            logLine('[DOCS] ✅ Upload concluído com sucesso');

        } catch (e) {
            logLine('[DOCS] ❌ Erro no upload: ' + e.message);
            alert('❌ Erro ao fazer upload: ' + e.message);
            return;
        }
    }

    // Switch to docs tab
    showTab('docs');

    // Show loading
    document.getElementById('docs-loading').style.display = 'block';
    document.getElementById('docs-table-body').innerHTML = '';
    document.getElementById('docs-stats').style.display = 'none';

    setStatus('📄 A carregar documentos do ficheiro XML...', 'info');
    logLine('[DOCS] A carregar documentos do upload_id=' + uploadId);

    try {
        const res = await fetch('/pt/upload/extract-documents', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': 'Bearer ' + (window.state && window.state.token ? window.state.token : '')
            },
            body: JSON.stringify({ upload_id: uploadId })
        });

        const data = await res.json();

        if (data.ok && data.documents) {
            allDocs = data.documents;
            logLine(`[DOCS] Encontrados ${allDocs.length} documentos`);
            setStatus(`✅ ${allDocs.length} documentos carregados`, 'success');

            // Show stats
            updateDocsStats();

            // Render table
            renderDocsTable(allDocs);
        } else {
            logLine('[DOCS] ❌ Erro: ' + (data.error || 'Erro desconhecido'));
            setStatus('❌ Erro ao carregar documentos', 'error');
            document.getElementById('docs-table-body').innerHTML = `
                <tr><td colspan="10" style="padding:2rem; text-align:center; color:#ef4444;">
                    ❌ Erro: ${data.error || data.detail || 'Erro desconhecido'}
                </td></tr>
            `;
        }
    } catch (e) {
        logLine('[DOCS] ❌ Exceção: ' + e.message);
        setStatus('❌ Erro ao carregar documentos', 'error');
        document.getElementById('docs-table-body').innerHTML = `
            <tr><td colspan="10" style="padding:2rem; text-align:center; color:#ef4444;">
                ❌ Erro: ${e.message}
            </td></tr>
        `;
    } finally {
        document.getElementById('docs-loading').style.display = 'none';
    }
};

window.renderDocsTable = function(docs) {
    const tbody = document.getElementById('docs-table-body');

    // IMPORTANT: Store docs globally for export (same as renderHistoryTable does)
    allDocs = docs || [];
    console.log('[renderDocsTable] Stored ' + allDocs.length + ' docs globally');

    if (!docs || docs.length === 0) {
        tbody.innerHTML = `
            <tr><td colspan="10" style="padding:2rem; text-align:center; color:#94a3b8;">
                Nenhum documento encontrado
            </td></tr>
        `;
        return;
    }

    tbody.innerHTML = docs.map((doc, idx) => {
        const statusBadge = doc.DocumentStatus === 'N'
            ? '<span style="background:#10b981;color:white;padding:2px 8px;border-radius:4px;font-size:0.75rem;">Normal</span>'
            : '<span style="background:#ef4444;color:white;padding:2px 8px;border-radius:4px;font-size:0.75rem;">Anulado</span>';

        const typeColor = {
            'FT': '#2563eb',
            'NC': '#ef4444',
            'ND': '#f59e0b',
            'FR': '#10b981',
            'GT': '#8b5cf6'
        }[doc.InvoiceType] || '#64748b';

        return `
            <tr style="border-bottom:1px solid #e2e8f0;" data-type="${doc.InvoiceType}" data-status="${doc.DocumentStatus}">
                <td style="padding:0.75rem;">${idx + 1}</td>
                <td style="padding:0.75rem;"><span style="color:${typeColor};font-weight:600;">${doc.InvoiceType}</span></td>
                <td style="padding:0.75rem;font-family:monospace;">${doc.InvoiceNo}</td>
                <td style="padding:0.75rem;">${doc.InvoiceDate}</td>
                <td style="padding:0.75rem;font-family:monospace;">${doc.CustomerID || '-'}</td>
                <td style="padding:0.75rem;">${doc.CustomerName || '-'}</td>
                <td style="padding:0.75rem; text-align:right;font-family:monospace;">€ ${parseFloat(doc.NetTotal || 0).toFixed(2)}</td>
                <td style="padding:0.75rem; text-align:right;font-family:monospace;">€ ${parseFloat(doc.TaxPayable || 0).toFixed(2)}</td>
                <td style="padding:0.75rem; text-align:right;font-family:monospace;font-weight:600;">€ ${parseFloat(doc.GrossTotal || 0).toFixed(2)}</td>
                <td style="padding:0.75rem; text-align:center;">${statusBadge}</td>
            </tr>
        `;
    }).join('');
};

window.updateDocsStats = function() {
    if (!allDocs || allDocs.length === 0) return;

    const total = allDocs.length;
    const totalValue = allDocs.reduce((sum, doc) => sum + parseFloat(doc.GrossTotal || 0), 0);
    const ftCount = allDocs.filter(d => d.InvoiceType === 'FT').length;
    const ncCount = allDocs.filter(d => d.InvoiceType === 'NC').length;

    document.getElementById('stats-total').textContent = total;
    document.getElementById('stats-total-value').textContent = `€ ${totalValue.toFixed(2)}`;
    document.getElementById('stats-ft').textContent = ftCount;
    document.getElementById('stats-nc').textContent = ncCount;
    document.getElementById('docs-stats').style.display = 'block';
};

window.filterDocsTable = function() {
    const searchTerm = document.getElementById('docs-search').value.toLowerCase();
    const typeFilter = document.getElementById('docs-filter-type').value;
    const statusFilter = document.getElementById('docs-filter-status').value;

    const filtered = allDocs.filter(doc => {
        // Text search
        const matchesSearch = !searchTerm ||
            doc.InvoiceNo.toLowerCase().includes(searchTerm) ||
            (doc.CustomerID && doc.CustomerID.toLowerCase().includes(searchTerm)) ||
            (doc.CustomerName && doc.CustomerName.toLowerCase().includes(searchTerm)) ||
            doc.GrossTotal.toString().includes(searchTerm);

        // Type filter
        const matchesType = !typeFilter || doc.InvoiceType === typeFilter;

        // Status filter
        const matchesStatus = !statusFilter || doc.DocumentStatus === statusFilter;

        return matchesSearch && matchesType && matchesStatus;
    });

    renderDocsTable(filtered);
    logLine(`[DOCS] Filtrado: ${filtered.length} de ${allDocs.length} documentos`);
};

window.exportDocsToCSV = function() {
    if (!allDocs || allDocs.length === 0) {
        alert('Nenhum documento para exportar');
        return;
    }

    const headers = ['Tipo', 'Número', 'Data', 'Cliente ID', 'Cliente Nome', 'Valor s/ IVA', 'IVA', 'Total', 'Status'];
    const rows = allDocs.map(doc => [
        doc.InvoiceType,
        doc.InvoiceNo,
        doc.InvoiceDate,
        doc.CustomerID || '',
        doc.CustomerName || '',
        doc.NetTotal,
        doc.TaxPayable,
        doc.GrossTotal,
        doc.DocumentStatus === 'N' ? 'Normal' : 'Anulado'
    ]);

    const csv = [headers, ...rows].map(row => row.map(cell => `"${cell}"`).join(',')).join('\n');
    const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');
    link.href = URL.createObjectURL(blob);
    link.download = `documentos_saft_${new Date().toISOString().slice(0,10)}.csv`;
    link.click();

    logLine('[DOCS] Exportado para CSV: ' + allDocs.length + ' documentos');
};

window.exportDocsToExcel = function() {
    console.log('[EXPORT-DOCS] Starting export...');
    console.log('[EXPORT-DOCS] typeof allDocs:', typeof allDocs);
    console.log('[EXPORT-DOCS] allDocs:', allDocs);
    console.log('[EXPORT-DOCS] allDocs.length:', allDocs ? allDocs.length : 'undefined');
    console.log('[EXPORT-DOCS] window.allDocs:', window.allDocs);

    // Try to get docs from table if allDocs is empty
    let docsToExport = allDocs;

    if (!docsToExport || docsToExport.length === 0) {
        console.log('[EXPORT-DOCS] allDocs is empty, checking table...');
        const tbody = document.getElementById('docs-table-body');
        if (tbody && tbody.rows && tbody.rows.length > 0) {
            console.log('[EXPORT-DOCS] Found ' + tbody.rows.length + ' rows in table, but allDocs is empty!');
            alert('⚠️ ERRO: Dados não encontrados na memória.\n\nPor favor:\n1. Recarregue a página (F5)\n2. Faça upload do ficheiro novamente\n3. Clique "📄 Checkar os Docs"\n4. Tente exportar novamente\n\nSe o problema persistir, verifique a consola (F12).');
            return;
        }

        alert('Nenhum documento para exportar.\n\nPrimeiro carregue documentos clicando em "📄 Checkar os Docs".');
        return;
    }

    console.log('[EXPORT-DOCS] Exporting ' + docsToExport.length + ' documents');
    console.log('[EXPORT-DOCS] First document:', docsToExport[0]);

    // Create Excel-compatible HTML with proper encoding
    let html = `<?xml version="1.0"?>
<?mso-application progid="Excel.Sheet"?>
<Workbook xmlns="urn:schemas-microsoft-com:office:spreadsheet"
 xmlns:o="urn:schemas-microsoft-com:office:office"
 xmlns:x="urn:schemas-microsoft-com:office:excel"
 xmlns:ss="urn:schemas-microsoft-com:office:spreadsheet"
 xmlns:html="http://www.w3.org/TR/REC-html40">
 <Worksheet ss:Name="Documentos SAFT">
  <Table>
   <Row>
    <Cell><Data ss:Type="String">Tipo</Data></Cell>
    <Cell><Data ss:Type="String">Número</Data></Cell>
    <Cell><Data ss:Type="String">Data</Data></Cell>
    <Cell><Data ss:Type="String">Cliente ID</Data></Cell>
    <Cell><Data ss:Type="String">Cliente Nome</Data></Cell>
    <Cell><Data ss:Type="String">Valor s/ IVA (€)</Data></Cell>
    <Cell><Data ss:Type="String">IVA (€)</Data></Cell>
    <Cell><Data ss:Type="String">Total (€)</Data></Cell>
    <Cell><Data ss:Type="String">Status</Data></Cell>
   </Row>`;

    // Add data rows
    docsToExport.forEach((doc, idx) => {
        const netTotal = parseFloat(doc.NetTotal) || 0;
        const taxPayable = parseFloat(doc.TaxPayable) || 0;
        const grossTotal = parseFloat(doc.GrossTotal) || 0;

        html += `
   <Row>
    <Cell><Data ss:Type="String">${escapeXml(doc.InvoiceType || '')}</Data></Cell>
    <Cell><Data ss:Type="String">${escapeXml(doc.InvoiceNo || '')}</Data></Cell>
    <Cell><Data ss:Type="String">${escapeXml(doc.InvoiceDate || '')}</Data></Cell>
    <Cell><Data ss:Type="String">${escapeXml(doc.CustomerID || '')}</Data></Cell>
    <Cell><Data ss:Type="String">${escapeXml(doc.CustomerName || '')}</Data></Cell>
    <Cell><Data ss:Type="Number">${netTotal.toFixed(2)}</Data></Cell>
    <Cell><Data ss:Type="Number">${taxPayable.toFixed(2)}</Data></Cell>
    <Cell><Data ss:Type="Number">${grossTotal.toFixed(2)}</Data></Cell>
    <Cell><Data ss:Type="String">${escapeXml(doc.DocumentStatus || '')}</Data></Cell>
   </Row>`;

        if (idx === 0) {
            console.log('[EXPORT-DOCS] First row generated:', doc);
        }
        if (idx % 100 === 0) {
            console.log('[EXPORT-DOCS] Progress: ' + idx + '/' + docsToExport.length);
        }
    });

    console.log('[EXPORT-DOCS] All rows generated: ' + docsToExport.length);

    html += `
  </Table>
 </Worksheet>
</Workbook>`;

    console.log('[EXPORT-DOCS] Total XML length:', html.length);
    console.log('[EXPORT-DOCS] First 500 chars:', html.substring(0, 500));

    // Create blob with proper BOM for UTF-8
    const blob = new Blob(['\ufeff' + html], {
        type: 'application/vnd.ms-excel'
    });

    console.log('[EXPORT-DOCS] Blob created, size:', blob.size);

    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'documentos_saft_' + new Date().toISOString().slice(0,10) + '.xls';
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    window.URL.revokeObjectURL(url);

    logLine('[DOCS] Exportado para Excel: ' + docsToExport.length + ' documentos');
    console.log('[EXPORT-DOCS] Export completed successfully');
    alert('✅ Exportação concluída!\n\n' + docsToExport.length + ' documentos exportados para Excel.');
};

// Helper function to escape XML special characters
function escapeXml(unsafe) {
    if (!unsafe) return '';
    return String(unsafe)
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&apos;');
}

// ==================== Auto-Fix Loop ====================
window.autoFixLoop = async function(uploadId, maxIterations = 20, shouldSubmit = false) {
    let iteration = 0;
    let totalFixed = 0;

    setStatus(`🔁 Auto-fix iniciado... (máx ${maxIterations} iterações)`, 'info');
    logLine(`[AUTO-FIX] Iniciando loop automático para upload_id=${uploadId}`);
    if (shouldSubmit) {
        logLine(`[AUTO-FIX] Modo: Corrigir + Enviar para AT`);
    }

    while (iteration < maxIterations) {
        iteration++;
        logLine(`\n[AUTO-FIX] Iteração ${iteration}/${maxIterations}`);
        setStatus(`🔁 Auto-fix: Iteração ${iteration}/${maxIterations}...`, 'info');

        try {
            // Validate to get current issues
            logLine(`[AUTO-FIX] A validar upload_id: ${uploadId}`);
            const validateRes = await fetch(`/pt/validate-jar-by-upload?upload_id=${uploadId}&operation=validar&full=1`, {
                method: 'POST',
                headers: {
                    'Authorization': 'Bearer ' + (window.state && window.state.token ? window.state.token : '')
                }
            });

            // Check for HTTP errors
            if (!validateRes.ok) {
                const errorText = await validateRes.text();
                logLine(`[AUTO-FIX] ❌ Erro HTTP ${validateRes.status}: ${errorText}`);
                setStatus(`❌ Erro ao validar: HTTP ${validateRes.status}`, 'error');
                alert(`❌ Erro no auto-fix:\n\nHTTP ${validateRes.status}\n${errorText}\n\nO ficheiro pode ter sido substituído. Tente novamente com o ficheiro atual.`);
                return;
            }

            const validateData = await validateRes.json();
            const issues = validateData.issues || [];

            // Log JAR validation details
            logLine(`[AUTO-FIX] ═══════════════════════════════════════`);
            logLine(`[AUTO-FIX] Validação JAR (Iteração ${iteration})`);
            logLine(`[AUTO-FIX] Return code: ${validateData.returncode}`);
            logLine(`[AUTO-FIX] Status: ${validateData.ok ? '✅ OK' : '❌ COM ERROS'}`);
            logLine(`[AUTO-FIX] Erros encontrados: ${issues.length}`);

            // Show JAR stdout if available
            if (validateData.stdout && validateData.stdout.trim()) {
                logLine(`[AUTO-FIX] ───────────────────────────────────────`);
                logLine(`[AUTO-FIX] JAR STDOUT:`);
                const stdoutLines = validateData.stdout.split('\n').slice(0, 20); // First 20 lines
                stdoutLines.forEach(line => {
                    if (line.trim()) logLine(`  ${line}`);
                });
                if (validateData.stdout.split('\n').length > 20) {
                    logLine(`  ... (truncado, ${validateData.stdout.split('\n').length} linhas no total)`);
                }
            }

            // Show JAR stderr if available
            if (validateData.stderr && validateData.stderr.trim()) {
                logLine(`[AUTO-FIX] ───────────────────────────────────────`);
                logLine(`[AUTO-FIX] JAR STDERR:`);
                const stderrLines = validateData.stderr.split('\n').slice(0, 10);
                stderrLines.forEach(line => {
                    if (line.trim()) logLine(`  ${line}`);
                });
            }

            // Show issues details
            if (issues.length > 0) {
                logLine(`[AUTO-FIX] ───────────────────────────────────────`);
                logLine(`[AUTO-FIX] Detalhes dos erros:`);
                issues.forEach((issue, idx) => {
                    const lineInfo = issue.location?.line ? ` (linha ${issue.location.line})` : '';
                    logLine(`  ${idx + 1}. [${issue.code}]${lineInfo}: ${issue.message?.substring(0, 100)}`);
                });
            }

            logLine(`[AUTO-FIX] ═══════════════════════════════════════`);

            // If no errors or validation succeeded, we're done
            if (validateData.ok || issues.length === 0) {
                logLine('[AUTO-FIX] ✅ Sem erros! Auto-fix concluído.');
                setStatus(`✅ Auto-fix concluído! ${totalFixed} correções aplicadas em ${iteration} iterações.`, 'success');

                // Show submit button
                const submitPhase = document.getElementById('submit-phase');
                if (submitPhase) {
                    submitPhase.style.display = 'block';
                    logLine('[AUTO-FIX] ✨ Botão de envio para AT ativado!');
                }

                // If should submit, do it now
                if (shouldSubmit) {
                    logLine('[AUTO-FIX] 📤 Iniciando envio automático para AT...');
                    setStatus('📤 A enviar para AT...', 'info');
                    await window.submitToAT(uploadId);
                } else {
                    alert(`✅ Auto-fix concluído!\n\n${totalFixed} correções aplicadas\n${iteration} iterações`);
                }
                return;
            }

            // Prepare fixes from issues with suggestions
            const fixes = [];
            issues.forEach((it, idx) => {
                if (it.suggestion) {
                    fixes.push(it);
                } else if (it.suggestions && Array.isArray(it.suggestions) && it.suggestions.length > 0) {
                    // Use first suggestion by default
                    fixes.push({
                        ...it,
                        selected_suggestion: it.suggestions[0]
                    });
                }
            });

            if (fixes.length === 0) {
                logLine('[AUTO-FIX] ⚠️ Sem correções automáticas disponíveis. Parando.');
                setStatus(`⚠️ Auto-fix parou: ${issues.length} erros sem correção automática`, 'warning');
                // Show popup with remaining issues
                window.showIssuesPopup(issues);
                return;
            }

            logLine(`[AUTO-FIX] 🔧 Aplicando ${fixes.length} correções...`);
            fixes.forEach((fix, idx) => {
                const lineInfo = fix.location?.line ? ` (linha ${fix.location.line})` : '';
                logLine(`  ${idx + 1}. ${fix.code}${lineInfo}`);
            });

            // Apply fixes
            const fixRes = await fetch('/pt/upload/apply-fixes-and-validate', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': 'Bearer ' + (window.state && window.state.token ? window.state.token : '')
                },
                body: JSON.stringify({ upload_id: uploadId, fixes })
            });

            const fixData = await fixRes.json();
            const applied = fixData.applied || 0;
            totalFixed += applied;

            logLine(`[AUTO-FIX] ✅ Aplicadas ${applied} correções (total acumulado: ${totalFixed})`);

            // Log revalidation result after fixes
            if (fixData.ok) {
                logLine(`[AUTO-FIX] 🎉 Revalidação após correções: SEM ERROS!`);
            } else if (fixData.issues && fixData.issues.length > 0) {
                logLine(`[AUTO-FIX] ⚠️ Revalidação após correções: ainda há ${fixData.issues.length} erros`);
            }

            // Small delay to avoid overwhelming the server
            await new Promise(resolve => setTimeout(resolve, 500));

        } catch (e) {
            logLine(`[AUTO-FIX] ❌ Erro: ${e.message}`);
            setStatus('❌ Erro no auto-fix: ' + e.message, 'error');
            alert('❌ Erro no auto-fix: ' + e.message);
            return;
        }
    }

    // Max iterations reached
    logLine(`[AUTO-FIX] ⚠️ Atingido limite de ${maxIterations} iterações`);
    setStatus(`⚠️ Auto-fix parou: limite de ${maxIterations} iterações atingido`, 'warning');
    alert(`⚠️ Auto-fix parou após ${maxIterations} iterações.\n\n${totalFixed} correções aplicadas.\n\nPode haver erros restantes.`);
};

window.saveCustomRule = async function() {
    const ruleId = document.getElementById('rule-id').value.trim();
    const ruleName = document.getElementById('rule-name').value.trim();
    const ruleCode = document.getElementById('rule-code').value.trim();
    const rulePattern = document.getElementById('rule-pattern').value.trim();

    if (!ruleId || !ruleName || !ruleCode || !rulePattern) {
        alert('Por favor preencha todos os campos obrigatórios');
        return;
    }

    // Collect suggestions
    const suggestions = [];
    const sugLabels = document.querySelectorAll('.sug-label');
    const sugReasons = document.querySelectorAll('.sug-reason');
    const sugCodes = document.querySelectorAll('.sug-code');

    for (let i = 0; i < sugLabels.length; i++) {
        const label = sugLabels[i].value.trim();
        const reason = sugReasons[i].value.trim();
        const code = sugCodes[i].value.trim();
        if (label && reason && code) {
            suggestions.push({ label, reason, code });
        }
    }

    const rule = {
        id: ruleId,
        name: ruleName,
        pattern: {
            type: 'regex',
            match: rulePattern,
            flags: ['IGNORECASE']
        },
        code: ruleCode,
        suggestions: suggestions,
        fix_type: 'custom',
        enabled: true
    };

    try {
        const token = (window.state && window.state.token) || '';
        const res = await fetch('/pt/fix-rules', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': 'Bearer ' + token
            },
            body: JSON.stringify({ rule })
        });

        const data = await res.json();

        if (data.ok) {
            alert('✅ Regra guardada com sucesso!');
            // Close modal
            const overlay = document.querySelector('[style*="position: fixed"][style*="z-index: 10000"]');
            if (overlay) document.body.removeChild(overlay);
        } else {
            alert('❌ Erro ao guardar regra: ' + (data.detail || 'Erro desconhecido'));
        }
    } catch (e) {
        alert('❌ Erro ao guardar regra: ' + e.message);
    }
};

