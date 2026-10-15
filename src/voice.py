"""Voice Input Wrapper module using SpeechRecognition and sounddevice.

Captures audio from the microphone, converts it to text via SpeechRecognition,
and returns the transcribed string to feed into terminal prompts.
"""

import time
from typing import Optional
import numpy as np
import speech_recognition as sr

from src.theme import console, print_ai, print_human


class VoiceInputWrapper:
    """Lightweight voice capture and speech-to-text wrapper."""

    def __init__(self, sample_rate: int = 16000):
        self.sample_rate = sample_rate
        self.recognizer = sr.Recognizer()

    def record_audio_sounddevice(self, duration: float = 4.0) -> sr.AudioData:
        """Record audio from the default input device using sounddevice."""
        import sounddevice as sd

        total_frames = int(duration * self.sample_rate)
        # Record 1 channel 16-bit PCM
        recording = sd.rec(
            total_frames,
            samplerate=self.sample_rate,
            channels=1,
            dtype="int16",
        )
        sd.wait()
        raw_bytes = recording.tobytes()
        return sr.AudioData(raw_bytes, self.sample_rate, 2)

    def listen_and_transcribe(
        self,
        duration: float = 4.0,
        prompt_message: str = "Listening to microphone... (Speak now)",
        fallback_text: Optional[str] = "replace requests with httpx in linkwatch/checker.py",
        mock_input: Optional[str] = None,
    ) -> str:
        """Capture voice from microphone and transcribe to text.

        Args:
            duration: Maximum recording duration in seconds.
            prompt_message: Status prompt shown to the user.
            fallback_text: Text used if silence is detected or audio is not understood.
            mock_input: If provided, bypasses mic for automated testing.

        Returns:
            Transcribed text string or fallback text.
        """
        if mock_input is not None:
            print_ai(f"🎙️ [Voice Mock]: Transcribed input '{mock_input}'")
            return mock_input

        print_human(f"🎤 {prompt_message}")
        console.print("[dim white]Recording audio for up to 4 seconds...[/dim white]")

        try:
            audio_data = self.record_audio_sounddevice(duration=duration)
            console.print("[dim white]Transcribing audio via SpeechRecognition...[/dim white]")
            transcribed = self.recognizer.recognize_google(audio_data)
            print_ai(f"✨ Transcribed: \"{transcribed}\"")
            return transcribed
        except sr.UnknownValueError:
            console.print(
                "[dim white]⚠️  No clear speech detected. Populating default suggested remediation.[/dim white]"
            )
            return fallback_text or ""
        except sr.RequestError as exc:
            console.print(f"[dim white]⚠️  Speech recognition service unreachable ({exc}).[/dim white]")
            return fallback_text or ""
        except Exception as exc:
            console.print(f"[dim white]⚠️  Audio capture error ({exc}).[/dim white]")
            return fallback_text or ""


# Shared singleton instance
voice_wrapper = VoiceInputWrapper()


def capture_voice_input(
    duration: float = 4.0,
    prompt_message: str = "Speak your remediation instruction into the mic:",
    fallback_text: str = "replace requests with httpx in linkwatch/checker.py",
    mock_input: Optional[str] = None,
) -> str:
    """Convenience helper to capture and transcribe voice."""
    return voice_wrapper.listen_and_transcribe(
        duration=duration,
        prompt_message=prompt_message,
        fallback_text=fallback_text,
        mock_input=mock_input,
    )
