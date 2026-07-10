<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Gerador de Roteiro</title>
    <link rel="stylesheet" href="css/style.css">
</head>
<body>
    <div class="app">
        <header class="header">
            <div class="header__brand">
                <span class="header__icon" aria-hidden="true">🎬</span>
                <div>
                    <h1>Gerador de Roteiro</h1>
                    <p class="header__subtitle">7 cenas · 70 segundos · vídeos virais com IA</p>
                </div>
            </div>
            <div class="header__meta" id="meta-info"></div>
        </header>

        <main class="layout">
            <section class="panel panel--form">
                <h2>Configuração</h2>
                <form id="form-roteiro" novalidate>
                    <div class="field">
                        <label for="idioma">Idioma dos diálogos</label>
                        <select id="idioma" name="idioma" required></select>
                    </div>

                    <div class="field">
                        <label for="aspect_ratio">Formato do vídeo</label>
                        <select id="aspect_ratio" name="aspect_ratio" required></select>
                    </div>

                    <div class="field">
                        <label for="universo">Universo dos personagens</label>
                        <select id="universo" name="universo" required></select>
                    </div>

                    <div class="field">
                        <label for="agent_confirm">Confirmação do agente</label>
                        <select id="agent_confirm" name="agent_confirm_between_steps">
                            <option value="1">Sim, pedir confirmação entre passos</option>
                            <option value="0">Não, continuar automaticamente</option>
                        </select>
                    </div>

                    <div class="field">
                        <label for="agent_videos">Vídeos por passo do agente</label>
                        <select id="agent_videos" name="agent_videos_per_step"></select>
                    </div>

                    <div class="field">
                        <label for="tema">Tema da história <span class="optional">(opcional)</span></label>
                        <input
                            type="text"
                            id="tema"
                            name="tema"
                            placeholder="Ex.: Traição, segredo de família, corrida proibida..."
                            autocomplete="off"
                        >
                        <p class="hint">Deixe em branco para usar o tema livre padrão.</p>
                    </div>

                    <button type="submit" class="btn btn--primary" id="btn-gerar">
                        <span class="btn__label">Gerar roteiro</span>
                    </button>
                </form>
            </section>

            <section class="panel panel--output">
                <div class="output-header">
                    <h2>Progresso</h2>
                    <span class="status-badge" id="status-badge">Aguardando</span>
                </div>

                <div class="log" id="log" role="log" aria-live="polite">
                    <p class="log__empty">Configure as opções e clique em <strong>Gerar roteiro</strong>.</p>
                </div>

                <div class="resultado hidden" id="resultado">
                    <h3>Entrega</h3>
                    <p class="resultado__titulo" id="resultado-titulo"></p>
                    <p class="resultado__historia" id="resultado-historia"></p>
                    <ul class="resultado__elenco" id="resultado-elenco"></ul>
                    <div class="resultado__stats" id="resultado-stats"></div>
                    <p class="resultado__pasta">Pasta: <code id="resultado-pasta"></code></p>
                </div>
            </section>
        </main>

        <footer class="footer">
            <p>Powered by xAI Grok · PHP + HTML + CSS + JavaScript</p>
        </footer>
    </div>

    <script src="js/app.js"></script>
</body>
</html>