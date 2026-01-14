from openai import OpenAI
from typing import List, Dict
import os
import time
from config import OPENAI_API_KEY


class TTSGenerator:
    # OpenAI voices for variety (rotating marin and cedar for Korean)
    VOICES = ["marin", "cedar"]

    def __init__(self, model: str = "gpt-4o-mini-tts"):
        self.client = OpenAI(api_key=OPENAI_API_KEY)
        self.model = model

    def generate_audio(self, text: str, output_path: str, voice_name: str) -> bool:
        """Generate audio for single text with specified voice."""
        try:
            with self.client.audio.speech.with_streaming_response.create(
                model=self.model,
                voice=voice_name,
                input=text,
                response_format="wav",  # WAV for Anki
            ) as response:
                response.stream_to_file(output_path)
            return True
        except Exception as e:
            print(f"Error generating audio for '{text}': {e}")
            return False

    def generate_batch(
        self, queries: Dict[str, List[str]], output_dir: str, chapter_num: int
    ) -> Dict[str, str]:
        """Generate audio for categorized queries, rotating through voices. Returns {query: filename} for successes."""
        results = {}
        os.makedirs(output_dir, exist_ok=True)

        idx = 0
        for category, query_list in queries.items():
            for j, query in enumerate(query_list):
                # Rotate voices based on global index for variety
                voice = self.VOICES[idx % len(self.VOICES)]
                # Better filename: chapterX_category_XX.wav
                filename = f"chapter{chapter_num}_{category}_{j + 1:02d}.wav"
                output_path = os.path.join(output_dir, filename)

                if os.path.exists(output_path):
                    print(f"  Skipping existing audio: {filename}")
                    results[query] = filename
                elif self.generate_audio(query, output_path, voice):
                    results[query] = filename

                idx += 1
                time.sleep(0.1)  # Short delay to avoid rate limits

        return results
