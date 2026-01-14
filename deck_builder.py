import genanki
import hashlib
from typing import Dict, List

# Model IDs (generate unique ones)
VOCAB_MODEL_ID = 1234567890  # Replace with random.randrange(1 << 30, 1 << 31)
CLOZE_MODEL_ID = 1234567891
READING_MODEL_ID = 1234567892

# Vocab Model
vocab_model = genanki.Model(
    VOCAB_MODEL_ID,
    "Sejeon Vocab",
    fields=[
        {"name": "Korean"},
        {"name": "English"},
        {"name": "Sentence_HTML"},
        {"name": "Audio"},
    ],
    templates=[
        {
            "name": "Forward",
            "qfmt": "{{Korean}}<br>{{Audio}}",
            "afmt": "{{FrontSide}}<hr>{{English}}<br>{{Sentence_HTML}}",
        },
        {
            "name": "Reverse",
            "qfmt": "{{English}}",
            "afmt": "{{FrontSide}}<hr>{{Korean}}<br>{{Sentence_HTML}}<br>{{Audio}}",
        },
    ],
    css="""
    .card {
        font-family: arial;
        font-size: 20px;
        text-align: center;
        color: black;
        background-color: white;
    }
    """,
)

# Cloze Model
cloze_model = genanki.CLOZE_MODEL

# Reading Model
reading_model = genanki.Model(
    READING_MODEL_ID,
    "Sejeon Reading",
    fields=[
        {"name": "Korean_Sentence"},
        {"name": "English_Translation"},
        {"name": "Audio"},
    ],
    templates=[
        {
            "name": "Reading",
            "qfmt": "{{Korean_Sentence}}<br>{{Audio}}",
            "afmt": "{{FrontSide}}<hr>{{English_Translation}}",
        },
    ],
    css="""
    .card {
        font-family: arial;
        font-size: 18px;
        text-align: center;
        color: black;
        background-color: white;
    }
    """,
)


def _make_guid(*fields):
    """Create stable GUID from fields."""
    data = "|".join(str(f) for f in fields)
    return hashlib.md5(data.encode("utf-8")).hexdigest()


def create_vocab_notes(
    chapter_data: Dict, audio_map: Dict[str, str]
) -> List[genanki.Note]:
    forwards = []
    reverses = []
    for item in chapter_data.get("vocabulary", []):
        korean = item["word_kr"]
        english = item["word_en"]
        sentence_html = item["sentence_kr_html"]
        audio_query = item["audio_query"]
        audio_filename = audio_map.get(audio_query, "")

        # Forward note
        forward_fields = [
            korean,
            english,
            sentence_html,
            f"[sound:{audio_filename}]" if audio_filename else "",
        ]
        forward_note = genanki.Note(
            model=vocab_model,
            fields=forward_fields,
            guid=_make_guid("vocab_forward", korean, english),
            tags=[
                "Korean",
                f"Lesson-{chapter_data['chapter_info']['number']}",
                "Vocab",
                item.get("category", "").replace(" ", "_"),
            ],
        )
        forwards.append(forward_note)

        # Reverse note
        reverse_fields = [
            english,
            korean,
            sentence_html,
            f"[sound:{audio_filename}]" if audio_filename else "",
        ]
        reverse_note = genanki.Note(
            model=vocab_model,
            fields=reverse_fields,
            guid=_make_guid("vocab_reverse", english, korean),
            tags=[
                "Korean",
                f"Lesson-{chapter_data['chapter_info']['number']}",
                "Vocab",
                "Reverse",
                item.get("category", "").replace(" ", "_"),
            ],
        )
        reverses.append(reverse_note)
    return forwards + reverses


def create_cloze_notes(
    chapter_data: Dict, audio_map: Dict[str, str]
) -> List[genanki.Note]:
    notes = []
    for item in chapter_data.get("grammar_clozes", []):
        cloze_text = item["sentence_cloze"]
        english = item["sentence_en"]
        usage = item.get("usage_note", "")
        # Audio for the cloze text (remove {{c1::}})
        audio_query = cloze_text.replace("{{c1::", "").replace("}}", "")
        audio_filename = audio_map.get(audio_query, "")

        # Cloze model expects [cloze_text, extra]
        extra = f"{english}<br><br>Usage: {usage}"
        if audio_filename:
            extra += f"<br>[sound:{audio_filename}]"
        fields = [cloze_text, extra]
        note = genanki.Note(
            model=cloze_model,
            fields=fields,
            guid=_make_guid("cloze", cloze_text),
            tags=[
                "Korean",
                f"Lesson-{chapter_data['chapter_info']['number']}",
                "Grammar",
                item["grammar_point"].replace(" ", "_"),
            ],
        )
        notes.append(note)
    return notes


def create_reading_notes(
    chapter_data: Dict, audio_map: Dict[str, str]
) -> List[genanki.Note]:
    notes = []
    for item in chapter_data.get("reading_passage", []):
        korean = item["sentence_kr"]
        english = item["sentence_en"]
        audio_filename = audio_map.get(korean, "")

        fields = [
            korean,
            english,
            f"[sound:{audio_filename}]" if audio_filename else "",
        ]
        note = genanki.Note(
            model=reading_model,
            fields=fields,
            guid=_make_guid("reading", korean),
            tags=[
                "Korean",
                f"Lesson-{chapter_data['chapter_info']['number']}",
                "Reading",
            ],
        )
        notes.append(note)
    return notes
