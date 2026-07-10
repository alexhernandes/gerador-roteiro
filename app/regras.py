"""
Regras de produção baseadas no prompt.txt.
Cada regra tem explicação e exemplo para o relatório de validação.
"""

from schema import DURACAO_CENA, DURACAO_TOTAL, NUM_CENAS, RESOLUCAO

REGRAS = [
    {
        "id": "character_lock",
        "nome": "Total Character Lock",
        "severidade": "aviso",
        "explicacao": (
            "Todo personagem que aparece na cena deve ser descrito no VISUAL_PROMPT "
            "com DNA físico/material e acessórios fixos coerentes com o universo."
        ),
        "exemplo": (
            "CARA (banana masculina, jersey amarelo nº10, shorts jeans, tênis branco, "
            "relógio preto, inchaço vermelho na testa) e BANANA_FEMALE (banana feminina, "
            "camiseta verde, shorts jeans, tênis branco) abraçados no canto do barraco."
        ),
    },
    {
        "id": "outfit_dna",
        "nome": "Outfit DNA (Head-to-Toe)",
        "severidade": "aviso",
        "explicacao": (
            "A roupa deve ser completa em cada cena: material, cor, corte e calçados. "
            "Nunca descreva só uma peça."
        ),
        "exemplo": (
            "wearing a COMPLETE red cotton t-shirt, dark green cargo shorts, "
            "white ankle socks, and red canvas sneakers, plus a silver analog watch."
        ),
    },
    {
        "id": "solda_textil",
        "nome": "Solda Têxtil",
        "severidade": "aviso",
        "explicacao": (
            "O personagem deve manter a mesma roupa em todas as cenas, "
            "a menos que a história peça troca de figurino."
        ),
        "exemplo": (
            "Se o morango começa com camiseta vermelha e shorts verdes, "
            "ele termina com as mesmas peças em todas as cenas."
        ),
    },
    {
        "id": "visual_motor",
        "nome": "Motor Visual 4K",
        "severidade": "aviso",
        "explicacao": (
            "O VISUAL_PROMPT deve usar linguagem cinematográfica: "
            "4K, PBR, iluminação volumétrica e SET travado."
        ),
        "exemplo": (
            "Cinematic 4K 3D animation. Hyper-realistic PBR textures. Volumetric lighting. "
            "SET: The dark interior of the palm-leaf shelter..."
        ),
    },
    {
        "id": "active_speaker",
        "nome": "Active Speaker (Lip-Sync)",
        "severidade": "info",
        "explicacao": (
            "Somente quem fala move a boca. O outro reage com expressão e postura, "
            "boca fechada. Mencionar isso no ACTION_DIRECTION ou PHYSICAL_MOVEMENT."
        ),
        "exemplo": (
            "Clean, non-overlapping sequential dialogue. "
            "Banana Female keeps mouth closed while Cara speaks, gripping his arm in fear."
        ),
    },
    {
        "id": "safety_filter",
        "nome": "Safety & Filter",
        "severidade": "erro",
        "explicacao": (
            "Substituir sangue/vinho por 'Deep purple sticky grape juice'. "
            "Substituir agressão física por gestos tensos ou confronto verbal."
        ),
        "exemplo": (
            "Em vez de 'blood on the floor' → 'Deep purple sticky grape juice on the floor'. "
            "Em vez de 'punch' → 'Sudden aggressive arm gesture'."
        ),
    },
    {
        "id": "pausa_dialogo",
        "nome": "Pausa entre falas",
        "severidade": "info",
        "explicacao": (
            "Pausas entre falas recomendadas em 0.2s. "
            "Outros valores são aceitos se fizerem sentido para a cena."
        ),
        "exemplo": '{"PAUSE": 0.2} entre cada fala no DIALOGUE_LINES.',
    },
    {
        "id": "duracao_cena",
        "nome": f"Duração de {DURACAO_CENA} segundos por cena",
        "severidade": "aviso",
        "explicacao": (
            f"Cada cena deve ter exatamente {DURACAO_CENA} segundos de vídeo. "
            f"O TIMESTAMP deve refletir blocos de {DURACAO_CENA}s sequenciais."
        ),
        "exemplo": (
            f"Cenas em blocos sequenciais de {DURACAO_CENA}s. "
            f"DURATION_SECONDS: {DURACAO_CENA} em todas."
        ),
    },
    {
        "id": "resolucao_video",
        "nome": f"Resolução {RESOLUCAO}",
        "severidade": "info",
        "explicacao": (
            f"Todo vídeo e imagem de referência deve ser gerado em {RESOLUCAO} "
            "no aspect ratio escolhido (9:16 ou 16:9)."
        ),
        "exemplo": (
            f"resolution: '{RESOLUCAO}', aspect_ratio: '9:16'. "
            f"AI_VIDEO_TASK: 'Create a {DURACAO_CENA}-second {RESOLUCAO} VIDEO...'"
        ),
    },
    {
        "id": "instrucoes_ia",
        "nome": "Instruções para agente de IA",
        "severidade": "info",
        "explicacao": (
            "O JSON deve conter ai_instructions e tarefas por item "
            "(ai_image_task no elenco, AI_VIDEO_TASK em cada cena)."
        ),
        "exemplo": (
            f"ai_image_task: 'AI AGENT: Create a {RESOLUCAO} reference IMAGE...' "
            f"AI_VIDEO_TASK: 'AI AGENT: Create a {DURACAO_CENA}-second {RESOLUCAO} VIDEO...'"
        ),
    },
    {
        "id": "sete_cenas",
        "nome": f"{DURACAO_TOTAL} segundos = {NUM_CENAS} cenas de {DURACAO_CENA}s",
        "severidade": "erro",
        "explicacao": (
            f"O vídeo completo tem {DURACAO_TOTAL} segundos, dividido em exatamente "
            f"{NUM_CENAS} cenas de {DURACAO_CENA} segundos cada."
        ),
        "exemplo": (
            f"SCENE_1 até SCENE_{NUM_CENAS}, em blocos de {DURACAO_CENA}s. "
            f"total_scenes: {NUM_CENAS}, total_duration_seconds: {DURACAO_TOTAL}."
        ),
    },
    {
        "id": "idioma_rigido",
        "nome": "Idioma do áudio (rigoroso)",
        "severidade": "erro",
        "explicacao": (
            "TODO texto em DIALOGUE_LINES > TEXT deve estar no idioma escolhido "
            "pelo usuário. PROIBIDO misturar ou usar outro idioma."
        ),
        "exemplo": (
            "Se idioma = Português: TEXT = 'Olha só, você não vai acreditar nisso!' "
            "VOICE_IDENTITY_LOCK deve conter 'Language: Portuguese (Brazil)'."
        ),
    },
    {
        "id": "dialogue_source",
        "nome": "Fonte do áudio: DIALOGUE_LINES > TEXT",
        "severidade": "erro",
        "explicacao": (
            "Todo áudio falado do vídeo vem exclusivamente do campo TEXT "
            "dentro de DIALOGUE_LINES. Nenhum outro campo gera voz."
        ),
        "exemplo": (
            'DIALOGUE_LINES: [{"SPEAKER": "Morango", "TEXT": "Isso é loucura!"}, '
            '{"PAUSE": 0.2}, {"SPEAKER": "Banana", "TEXT": "Eu sei..."}]'
        ),
    },
    {
        "id": "densidade_dialogo",
        "nome": "Densidade de diálogo (timing)",
        "severidade": "erro",
        "explicacao": (
            f"Cada cena de {DURACAO_CENA}s precisa de 4-6 falas curtas e áudio bem preenchido. "
            "A história deve ser contada pelo diálogo, preenchendo quase todo o clipe."
        ),
        "exemplo": (
            f"4-6 falas alternadas + pausas 0.2s, preenchendo ate perto dos {DURACAO_CENA}s. "
            "A meta de palavras/caracteres varia conforme o idioma."
        ),
    },
    {
        "id": "hook_2_segundos",
        "nome": "Hook nos primeiros 2 segundos",
        "severidade": "erro",
        "explicacao": (
            "A SCENE_1 deve começar com ação, diálogo ou gancho forte "
            "nos primeiros 2 segundos. Campo OPENING_HOOK obrigatório."
        ),
        "exemplo": (
            "OPENING_HOOK: 'Morango já entra gritando no segundo 0: Olha isso!' "
            "ou ação visual impactante imediata (explosão, revelação, confronto)."
        ),
    },
    {
        "id": "narrativa_coesa",
        "nome": "Narrativa coesa (começo, meio, fim)",
        "severidade": "erro",
        "explicacao": (
            "A história deve ter arco completo: início (cenas 1-2), meio (3-5), fim (6-7). "
            "Cada cena conecta com a anterior. NARRATIVE_BEAT e story_summary obrigatórios."
        ),
        "exemplo": (
            "story_summary: 'Morango descobre traição, confronta o parceiro, "
            "descobre que a amiga era cúmplice, e no final descobre que ela planejou tudo.' "
            "Cada NARRATIVE_BEAT avança essa cadeia."
        ),
    },
    {
        "id": "dialogo_narrativo",
        "nome": "Diálogo que conta a história",
        "severidade": "erro",
        "explicacao": (
            "Cada TEXT em DIALOGUE_LINES deve avançar o enredo — "
            "revelar algo, reagir ao anterior, ou criar tensão. Proibido filler."
        ),
        "exemplo": (
            "Ruim: 'Oi, tudo bem?' — Bom: 'Eu vi vocês dois no quarto ontem à noite!' "
            "O áudio sozinho deve contar a história."
        ),
    },
    {
        "id": "camera_detalhada",
        "nome": "Direção de câmera detalhada",
        "severidade": "aviso",
        "explicacao": (
            f"CAMERA_DIRECTION deve ter timeline 0-{DURACAO_CENA}s com shots, movimentos, zoom, "
            "ângulos e transições."
        ),
        "exemplo": (
            "0-3s: Wide shot. 3-8s: Dolly in. 8-12s: Rack focus. "
            f"12-{DURACAO_CENA}s: Zoom out reveal."
        ),
    },
    {
        "id": "trama_complexa",
        "nome": "Trama complexa com reviravoltas",
        "severidade": "aviso",
        "explicacao": (
            "A história deve ter conflito, reviravoltas e tensão crescente "
            f"para prender o espectador nos {DURACAO_TOTAL} segundos."
        ),
        "exemplo": (
            "SCENE_1 hook → SCENE_2-3 conflito → SCENE_4-5 reviravolta → "
            "SCENE_6 crise → SCENE_7 cliffhanger chocante."
        ),
    },
    {
        "id": "voice_registry",
        "nome": "Voice Registry canonico",
        "severidade": "erro",
        "explicacao": (
            "As vozes precisam vir de um registro unico do elenco. "
            "Cada fala deve copiar o SPEAKER, VOICE_IDENTITY_LOCK e metadata canonicos."
        ),
        "exemplo": (
            "SPEAKER: 'CARA' sempre usa o mesmo Voice Model, genero, peso vocal, "
            "TONE_PROFILE e FORCE_SYNTHESIS em todas as cenas."
        ),
    },
    {
        "id": "continuidade_causal",
        "nome": "Continuidade causal",
        "severidade": "erro",
        "explicacao": (
            "Cada cena precisa seguir o story contract: comecar como consequencia "
            "da cena anterior, entregar a revelacao planejada e plantar a proxima cena."
        ),
        "exemplo": (
            "Cena 3 revela a mentira prometida, Cena 4 usa essa mentira como reviravolta, "
            "Cena 5 mostra a consequencia direta."
        ),
    },
    {
        "id": "cliffhanger",
        "nome": "Cliffhanger (Parte 2)",
        "severidade": "info",
        "explicacao": (
            "A última cena deve deixar gancho para continuação, "
            "gerando curiosidade ou debate."
        ),
        "exemplo": (
            "Última fala: 'Espera... você ouviu isso?' enquanto uma sombra gigante "
            "aparece na porta — corte seco."
        ),
    },
    {
        "id": "antropomorfico",
        "nome": "DNA do personagem",
        "severidade": "aviso",
        "explicacao": (
            "Cada personagem precisa ter um DNA visual completo e coerente com o universo escolhido. "
            "O prompt deve travar silhueta, materiais/texturas, marcas visuais e proporções."
        ),
        "exemplo": (
            "Frutinha: morango vermelho com sementes e coroa verde. "
            "Carro: hatch vermelho com faróis expressivos e adesivo fixo. "
            "Prédio: fachada art-deco com janelas como olhos. "
            "Animal: capivara com pelagem castanha, cicatriz na orelha e mochila fixa."
        ),
    },
    {
        "id": "variedade_elenco",
        "nome": "Variedade do elenco",
        "severidade": "erro",
        "explicacao": (
            "O elenco deve ter 3-5 personagens com nomes e character_type distintos, "
            "explorando a variedade disponivel no universo selecionado."
        ),
        "exemplo": (
            "Evite quatro bananas ou quatro hatches quase iguais; combine especies/modelos, "
            "portes, silhuetas, idades, papeis e vozes contrastantes."
        ),
    },
]
