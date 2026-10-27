import io
import wave
import time
import queue
import threading
from dataclasses import dataclass, field
from typing import Callable, Optional

import numpy as np

from copilote.config import RMS_THRESHOLD, SILENCE_SEC, MIN_SPEECH_SEC, MAX_SEGMENT_SEC


@dataclass
class Segmenter:
    """Classe pure : segmente un flux audio mono 16kHz en phrases distinctes.

    Appeler feed() pour chaque bloc audio et tick() périodiquement.
    Retourne un tableau int16 quand un segment est complet, sinon None.
    """

    sample_rate: int = 16000
    rms_threshold: float = RMS_THRESHOLD
    silence_sec: float = SILENCE_SEC
    min_speech_sec: float = MIN_SPEECH_SEC
    max_segment_sec: float = MAX_SEGMENT_SEC

    _en_parole: bool = field(default=False, init=False)
    _debut_parole: float = field(default=0.0, init=False)
    _dernier_son: float = field(default=0.0, init=False)
    _duree_voix: float = field(default=0.0, init=False)
    _tampon: list = field(default_factory=list, init=False)
    _preroll: list = field(default_factory=list, init=False)
    _preroll_sec: float = field(default=0.3, init=False)

    def feed(self, bloc_mono: np.ndarray, t: float) -> Optional[np.ndarray]:
        duree_bloc = len(bloc_mono) / self.sample_rate
        rms = float(np.sqrt(np.mean(bloc_mono.astype(np.float32) ** 2)))

        # Fenêtre glissante de pré-roll
        self._preroll.append((bloc_mono.copy(), t))
        cutoff = t - self._preroll_sec
        self._preroll = [(b, ts) for b, ts in self._preroll if ts >= cutoff]

        if rms >= self.rms_threshold:
            if not self._en_parole:
                self._en_parole = True
                self._debut_parole = t
                self._duree_voix = 0.0
                self._tampon = [b for b, _ in self._preroll]
            else:
                self._tampon.append(bloc_mono.copy())
            self._duree_voix += duree_bloc
            self._dernier_son = t
        elif self._en_parole:
            self._tampon.append(bloc_mono.copy())
            if t - self._dernier_son >= self.silence_sec:
                return self._finaliser()

        if self._en_parole and t - self._debut_parole >= self.max_segment_sec:
            return self._finaliser()

        return None

    def tick(self, t: float) -> Optional[np.ndarray]:
        """Appel périodique pour détecter la fin sans nouvelles trames audio."""
        if not self._en_parole:
            return None
        if self._dernier_son > 0 and t - self._dernier_son >= self.silence_sec:
            return self._finaliser()
        if t - self._debut_parole >= self.max_segment_sec:
            return self._finaliser()
        return None

    def _finaliser(self) -> Optional[np.ndarray]:
        tampon, duree_voix = self._tampon, self._duree_voix
        self._en_parole = False
        self._tampon = []
        self._duree_voix = 0.0
        self._dernier_son = 0.0

        if not tampon or duree_voix < self.min_speech_sec:
            return None
        return np.concatenate(tampon)

    def reset(self):
        self._en_parole = False
        self._tampon = []
        self._preroll = []
        self._duree_voix = 0.0
        self._dernier_son = 0.0


def resample_mono(data: bytes, src_channels: int, src_rate: int, dst_rate: int = 16000) -> np.ndarray:
    samples = np.frombuffer(data, dtype=np.int16).astype(np.float32)
    if src_channels > 1:
        samples = samples.reshape(-1, src_channels).mean(axis=1)
    if src_rate != dst_rate:
        n_old = len(samples)
        n_new = int(n_old * dst_rate / src_rate)
        samples = np.interp(
            np.linspace(0, 1, n_new),
            np.linspace(0, 1, n_old),
            samples,
        )
    peak = np.max(np.abs(samples))
    if peak > 0:
        gain = min(32767.0 / peak, 10.0)
        samples = samples * gain
    return np.clip(samples, -32768, 32767).astype(np.int16)


def pcm_to_wav(audio_int16: np.ndarray, sample_rate: int = 16000) -> bytes:
    buf = io.BytesIO()
    with wave.open(buf, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        wf.writeframes(audio_int16.tobytes())
    return buf.getvalue()


class AudioCapture:
    def __init__(
        self,
        on_segment: Callable[[bytes], None],
        on_rms: Callable[[float], None],
        device_index: Optional[int] = None,
    ):
        self._on_segment = on_segment
        self._on_rms = on_rms
        self._device_index = device_index
        self._queue: queue.Queue = queue.Queue()
        self._stop_event = threading.Event()
        self._thread: Optional[threading.Thread] = None
        self._erreur: Optional[str] = None

    @staticmethod
    def lister_peripheriques() -> list[dict]:
        try:
            import pyaudiowpatch as pyaudio
            p = pyaudio.PyAudio()
            devs = list(p.get_loopback_device_info_generator())
            p.terminate()
            return devs
        except Exception as e:
            return [{"name": f"Erreur PyAudio: {e}", "index": -1, "defaultSampleRate": 0, "maxInputChannels": 0}]

    def demarrer(self, device_index: Optional[int] = None):
        if device_index is not None:
            self._device_index = device_index
        self._stop_event.clear()
        self._erreur = None
        self._thread = threading.Thread(target=self._run, daemon=True, name="AudioCapture")
        self._thread.start()

    def arreter(self):
        self._stop_event.set()
        if self._thread:
            self._thread.join(timeout=3.0)

    def erreur(self) -> Optional[str]:
        return self._erreur

    def _run(self):
        try:
            self._run_interne()
        except Exception as e:
            self._erreur = str(e)

    def _run_interne(self):
        import pyaudiowpatch as pyaudio

        p = pyaudio.PyAudio()
        try:
            if self._device_index is not None:
                dev = p.get_device_info_by_index(self._device_index)
            else:
                wasapi = p.get_host_api_info_by_type(pyaudio.paWASAPI)
                sortie = p.get_device_info_by_index(wasapi["defaultOutputDevice"])
                loopbacks = list(p.get_loopback_device_info_generator())
                if not loopbacks:
                    raise RuntimeError("Aucun périphérique loopback trouvé.")
                dev = next(
                    (d for d in loopbacks if sortie["name"] in d["name"]),
                    loopbacks[0],
                )

            src_rate = int(dev["defaultSampleRate"])
            channels = int(dev["maxInputChannels"])
            frames_per_buf = int(src_rate * 0.05)

            seg = Segmenter(sample_rate=16000)
            rms_acc: list[float] = []
            rms_last_t = time.monotonic()

            def _callback(in_data, frame_count, time_info, status):
                self._queue.put((in_data, time.monotonic()))
                return (None, pyaudio.paContinue)

            stream = p.open(
                format=pyaudio.paInt16,
                channels=channels,
                rate=src_rate,
                input=True,
                input_device_index=dev["index"],
                frames_per_buffer=frames_per_buf,
                stream_callback=_callback,
            )
            stream.start_stream()
            try:
                while not self._stop_event.is_set():
                    t_now = time.monotonic()
                    got_data = False

                    while True:
                        try:
                            raw, t = self._queue.get_nowait()
                        except queue.Empty:
                            break
                        bloc = resample_mono(raw, channels, src_rate, 16000)
                        got_data = True
                        result = seg.feed(bloc, t)
                        if result is not None:
                            self._on_segment(pcm_to_wav(result))
                        rms_acc.append(float(np.sqrt(np.mean(bloc.astype(np.float32) ** 2))))

                    result = seg.tick(t_now)
                    if result is not None:
                        self._on_segment(pcm_to_wav(result))

                    if t_now - rms_last_t >= 0.1:
                        val = float(np.mean(rms_acc)) if rms_acc else 0.0
                        self._on_rms(val)
                        rms_acc.clear()
                        rms_last_t = t_now

                    if not got_data:
                        time.sleep(0.01)
            finally:
                stream.stop_stream()
                stream.close()
        finally:
            p.terminate()
