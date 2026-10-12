"""Safety layers for Soi Sacré – Rituel du jour.

Implements the code side of guardrails.md:
- distress pre-check on free text
- output validation (structure, durations, forbidden words)
- pre-written care responses and fallback rituals
"""
import os
import re
import unicodedata

# ---------------------------------------------------------------- helpers


def normalize(text: str) -> str:
    """Lowercase, strip accents, unify apostrophes."""
    text = text.replace("\u2019", "'").replace("\u2018", "'")
    text = unicodedata.normalize("NFKD", text.lower())
    return "".join(c for c in text if not unicodedata.combining(c))


# ---------------------------------------------------------------- distress
# Err on the side of caution: a false positive shows a gentle care message,
# a false negative could miss someone in real distress.
# NOTE: review and extend this list with a native speaker (Darija / Arabic).
DISTRESS_PATTERNS = [
    # French
    r"suicid", r"me tuer", r"en finir", r"envie de mourir", r"veux mourir",
    r"veux disparaitre", r"plus envie de vivre", r"plus envie d'exister",
    r"peux plus de vivre", r"me faire du mal", r"automutil", r"me scarifi",
    r"tout est fini", r"aucun espoir", r"plus aucun sens", r"plus de raison de vivre",
    r"me frappe", r"me bat\b", r"\bviol(e|ee|ence|ences|er|ent|ente)?\b",
    r"\babus(e|ee|er|ive|if)?\b", r"crise de panique", r"attaque de panique",
    r"anorex", r"boulimi", r"me faire vomir", r"j'ai peur de lui",
    # English
    r"kill myself", r"end my life", r"want to die", r"wanna die", r"disappear forever",
    r"self[- ]?harm", r"hurt myself", r"no reason to live", r"hopeless",
    r"hits me", r"beats me", r"panic attack", r"don't want to live",
    # Darija (Latin script) / Arabic
    r"nmout", r"n9tel rwahi", r"bghit nmout", r"nheb nmout",
    "\u0627\u0646\u062a\u062d\u0627\u0631", "\u0627\u0645\u0648\u062a", "\u0623\u0645\u0648\u062a",
    "\u0627\u0642\u062a\u0644 \u0646\u0641\u0633\u064a",
]
_DISTRESS_RE = re.compile("|".join(DISTRESS_PATTERNS))


def check_distress(text: str | None) -> bool:
    if not text:
        return False
    return bool(_DISTRESS_RE.search(normalize(text)))


# ---------------------------------------------------------------- output rules
GUILT_PATTERNS = [
    r"tu dois", r"il faut", r"n'oublie pas", r"noublie pas", r"tu devrais",
    r"you must", r"you should", r"don't forget", r"dont forget", r"you need to",
    r"\bmust\b",
]
BLOCKED_PATTERNS = [
    r"diagnosti", r"traitement", r"medicament", r"therapie", r"\bregime\b",
    r"perte de poids", r"detox", r"gueri", r"anxiolytique", r"antidepresseur",
    r"calories?", r"\bdiet\b", r"medication", r"therapy", r"weight loss",
    r"treatment", r"diagnos", r"\bcure\b", r"supplement", r"complement alimentaire",
]
_GUILT_RE = re.compile("|".join(GUILT_PATTERNS))
_BLOCKED_RE = re.compile("|".join(BLOCKED_PATTERNS))


def validate_ritual(out: dict, time_minutes: int) -> list[str]:
    """Return a list of problems; empty list means the ritual is valid."""
    problems: list[str] = []
    expected_keys = {"status", "title", "reassurance", "total_duration_minutes",
                     "steps", "beauty_gesture", "mantra"}
    if not isinstance(out, dict) or out.get("status") != "ritual":
        return ["not a ritual object"]
    if set(out.keys()) != expected_keys:
        problems.append("unexpected or missing keys")
        return problems

    for key in ("title", "reassurance", "beauty_gesture", "mantra"):
        if not isinstance(out[key], str) or not out[key].strip():
            problems.append(f"{key} empty")
    if problems:
        return problems

    if out["total_duration_minutes"] != time_minutes:
        problems.append("total duration does not match requested time")

    steps = out["steps"]
    if not isinstance(steps, list):
        return problems + ["steps not a list"]
    min_steps = 3
    if not (min_steps <= len(steps) <= 5):
        problems.append("steps count must be 3 to 5")
    total = 0.0
    texts = [out["title"], out["reassurance"], out["beauty_gesture"], out["mantra"]]
    for s in steps:
        if not isinstance(s, dict) or set(s.keys()) != {"action", "duration_minutes"}:
            problems.append("bad step shape")
            continue
        if not isinstance(s["action"], str) or not s["action"].strip():
            problems.append("empty step action")
            continue
        d = s["duration_minutes"]
        if not isinstance(d, (int, float)) or isinstance(d, bool) or d <= 0:
            problems.append("bad step duration")
            continue
        total += d
        texts.append(s["action"])
    if abs(total - time_minutes) > 0.01:
        problems.append("step durations do not sum to total")

    if len(out["title"]) > 60 or len(out["mantra"]) > 100:
        problems.append("title or mantra too long")

    joined = normalize(" ".join(texts))
    if _GUILT_RE.search(joined):
        problems.append("pressure/guilt wording")
    if _BLOCKED_RE.search(joined):
        problems.append("medical wording")
    return problems


# ---------------------------------------------------------------- care response
_CARE = {
    "fr": {
        "message": ("Merci de t'être confiée. Ce que tu traverses compte, et tu mérites "
                    "d'être entourée avec douceur. Ce moment n'est pas fait pour un rituel aujourd'hui."),
        "suggestion": ("Si tu en as la force, parle à une personne de confiance ou à un "
                       "professionnel de santé. Tu n'as pas à porter cela seule."),
    },
    "en": {
        "message": ("Thank you for trusting me with this. What you are going through matters, "
                    "and you deserve to be supported gently. A ritual is not what this moment needs today."),
        "suggestion": ("If you can, talk to someone you trust or a health professional. "
                       "You don't have to carry this alone."),
    },
}


def care_response(lang: str = "fr") -> dict:
    base = _CARE.get(lang, _CARE["fr"])
    suggestion = base["suggestion"]

    urgent_text = {
        "fr": (
            "Si tu es en danger immédiat, éloigne-toi du danger si tu peux "
            "le faire sans risque et contacte les services d'urgence locaux."
        ),
        "en": (
            "If you are in immediate danger, move away from the danger if "
            "you can do so safely and contact local emergency services."
        ),
    }

    suggestion = f"{suggestion} {urgent_text.get(lang, urgent_text['fr'])}"

    helpline = os.getenv("HELPLINE_TEXT", "").strip()
    if helpline:
        suggestion = f"{suggestion} {helpline}"

    return {
        "status": "care",
        "message": base["message"],
        "suggestion": suggestion,
    }


# ---------------------------------------------------------------- fallback rituals
_FALLBACK = {
    "fr": {
        2: {
            "title": "Un souffle pour toi",
            "reassurance": "Tu as le droit de t'arrêter deux minutes, sans rien prouver à personne. Ce moment t'appartient.",
            "steps": [
                {"action": "Laisse tes épaules descendre et ferme les yeux.", "duration_minutes": 0.5},
                {"action": "Respire lentement trois fois, en allongeant l'expiration.", "duration_minutes": 1},
                {"action": "Pose une main sur ton cœur et souris doucement.", "duration_minutes": 0.5},
            ],
            "beauty_gesture": "Masse tes tempes du bout des doigts, puis détends ta mâchoire.",
            "mantra": "Je m'accorde ce moment avec douceur.",
        },
        5: {
            "title": "Une pause lumineuse",
            "reassurance": "Prendre soin de toi n'est pas une tâche de plus. C'est une permission que tu peux t'offrir.",
            "steps": [
                {"action": "Installe-toi confortablement et relâche ta mâchoire.", "duration_minutes": 1},
                {"action": "Savoure lentement une gorgée d'eau ou de thé.", "duration_minutes": 1},
                {"action": "Inspire sur quatre temps, expire sur six, au rythme qui te va.", "duration_minutes": 2},
                {"action": "Masse tes mains avec une crème, doigt après doigt.", "duration_minutes": 1},
            ],
            "beauty_gesture": "Un massage des mains, lent et enveloppant, avec ta crème préférée.",
            "mantra": "Je mérite la douceur, maintenant.",
        },
        10: {
            "title": "Mon refuge du soir",
            "reassurance": "Tu n'as rien à mériter pour te poser. Ces dix minutes sont à toi, simplement.",
            "steps": [
                {"action": "Trouve un coin calme et installe-toi, sans te presser.", "duration_minutes": 1},
                {"action": "Respire profondément, en laissant le souffle te bercer.", "duration_minutes": 2},
                {"action": "Étire doucement ta nuque et tes épaules.", "duration_minutes": 3},
                {"action": "Rafraîchis ton visage avec un peu d'eau fraîche.", "duration_minutes": 2},
                {"action": "Écris une phrase douce pour toi sur un papier.", "duration_minutes": 2},
            ],
            "beauty_gesture": "Lisse ton visage de l'intérieur vers l'extérieur, du bout des doigts, avec lenteur.",
            "mantra": "Je me retrouve, à mon rythme.",
        },
    },
    "en": {
        2: {
            "title": "A breath for you",
            "reassurance": "You are allowed to pause for two minutes without proving anything to anyone. This moment is yours.",
            "steps": [
                {"action": "Let your shoulders drop and close your eyes.", "duration_minutes": 0.5},
                {"action": "Breathe slowly three times, lengthening the exhale.", "duration_minutes": 1},
                {"action": "Rest a hand on your heart and smile softly.", "duration_minutes": 0.5},
            ],
            "beauty_gesture": "Massage your temples with your fingertips, then soften your jaw.",
            "mantra": "I give myself this moment, gently.",
        },
        5: {
            "title": "A luminous pause",
            "reassurance": "Caring for yourself is not one more task. It is a permission you can offer yourself.",
            "steps": [
                {"action": "Settle comfortably and release your jaw.", "duration_minutes": 1},
                {"action": "Slowly enjoy a sip of water or tea.", "duration_minutes": 1},
                {"action": "Breathe in for four, out for six, at whatever pace suits you.", "duration_minutes": 2},
                {"action": "Massage your hands with cream, one finger at a time.", "duration_minutes": 1},
            ],
            "beauty_gesture": "A slow, wrapping hand massage with your favorite cream.",
            "mantra": "I deserve gentleness, right now.",
        },
        10: {
            "title": "My evening refuge",
            "reassurance": "You don't have to earn the right to rest. These ten minutes are simply yours.",
            "steps": [
                {"action": "Find a quiet corner and settle in, without hurrying.", "duration_minutes": 1},
                {"action": "Breathe deeply and let your breath rock you.", "duration_minutes": 2},
                {"action": "Gently stretch your neck and shoulders.", "duration_minutes": 3},
                {"action": "Refresh your face with a little cool water.", "duration_minutes": 2},
                {"action": "Write one kind sentence to yourself on paper.", "duration_minutes": 2},
            ],
            "beauty_gesture": "Smooth your face from the center outward with your fingertips, slowly.",
            "mantra": "I find my way back, at my own pace.",
        },
    },
}


def fallback_ritual(time_minutes: int, lang: str = "fr") -> dict:
    data = _FALLBACK.get(lang, _FALLBACK["fr"])[time_minutes]
    return {"status": "ritual", "total_duration_minutes": time_minutes, **data}
