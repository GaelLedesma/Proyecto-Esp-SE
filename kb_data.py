kb_base = {
    ("harry", "hermione"): "amigos",
    ("harry", "ron"): "mejores amigos",
    ("harry", "voldemort"): "archienemigos",
    ("harry", "dumbledore"): "mentor",
    ("harry", "snape"): "relación compleja",
    ("harry", "draco"): "rivales",
    ("harry", "sirius"): "ahijado y padrino",
    ("harry", "hagrid"): "protector",
    ("harry", "luna"): "amigos",
    ("harry", "ginny"): "pareja",
    ("harry", "neville"): "compañeros",
    ("hermione", "ron"): "pareja",
    ("hermione", "hagrid"): "amigos",
    ("hermione", "draco"): "enemigos",
    ("hermione", "ginny"): "amigas",
    ("ron", "ginny"): "hermanos",
    ("ron", "dumbledore"): "aliados",
    ("ron", "draco"): "enemigos",
    ("voldemort", "dumbledore"): "enemigos",
    ("voldemort", "bellatrix"): "aliados",
    ("voldemort", "snape"): "alianza tensa",
    ("snape", "lily"): "amor",
    ("snape", "dumbledore"): "aliados secretos",
    ("draco", "lucius"): "padre e hijo",
    ("draco", "narcissa"): "madre e hijo",
    ("sirius", "lupin"): "amigos",
    ("fred", "george"): "hermanos gemelos",
    ("james", "lily"): "pareja",
    ("james", "snape"): "enemigos",
    ("cedric", "harry"): "rivales amistosos",
}


equivalentes = {
    # harry
    "hari": "harry",
    "jari": "harry",
    "ari": "harry",
    "harri": "harry",
    "jarry": "harry",
    "hary": "harry",
    "happy": "harry",

    # hermione
    "hermio": "hermione",
    "ermio": "hermione",
    "ermione": "hermione",
    "hermion": "hermione",
    "hermionee": "hermione",
    "mione": "hermione",

    # ron
    "rom": "ron",
    "roon": "ron",
    "bron": "ron",

    # voldemort
    "voldemor": "voldemort",
    "boldemort": "voldemort",
    "volde": "voldemort",

    # dumbledore
    "dumbladore": "dumbledore",
    "dumbeldore": "dumbledore",
    "dumbledor": "dumbledore",
    "dumbador": "dumbledore",

    # sirius
    "siriu": "sirius",

    # snape
    "esneip": "snape",
    "sneip": "snape",
    "Snape": "snape",

    # hagrid
    "jagrid": "hagrid",
    "agrid": "hagrid",

    # draco
    "drako": "draco",

    # ginny
    "gini": "ginny",

    # lupin
    "lupen": "lupin",

    # neville
    "nevil": "neville",

    # bellatrix
    "belatrix": "bellatrix",

    # lucius
    "lusius": "lucius",

    # narcissa
    "narsisa": "narcissa",

    # cedric
    "cedrik": "cedric",
}

system_prompt = (
        "Eres un asistente de voz inteligente integrado en un dispositivo.\n"
        "Responde SIEMPRE en español.\n"
        "\n"
        "Reglas:\n"
        "- Responde de forma breve, clara y natural (máximo 1-2 frases).\n"
        "- No inventes código.\n"
        "- Solo responde con código si el usuario dice explícitamente la palabra 'codigo'.\n"
        "- Si generas código, devuelve SOLO el código sin explicaciones.\n"
        "- Si NO es código, responde como una persona normal, sin mencionar que eres una IA.\n"
        "- Evita respuestas largas o técnicas innecesarias.\n"
        "\n"
        "Contexto:\n"
        "- El usuario habla por voz.\n"
        "- La respuesta puede convertirse en audio, así que debe sonar natural.\n"
    )