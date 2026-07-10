(function () {
    'use strict';

    const form = document.getElementById('form-roteiro');
    const btnGerar = document.getElementById('btn-gerar');
    const logEl = document.getElementById('log');
    const statusBadge = document.getElementById('status-badge');
    const metaInfo = document.getElementById('meta-info');
    const resultadoEl = document.getElementById('resultado');

    const selects = {
        idioma: document.getElementById('idioma'),
        aspect_ratio: document.getElementById('aspect_ratio'),
        universo: document.getElementById('universo'),
        agent_confirm: document.getElementById('agent_confirm'),
        agent_videos: document.getElementById('agent_videos'),
    };

    function setStatus(text, className) {
        statusBadge.textContent = text;
        statusBadge.className = 'status-badge' + (className ? ' ' + className : '');
    }

    function preencherSelect(select, opcoes, valorPadrao, usarValueLabel) {
        select.innerHTML = '';
        opcoes.forEach(function (opcao) {
            const opt = document.createElement('option');
            if (usarValueLabel) {
                opt.value = opcao.value;
                opt.textContent = opcao.label;
            } else {
                opt.value = opcao;
                opt.textContent = opcao;
            }
            if (String(opt.value) === String(valorPadrao)) {
                opt.selected = true;
            }
            select.appendChild(opt);
        });
    }

    function limparLog() {
        logEl.innerHTML = '';
    }

    function adicionarLinha(type, message, time) {
        const p = document.createElement('p');
        p.className = 'log__line' + (type ? ' log__line--' + type : '');
        const timeSpan = document.createElement('span');
        timeSpan.className = 'log__time';
        timeSpan.textContent = time || '';
        p.appendChild(timeSpan);
        p.appendChild(document.createTextNode(message));
        logEl.appendChild(p);
        logEl.scrollTop = logEl.scrollHeight;
    }

    function mostrarResultado(extra) {
        if (!extra) return;

        resultadoEl.classList.remove('hidden');
        document.getElementById('resultado-titulo').textContent = extra.titulo || 'Roteiro';
        document.getElementById('resultado-historia').textContent = extra.historia || '';
        document.getElementById('resultado-pasta').textContent = extra.sessao || '';

        const elencoUl = document.getElementById('resultado-elenco');
        elencoUl.innerHTML = '';
        (extra.elenco || []).forEach(function (p) {
            const li = document.createElement('li');
            li.textContent = p.name + (p.type ? ' (' + p.type + ')' : '');
            elencoUl.appendChild(li);
        });

        const stats = document.getElementById('resultado-stats');
        stats.innerHTML = '';
        const resumo = extra.resumo || {};
        [
            ['Verificações', resumo.verificacoes],
            ['Problemas', resumo.problemas],
            ['Erros', resumo.erros],
            ['Avisos', resumo.avisos],
        ].forEach(function (par) {
            if (par[1] === undefined) return;
            const chip = document.createElement('span');
            chip.className = 'stat-chip';
            chip.textContent = par[0] + ': ' + par[1];
            stats.appendChild(chip);
        });
    }

    async function carregarOpcoes() {
        const resp = await fetch('api/opcoes.php');
        if (!resp.ok) throw new Error('Falha ao carregar opções.');
        const data = await resp.json();

        preencherSelect(selects.idioma, data.idiomas, data.defaults.idioma, false);
        preencherSelect(selects.aspect_ratio, data.formatos, data.defaults.aspect_ratio, true);
        preencherSelect(selects.universo, data.universos, data.defaults.universo, true);

        selects.agent_confirm.value = data.defaults.agent_confirm_between_steps ? '1' : '0';

        const videosOpts = data.videos_por_passo.map(function (n) {
            return {
                value: String(n),
                label: n + ' vídeo(s) antes do próximo passo',
            };
        });
        preencherSelect(selects.agent_videos, videosOpts, String(data.defaults.agent_videos_per_step), true);

        if (data.meta) {
            metaInfo.innerHTML =
                'Modelo: <strong>' + escapeHtml(data.meta.model) + '</strong><br>' +
                data.meta.total_scenes + ' cenas × ' + data.meta.scene_duration + 's = ' +
                data.meta.total_duration + 's · ' + escapeHtml(data.meta.resolution);
        }

        const temaInput = document.getElementById('tema');
        if (!temaInput.value && data.defaults.tema) {
            temaInput.placeholder = data.defaults.tema.slice(0, 60) + '...';
        }
    }

    function escapeHtml(str) {
        const div = document.createElement('div');
        div.textContent = str;
        return div.innerHTML;
    }

    async function gerarRoteiro(payload) {
        const resp = await fetch('api/gerar.php', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload),
        });

        if (!resp.ok && !resp.body) {
            throw new Error('Erro na requisição: ' + resp.status);
        }

        const reader = resp.body.getReader();
        const decoder = new TextDecoder();
        let buffer = '';

        while (true) {
            const { done, value } = await reader.read();
            if (done) break;

            buffer += decoder.decode(value, { stream: true });
            const linhas = buffer.split('\n');
            buffer = linhas.pop() || '';

            linhas.forEach(function (linha) {
                linha = linha.trim();
                if (!linha) return;
                try {
                    const evt = JSON.parse(linha);
                    const tipo = evt.type === 'log' ? '' : evt.type;
                    adicionarLinha(tipo, evt.message, evt.time);

                    if (evt.type === 'done') {
                        setStatus('Concluído', 'status-badge--done');
                        mostrarResultado(evt.extra);
                    }
                    if (evt.type === 'error') {
                        setStatus('Erro', 'status-badge--error');
                    }
                    if (evt.type === 'step') {
                        setStatus('Gerando...', 'status-badge--running');
                    }
                } catch (e) {
                    adicionarLinha('', linha);
                }
            });
        }
    }

    form.addEventListener('submit', async function (e) {
        e.preventDefault();

        limparLog();
        resultadoEl.classList.add('hidden');
        setStatus('Gerando...', 'status-badge--running');
        btnGerar.disabled = true;

        const payload = {
            idioma: selects.idioma.value,
            aspect_ratio: selects.aspect_ratio.value,
            universo: selects.universo.value,
            tema: document.getElementById('tema').value.trim(),
            agent_confirm_between_steps: selects.agent_confirm.value === '1',
            agent_videos_per_step: parseInt(selects.agent_videos.value, 10),
        };

        try {
            await gerarRoteiro(payload);
        } catch (err) {
            adicionarLinha('error', err.message || String(err));
            setStatus('Erro', 'status-badge--error');
        } finally {
            btnGerar.disabled = false;
        }
    });

    carregarOpcoes().catch(function (err) {
        adicionarLinha('error', 'Não foi possível carregar opções: ' + err.message);
        setStatus('Erro', 'status-badge--error');
    });
})();