"""
Anki Deck Generator for Sejeon Korean Textbook

Usage:
- Set variables below for easy running.
- Run: python generate_decks.py [options]
- Dry run: python generate_decks.py --dry_run
- Single chapter: python generate_decks.py --chapter_num 1
- All chapters: python generate_decks.py

Notes:
- Audio is generated with 1s delays to avoid rate limits (10/min free tier).
- Rerun to resume failed audio generation.
- Import .apkg into Anki.
"""

# Easy config variables
DEFAULT_JSON_DIR = "KLEAR-Lesson-JSON"  # Directory with chapter JSONs
DEFAULT_OUTPUT_DIR = "KLEAR_Decks"  # Output dir for .apkg and media/
DEFAULT_CHAPTER_NUM = None  # None for all chapters, or int for specific

import json
import os
import glob
import argparse
from typing import List, Dict
from tts import TTSGenerator
from deck_builder import create_vocab_notes, create_cloze_notes, create_reading_notes
import genanki
import random


def collect_audio_queries(chapter_data: dict) -> Dict[str, List[str]]:
    queries = {
        "vocabulary": [
            item["audio_query"] for item in chapter_data.get("vocabulary", [])
        ],
        "grammar_clozes": [
            item["sentence_cloze"].replace("{{c1::", "").replace("}}", "")
            for item in chapter_data.get("grammar_clozes", [])
        ],
        "reading_passage": [
            item["sentence_kr"] for item in chapter_data.get("reading_passage", [])
        ],
    }
    return queries


def main():
    parser = argparse.ArgumentParser(
        description="Generate Anki decks from Sejeon JSON chapters."
    )
    parser.add_argument(
        "json_dir",
        nargs="?",
        default=DEFAULT_JSON_DIR,
        help="Directory containing chapter JSON files",
    )
    parser.add_argument(
        "--output_dir",
        default=DEFAULT_OUTPUT_DIR,
        help="Output directory for .apkg files",
    )
    parser.add_argument(
        "--dry_run", action="store_true", help="Preview without generating files"
    )
    parser.add_argument(
        "--chapter_num",
        type=int,
        default=DEFAULT_CHAPTER_NUM,
        help="Process only specific chapter number (None for all)",
    )
    args = parser.parse_args()

    # Find and sort chapter/lesson files (supports both chapter-*.json and lesson-*.json)
    json_files = glob.glob(os.path.join(args.json_dir, "chapter-*.json")) + glob.glob(
        os.path.join(args.json_dir, "lesson-*.json")
    )
    json_files.sort(key=lambda x: int(os.path.basename(x).split("-")[1].split(".")[0]))

    # Determine source for naming (Sejeon vs Integrated Korean)
    is_sejeon = "Sejeon" in args.json_dir

    if args.chapter_num:
        json_files = [
            f
            for f in json_files
            if int(os.path.basename(f).split("-")[1].split(".")[0]) == args.chapter_num
        ]

    tts_gen = TTSGenerator()

    for json_file in json_files:
        with open(json_file, "r", encoding="utf-8") as f:
            chapter_data = json.load(f)

        chapter_num = chapter_data["chapter_info"]["number"]
        chapter_title = chapter_data["chapter_info"]["title_kr"]
        print(f"Processing Chapter {chapter_num}: {chapter_title}")

        queries = collect_audio_queries(chapter_data)
        total_queries = sum(len(v) for v in queries.values())
        print(f"  Found {total_queries} audio queries")

        if args.dry_run:
            # Count notes
            vocab_count = (
                len(chapter_data.get("vocabulary", [])) * 2
            )  # forwards + reverses
            cloze_count = len(chapter_data.get("grammar_clozes", []))
            reading_count = len(chapter_data.get("reading_passage", []))
            print(
                f"  Would create: {vocab_count} vocab, {cloze_count} cloze, {reading_count} reading notes"
            )
            continue

        # Create media dir
        media_dir = os.path.join(args.output_dir, f"media/lesson-{chapter_num}")
        os.makedirs(media_dir, exist_ok=True)

        # Generate TTS
        print(f"  Generating {total_queries} audio files...")
        audio_map = tts_gen.generate_batch(queries, media_dir, chapter_num)
        print(f"  Generated {len(audio_map)} audio files successfully")

        # Create notes
        notes = []
        notes.extend(create_vocab_notes(chapter_data, audio_map))
        notes.extend(create_cloze_notes(chapter_data, audio_map))
        notes.extend(create_reading_notes(chapter_data, audio_map))
        print(f"  Created {len(notes)} notes")

        # Create deck
        deck_id = random.randrange(1 << 30, 1 << 31)  # Unique per chapter
        # Use appropriate naming based on source
        deck_name_prefix = "Sejeon Korean" if is_sejeon else "Integrated Korean"
        deck = genanki.Deck(
            deck_id, f"{deck_name_prefix} - Lesson {chapter_num}: {chapter_title}"
        )
        for note in notes:
            deck.add_note(note)

        # Set media files
        media_files = [
            os.path.join(media_dir, filename) for filename in audio_map.values()
        ]
        package = genanki.Package(deck)
        package.media_files = media_files

        # Write package
        output_file = os.path.join(args.output_dir, f"Korean_Lesson_{chapter_num}.apkg")
        package.write_to_file(output_file)
        print(f"  Saved to {output_file}")


if __name__ == "__main__":
    main()
