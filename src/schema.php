<?php
declare(strict_types=1);

require_once __DIR__ . '/config.php';

define('RESOLUCAO', VIDEO_RESOLUTION);
define('DURACAO_CENA', SCENE_DURATION_SECONDS);
define('NUM_CENAS', TOTAL_SCENES);
define('DURACAO_TOTAL', TOTAL_DURATION_SECONDS);

$VOICE_OVERRIDE = [
    'type' => 'object',
    'properties' => [
        'VOICE_GENDER' => ['type' => 'string'],
        'VOCAL_WEIGHT' => ['type' => 'string'],
        'TONE_PROFILE' => ['type' => 'string'],
        'FORCE_SYNTHESIS' => ['type' => 'string'],
    ],
    'required' => ['VOICE_GENDER', 'VOCAL_WEIGHT', 'TONE_PROFILE', 'FORCE_SYNTHESIS'],
    'additionalProperties' => false,
];

$DIALOGUE_LINE = [
    'oneOf' => [
        [
            'type' => 'object',
            'properties' => [
                'SPEAKER' => ['type' => 'string'],
                'VOICE_IDENTITY_LOCK' => ['type' => 'string'],
                'TEXT' => ['type' => 'string'],
            ],
            'required' => ['SPEAKER', 'VOICE_IDENTITY_LOCK', 'TEXT'],
            'additionalProperties' => false,
        ],
        [
            'type' => 'object',
            'properties' => [
                'PAUSE' => ['type' => 'number'],
            ],
            'required' => ['PAUSE'],
            'additionalProperties' => false,
        ],
    ],
];

$AI_INSTRUCTIONS_ELENCO = [
    'type' => 'object',
    'properties' => [
        'task' => ['type' => 'string'],
        'resolution' => ['type' => 'string'],
        'aspect_ratio' => ['type' => 'string'],
        'output' => ['type' => 'string'],
        'style' => ['type' => 'string'],
    ],
    'required' => ['task', 'resolution', 'aspect_ratio', 'output', 'style'],
    'additionalProperties' => false,
];

$AI_INSTRUCTIONS_ROTEIRO = [
    'type' => 'object',
    'properties' => [
        'task' => ['type' => 'string'],
        'resolution' => ['type' => 'string'],
        'aspect_ratio' => ['type' => 'string'],
        'duration_per_scene_seconds' => ['type' => 'integer'],
        'total_duration_seconds' => ['type' => 'integer'],
        'total_scenes' => ['type' => 'integer'],
        'audio_source' => ['type' => 'string'],
        'output' => ['type' => 'string'],
        'style' => ['type' => 'string'],
        'note' => ['type' => 'string'],
        'post_generation_qa' => ['type' => 'string'],
        'agent_execution' => ['type' => 'string'],
    ],
    'required' => [
        'task',
        'resolution',
        'aspect_ratio',
        'duration_per_scene_seconds',
        'total_duration_seconds',
        'total_scenes',
        'audio_source',
        'output',
        'style',
    ],
    'additionalProperties' => false,
];

$BEAT = [
    'type' => 'object',
    'properties' => [
        'scene_number' => ['type' => 'integer'],
        'story_position' => ['type' => 'string'],
        'narrative_beat' => ['type' => 'string'],
        'dialogue_intent' => ['type' => 'string'],
        'camera_concept' => ['type' => 'string'],
        'key_action' => ['type' => 'string'],
    ],
    'required' => [
        'scene_number',
        'story_position',
        'narrative_beat',
        'dialogue_intent',
        'camera_concept',
        'key_action',
    ],
    'additionalProperties' => false,
];

$SINOPSE_SCHEMA = [
    'type' => 'object',
    'properties' => [
        'title' => ['type' => 'string'],
        'theme' => ['type' => 'string'],
        'language' => ['type' => 'string'],
        'story_summary' => ['type' => 'string'],
        'act_1' => ['type' => 'string'],
        'act_2' => ['type' => 'string'],
        'act_3' => ['type' => 'string'],
        'beats' => [
            'type' => 'array',
            'items' => $BEAT,
            'minItems' => NUM_CENAS,
            'maxItems' => NUM_CENAS,
        ],
    ],
    'required' => [
        'title',
        'theme',
        'language',
        'story_summary',
        'act_1',
        'act_2',
        'act_3',
        'beats',
    ],
    'additionalProperties' => false,
];

$SCENE = [
    'type' => 'object',
    'properties' => [
        'SCENE_NUMBER' => ['type' => 'integer'],
        'SCENE_NAME' => ['type' => 'string'],
        'SCENE_ROLE' => ['type' => 'string'],
        'STORY_POSITION' => ['type' => 'string'],
        'NARRATIVE_BEAT' => ['type' => 'string'],
        'OPENING_HOOK' => ['type' => 'string'],
        'DURATION_SECONDS' => ['type' => 'integer'],
        'TIMESTAMP' => ['type' => 'string'],
        'AI_VIDEO_TASK' => ['type' => 'string'],
        'VISUAL_PROMPT' => ['type' => 'string'],
        'CAMERA_DIRECTION' => ['type' => 'string'],
        'PHYSICAL_MOVEMENT' => ['type' => 'string'],
        'ACTION_DIRECTION' => ['type' => 'string'],
        'HAS_DIALOGUE' => ['type' => 'boolean'],
        'AUDIO_SPEAKER' => ['type' => 'string'],
        'AUDIO_TARGET' => ['type' => 'string'],
        'AUDIO_TIMING_CONTROLS' => [
            'type' => 'object',
            'properties' => [
                'OVERALL_PACE' => ['type' => 'string'],
                'SPEECH_PAUSE_SECONDS' => ['type' => 'number'],
            ],
            'required' => ['OVERALL_PACE', 'SPEECH_PAUSE_SECONDS'],
            'additionalProperties' => false,
        ],
        'DELIVERY_STYLE' => ['type' => 'string'],
        'DIALOGUE_LINES' => [
            'type' => 'array',
            'items' => $DIALOGUE_LINE,
            'minItems' => 7,
        ],
        'VOICE_OVERRIDE_METADATA' => [
            'type' => 'object',
            'additionalProperties' => $VOICE_OVERRIDE,
        ],
    ],
    'required' => [
        'SCENE_NUMBER',
        'SCENE_NAME',
        'SCENE_ROLE',
        'STORY_POSITION',
        'NARRATIVE_BEAT',
        'OPENING_HOOK',
        'DURATION_SECONDS',
        'TIMESTAMP',
        'AI_VIDEO_TASK',
        'VISUAL_PROMPT',
        'CAMERA_DIRECTION',
        'PHYSICAL_MOVEMENT',
        'ACTION_DIRECTION',
        'HAS_DIALOGUE',
        'AUDIO_SPEAKER',
        'AUDIO_TARGET',
        'AUDIO_TIMING_CONTROLS',
        'DELIVERY_STYLE',
        'DIALOGUE_LINES',
        'VOICE_OVERRIDE_METADATA',
    ],
    'additionalProperties' => false,
];

$ELENCO_SCHEMA = [
    'type' => 'object',
    'properties' => [
        'title' => ['type' => 'string'],
        'theme' => ['type' => 'string'],
        'language' => ['type' => 'string'],
        'aspect_ratio' => ['type' => 'string'],
        'resolution' => ['type' => 'string'],
        'ai_instructions' => $AI_INSTRUCTIONS_ELENCO,
        'cast' => [
            'type' => 'array',
            'items' => [
                'type' => 'object',
                'properties' => [
                    'name' => ['type' => 'string'],
                    'character_type' => ['type' => 'string'],
                    'fruit_type' => ['type' => 'string'],
                    'age' => ['type' => 'integer'],
                    'gender' => ['type' => 'string'],
                    'physical_dna' => ['type' => 'string'],
                    'outfit_dna' => ['type' => 'string'],
                    'voice_profile' => ['type' => 'string'],
                    'ai_image_task' => ['type' => 'string'],
                ],
                'required' => [
                    'name',
                    'character_type',
                    'age',
                    'gender',
                    'physical_dna',
                    'outfit_dna',
                    'voice_profile',
                    'ai_image_task',
                ],
                'additionalProperties' => false,
            ],
            'minItems' => 1,
        ],
    ],
    'required' => [
        'title',
        'theme',
        'language',
        'aspect_ratio',
        'resolution',
        'ai_instructions',
        'cast',
    ],
    'additionalProperties' => false,
];

$ROTEIRO_SCHEMA = [
    'type' => 'object',
    'properties' => [
        'title' => ['type' => 'string'],
        'story_summary' => ['type' => 'string'],
        'language' => ['type' => 'string'],
        'aspect_ratio' => ['type' => 'string'],
        'resolution' => ['type' => 'string'],
        'scene_duration_seconds' => ['type' => 'integer'],
        'total_duration_seconds' => ['type' => 'integer'],
        'total_scenes' => ['type' => 'integer'],
        'ai_instructions' => $AI_INSTRUCTIONS_ROTEIRO,
        'agent_execution' => [
            'type' => 'object',
            'properties' => [
                'videos_per_step' => ['type' => 'integer'],
                'confirm_between_steps' => ['type' => 'boolean'],
            ],
            'required' => ['videos_per_step', 'confirm_between_steps'],
            'additionalProperties' => false,
        ],
        'scenes' => [
            'type' => 'object',
            'additionalProperties' => $SCENE,
            'minProperties' => NUM_CENAS,
            'maxProperties' => NUM_CENAS,
        ],
    ],
    'required' => [
        'title',
        'story_summary',
        'language',
        'aspect_ratio',
        'resolution',
        'scene_duration_seconds',
        'total_duration_seconds',
        'total_scenes',
        'ai_instructions',
        'scenes',
    ],
    'additionalProperties' => false,
];

$SINOPSE_RESPONSE_FORMAT = [
    'name' => 'sinopse',
    'strict' => true,
    'schema' => $SINOPSE_SCHEMA,
];

$ELENCO_RESPONSE_FORMAT = [
    'name' => 'elenco',
    'strict' => true,
    'schema' => $ELENCO_SCHEMA,
];

$TRADUCAO_TEMA_SCHEMA = [
    'type' => 'object',
    'properties' => [
        'original_theme' => ['type' => 'string'],
        'target_language' => ['type' => 'string'],
        'translated_theme' => ['type' => 'string'],
    ],
    'required' => ['original_theme', 'target_language', 'translated_theme'],
    'additionalProperties' => false,
];

$TRADUCAO_TEMA_RESPONSE_FORMAT = [
    'name' => 'traducao_tema',
    'strict' => true,
    'schema' => $TRADUCAO_TEMA_SCHEMA,
];

$ROTEIRO_RESPONSE_FORMAT = [
    'name' => 'roteiro',
    'strict' => true,
    'schema' => $ROTEIRO_SCHEMA,
];

$CORRECAO_SCENE = [
    'type' => 'object',
    'properties' => [
        'SCENE_NUMBER' => ['type' => 'integer'],
        'DIALOGUE_LINES' => [
            'type' => 'array',
            'items' => $DIALOGUE_LINE,
            'minItems' => 7,
        ],
        'DELIVERY_STYLE' => ['type' => 'string'],
        'VOICE_OVERRIDE_METADATA' => [
            'type' => 'object',
            'additionalProperties' => $VOICE_OVERRIDE,
        ],
    ],
    'required' => [
        'SCENE_NUMBER',
        'DIALOGUE_LINES',
        'DELIVERY_STYLE',
        'VOICE_OVERRIDE_METADATA',
    ],
    'additionalProperties' => false,
];

$CORRECAO_DIALOGOS_SCHEMA = [
    'type' => 'object',
    'properties' => [
        'scenes' => [
            'type' => 'object',
            'additionalProperties' => $CORRECAO_SCENE,
            'minProperties' => NUM_CENAS,
            'maxProperties' => NUM_CENAS,
        ],
    ],
    'required' => ['scenes'],
    'additionalProperties' => false,
];

$CORRECAO_DIALOGOS_RESPONSE_FORMAT = [
    'name' => 'correcao_dialogos',
    'strict' => true,
    'schema' => $CORRECAO_DIALOGOS_SCHEMA,
];

$AUDITORIA_PROBLEMA = [
    'type' => 'object',
    'properties' => [
        'scene_number' => ['type' => 'integer'],
        'category' => ['type' => 'string'],
        'severity' => ['type' => 'string'],
        'issue' => ['type' => 'string'],
        'suggested_fix' => ['type' => 'string'],
    ],
    'required' => ['scene_number', 'category', 'severity', 'issue', 'suggested_fix'],
    'additionalProperties' => false,
];

$AUDITORIA_SCHEMA = [
    'type' => 'object',
    'properties' => [
        'overall_status' => ['type' => 'string'],
        'problems' => [
            'type' => 'array',
            'items' => $AUDITORIA_PROBLEMA,
        ],
    ],
    'required' => ['overall_status', 'problems'],
    'additionalProperties' => false,
];

$AUDITORIA_RESPONSE_FORMAT = [
    'name' => 'auditoria_narrativa',
    'strict' => true,
    'schema' => $AUDITORIA_SCHEMA,
];

$CENA_RESPONSE_FORMAT = [
    'name' => 'cena',
    'strict' => true,
    'schema' => $SCENE,
];