import os
import subprocess
import json
import urllib.parse
import shutil
from pathlib import Path

class SpeechScorer:
    def __init__(self, kaldi_root_dir="~/speech-scoring/kaldi-dnn-ali-gop/egs/gop-compute"):
        self.base_dir = os.path.expanduser(kaldi_root_dir)
        self.demo_sh = os.path.join(self.base_dir, "demo.sh")
        self.wav_dir = os.path.join(self.base_dir, "local/demo/source/ch")
        self.text_path = os.path.abspath("./speech_text.txt")
        self.utt_id = "temp_audio"
        self.output_dir = os.path.join(
            self.base_dir, f"local/demo/web/exp/tdnnf/{self.utt_id}/json"
        )
        self.tmp_dir = os.path.join(self.base_dir, "local/demo/web/tmp")

        os.makedirs(self.wav_dir, exist_ok=True)
        os.makedirs(self.tmp_dir, exist_ok=True)

    def convert_audio(self, input_wav_path):
        """Convert input WAV to Kaldi-compatible format (16kHz mono 16-bit)"""
        input_wav_path = urllib.parse.unquote(input_wav_path)
        converted_wav = os.path.join(self.wav_dir, f"{self.utt_id}_16k.wav")
        print(f"[1] Converting audio: {input_wav_path} → {converted_wav}")
        subprocess.run([
            "sox", input_wav_path, "-r", "16000", "-c", "1", "-b", "16", converted_wav
        ], check=True)

        # Copy to expected tmp folder with correct naming
        shutil.copy(converted_wav, os.path.join(self.tmp_dir, f"{self.utt_id}.wav"))
        return converted_wav

    def validate_text_file(self):
        """Ensure speech_text.txt is copied into proper tmp folder"""
        if not os.path.exists(self.text_path):
            raise FileNotFoundError(f"Transcript file not found: {self.text_path}")
        print(f"[2] Using transcript file: {self.text_path}")
        shutil.copy(self.text_path, os.path.join(self.tmp_dir, f"{self.utt_id}.txt"))

    def run_demo_sh(self):
        """Run Kaldi's scoring pipeline using demo.sh"""
        print(f"[3] Running demo.sh with utt_id={self.utt_id}, lang='ch'...")
        subprocess.run([self.demo_sh, self.utt_id, "ch"], cwd=self.base_dir, check=True)

    def parse_result(self):
        """Parse and return the GOP score from JSON"""
        json_file = os.path.join(self.output_dir, f"{self.utt_id}.json")
        print(f"[4] Reading result JSON: {json_file}")
        if not os.path.exists(json_file):
            raise FileNotFoundError("Scoring output JSON not found!")

        with open(json_file, "r", encoding="utf-8") as f:
            result = json.load(f)

        return result["phones"]

    def score(self, wav_path):
        """Run the full scoring process and clean up"""
        self.validate_text_file()
        wav_16k = self.convert_audio(wav_path)

        # Copy original audio to expected .wav location
        kaldi_expected_path = os.path.join(self.wav_dir, f"{self.utt_id}.wav")
        shutil.copyfile(wav_path, kaldi_expected_path)

        try:
            self.run_demo_sh()
            scores = self.parse_result()
        finally:
            if os.path.exists(wav_16k):
                os.remove(wav_16k)
                print(f"[🧹] Removed temporary file: {wav_16k}")
            if os.path.exists(kaldi_expected_path):
                os.remove(kaldi_expected_path)
                print(f"[🧹] Removed temporary file: {kaldi_expected_path}")

        print("\n🎯 Pronunciation Scores (GOP):")
        for p in scores:
            print(f"{p['phone']:>10}: GOP = {p['gop']:.3f}")
        return scores
