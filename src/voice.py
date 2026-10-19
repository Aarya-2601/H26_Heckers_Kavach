"""Voice Input Wrapper module using SpeechRecognition and sounddevice.

Dynamically records for however long the user speaks, waiting for 5 seconds
of silence after speech finishes before concluding recording and transcribing.
"""

import time
from typing import List, Optional
import numpy as np
import speech_recognition as sr

from src.theme import console


class VoiceInputWrapper:
    """Lightweight voice capture and speech-to-text wrapper with dynamic duration."""

    def __init__(self, sample_rate: int = 16000):
        self.sample_rate = sample_rate
        self.recognizer = sr.Recognizer()

    def record_dynamic_audio(
        self,
        silence_after_speech: float = 5.0,
        max_wait_to_start: float = 12.0,
        max_total_duration: float = 60.0,
    ) -> sr.AudioData:
        """Record audio dynamically: records while the user speaks, then stops 5s after silence."""
        import sounddevice as sd

        chunk_duration = 0.2  # 200ms per block
        chunk_frames = int(chunk_duration * self.sample_rate)

        blocks: List[np.ndarray] = []
        ambient_samples: List[float] = []

        console.print("[dim white]🎤 Calibrating microphone for ambient sound...[/dim white]")

        with sd.InputStream(
            samplerate=self.sample_rate,
            channels=1,
            dtype="int16",
            blocksize=chunk_frames,
        ) as stream:
            # Calibrate ambient noise across 3 chunks (~0.6s)
            for _ in range(3):
                data, _ = stream.read(chunk_frames)
                blocks.append(data)
                rms = float(np.sqrt(np.mean(data.astype(float) ** 2)))
                ambient_samples.append(rms)

            avg_ambient = sum(ambient_samples) / max(len(ambient_samples), 1)
            # Threshold to distinguish active speech from ambient silence
            speech_threshold = max(avg_ambient * 2.2, 25.0)

            console.print(
                "[bright_cyan]🎙️  Microphone live! Speak for however long you need. Recording concludes 5 seconds after you finish speaking.[/bright_cyan]"
            )

            speech_started = False
            silence_elapsed = 0.0
            wait_elapsed = 0.0
            total_elapsed = 0.6
            last_status_print = 0.0

            while total_elapsed < max_total_duration:
                data, _ = stream.read(chunk_frames)
                blocks.append(data)
                total_elapsed += chunk_duration
                rms = float(np.sqrt(np.mean(data.astype(float) ** 2)))

                if not speech_started:
                    if rms > speech_threshold:
                        speech_started = True
                        silence_elapsed = 0.0
                        console.print("[bright_cyan]  ▶ Speaking detected! Recording in progress...[/bright_cyan]")
                    else:
                        wait_elapsed += chunk_duration
                        if wait_elapsed >= max_wait_to_start:
                            console.print("[dim white]  ⏹ No speech detected within wait timeout.[/dim white]")
                            break
                else:
                    if rms > speech_threshold:
                        # User is speaking, reset silence countdown
                        silence_elapsed = 0.0
                    else:
                        # Silence detected after speech
                        silence_elapsed += chunk_duration
                        now = time.time()
                        if now - last_status_print >= 1.0:
                            remaining = max(0.0, silence_after_speech - silence_elapsed)
                            console.print(
                                f"[dim white]  ⏸ Silence detected: waiting {remaining:.1f}s before finalizing...[/dim white]"
                            )
                            last_status_print = now

                        if silence_elapsed >= silence_after_speech:
                            console.print("[bright_cyan]  ✔ 5 seconds of silence elapsed. Finalizing audio capture...[/bright_cyan]")
                            break

        if not blocks:
            raw_bytes = np.zeros(self.sample_rate, dtype=np.int16).tobytes()
        else:
            full_audio = np.concatenate(blocks, axis=0).flatten()
            raw_bytes = full_audio.tobytes()

        return sr.AudioData(raw_bytes, self.sample_rate, 2)

    def listen_and_transcribe(
        self,
        silence_after_speech: float = 5.0,
        fallback_text: Optional[str] = "replace requests with httpx in linkwatch/checker.py",
        mock_input: Optional[str] = None,
    ) -> str:
        """Capture voice from microphone and transcribe to text.

        Records for however long the user speaks, then waits 5 seconds after speech is done.
        """
        if mock_input is not None:
            console.print(f"[dim white]🎙️ [Voice Mock]: \"{mock_input}\"[/dim white]")
            return mock_input

        try:
            audio_data = self.record_dynamic_audio(silence_after_speech=silence_after_speech)
            console.print("[dim white]Transcribing audio via SpeechRecognition...[/dim white]")
            transcribed = self.recognizer.recognize_google(audio_data)
            console.print(f"[bright_cyan]✔ Transcribed: \"{transcribed}\"[/bright_cyan]")
            return transcribed
        except sr.UnknownValueError:
            console.print(
                "[dim white]⚠️  No clear speech detected. You can type or edit your input manually below.[/dim white]"
            )
            return fallback_text or ""
        except sr.RequestError as exc:
            console.print(
                f"[dim white]⚠️  Speech recognition service unreachable ({exc}). You can type input manually.[/dim white]"
            )
            return fallback_text or ""
        except Exception as exc:
            console.print(f"[dim white]⚠️  Audio capture error ({exc}). You can type input manually.[/dim white]")
            return fallback_text or ""


# Shared singleton instance
voice_wrapper = VoiceInputWrapper()


def capture_voice_input(
    silence_after_speech: float = 5.0,
    fallback_text: str = "replace requests with httpx in linkwatch/checker.py",
    mock_input: Optional[str] = None,
) -> str:
    """Convenience helper to capture and transcribe dynamic voice input."""
    return voice_wrapper.listen_and_transcribe(
        silence_after_speech=silence_after_speech,
        fallback_text=fallback_text,
        mock_input=mock_input,
    )
