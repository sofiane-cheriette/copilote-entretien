<div align="center">

# 🎤 Interview Copilot

**Assistant IA en temps réel pour les entretiens professionnels en visio**

[![CI](https://github.com/sofiane-cheriette/copilote-entretien/actions/workflows/ci.yml/badge.svg)](https://github.com/sofiane-cheriette/copilote-entretien/actions/workflows/ci.yml)
[![Python](https://img.shields.io/badge/Python-3.11%2B-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![PySide6](https://img.shields.io/badge/UI-PySide6-41CD52?logo=qt&logoColor=white)](https://doc.qt.io/qtforpython/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Platform](https://img.shields.io/badge/Platform-Windows-0078D4?logo=windows&logoColor=white)](https://www.microsoft.com/windows)

[Fonctionnalités](#-fonctionnalités) · [Installation](#-installation) · [Configuration](#-configuration) · [Architecture](#%EF%B8%8F-architecture) · [Tests](#-tests)

</div>

---

## 🧠 Présentation

Interview Copilot écoute la voix de votre interlocuteur pendant un entretien en visio (**Teams, Zoom, Meet…**) et vous suggère une réponse en temps réel, dès qu'il pose une question.

La fenêtre s'affiche sur votre **second écran**, hors du partage d'écran. Le programme ne capte que le son qui sort dans votre casque — uniquement la voix du recruteur, pas la vôtre.

```
┌─────────────────────────────────────────────────────────────────────┐
│  ● Écoute en cours…   ████████░░  RMS: 480  │  Casque ▼     1.4s  │
├─────────────────────────────────────────────────────────────────────┤
│  Il a dit :                                                          │
│  « Pouvez-vous me parler de votre expérience la plus marquante ? »  │
├─────────────────────────────────────────────────────────────────────┤
│  Réponse :                                                           │
│                                                                      │
│   Ma mission la plus structurante a été le développement d'une      │
│   plateforme e-commerce de A à Z, du design à la mise en prod.      │
│   Ce projet m'a appris à gérer les imprévus et à livrer dans les    │
│   délais, même seul sur un périmètre complet.                       │
├─────────────────────────────────────────────────────────────────────┤
│  → paiement Stripe · déploiement OVH · React / Node.js              │
└─────────────────────────────────────────────────────────────────────┘
```

---

## ✨ Fonctionnalités

- 🎧 **Capture loopback WASAPI** — écoute le son système sans micro virtuel ni logiciel tiers
- ✂️ **Segmentation automatique** — détecte le début et la fin de chaque prise de parole
- 🤖 **Analyse par Gemini** — transcription + détection de question + suggestion en un seul appel API
- 💬 **Réponses naturelles** — 2 à 5 phrases à la première personne, adaptées à votre CV
- 🏷️ **Mots-clés** — 3 à 5 repères pour développer (chiffres, technologies, expériences)
- 🔄 **Historique de contexte** — l'IA comprend les relances (« et pourquoi ? », « un exemple ? »)
- ⌨️ **Saisie manuelle** — testez une question sans audio
- 📊 **Vumètre RMS** — réglez le seuil de détection vocale en direct
- 🔌 **Sélecteur de périphérique** — choisissez le bon casque si vous en avez plusieurs
- 📌 **Toujours au-dessus** — reste visible même quand la visio est en plein écran
- ⚡ **Bascule de modèles** — si un modèle est indisponible (429/503), passe automatiquement au suivant
- 📝 **Journal Markdown** — chaque session est sauvegardée dans `sessions/`

---

## 🚀 Installation

### Prérequis

| Élément | Détail |
|---|---|
| **OS** | Windows 10 ou 11 |
| **Python** | 3.11 ou supérieur |
| **Matériel** | Casque audio connecté |
| **Clé API** | [Google AI Studio](https://aistudio.google.com/apikey) — gratuit |

> La capture loopback WASAPI est une fonctionnalité exclusive à Windows. Elle permet d'écouter le son du système sans installer de pilote virtuel.

### Étapes

**1. Cloner le dépôt**

```bash
git clone https://github.com/sofiane-cheriette/copilote-entretien.git
cd copilote-entretien
```

**2. Créer les fichiers de configuration**

```bash
copy .env.example     .env
copy cv.txt.example   cv.txt
copy contexte.txt.example  contexte.txt
```

**3. Remplir `.env`**

```env
GEMINI_API_KEY=AIza...   # https://aistudio.google.com/apikey
USER_NAME=Votre prénom   # Utilisé dans les suggestions
```

**4. Remplir `cv.txt` et `contexte.txt`** avec votre CV et les informations sur l'entretien.

**5. Lancer**

```bash
# Méthode simple (crée le venv et installe automatiquement)
lancer.bat

# Méthode manuelle
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python main.py
```

---

## ⚙️ Configuration

Toutes les options se trouvent dans `.env` :

| Variable | Défaut | Description |
|---|---|---|
| `GEMINI_API_KEY` | *(requis)* | Clé API Google AI Studio |
| `USER_NAME` | `le candidat` | Votre prénom, utilisé dans le prompt |
| `GEMINI_MODELS` | `gemini-3.6-flash,…` | Modèles essayés dans l'ordre, avec bascule automatique |
| `RMS_THRESHOLD` | `350` | Seuil de détection vocale (ajustez avec le vumètre) |
| `SILENCE_SEC` | `1.0` | Silence en secondes avant de clore une prise de parole |
| `MIN_SPEECH_SEC` | `0.7` | Durée minimale pour qu'un segment soit envoyé à l'IA |
| `MAX_SEGMENT_SEC` | `25` | Coupure forcée si l'interlocuteur parle trop longtemps |
| `FONT_SIZE` | `22` | Taille de la police de réponse (points) |
| `HISTORY_TURNS` | `6` | Nombre d'échanges gardés en contexte |

### Choisir le bon périphérique audio

```bash
python main.py --devices
```

Sélectionnez le **loopback de votre casque** dans la liste déroulante (ex. `Haut-parleurs (Logitech) [Loopback]`). C'est le flux qui contient uniquement la voix de votre interlocuteur.

### Vérifier la clé API

```bash
python main.py --check
```

Affiche les modèles disponibles, effectue un appel test et mesure la latence (cible : < 3 s).

---

## ⌨️ Raccourcis clavier

| Touche | Action |
|---|---|
| `F9` | Pause / Reprendre l'écoute |
| `Ctrl` `+` | Agrandir le texte de réponse |
| `Ctrl` `-` | Réduire le texte de réponse |
| `Entrée` | Envoyer une question manuelle (champ texte en bas) |

---

## 🏗️ Architecture

```
copilote-entretien/
├── main.py                     # Point d'entrée — CLI (--check, --devices) + UI
├── copilote/
│   ├── config.py               # Variables .env + chemins (compatible PyInstaller)
│   ├── prompts.py              # Construction du prompt système Gemini
│   ├── ia.py                   # Client Gemini : JSON structuré, bascule de modèles
│   ├── audio.py                # Capture WASAPI + Segmenter (classe pure)
│   └── ui.py                   # Interface PySide6
├── tests/
│   └── test_segmenter.py       # Tests unitaires — segmentation sans matériel
├── .github/
│   └── workflows/ci.yml        # CI GitHub Actions
├── .env.example                # Modèle de configuration
├── cv.txt.example              # Modèle de CV
├── contexte.txt.example        # Modèle de contexte d'entretien
├── requirements.txt            # Dépendances de production
├── requirements-test.txt       # Dépendances légères pour la CI
├── lancer.bat                  # Lancement en un clic
└── build_exe.bat               # Build PyInstaller → CopiloteEntretien.exe
```

### Flux de données

```
  Casque (loopback WASAPI)
          │
          ▼
    AudioCapture                         thread dédié
    ┌─────────────────┐
    │ stream_callback │──► Queue ──► Segmenter.feed() / .tick()
    └─────────────────┘                       │
                                              │  WAV 16 kHz mono
                                              ▼
                                    ThreadPoolExecutor (2 workers)
                                              │
                                              ▼
                                    ClientIA.analyser_audio()
                                              │
                                              ▼
                              ┌───────────────────────────────┐
                              │  API Gemini                    │
                              │  system prompt + historique   │
                              │  + audio → JSON (Pydantic)    │
                              └───────────────────────────────┘
                                              │
                                              ▼
                                    Signal Qt → thread principal
                                              │
                                              ▼
                                    FenetreUI.maj_analyse()
```

### La classe `Segmenter`

`Segmenter` est **pure** (zéro I/O, testable sans matériel) et gère :

| Mécanisme | Détail |
|---|---|
| **Pré-roll** | Fenêtre glissante de 300 ms incluse au début de chaque segment |
| **Détection vocale** | Seuil RMS configurable par bloc de 50 ms |
| **Fin par silence** | `SILENCE_SEC` sans voix → segment clos |
| **Fin par tick** | `tick(t)` détecte le silence même sans nouvelles trames audio |
| **Coupure forcée** | `MAX_SEGMENT_SEC` évite les segments trop longs |
| **Rejet court** | Segments < `MIN_SPEECH_SEC` ignorés (bruits parasites) |

---

## 🧪 Tests

```bash
pip install -r requirements-test.txt
pytest tests/ -v
```

| Test | Scénario couvert |
|---|---|
| `test_segment_simple` | Voix + silence → un segment produit |
| `test_segment_trop_court` | Voix < `MIN_SPEECH_SEC` → segment rejeté |
| `test_coupure_forcee` | Voix longue → coupure à `MAX_SEGMENT_SEC` |
| `test_tick_sans_trames` | `tick()` détecte la fin sans nouvelles trames |
| `test_silence_pur_sans_segment` | Silence seul → aucun segment |
| `test_deux_phrases_successives` | Deux prises de parole → deux segments distincts |
| `test_preroll_inclus` | Le pré-roll est bien inclus dans le segment |

---

## 📦 Build (exécutable Windows)

```bash
build_exe.bat
```

Produit `dist/CopiloteEntretien.exe` autonome — Python n'est pas requis sur la machine cible. Le script copie automatiquement `.env`, `cv.txt` et `contexte.txt` dans `dist/`.

> Si le démarrage est trop lent, remplacez `--onefile` par `--onedir` dans `build_exe.bat`.

---

## 📚 Dépendances

| Bibliothèque | Rôle |
|---|---|
| [`google-genai`](https://pypi.org/project/google-genai/) | SDK Gemini — transcription + réponse JSON |
| [`pydantic`](https://docs.pydantic.dev/) | Schéma de réponse structurée |
| [`PySide6`](https://doc.qt.io/qtforpython/) | Interface graphique |
| [`PyAudioWPatch`](https://github.com/s0d3s/PyAudioWPatch) | Capture loopback WASAPI (Windows) |
| [`numpy`](https://numpy.org/) | RMS, rééchantillonnage, normalisation |
| [`python-dotenv`](https://pypi.org/project/python-dotenv/) | Chargement de `.env` |
| [`pyinstaller`](https://pyinstaller.org/) | Compilation en `.exe` |

---

## 🔭 Pistes d'amélioration

- **Mode local** — transcription avec `faster-whisper` (GPU) + LLM local via Ollama
- **Capture du micro** — suivre ses propres réponses pour enrichir l'historique
- **Streaming** — afficher la transcription mot par mot en temps réel
- **Multi-OS** — support macOS/Linux via BlackHole ou PulseAudio

---

## 🤝 Contribuer

1. Forkez le dépôt
2. Créez une branche : `git checkout -b feature/ma-feature`
3. Committez : `git commit -m 'feat: description'`
4. Poussez : `git push origin feature/ma-feature`
5. Ouvrez une Pull Request

Assurez-vous que `pytest tests/ -v` passe avant de soumettre.

---

## 📄 Licence

MIT — voir [LICENSE](LICENSE).
