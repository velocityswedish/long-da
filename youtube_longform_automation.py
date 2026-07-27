"""
YouTube Long-Form Video Automation - Bilingual English/Danish Content Generator
GENERATES 10-MINUTE VIDEOS with improved backgrounds for YouTube
"""

import os
import sys
import json
import random
import asyncio
import subprocess
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

load_dotenv()

POLLINATIONS_API_KEY = os.getenv("POLLINATIONS_API_KEY")

# Directories
BASE_DIR = Path(__file__).parent
OUTPUT_DIR = BASE_DIR / "output"
IMAGES_DIR = OUTPUT_DIR / "images"
AUDIO_DIR = OUTPUT_DIR / "audio"
VIDEO_DIR = OUTPUT_DIR / "video"
HISTORY_DIR = OUTPUT_DIR / "history"
LONGFORM_DIR = OUTPUT_DIR / "longform_videos"

for d in [OUTPUT_DIR, IMAGES_DIR, AUDIO_DIR, VIDEO_DIR, HISTORY_DIR, LONGFORM_DIR]:
    d.mkdir(exist_ok=True)

# Video settings (16:9 horizontal for YouTube long-form)
VIDEO_WIDTH = 1920
VIDEO_HEIGHT = 1080
FPS = 30
TARGET_DURATION_MINUTES = 5
TARGET_PHRASES = 120

# English category names
CATEGORIES_ENGLISH = [
    "Motivation", "Love", "Success", "Wisdom", "Happiness",
    "Self Improvement", "Gratitude", "Friendship", "Hope", "Creativity",
    "Inner Peace", "Confidence", "Perseverance", "Inspiration", "Positive Life",
    "Courage", "Kindness", "Patience", "Forgiveness", "Strength",
    "Joy", "Balance", "Growth", "Purpose", "Mindfulness",
]

# Danish translations
CATEGORIES_DANISH = {
    "Motivation": "Motivation",
    "Love": "Kærlighed",
    "Success": "Succes",
    "Wisdom": "Visdom",
    "Happiness": "Lykke",
    "Self Improvement": "Selvudvikling",
    "Gratitude": "Taknemmelighed",
    "Friendship": "Venskab",
    "Hope": "Håb",
    "Creativity": "Kreativitet",
    "Inner Peace": "Indre Fred",
    "Confidence": "Selvtillid",
    "Perseverance": "Udholdenhed",
    "Inspiration": "Inspiration",
    "Positive Life": "Positivt Liv",
    "Courage": "Mod",
    "Kindness": "Venlighed",
    "Patience": "Tålmodighed",
    "Forgiveness": "Tilgivelse",
    "Strength": "Styrke",
    "Joy": "Glæde",
    "Balance": "Balance",
    "Growth": "Vækst",
    "Purpose": "Formål",
    "Mindfulness": "Opmærksomhed",
}

# Edge TTS voices
ENGLISH_VOICE = "en-US-GuyNeural"
LANG_VOICE = "da-DK-ChristelNeural"

# Phrase history file
PHRASE_HISTORY_FILE = HISTORY_DIR / "all_generated_phrases.json"

# Viral hook styles for engagement
VIRAL_STYLES = [
    "surprising fact",
    "common mistake correction",
    "quick tip",
    "must-know phrase",
    "local secret",
    "travel hack",
    "flirty phrase",
    "funny expression",
    "cultural insight",
    "word origin story"
]

# AI Model
AI_MODEL = os.getenv("AI_MODEL")

if not AI_MODEL:
    raise ValueError(
        "AI_MODEL not set! Please add 'AI_MODEL=gemini-fast' to your .env file."
    )


# ============== PHRASE HISTORY MANAGEMENT ==============

def load_phrase_history():
    if PHRASE_HISTORY_FILE.exists():
        with open(PHRASE_HISTORY_FILE, "r", encoding="utf-8-sig") as f:
            return json.load(f)
    return {"phrases": [], "last_updated": None}


def save_phrase_history(data):
    data["last_updated"] = datetime.now().isoformat()
    with open(PHRASE_HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def is_phrase_used(english_phrase):
    history = load_phrase_history()
    english_lower = english_phrase.lower().strip()
    for p in history.get("phrases", []):
        if p.get("english", "").lower().strip() == english_lower:
            return True
    return False


def is_phrase_similar(new_phrase, used_phrases, similarity_threshold=0.6):
    new_words = set(new_phrase.lower().split())
    if len(new_words) < 3:
        for used in used_phrases:
            if new_phrase.lower() in used.lower() or used.lower() in new_phrase.lower():
                return True
        return False
    for used in used_phrases:
        used_words = set(used.lower().split())
        if len(new_words) == 0 or len(used_words) == 0:
            continue
        intersection = len(new_words.intersection(used_words))
        union = len(new_words.union(used_words))
        similarity = intersection / union if union > 0 else 0
        if similarity >= similarity_threshold:
            return True
    return False


def filter_similar_phrases(phrases, history, similarity_threshold=0.6):
    used_phrases = [p.get("english", "") for p in history.get("phrases", [])]
    unique_phrases = []
    for phrase in phrases:
        english_text = phrase.get("english", "")
        if not is_phrase_similar(english_text, used_phrases, similarity_threshold):
            unique_phrases.append(phrase)
        else:
            print(f"[filter] Skipping similar: {english_text[:50]}...")
    return unique_phrases


def add_phrases_to_history(phrases, category):
    history = load_phrase_history()
    for phrase in phrases:
        history["phrases"].append({
            "english": phrase["english"],
            "danish": phrase["danish"],
            "category": category,
            "generated_at": datetime.now().isoformat()
        })
    save_phrase_history(history)
    print(f"[history] Added {len(phrases)} phrases to history (total: {len(history['phrases'])})")


# ============== CONTENT GENERATION ==============

def calculate_phrases_needed(target_minutes: int) -> int:
    avg_phrase_duration = 5.0
    total_seconds = target_minutes * 60
    return int(total_seconds / avg_phrase_duration)


def generate_phrases_for_longform(category_english: str, num_phrases: int) -> list:
    category_danish = CATEGORIES_DANISH[category_english]
    history = load_phrase_history()
    used_phrases = [p.get("english", "") for p in history.get("phrases", [])]
    viral_style = random.choice(VIRAL_STYLES)
    all_phrases = []
    batch_size = 20
    max_attempts = 5

    for batch_num in range((num_phrases + batch_size - 1) // batch_size):
        remaining = num_phrases - len(all_phrases)
        current_batch_size = min(batch_size, remaining)
        if current_batch_size <= 0:
            break
        for attempt in range(max_attempts):
            try:
                import requests
                url = "https://gen.pollinations.ai/v1/chat/completions"
                headers = {
                    "Authorization": f"Bearer {POLLINATIONS_API_KEY}",
                    "Content-Type": "application/json"
                }
                exclusion_note = ""
                if used_phrases:
                    recent = used_phrases[-30:] if len(used_phrases) > 30 else used_phrases
                    exclusion_note = f"\n\nAVOID these phrases (already used): {recent}"

                prompt = f"""Create {current_batch_size * 2} unique {category_english} phrases for English speakers learning Danish.

Style: Make each phrase feel like a {viral_style} - something people would want to share!

CRITICAL RULE - ABSOLUTELY ZERO Danish IN ENGLISH FIELD:
The "english" field must contain ONLY English words. NO Danish words at all.
The "danish" field contains the Danish translation.
The "pronunciation" field is phonetic English spelling approximating Danish sounds.

These are INSPIRATIONAL PHRASES about the topic, NOT language-learning tips.

WRONG (teaching tip with Danish words): {{"english": "Don't say 'ha' det godt,' it means more than 'goodbye.'", ...}}
WRONG (Danish word in english): {{"english": "Use 'tak' for thank you", ...}}
WRONG (lesson tip): {{"english": "Say 'v\u00e6r s\u00e5 venlig' for please", ...}}
CORRECT (pure english phrase): {{"english": "Knowledge is the key to wisdom.", "danish": "Kundskab er n\u00f8glen til visdom", "pronunciation": "kund-skab er n\u00f8g-len til vis-dom"}}
CORRECT: {{"english": "A wise person listens more than they speak.", "danish": "En vis person lytter mere end de taler", "pronunciation": "en vis per-son lyt-ter me-re end de ta-ler"}}

The english field MUST be 100% English words only. Absolutely NO Danish words in the english field.

IMPORTANT RULES FOR NATURAL SPEECH:
1. Keep phrases SHORT (5-12 words max per language)
2. Add NATURAL PAUSES using commas (e.g., "Dream big, start small")
3. Use punctuation for breathing room in TTS
4. Avoid long run-on sentences
5. Each phrase should be speakable in 3-5 seconds
6. Use everyday vocabulary - avoid exotic or rare words
7. Avoid complex grammar - keep it simple and practical
8. Vary sentence structure for natural flow

For each phrase:
1. English phrase (pure English, zero Danish words) with commas for natural pauses
2. Danish translation
3. Pronunciation guide (phonetic English spelling)

Return as JSON array:
[{{"english": "...", "danish": "...", "pronunciation": "..."}}]

IMPORTANT: Create FRESH, UNIQUE phrases that haven't been used before.{exclusion_note}"""

                payload = {
                    "model": AI_MODEL,
                    "messages": [
                        {"role": "system", "content": "You create INSPIRATIONAL PHRASES for YouTube language learning videos. CRITICAL: The 'english' field must be PURE ENGLISH with ZERO Danish words - no Danish words at all. These are universal inspirational phrases, NOT language learning tips. Danish goes ONLY in the 'danish' field."},
                        {"role": "user", "content": prompt}
                    ],
                    "temperature": 1.0
                }

                response = requests.post(url, headers=headers, json=payload, timeout=90)
                response.raise_for_status()

                data = response.json()
                content = data["choices"][0]["message"]["content"].strip()

                if "```json" in content:
                    content = content.split("```json")[1].split("```")[0].strip()
                elif "```" in content:
                    content = content.split("```")[1].split("```")[0].strip()

                phrases = json.loads(content)
                filtered_phrases = filter_similar_phrases(phrases, history)
                unique_phrases = []
                for phrase in filtered_phrases:
                    if len(phrase["english"].split()) > 15:
                        continue
                    if not is_phrase_used(phrase["english"]):
                        unique_phrases.append(phrase)
                for phrase in unique_phrases:
                    if len(all_phrases) < num_phrases:
                        all_phrases.append(phrase)
                if len(all_phrases) >= num_phrases:
                    break
            except Exception as e:
                print(f"[content] Batch {batch_num + 1}, Attempt {attempt + 1} failed: {e}")
        if len(all_phrases) < num_phrases:
            import time
            time.sleep(1)

    final_phrases = all_phrases[:num_phrases]
    if final_phrases:
        add_phrases_to_history(final_phrases, category_english)
    print(f"[content] Generated {len(final_phrases)} phrases for long-form video")
    return final_phrases


def get_fresh_fallback_phrases(category: str, num_phrases: int) -> list:
    all_fallbacks = {
        "Motivation": [
            {"english": "Believe in yourself.", "danish": "Tro p\u00e5 dig selv.", "pronunciation": "tro p\u00e5 dij selv"},
            {"english": "You are capable of amazing things.", "danish": "Du er i stand til fantastiske ting.", "pronunciation": "du er i stan til fan-tas-tis-ke ting"},
            {"english": "Dream big, start small.", "danish": "Dr\u00f8m stort, start sm\u00e5t.", "pronunciation": "dr\u00f8m stort, start sm\u00e5t"},
            {"english": "Your future is created by your actions.", "danish": "Fremtiden din skabes af dine handlinger.", "pronunciation": "frem-ti-den din ska-bes af di-ne hand-ling-er"},
            {"english": "Never give up on your dreams.", "danish": "Giv aldrig op p\u00e5 dr\u00f8mmene dine.", "pronunciation": "giv al-drig op p\u00e5 dr\u00f8m-me-ne di-ne"},
            {"english": "Small steps lead to big changes.", "danish": "Sm\u00e5 skridt f\u00f8rer til store \u00e6ndringer.", "pronunciation": "sm\u00e5 skrid f\u00f8-rer til sto-re \u00e6nd-ring-er"},
            {"english": "You are stronger than you think.", "danish": "Du er st\u00e6rkere end du tror.", "pronunciation": "du er st\u00e6r-ke-re en du tror"},
        ],
        "Love": [
            {"english": "Love yourself first.", "danish": "Elsk dig selv f\u00f8rst.", "pronunciation": "elsk dij selv f\u00f8rst"},
            {"english": "Love makes everything possible.", "danish": "K\u00e6rlighed g\u00f8r alt muligt.", "pronunciation": "k\u00e6r-lig-hed g\u00f8r alt mu-ligt"},
            {"english": "My heart beats for you.", "danish": "Mit hjerte sl\u00e5r for dig.", "pronunciation": "mit hjer-te sl\u00e5r for dij"},
            {"english": "You are my everything.", "danish": "Du er alt for mig.", "pronunciation": "du er alt for mej"},
            {"english": "Together forever, hand in hand.", "danish": "Sammen for altid, h\u00e5nd i h\u00e5nd.", "pronunciation": "sam-men for al-tid, h\u00e5nd i h\u00e5nd"},
        ],
        "Success": [
            {"english": "Success comes from hard work.", "danish": "Succes kommer fra h\u00e5rdt arbejde.", "pronunciation": "suk-ses kom-mer fr\u00e5 h\u00e5rdt ar-bej-de"},
            {"english": "Keep going, you're getting there.", "danish": "Forts\u00e6t, du n\u00e6rmer dig.", "pronunciation": "for-ts\u00e6t, du n\u00e6r-mer dij"},
            {"english": "Winners never quit.", "danish": "Vindere giver aldrig op.", "pronunciation": "vin-de-re gi-ver al-drig op"},
            {"english": "Your effort will pay off.", "danish": "Din indsats vil l\u00f8nne sig.", "pronunciation": "din ind-sats vil l\u00f8n-ne sej"},
        ],
        "Wisdom": [
            {"english": "Knowledge is power.", "danish": "Kundskab er magt.", "pronunciation": "kund-skab er magt"},
            {"english": "Learn from yesterday, live for today.", "danish": "L\u00e6r fra i g\u00e5r, lev for i dag.", "pronunciation": "l\u00e6r fra i g\u00e5r, lev for i dag"},
            {"english": "Think before you act.", "danish": "T\u00e6nk f\u00f8r du handler.", "pronunciation": "t\u00e6nk f\u00f8r du hand-ler"},
            {"english": "Experience is the best teacher.", "danish": "Erfaring er den bedste l\u00e6rer.", "pronunciation": "er-fa-ring er den bed-ste l\u00e6-rer"},
        ],
        "Happiness": [
            {"english": "Happiness is a choice.", "danish": "Lykke er et valg.", "pronunciation": "lyk-ke er et valg"},
            {"english": "Find joy in the little things.", "danish": "Find gl\u00e6de i de sm\u00e5 ting.", "pronunciation": "find gle-de i de sm\u00e5 ting"},
            {"english": "Smile, it makes others happy.", "danish": "Smil, det g\u00f8r andre glade.", "pronunciation": "smil, det g\u00f8r an-dre gla-de"},
            {"english": "Today is a gift.", "danish": "I dag er en gave.", "pronunciation": "i dag er en ga-ve"},
        ],
        "Self Improvement": [
            {"english": "Be better than yesterday.", "danish": "V\u00e6r bedre end i g\u00e5r.", "pronunciation": "v\u00e6r bed-re en i g\u00e5r"},
            {"english": "Grow through what you go through.", "danish": "Voks gennem det du g\u00e5r gennem.", "pronunciation": "voks gen-nem det du g\u00e5r gen-nem"},
            {"english": "Invest in yourself daily.", "danish": "Invest\u00e9r i dig selv dagligt.", "pronunciation": "in-ves-t\u00e9r i dij selv dag-ligt"},
        ],
        "Gratitude": [
            {"english": "Thank you for everything.", "danish": "Tak for alt.", "pronunciation": "tak for alt"},
            {"english": "I appreciate your help.", "danish": "Jeg s\u00e6tter pris p\u00e5 din hj\u00e6lp.", "pronunciation": "jeg set-ter pris p\u00e5 din hj\u00e6lp"},
            {"english": "Grateful for this moment.", "danish": "Taknemmelig for dette \u00f8jeblik.", "pronunciation": "tak-nem-me-lig for det-te \u00f8je-blik"},
        ],
        "Friendship": [
            {"english": "Friends forever, no matter what.", "danish": "Venner for altid, uanset hvad.", "pronunciation": "ven-ner for al-tid, uan-set hvad"},
            {"english": "You are my best friend.", "danish": "Du er min bedste ven.", "pronunciation": "du er min bed-ste ven"},
            {"english": "True friends stick together.", "danish": "\u00c6gte venner holder sammen.", "pronunciation": "\u00e6g-te ven-ner hol-der sam-men"},
        ],
        "Hope": [
            {"english": "There is always hope.", "danish": "Der er altid h\u00e5b.", "pronunciation": "der er al-tid h\u00e5b"},
            {"english": "Better days are coming.", "danish": "Bedre dage kommer.", "pronunciation": "bed-re da-ge kom-mer"},
            {"english": "Keep faith, keep going.", "danish": "Behold troen, forts\u00e6t.", "pronunciation": "be-hold tro-en, fort-s\u00e6t"},
        ],
        "Creativity": [
            {"english": "Create something beautiful today.", "danish": "Skab noget smukt i dag.", "pronunciation": "skab no-get smukt i dag"},
            {"english": "Your imagination is unlimited.", "danish": "Din fantasi er ubegr\u00e6nset.", "pronunciation": "din fan-ta-si er u-be-gr\u00e6n-set"},
            {"english": "Art comes from the heart.", "danish": "Kunst kommer fra hjertet.", "pronunciation": "kunst kom-mer fra hjer-tet"},
            {"english": "Express yourself freely.", "danish": "Udtryk dig frit.", "pronunciation": "ud-tryk dij frit"},
            {"english": "Innovation starts with curiosity.", "danish": "Innovation starter med nysgerrighed.", "pronunciation": "in-no-va-sjon star-ter med nys-ger-rig-hed"},
        ],
        "Inner Peace": [
            {"english": "Find peace within yourself.", "danish": "Find fred i dig selv.", "pronunciation": "find fred i dij selv"},
            {"english": "Breathe, relax, let go.", "danish": "Tr\u00e6k vejret, slap af, slip taget.", "pronunciation": "tr\u00e6k vej-ret, slap af, slip ta-get"},
            {"english": "Calm mind, happy heart.", "danish": "Roligt sind, glad hjerte.", "pronunciation": "ro-ligt sind, glad hjer-te"},
        ],
        "Confidence": [
            {"english": "You are enough, just as you are.", "danish": "Du er nok, pr\u00e6cis som du er.", "pronunciation": "du er nok, pr\u00e6-cis som du er"},
            {"english": "Stand tall, speak up.", "danish": "St\u00e5 rank, sig til.", "pronunciation": "st\u00e5 rank, sij til"},
            {"english": "Believe in your abilities.", "danish": "Tro p\u00e5 dine evner.", "pronunciation": "tro p\u00e5 di-ne ev-ner"},
        ],
        "Perseverance": [
            {"english": "Never give up, keep pushing.", "danish": "Giv aldrig op, forts\u00e6t med at k\u00e6mpe.", "pronunciation": "giv al-drig op, for-ts\u00e6t med at k\u00e6m-pe"},
            {"english": "Storms make trees take deeper roots.", "danish": "Storme f\u00e5r tr\u00e6er til at sl\u00e5 dybere r\u00f8dder.", "pronunciation": "stor-me f\u00e5r tr\u00e6-er til \u00e5 sl\u00e5 dy-be-re r\u00f8d-der"},
            {"english": "Patience and persistence win.", "danish": "T\u00e5lmodighed og udholdenhed vinder.", "pronunciation": "t\u00e5l-mo-dig-hed og ud-hol-den-hed vin-der"},
        ],
        "Inspiration": [
            {"english": "Let your light shine bright.", "danish": "Lad dit lys skinne klart.", "pronunciation": "lad dit lys skin-ne klart"},
            {"english": "Inspire others by your actions.", "danish": "Inspir\u00e9r andre med dine handlinger.", "pronunciation": "in-spi-r\u00e9r an-dre med di-ne hand-ling-er"},
            {"english": "Be the change you want to see.", "danish": "V\u00e6r forandringen du vil se.", "pronunciation": "v\u00e6r for-and-ring-en du vil se"},
        ],
        "Positive Life": [
            {"english": "Choose positivity every day.", "danish": "V\u00e6lg positivitet hver dag.", "pronunciation": "v\u00e6lg po-si-ti-vi-tet v\u00e6r dag"},
            {"english": "Good vibes only.", "danish": "Kun gode vibes.", "pronunciation": "kun go-de vajbs"},
            {"english": "Life is what you make it.", "danish": "Livet er hvad du g\u00f8r det til.", "pronunciation": "li-vet er hvad du g\u00f8r det til"},
        ],
        "Courage": [
            {"english": "Be brave, take the first step.", "danish": "V\u00e6r modig, tag det f\u00f8rste skridt.", "pronunciation": "v\u00e6r mo-dig, tag det f\u00f8r-ste skridt"},
            {"english": "Courage is not the absence of fear.", "danish": "Mod er ikke frav\u00e6r af frygt.", "pronunciation": "mod er ik-ke fra-v\u00e6r af frygt"},
            {"english": "Face your fears head on.", "danish": "M\u00f8d din frygt direkte.", "pronunciation": "m\u00f8d din frygt di-rek-te"},
        ],
        "Kindness": [
            {"english": "Be kind to everyone you meet.", "danish": "V\u00e6r venlig mod alle du m\u00f8der.", "pronunciation": "v\u00e6r ven-lig mod al-le du m\u00f8-der"},
            {"english": "Kindness costs nothing, means everything.", "danish": "Venlighed koster ingenting, betyder alt.", "pronunciation": "ven-lig-hed kos-ter in-gen-ting, be-ty-der alt"},
            {"english": "Spread kindness wherever you go.", "danish": "Spred venlighed hvor end du g\u00e5r.", "pronunciation": "spred ven-lig-hed hvor en du g\u00e5r"},
        ],
        "Patience": [
            {"english": "Good things take time.", "danish": "Gode ting tager tid.", "pronunciation": "go-de ting ta-ger tid"},
            {"english": "Wait patiently, trust the process.", "danish": "Vent t\u00e5lmodigt, stol p\u00e5 processen.", "pronunciation": "vent t\u00e5l-mo-digt, stol p\u00e5 pro-ses-sen"},
            {"english": "Rome wasn't built in a day.", "danish": "Rom blev ikke bygget p\u00e5 en dag.", "pronunciation": "rom blev ik-ke byg-get p\u00e5 en dag"},
        ],
        "Forgiveness": [
            {"english": "Forgive and set yourself free.", "danish": "Tilgiv og s\u00e6t dig selv fri.", "pronunciation": "til-giv og s\u00e6t dij selv fri"},
            {"english": "Let go of grudges, find peace.", "danish": "Slip nag, find fred.", "pronunciation": "slip nag, find fred"},
            {"english": "Forgiveness is a gift to yourself.", "danish": "Tilgivelse er en gave til dig selv.", "pronunciation": "til-gi-vel-se er en ga-ve til dij selv"},
        ],
        "Strength": [
            {"english": "You are stronger than you know.", "danish": "Du er st\u00e6rkere end du ved.", "pronunciation": "du er st\u00e6r-ke-re en du ved"},
            {"english": "Inner strength comes from within.", "danish": "Indre styrke kommer fra indersiden.", "pronunciation": "in-dre styr-ke kom-mer fra in-der-si-den"},
            {"english": "Challenges make you stronger.", "danish": "Udfordringer g\u00f8r dig st\u00e6rkere.", "pronunciation": "ud-for-dring-er g\u00f8r dij st\u00e6r-ke-re"},
        ],
        "Joy": [
            {"english": "Find joy in every moment.", "danish": "Find gl\u00e6de i hvert \u00f8jeblik.", "pronunciation": "find gle-de i hvert \u00f8je-blik"},
            {"english": "Joy is contagious, spread it.", "danish": "Gl\u00e6de er smitsomt, spred det.", "pronunciation": "gle-de er smit-somt, spred det"},
            {"english": "Dance like nobody's watching.", "danish": "Dans som om ingen ser p\u00e5.", "pronunciation": "dans som om in-gen ser p\u00e5"},
        ],
        "Balance": [
            {"english": "Find balance in your life.", "danish": "Find balance i livet dit.", "pronunciation": "find ba-lan-se i li-vet dit"},
            {"english": "Work hard, rest well.", "danish": "Arbejd h\u00e5rdt, hvil godt.", "pronunciation": "ar-bejd h\u00e5rdt, hvil godt"},
            {"english": "Too much of anything is not good.", "danish": "For meget af noget er ikke godt.", "pronunciation": "for me-get af no-get er ik-ke godt"},
        ],
        "Growth": [
            {"english": "Growth happens outside your comfort zone.", "danish": "V\u00e6kst sker uden for komfortzonen.", "pronunciation": "v\u00e6kst sker u-den for kom-fort-zo-nen"},
            {"english": "Embrace change, grow stronger.", "danish": "Omfavn forandring, bliv st\u00e6rkere.", "pronunciation": "om-favn for-and-ring, bliv st\u00e6r-ke-re"},
            {"english": "Every challenge is a chance to grow.", "danish": "Hver udfordring er en chance til at vokse.", "pronunciation": "hver ud-for-dring er en sjan-se til at vok-se"},
        ],
        "Purpose": [
            {"english": "Find your purpose, follow it.", "danish": "Find dit form\u00e5l, f\u00f8lg det.", "pronunciation": "find dit form\u00e5l, f\u00f8lg det"},
            {"english": "Your life has meaning.", "danish": "Dit liv har mening.", "pronunciation": "dit liv har me-ning"},
            {"english": "Live with intention, not accident.", "danish": "Lev med hensigt, ikke tilf\u00e6ldigt.", "pronunciation": "lev med hen-sigt, ik-ke til-f\u00e6l-digt"},
        ],
        "Mindfulness": [
            {"english": "Be present in this moment.", "danish": "V\u00e6r til stede i dette \u00f8jeblik.", "pronunciation": "v\u00e6r til ste-de i det-te \u00f8je-blik"},
            {"english": "Breathe deeply, stay grounded.", "danish": "Tr\u00e6k vejret dybt, hold dig jordet.", "pronunciation": "tr\u00e6k vej-ret dybt, hold dij jor-det"},
            {"english": "Notice the little things around you.", "danish": "L\u00e6g m\u00e6rke til de sm\u00e5 ting omkring dig.", "pronunciation": "l\u00e6g m\u00e6r-ke til de sm\u00e5 ting om-kring dij"},
        ],
    }

    fallbacks = all_fallbacks.get(category, all_fallbacks["Motivation"])
    history = load_phrase_history()
    fresh_phrases = []
    for p in fallbacks:
        if not is_phrase_used(p["english"]) and not is_phrase_similar(p["english"], [h.get("english", "") for h in history.get("phrases", [])]):
            fresh_phrases.append(p)

    if len(fresh_phrases) < num_phrases:
        for cat, cat_fallbacks in all_fallbacks.items():
            if cat != category:
                for p in cat_fallbacks:
                    if not is_phrase_used(p["english"]) and not is_phrase_similar(p["english"], [h.get("english", "") for h in history.get("phrases", [])]):
                        fresh_phrases.append(p)
                    if len(fresh_phrases) >= num_phrases:
                        break
            if len(fresh_phrases) >= num_phrases:
                break

    return fresh_phrases[:num_phrases]


# ============== AUDIO GENERATION ==============

async def generate_single_audio(text: str, voice: str, output_path: str):
    try:
        import edge_tts
        communicate = edge_tts.Communicate(text, voice)
        await communicate.save(output_path)
        return True
    except Exception as e:
        print(f"  TTS error: {e}")
        return False


def generate_all_audio(phrases: list, output_dir: str):
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    audio_files = []

    for i, phrase in enumerate(phrases):
        english_file = output_dir / f"english_{i}.mp3"
        lang_file = output_dir / f"lang_{i}.mp3"
        combined_file = output_dir / f"combined_{i}.mp3"

        if (i + 1) % 20 == 0:
            print(f"  Generating audio {i+1}/{len(phrases)}...")

        en_success = asyncio.run(generate_single_audio(phrase["english"], ENGLISH_VOICE, str(english_file)))
        if not en_success:
            cmd = ["ffmpeg", "-y", "-f", "lavfi", "-i", "anullsrc=r=24000:cl=mono", "-t", "2", str(english_file)]
            subprocess.run(cmd, capture_output=True)

        lang_success = asyncio.run(generate_single_audio(phrase["danish"], LANG_VOICE, str(lang_file)))
        if not lang_success:
            cmd = ["ffmpeg", "-y", "-f", "lavfi", "-i", "anullsrc=r=24000:cl=mono", "-t", "2", str(lang_file)]
            subprocess.run(cmd, capture_output=True)

        en_duration = get_audio_duration(str(english_file))
        lang_duration = get_audio_duration(str(lang_file))

        pause_between = 0.5
        total_duration = en_duration + pause_between + lang_duration

        cmd = [
            "ffmpeg", "-y",
            "-i", str(english_file),
            "-i", str(lang_file),
            "-filter_complex", f"[0:a][1:a]concat=n=2:v=0:a=1[out]",
            "-map", "[out]",
            str(combined_file)
        ]

        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode != 0:
            concat_file = output_dir / f"concat_{i}.txt"
            with open(concat_file, "w", encoding="utf-8") as f:
                f.write(f"file '{english_file.as_posix()}'\n")
                f.write(f"file '{lang_file.as_posix()}'\n")
            cmd = [
                "ffmpeg", "-y",
                "-f", "concat", "-safe", "0",
                "-i", str(concat_file),
                "-c:a", "aac",
                str(combined_file)
            ]
            subprocess.run(cmd, capture_output=True)
            if concat_file.exists():
                concat_file.unlink()

        actual_duration = get_audio_duration(str(combined_file))

        audio_files.append({
            "index": i,
            "english": str(english_file),
            "lang": str(lang_file),
            "combined": str(combined_file),
            "duration": actual_duration,
            "en_duration": en_duration,
            "lang_duration": lang_duration
        })

    print(f"\n[audio] Generated {len(audio_files)} phrase audios")
    return audio_files


def get_audio_duration(audio_file: str) -> float:
    if not Path(audio_file).exists():
        return 2.0
    cmd = ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", audio_file]
    result = subprocess.run(cmd, capture_output=True, text=True)
    try:
        return float(result.stdout.strip())
    except:
        return 2.0


def create_final_narration(audio_files: list, output_file: str):
    n = len(audio_files)
    print(f"[audio] Combining {n} audio files...")
    concat_file = Path(output_file).parent / "narration_list.txt"
    with open(concat_file, "w", encoding="utf-8") as f:
        for audio_info in audio_files:
            combined_path = Path(audio_info["combined"])
            if combined_path.exists():
                path_str = str(combined_path.resolve()).replace("\\", "/").replace("'", "'\\''")
                f.write(f"file '{path_str}'\n")
    cmd = ["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(concat_file), "-c:a", "copy", str(output_file)]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if concat_file.exists():
        concat_file.unlink()
    if result.returncode == 0 and Path(output_file).exists() and Path(output_file).stat().st_size > 0:
        size = Path(output_file).stat().st_size
        print(f"\n[audio] Final narration: {Path(output_file).name} ({size/1024:.1f} KB)")
        return True
    return False


# ============== BACKGROUND GENERATION ==============

def create_premium_background(category_english: str):
    from PIL import Image, ImageDraw
    img = Image.new('RGB', (VIDEO_WIDTH, VIDEO_HEIGHT))
    draw = ImageDraw.Draw(img)
    for y in range(VIDEO_HEIGHT):
        ratio = y / VIDEO_HEIGHT
        if ratio < 0.5:
            r, g, b = 255, 252, 245
        else:
            r = int(255 + (245 - 255) * ((ratio - 0.5) * 2))
            g = int(252 + (240 - 252) * ((ratio - 0.5) * 2))
            b = int(245 + (230 - 245) * ((ratio - 0.5) * 2))
        draw.rectangle([(0, y), (VIDEO_WIDTH, y + 1)], fill=(r, g, b))
    return img


def generate_complete_image(phrase_data: dict, category_english: str, output_path: str):
    try:
        from PIL import Image, ImageDraw, ImageFont, ImageFilter
    except ImportError:
        print("PIL not available. Install: pip install Pillow")
        return None

    img = create_premium_background(category_english)
    img = img.convert('RGBA')
    draw = ImageDraw.Draw(img)

    # Font paths - check fonts/ directory first
    english_font_paths = [
        str(BASE_DIR / "fonts" / "DejaVuSans-Bold.ttf"),
        "C:/Windows/Fonts/segoeuib.ttf",
        "C:/Windows/Fonts/arialbd.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    ]

    lang_font_paths = [
        str(BASE_DIR / "fonts" / "DejaVuSans-Bold.ttf"),
        "C:/Windows/Fonts/arialbd.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    ]

    def load_font(font_paths, size):
        for font_path in font_paths:
            try:
                return ImageFont.truetype(font_path, size)
            except:
                continue
        return ImageFont.load_default()

    font_category = load_font(english_font_paths, 42)
    font_english = load_font(english_font_paths, 68)
    font_lang = load_font(lang_font_paths, 82)
    font_pronunciation = load_font(lang_font_paths, 48)
    font_branding = load_font(english_font_paths, 38)

    english = phrase_data.get("english", "")
    danish = phrase_data.get("danish", "")
    pronunciation = phrase_data.get("pronunciation", "")

    def wrap_text(text, font, max_width):
        words = text.split()
        lines = []
        current_line = []
        for word in words:
            test_line = ' '.join(current_line + [word])
            bbox = draw.textbbox((0, 0), test_line, font=font)
            if bbox[2] - bbox[0] <= max_width:
                current_line.append(word)
            else:
                if current_line: lines.append(' '.join(current_line))
                current_line = [word]
        if current_line: lines.append(' '.join(current_line))
        return lines

    # Header Bar
    cat_text = category_english.upper()
    cat_bbox = draw.textbbox((0, 0), cat_text, font=font_category)
    cat_w = cat_bbox[2] - cat_bbox[0]
    badge_h = 75
    badge_pad_x = 40
    container_w = cat_w + (badge_pad_x * 2)
    container_x = 60
    container_y = 60
    draw.rounded_rectangle(
        [(container_x, container_y), (container_x + container_w, container_y + badge_h)],
        radius=15, fill=(45, 35, 65, 255)
    )
    draw.text(
        (container_x + container_w // 2, container_y + badge_h // 2 + 2),
        cat_text,
        fill=(255, 255, 255, 255),
        font=font_category,
        anchor="mm"
    )

    CONTENT_Y_CENTER = VIDEO_HEIGHT // 2
    GAP = 60

    en_lines = wrap_text(english, font_english, VIDEO_WIDTH - 300)
    en_line_h = 80
    en_total_h = len(en_lines) * en_line_h

    lang_lines = wrap_text(danish, font_lang, VIDEO_WIDTH - 300)
    lang_line_h = 100
    lang_total_h = len(lang_lines) * lang_line_h

    pron_text = f"[{pronunciation}]"
    pron_lines = wrap_text(pron_text, font_pronunciation, VIDEO_WIDTH - 400)
    pron_line_h = 60
    pron_total_h = len(pron_lines) * pron_line_h

    total_content_h = en_total_h + lang_total_h + pron_total_h + (GAP * 2)
    y_start = CONTENT_Y_CENTER - (total_content_h // 2)

    box_w = VIDEO_WIDTH - 200
    box_x = (VIDEO_WIDTH - box_w) // 2

    # English Box
    en_box_h = en_total_h + 60
    draw.rounded_rectangle(
        [(box_x, y_start), (box_x + box_w, y_start + en_box_h)],
        radius=25, fill=(65, 50, 95, 255)
    )
    for i, line in enumerate(en_lines):
        draw.text((VIDEO_WIDTH // 2, y_start + 30 + (i * en_line_h) + en_line_h // 2),
                  line, fill=(255, 255, 255), font=font_english, anchor="mm")

    y_cursor = y_start + en_box_h + GAP

    # Danish Section
    lang_box_h = lang_total_h + 60
    draw.rounded_rectangle(
        [(box_x, y_cursor), (box_x + box_w, y_cursor + lang_box_h)],
        radius=25, fill=(95, 80, 125, 255)
    )
    for i, line in enumerate(lang_lines):
        draw.text((VIDEO_WIDTH // 2, y_cursor + 30 + (i * lang_line_h) + lang_line_h // 2),
                  line, fill=(255, 255, 255), font=font_lang, anchor="mm")

    y_cursor += lang_box_h + (GAP // 2)

    # Pronunciation Section
    pron_box_h = pron_total_h + 40
    pron_box_w = box_w - 200
    pron_box_x = (VIDEO_WIDTH - pron_box_w) // 2
    draw.rounded_rectangle(
        [(pron_box_x, y_cursor), (pron_box_x + pron_box_w, y_cursor + pron_box_h)],
        radius=20, fill=(255, 210, 160, 255)
    )
    for i, line in enumerate(pron_lines):
        draw.text((VIDEO_WIDTH // 2, y_cursor + 20 + (i * pron_line_h) + pron_line_h // 2),
                  line, fill=(70, 45, 25), font=font_pronunciation, anchor="mm")

    # Branding
    brand_text = "VELOCITY DANISH"
    brand_bbox = draw.textbbox((0, 0), brand_text, font=font_branding)
    brand_w = brand_bbox[2] - brand_bbox[0]
    draw.text((VIDEO_WIDTH - brand_w - 60, VIDEO_HEIGHT - 80), brand_text,
              fill=(45, 35, 65, 255), font=font_branding)

    img = img.convert('RGB')
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    img.save(output_path, quality=95, optimize=True)
    return output_path


# ============== THUMBNAIL GENERATION ==============

def generate_thumbnail(category_english: str, category_danish: str, output_path: str):
    try:
        from PIL import Image, ImageDraw, ImageFont
    except ImportError:
        print("PIL not available for thumbnail. Install: pip install Pillow")
        return None

    img = create_premium_background(category_english)
    img = img.convert('RGBA')
    draw = ImageDraw.Draw(img)

    english_font_paths = [
        str(BASE_DIR / "fonts" / "DejaVuSans-Bold.ttf"),
        "C:/Windows/Fonts/segoeuib.ttf",
        "C:/Windows/Fonts/arialbd.ttf",
    ]
    lang_font_paths = [
        str(BASE_DIR / "fonts" / "DejaVuSans-Bold.ttf"),
        "C:/Windows/Fonts/arialbd.ttf",
    ]

    def load_font(font_paths, size):
        for font_path in font_paths:
            try: return ImageFont.truetype(font_path, size)
            except: continue
        return ImageFont.load_default()

    font_huge = load_font(english_font_paths, 130)
    font_main = load_font(lang_font_paths, 110)
    font_sub = load_font(english_font_paths, 60)
    font_badge = load_font(english_font_paths, 45)

    draw.text((VIDEO_WIDTH // 2, 220), "MASTER DANISH", fill=(45, 35, 65), font=font_huge, anchor="mm")

    cat_text = category_english.upper()
    cat_bbox = draw.textbbox((0, 0), cat_text, font=font_sub)
    cat_w = cat_bbox[2] - cat_bbox[0]
    draw.rounded_rectangle(
        [(VIDEO_WIDTH // 2 - cat_w // 2 - 40, 320), (VIDEO_WIDTH // 2 + cat_w // 2 + 40, 410)],
        radius=20, fill=(65, 50, 95, 255)
    )
    draw.text((VIDEO_WIDTH // 2, 365), cat_text, fill=(255, 255, 255), font=font_sub, anchor="mm")

    draw.text((VIDEO_WIDTH // 2, 530), category_danish, fill=(45, 35, 65), font=font_main, anchor="mm")

    cta_text = "60 VIGTIGE FRASER"
    draw.rounded_rectangle(
        [(VIDEO_WIDTH // 2 - 300, 650), (VIDEO_WIDTH // 2 + 300, 730)],
        radius=15, fill=(255, 210, 160, 255)
    )
    draw.text((VIDEO_WIDTH // 2, 690), cta_text, fill=(70, 45, 25), font=font_badge, anchor="mm")

    draw.rectangle([(0, VIDEO_HEIGHT - 100), (VIDEO_WIDTH, VIDEO_HEIGHT)], fill=(45, 35, 65, 255))
    draw.text((VIDEO_WIDTH // 2, VIDEO_HEIGHT - 50), "VELOCITY DANISH", fill=(255, 255, 255), font=font_badge, anchor="mm")

    img = img.convert('RGB')
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    img.save(output_path, quality=95, optimize=True)
    return output_path


def extract_video_thumbnail(video_path: str, output_path: str, timestamp_seconds: int = 5):
    try:
        cmd = [
            "ffmpeg", "-y",
            "-ss", str(timestamp_seconds),
            "-i", str(video_path),
            "-vframes", "1",
            "-q:v", "2",
            str(output_path)
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0 and Path(output_path).exists():
            print(f"  Video thumbnail extracted: {Path(output_path).name}")
            return str(output_path)
        else:
            print(f"  Could not extract video thumbnail")
            return None
    except Exception as e:
        print(f"  Thumbnail extraction error: {e}")
        return None


# ============== TITLE & DESCRIPTION GENERATION ==============

def generate_title_description(category_english: str, category_danish: str, phrases: list, duration_minutes: float, output_dir: str):
    titles = [
        f"Learn Danish in 10 Minutes | {category_english} Phrases Every Beginner NEEDS to Know! ({category_danish})",
        f"60 Danish Phrases for {category_english} | Speak Danish Like a Native! ({category_danish})",
        f"Master Danish {category_english} | 60 Essential Danish Phrases with Pronunciation | Velocity Danish",
        f"Danish Learning Made Easy | {category_english} Vocabulary | 10 Minute Lesson",
        f"Speak Danish Fluently | {category_english} Phrases | English + Danish + Pronunciation",
    ]

    description = f"""\U0001F1E9\U0001F1F0 Learn Danish with Velocity Danish! \U0001F1E9\U0001F1F0

In this video, you'll learn 60 essential Danish phrases about {category_english} ({category_danish}).
Perfect for beginners and intermediate learners!

\U0001F4DA WHAT YOU'LL LEARN:
\u2022 60 practical {category_english} phrases in Danish
\u2022 Correct pronunciation guide
\u2022 Natural pauses for speaking practice
\u2022 Common expressions used by native speakers

\U0001F551 VIDEO TIMESTAMPS:
"""

    avg_phrase_duration = duration_minutes * 60 / len(phrases)
    for i in range(0, len(phrases), 10):
        timestamp = int(i * avg_phrase_duration / 60)
        minute = timestamp
        second = int((i * avg_phrase_duration) % 60)
        end_phrase = min(i + 10, len(phrases))
        description += f"{minute:02d}:{second:02d} Phrases {i+1}-{end_phrase}\n"

    description += """
\U0001F4DD ALL PHRASES IN THIS VIDEO:
"""

    for i, phrase in enumerate(phrases, 1):
        description += f"""
{i}. {phrase['english']}
   Danish: {phrase['danish']}
    Pronunciation: {phrase['pronunciation']}
"""

    description += """
\U0001F3AF PERFECT FOR:
\u2022 Danish beginners wanting to expand vocabulary
\u2022 Intermediate learners practicing pronunciation
\u2022 Anyone interested in Danish language and culture
\u2022 Language enthusiasts and polyglots
\u2022 Students preparing for exams

\U0001F4A1 TIPS FOR LEARNING:
1. Repeat each phrase out loud
2. Practice daily for best results
3. Use the pauses to speak along
4. Write down phrases you find difficult
5. Review this video multiple times

\U0001F514 SUBSCRIBE for more Danish learning content!
\U0001F44D LIKE this video if you found it helpful!
\U0001F4AC COMMENT which phrases you want to learn next!

\U0001F4F1 FOLLOW VELOCITY DANISH:
[Add your social media links here]

\U0001F3B5 MUSIC:
[Add music credits if applicable]

\U0001F4D6 RELATED VIDEOS:
\u2022 Danish Motivation Phrases
\u2022 Danish Love Expressions
\u2022 Basic Danish Greetings

#LearnDanish #DanishPhrases #DanishLanguage #{category_english.replace(' ', '')} #VelocityDanish #DanishForBeginners #SpeakDanish #DanishVocabulary #Pronunciation #LanguageLearning #Danish101 #DanishLesson

---
\u00A9 Velocity Danish - Making Danish learning accessible to everyone!
"""

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    with open(output_dir / "youtube_upload_info.txt", "w", encoding="utf-8") as f:
        f.write("=" * 80 + "\n")
        f.write("YOUTUBE VIDEO UPLOAD INFORMATION\n")
        f.write("=" * 80 + "\n\n")
        f.write("RECOMMENDED TITLES (Choose one):\n")
        f.write("-" * 80 + "\n")
        for i, title in enumerate(titles, 1):
            f.write(f"\n{i}. {title}\n")
        f.write("\n" + "=" * 80 + "\n")
        f.write("SELECTED TITLE (Recommended):\n")
        f.write("-" * 80 + "\n")
        f.write(f"\n{titles[0]}\n")
        f.write("\n" + "=" * 80 + "\n")
        f.write("VIDEO DESCRIPTION:\n")
        f.write("-" * 80 + "\n\n")
        f.write(description)
        f.write("\n" + "=" * 80 + "\n")
        f.write("VIDEO TAGS (for YouTube):\n")
        f.write("-" * 80 + "\n")
        tags = [
            "Learn Danish",
            "Danish Phrases",
            "Danish Language",
            category_english,
            "Velocity Danish",
            "Danish for Beginners",
            "Speak Danish",
            "Danish Vocabulary",
            "Pronunciation",
            "Language Learning",
            "Danish 101",
            "Danish Lesson"
        ]
        f.write(", ".join(tags) + "\n")

    metadata = {
        "recommended_titles": titles,
        "selected_title": titles[0],
        "description": description,
        "category_english": category_english,
        "category_danish": category_danish,
        "phrases_count": len(phrases),
        "duration_minutes": round(duration_minutes, 2),
        "tags": tags
    }

    with open(output_dir / "video_metadata.json", "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2, ensure_ascii=False)

    print(f"\n[metadata] Generated YouTube upload files")
    print(f"  youtube_upload_info.txt (title + description + tags)")
    print(f"  video_metadata.json")

    return metadata


# ============== VIDEO CREATION ==============

def create_video_from_images_audio(image_files: list, audio_files: list, combined_audio: str, output_file: str):
    print(f"\n[video] Creating long-form video from {len(image_files)} images...")

    temp_clips = []

    for i, (img_path, audio_info) in enumerate(zip(image_files, audio_files)):
        duration = audio_info['duration']
        print(f"  Image {i+1}/{len(image_files)}: {duration:.2f}s")

        temp_clip = Path(output_file).parent / f"temp_clip_{i:02d}.mp4"
        temp_clips.append(temp_clip)

        cmd = [
            "ffmpeg", "-y",
            "-loop", "1",
            "-i", str(img_path),
            "-i", audio_info['combined'],
            "-vf", f"scale={VIDEO_WIDTH}:{VIDEO_HEIGHT}:force_original_aspect_ratio=decrease,pad={VIDEO_WIDTH}:{VIDEO_HEIGHT}:(ow-iw)/2:(oh-ih)/2,fps={FPS}",
            "-c:v", "libx264",
            "-c:a", "aac",
            "-b:a", "128k",
            "-pix_fmt", "yuv420p",
            "-preset", "medium",
            "-shortest",
            "-vsync", "cfr",
            str(temp_clip)
        ]

        subprocess.run(cmd, check=True, capture_output=True)

    print("[video] Concatenating clips...")
    concat_file = Path(output_file).parent / "concat_list.txt"

    with open(concat_file, "w", encoding="utf-8") as f:
        for clip in temp_clips:
            f.write(f"file '{clip.resolve().as_posix()}'\n")

    cmd = ["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(concat_file), "-c", "copy", str(output_file)]
    subprocess.run(cmd, check=True, capture_output=True)

    if concat_file.exists():
        concat_file.unlink()

    video_duration = get_audio_duration(str(output_file))
    print(f"[video] Video created: {Path(output_file).name} ({video_duration:.2f}s)")

    for clip in temp_clips:
        if clip.exists():
            clip.unlink()


# ============== MAIN WORKFLOW ==============

def generate_longform_video(category_english: str = None, target_phrases: int = None):
    if not category_english:
        category_english = random.choice(CATEGORIES_ENGLISH)

    phrases_count = target_phrases if target_phrases else TARGET_PHRASES

    print(f"\n{'='*80}")
    print(f"LONG-FORM VIDEO - Category: {category_english} ({CATEGORIES_DANISH[category_english]})")
    print(f"Target Phrases: {phrases_count}")
    print(f"{'='*80}\n")

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    video_dir = LONGFORM_DIR / f"{category_english}_longform_{timestamp}"
    video_dir.mkdir(exist_ok=True)

    print(f"[1/6] Generating {phrases_count} unique phrases (checking history)...")
    phrases = generate_phrases_for_longform(category_english, phrases_count)

    for i, phrase in enumerate(phrases, 1):
        print(f"  {i}. {phrase['english']} -> {phrase['danish']}")

    print(f"\n[info] Total phrases: {len(phrases)}")

    print(f"\n[2/6] Generating {len(phrases)} images with premium backgrounds...")
    for i, phrase in enumerate(phrases):
        output_path = video_dir / f"phrase_{i:04d}.jpg"
        generate_complete_image(phrase, category_english, str(output_path))
        if (i + 1) % 10 == 0:
            print(f"  Progress: {i+1}/{len(phrases)} images...")

    print(f"\n    print(f"\n[3/6] Using first phrase image as thumbnail...")
    thumbnail_path = video_dir / "thumbnail.jpg"
    first_phrase = sorted(video_dir.glob("phrase_*.jpg"))
    if first_phrase:
        import shutil
        shutil.copy2(str(first_phrase[0]), str(thumbnail_path))
        print(f"  Thumbnail: {first_phrase[0].name} (content-based)")
    else:
        try:
            from generate_thumbnail import generate_scenic_image
            result = generate_scenic_image(category_english, category_english, str(thumbnail_path))
            if result and Path(result).exists():
                print(f"  gpt-image-2 thumbnail saved")
            else:
                print(f"  gpt-image-2 failed, using built-in")
                generate_thumbnail(category_english, CATEGORIES_ENGLISH[category_english], str(thumbnail_path))
        except Exception as e:
            print(f"  Thumbnail error: {e}, using built-in")
            generate_thumbnail(category_english, CATEGORIES_ENGLISH[category_english], str(thumbnail_path))
    video_thumbnail_path = video_dir / "video_thumbnail_frame.jpg"[4/6] Generating audio for {len(phrases)} phrases...")
    audio_files = generate_all_audio(phrases, str(video_dir))

    final_audio = video_dir / "narration.mp3"
    create_final_narration(audio_files, str(final_audio))

    total_duration = sum(a['duration'] for a in audio_files)
    print(f"\n[info] Total audio duration: {total_duration:.2f}s ({total_duration/60:.2f} minutes)")

    print(f"\n[5/6] Creating long-form video with transitions...")
    output_video = video_dir / "final_video.mp4"

    image_files = sorted([str(p) for p in video_dir.glob("phrase_*.jpg")])

    create_video_from_images_audio(
        image_files,
        audio_files,
        str(final_audio),
        str(output_video)
    )

    print(f"\n[5.5/6] Extracting video frame for thumbnail...")
    extract_video_thumbnail(str(output_video), str(video_thumbnail_path), timestamp_seconds=5)

    print(f"\n[6/6] Generating YouTube title, description, and metadata...")
    title_meta = generate_title_description(
        category_english,
        CATEGORIES_DANISH[category_english],
        phrases,
        total_duration / 60,
        str(video_dir)
    )

    import json as _json
    from pathlib import Path as _Path
    meta_out = {
        "title": title_meta.get("selected_title", f"Learn Danish: {category_english}"),
        "description": title_meta.get("description", ""),
        "tags": ["Learn Danish", "Danish Phrases", "Danish", category_english, "Velocity Danish"],
        "category_english": category_english,
        "category_danish": CATEGORIES_DANISH[category_english],
        "phrases_count": len(phrases),
        "duration_seconds": total_duration,
        "duration_minutes": total_duration / 60,
        "video_path": str(output_video),
        "thumbnail_path": str(thumbnail_path),
        "phrases": phrases,
        "generated_at": datetime.now().isoformat(),
    }
    _Path("output").mkdir(exist_ok=True)
    with open(_Path("output") / "latest_video.json", "w", encoding="utf-8") as f:
        _json.dump(meta_out, f, indent=2, ensure_ascii=False)
    with open(_Path("output") / "latest_upload_info.json", "w", encoding="utf-8") as f:
        _json.dump({"title": meta_out["title"], "description": meta_out["description"],
                     "category": category_english, "phrases_count": len(phrases)}, f, indent=2)

    print(f"\n{'='*80}")
    print(f"LONG-FORM VIDEO COMPLETE!")
    print(f"  {video_dir}")
    print(f"  {output_video.name}")
    print(f"  thumbnail.jpg (generated)")
    print(f"  {video_thumbnail_path.name} (from video)")
    print(f"  youtube_upload_info.txt (title + description + tags)")
    print(f"  Duration: {total_duration/60:.2f} minutes")
    print(f"  Phrases: {len(phrases)}")
    print(f"  Branding: Velocity Danish")
    print(f"  Format: 16:9 (1920x1080)")
    print(f"{'='*80}\n")

    return meta_out


def generate_multiple_longform(count: int = 1, target_phrases: int = None):
    print(f"\nGenerating {count} long-form video(s)...")
    print("="*80)
    for i in range(count):
        print(f"\n{'='*80}")
        print(f"VIDEO {i+1}/{count}")
        print("="*80)
        generate_longform_video(target_phrases=target_phrases)
    print("\n" + "="*80)
    print(f"ALL {count} LONG-FORM VIDEOS COMPLETE!")
    print("="*80)


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Velocity Danish YouTube Long-form Video Generator")
    parser.add_argument("--phrases", type=int, default=TARGET_PHRASES, help="Number of phrases to generate")
    parser.add_argument("--category", type=str, default=None, help="Specific category to generate")
    args = parser.parse_args()

    print("\n" + "="*80)
    print("VELOCITY DANISH - YOUTUBE LONG-FORM AUTOMATION")
    print("="*80)
    print("\nFEATURES:")
    print("  16:9 format (1920x1080) for YouTube long-form")
    print(f"  Target {args.phrases} phrases (~{args.phrases * 5.5 / 60:.1f} minute video)")
    print("  Light Theme (Cream background, dark/light purple + peach containers)")
    print("  Natural pauses with commas (non-robotic TTS)")
    print("  Perfect audio-video synchronization")
    print("  NEVER repeats phrases (permanent history tracking)")
    print(f"\nAVAILABLE CATEGORIES ({len(CATEGORIES_ENGLISH)} total):")
    for i, cat in enumerate(CATEGORIES_ENGLISH, 1):
        print(f"   {i:2d}. {cat} ({CATEGORIES_DANISH[cat]})")
    print(f"\nVIDEO SPECIFICATIONS:")
    print(f"  Resolution: {VIDEO_WIDTH}x{VIDEO_HEIGHT} (16:9)")
    print(f"  Frame Rate: {FPS} FPS")
    print(f"  Target Phrases: {args.phrases}")
    print(f"  Estimated Duration: ~{args.phrases * 5.5 / 60:.1f} minutes")
    print(f"  Phrase History: PERMANENT (never deletes)")
    print("="*80)

    generate_longform_video(category_english=args.category, target_phrases=args.phrases)
