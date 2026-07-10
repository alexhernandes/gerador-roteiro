<?php

declare(strict_types=1);

// Segredo: fica no .env (carregado em bootstrap.php).
define('XAI_API_KEY', getenv('XAI_API_KEY') ?: '');

// API/modelo.
define('XAI_BASE_URL', 'https://api.x.ai/v1');
define('MODEL', 'grok-4.3');
define('REASONING_EFFORT', 'low');

// Defaults da interface.
define('DEFAULT_LANGUAGE', 'Português (Brasil)');
define('DEFAULT_ASPECT_RATIO', '9:16');
define('DEFAULT_THEME', 'Livre — crie uma história viral com drama e humor');

// Universo/preset visual dos personagens.
define('DEFAULT_UNIVERSE', 'frutinhas');
define('UNIVERSE_OPTIONS', [
    'frutinhas',
    'carros',
    'predios_falantes',
    'humanos_desenhados',
]);

// Configuração do vídeo/roteiro.
define('VIDEO_RESOLUTION', '720p');
define('SCENE_DURATION_SECONDS', 10);
define('TOTAL_SCENES', 7);
define('TOTAL_DURATION_SECONDS', SCENE_DURATION_SECONDS * TOTAL_SCENES);

// Execução do agente de vídeo.
define('AGENT_CONFIRM_BETWEEN_STEPS', true);
define('AGENT_VIDEOS_PER_STEP', 1);

// UX local.
define('OPEN_OUTPUT_FOLDER_ON_FINISH', true);