"""VELOCITY LONGFORM - 16:9 chapter lesson, brand and motion constants."""

import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

OUTPUT_DIR = BASE_DIR / "output"
LESSONS_DIR = OUTPUT_DIR / "lessons"
HISTORY_DIR = OUTPUT_DIR / "history"
SCENE_DIR = BASE_DIR / "scene"

VIDEO_WIDTH = 1920
VIDEO_HEIGHT = 1080
FPS = 30

TARGET_CHAPTERS = 8
PHRASES_PER_CHAPTER = 7
TARGET_PHRASES = TARGET_CHAPTERS * PHRASES_PER_CHAPTER

# ---------------------------------------------------------------- brand

BRAND = "VELOCITY DANISH"
BRAND_LOCKUP_TOP = "VELOCITY"
BRAND_LOCKUP_BOTTOM = "DANISH"
HANDLE = "@velocitydanish"
MASCOT_NAME = "Velo"

# ==== LANGUAGE PACK START ====
LANGUAGE = {'code': 'da',
 'name': 'Danish',
 'native_name': 'Dansk',
 'history_key': 'danish',
 'english_voice': 'en-US-AvaNeural',
 'english_fallback_voice': 'en-US-GuyNeural',
 'native_voice': 'da-DK-ChristelNeural',
 'native_fallback_voice': 'da-DK-JeppeNeural',
 'native_engine': 'edge',
 'native_lang_code': 'da',
 'english_rate': '-4%',
 'native_rate': '-10%',
 'english_pitch': '+0Hz',
 'native_pitch': '+0Hz',
 'native_label': 'DANSK',
 'translit_label': 'SAY IT LIKE',
 'flag': 'dk',
 'greeting': 'Hej!',
 'encouragement': 'Fantastisk!',
 'rtl': False,
 'char_tiles': False,
 'script_font': '',
 'glyphs': 'ABCDEFGHIJKLMNOPQRSTUVWXYZÆØÅæøå'}
# ==== LANGUAGE PACK END ====

# ==== CATEGORIES START ====
CATEGORIES = {'Motivation': 'Motivation',
 'Love': 'Kærlighed',
 'Success': 'Succes',
 'Wisdom': 'Visdom',
 'Happiness': 'Lykke',
 'Self Improvement': 'Selvudvikling',
 'Gratitude': 'Taknemmelighed',
 'Friendship': 'Venskab',
 'Hope': 'Håb',
 'Creativity': 'Kreativitet',
 'Inner Peace': 'Indre Fred',
 'Confidence': 'Selvtillid',
 'Perseverance': 'Udholdenhed',
 'Inspiration': 'Inspiration',
 'Positive Life': 'Positivt Liv',
 'Courage': 'Mod',
 'Kindness': 'Venlighed',
 'Patience': 'Tålmodighed',
 'Forgiveness': 'Tilgivelse',
 'Strength': 'Styrke',
 'Joy': 'Glæde',
 'Balance': 'Balance',
 'Growth': 'Vækst',
 'Purpose': 'Formål',
 'Mindfulness': 'Opmærksomhed',
 'Travel & Airport': 'Rejser & Lufthavn',
 'Ordering Food & Dining': 'Bestilling af mad & Spisning',
 'Shopping & Prices': 'Shopping & Priser',
 'Asking for Directions': 'At spørge om vej',
 'Hotel & Accommodation': 'Hotel & Overnatning',
 'Daily Routine': 'Daglig rutine',
 'Meeting People & Greetings': 'At møde folk & Hilsner',
 'Emergency & Health': 'Nødsituationer & Sundhed',
 'Public Transportation': 'Offentlig transport',
 'Work & Office': 'Arbejde & Kontor',
 'Weather & Small Talk': 'Vejr & Småsnak',
 'Coffee Shop & Bakery': 'Kaffebar & Bageri',
 'Family & Home': 'Familie & Hjem',
 'Hobbies & Free Time': 'Hobbyer & Fritid',
 'Dating & Romance': 'Dating & Romantik',
 'Phone Calls & Messages': 'Telefonopkald & Beskeder',
 'Banking & Money': 'Bank & Penge',
 'Doctor & Pharmacy': 'Læge & Apotek',
 'Sports & Fitness': 'Sport & Fitness',
 'Celebrations & Parties': 'Fejringer & Fester',
 'Feelings & Emotions': 'Følelser & Stemninger',
 'Agreeing & Disagreeing': 'At være enig & Uenig',
 'Making Plans': 'At lave planer',
 'Common Native Slang': 'Almindelig slang',
 'Cultural Traditions': 'Kulturelle traditioner'}
# ==== CATEGORIES END ====

CATEGORY_NAMES = list(CATEGORIES.keys())

AI_MODEL = os.getenv("AI_MODEL", "openai/gpt-5.4-nano")
AI_FALLBACK_MODEL = os.getenv("AI_FALLBACK_MODEL", "gemini-fast")
POLLINATIONS_API_KEY = os.getenv("POLLINATIONS_API_KEY", "")

# ---------------------------------------------------------------- timing (seconds)

INTRO_DURATION = 7.2
CHAPTER_INTRO_DURATION = 4.4
OUTRO_DURATION = 13.0

EN_CARD_IN = 0.70
GAP_EN_NATIVE = 0.60
NATIVE_CARD_LEAD = 0.40
GAP_BEFORE_REPEAT = 1.00
TAIL_HOLD = 1.30

# ---------------------------------------------------------------- palette

INK = "#30303A"
MUTED = "#8A8A8A"
CREAM = "#FFF8E7"
GREEN = "#58CC02"
GREEN_DARK = "#46A302"
GREEN_DEEP = "#3D8F00"
BLUE = "#1CB0F6"
PURPLE = "#7C5CFF"
ORANGE = "#FF7A00"
RED = "#FF4B4B"
YELLOW = "#F5A700"
TEAL = "#00A889"
PINK = "#E056A0"

# ==== HASHTAGS START ====
HASHTAGS = ['#learndanish',
 '#danishlessons',
 '#danishforbeginners',
 '#languagelearning',
 '#danishvocabulary',
 '#velocitydanish',
 '#dailydanish',
 '#danish',
 '#learnlanguages',
 '#speakdanish']
# ==== HASHTAGS END ====
