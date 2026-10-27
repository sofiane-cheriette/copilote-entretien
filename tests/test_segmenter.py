import numpy as np
import pytest
from copilote.audio import Segmenter

RATE = 16000
DT = 0.05  # 50 ms par bloc, comme en capture réelle


def _silence(dur: float) -> np.ndarray:
    return np.zeros(int(RATE * dur), dtype=np.int16)


def _voix(dur: float, rms: float = 1000.0) -> np.ndarray:
    n = int(RATE * dur)
    return (np.random.default_rng(42).standard_normal(n) * rms).clip(-32768, 32767).astype(np.int16)


def _feed_blocs(seg: Segmenter, blocs, t_start: float = 0.0):
    """Envoie une liste de (tableau, durée) et retourne (résultats, t_final)."""
    results = []
    t = t_start
    for bloc, dur in blocs:
        r = seg.feed(bloc, t)
        if r is not None:
            results.append(r)
        t += dur
    return results, t


def test_segment_simple():
    """Voix suivie d'un silence long → un segment."""
    seg = Segmenter(rms_threshold=350, silence_sec=0.5, min_speech_sec=0.3, max_segment_sec=25)
    blocs = [(_voix(DT), DT)] * 20 + [(_silence(DT), DT)] * 20
    results, _ = _feed_blocs(seg, blocs)
    assert len(results) == 1
    assert len(results[0]) > 0


def test_segment_trop_court():
    """Voix trop courte (< min_speech_sec) → rejetée."""
    seg = Segmenter(rms_threshold=350, silence_sec=0.3, min_speech_sec=0.7, max_segment_sec=25)
    blocs = [(_voix(DT), DT)] * 6 + [(_silence(DT), DT)] * 20  # 0.3s de voix
    results, _ = _feed_blocs(seg, blocs)
    assert results == []


def test_coupure_forcee():
    """Voix continue > max_segment_sec → coupure forcée."""
    seg = Segmenter(rms_threshold=350, silence_sec=5.0, min_speech_sec=0.3, max_segment_sec=2.0)
    blocs = [(_voix(DT), DT)] * 80  # 4 secondes
    results, _ = _feed_blocs(seg, blocs)
    assert len(results) >= 1
    duree = len(results[0]) / RATE
    assert abs(duree - 2.0) < 0.3


def test_tick_sans_trames():
    """tick() détecte la fin de phrase même sans nouvelles trames."""
    seg = Segmenter(rms_threshold=350, silence_sec=0.5, min_speech_sec=0.3, max_segment_sec=25)
    # Voix pendant 1s
    t = 0.0
    for _ in range(20):
        seg.feed(_voix(DT), t)
        t += DT
    # Saut dans le temps de 1 seconde (aucune trame)
    t += 1.0
    result = seg.tick(t)
    assert result is not None


def test_silence_pur_sans_segment():
    """Silence seul → aucun segment."""
    seg = Segmenter(rms_threshold=350)
    blocs = [(_silence(DT), DT)] * 40
    results, t = _feed_blocs(seg, blocs)
    # tick final
    r = seg.tick(t + 2.0)
    if r is not None:
        results.append(r)
    assert results == []


def test_deux_phrases_successives():
    """Deux séquences voix/silence → deux segments distincts."""
    seg = Segmenter(rms_threshold=350, silence_sec=0.4, min_speech_sec=0.3, max_segment_sec=25)
    blocs = (
        [(_voix(DT), DT)] * 20   # phrase 1
        + [(_silence(DT), DT)] * 12  # silence
        + [(_voix(DT), DT)] * 20   # phrase 2
        + [(_silence(DT), DT)] * 12  # silence final
    )
    results, _ = _feed_blocs(seg, blocs)
    assert len(results) == 2


def test_preroll_inclus():
    """Le pré-roll doit être inclus dans le segment (durée > voix nette)."""
    seg = Segmenter(
        rms_threshold=350, silence_sec=0.4, min_speech_sec=0.3, max_segment_sec=25,
    )
    seg._preroll_sec = 0.3
    # 0.3s de silence (tombe dans le preroll), puis 0.5s de voix, puis silence
    blocs = (
        [(_silence(DT), DT)] * 6
        + [(_voix(DT), DT)] * 10
        + [(_silence(DT), DT)] * 12
    )
    results, _ = _feed_blocs(seg, blocs)
    assert len(results) == 1
    duree = len(results[0]) / RATE
    # Avec preroll, durée doit dépasser les seules 0.5s de voix
    assert duree > 0.5
