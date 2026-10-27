import time
from pydantic import BaseModel
from google import genai
from google.genai import types

from copilote.config import GEMINI_API_KEY, GEMINI_MODELS, HISTORY_TURNS
from copilote.prompts import construire_systeme


class Analyse(BaseModel):
    transcription: str
    est_question: bool
    langue: str
    reponse: str
    mots_cles: list[str]


class ClientIA:
    def __init__(self):
        if not GEMINI_API_KEY:
            raise ValueError(
                "GEMINI_API_KEY manquante. Créez un fichier .env avec votre clé."
            )
        self._client = genai.Client(
            api_key=GEMINI_API_KEY,
            http_options=types.HttpOptions(timeout=20_000),
        )
        self._modeles: list[str] = list(GEMINI_MODELS)
        self._modele_actuel: str = self._modeles[0] if self._modeles else ""
        self._no_thinking: set[str] = set()
        self._systeme: str = construire_systeme()
        self._historique: list[tuple[str, str]] = []

    def modele_actuel(self) -> str:
        return self._modele_actuel

    def lister_modeles_flash(self) -> list[str]:
        try:
            return [m.name for m in self._client.models.list() if "flash" in m.name.lower()]
        except Exception as e:
            return [f"Erreur: {e}"]

    def _historique_txt(self) -> str:
        if not self._historique:
            return ""
        lignes = ["# Historique récent"]
        for q, r in self._historique[-HISTORY_TURNS:]:
            lignes.append(f"Recruteur: {q}")
            lignes.append(f"Suggestion: {r}")
        return "\n".join(lignes)

    def _config(self, modele: str, avec_thinking: bool) -> types.GenerateContentConfig:
        kwargs: dict = dict(
            system_instruction=self._systeme,
            temperature=0.4,
            response_mime_type="application/json",
            response_schema=Analyse,
        )
        if avec_thinking:
            kwargs["thinking_config"] = types.ThinkingConfig(thinking_level="low")
        return types.GenerateContentConfig(**kwargs)

    def _appel_modele(self, contents: list, modele: str) -> tuple[Analyse, float]:
        avec_thinking = modele not in self._no_thinking
        t0 = time.monotonic()
        try:
            resp = self._client.models.generate_content(
                model=modele,
                contents=contents,
                config=self._config(modele, avec_thinking),
            )
        except Exception as e:
            msg = str(e).lower()
            if avec_thinking and ("thinking" in msg or "400" in msg or "validation" in msg):
                self._no_thinking.add(modele)
                resp = self._client.models.generate_content(
                    model=modele,
                    contents=contents,
                    config=self._config(modele, False),
                )
            else:
                raise
        return resp.parsed, time.monotonic() - t0

    def _essayer_modeles(self, contents: list) -> tuple[Analyse, float, str]:
        derniere_erreur = None
        for i, modele in enumerate(self._modeles):
            try:
                analyse, latence = self._appel_modele(contents, modele)
                if i != 0:
                    self._modeles.pop(i)
                    self._modeles.insert(0, modele)
                self._modele_actuel = modele
                return analyse, latence, modele
            except Exception as e:
                derniere_erreur = e
                if any(code in str(e) for code in ("404", "429", "503")):
                    continue
                raise
        raise RuntimeError(
            f"Tous les modèles ont échoué. Dernière erreur : {derniere_erreur}"
        )

    def analyser_audio(self, wav_bytes: bytes) -> tuple[Analyse, float, str]:
        hist = self._historique_txt()
        contents = []
        if hist:
            contents.append(hist)
        contents.append(
            types.Part.from_bytes(data=wav_bytes, mime_type="audio/wav")
        )
        contents.append("Analyse cet extrait audio et remplis le JSON.")
        analyse, latence, modele = self._essayer_modeles(contents)
        self._maj_historique(analyse)
        return analyse, latence, modele

    def analyser_texte(self, question: str) -> tuple[Analyse, float, str]:
        hist = self._historique_txt()
        contents = []
        if hist:
            contents.append(hist)
        contents.append(f"Question du recruteur (saisie manuelle) : {question}")
        analyse, latence, modele = self._essayer_modeles(contents)
        self._maj_historique(analyse)
        return analyse, latence, modele

    def _maj_historique(self, analyse: Analyse):
        if analyse.est_question and analyse.reponse:
            self._historique.append((analyse.transcription or "?", analyse.reponse))
            if len(self._historique) > HISTORY_TURNS:
                self._historique = self._historique[-HISTORY_TURNS:]

    def effacer_historique(self):
        self._historique.clear()

    def test_connexion(self) -> tuple[str, float]:
        analyse, latence, modele = self.analyser_texte("Pouvez-vous vous présenter ?")
        extrait = analyse.reponse[:80] + ("…" if len(analyse.reponse) > 80 else "")
        return f"OK · {modele} · {latence:.1f}s · {extrait}", latence
