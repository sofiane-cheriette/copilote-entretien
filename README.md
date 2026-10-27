# Interview Copilot

> Assistant IA en temps réel pour les entretiens professionnels en visio

[![CI](https://github.com/sofiane-cheriette/copilote-entretien/actions/workflows/ci.yml/badge.svg)](https://github.com/sofiane-cheriette/copilote-entretien/actions/workflows/ci.yml)
[![Python](https://img.shields.io/badge/Python-3.11%2B-blue?logo=python&logoColor=white)](https://www.python.org/)
[![PySide6](https://img.shields.io/badge/UI-PySide6-41CD52?logo=qt&logoColor=white)](https://doc.qt.io/qtforpython/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Platform](https://img.shields.io/badge/Platform-Windows-0078D4?logo=windows&logoColor=white)](https://www.microsoft.com/windows)

---

## Présentation

**Interview Copilot** écoute en temps réel la voix de votre interlocuteur pendant un entretien en visio (Teams, Zoom, Meet…) et vous suggère discrètement une réponse dès qu'il pose une question.

Le programme s'affiche sur un **second écran**, hors du partage, et ne capture que le son qui sort dans votre casque — c'est-à-dire uniquement la voix du recruteur.

```
┌─────────────────────────────────────────────────────────────────┐
│ ● Écoute en cours…  ████░░░░ RMS: 412  │ Casque Logitech ▼  1.2s│
├─────────────────────────────────────────────────────────────────┤
│ Il a dit :                                                       │
│ « Pouvez-vous vous présenter et m'expliquer votre projet ? »    │
├─────────────────────────────────────────────────────────────────┤
│ Réponse :                                                        │
│                                                                  │
│  Je suis en Master IA & Big Data et je cherche une alternance   │
│  pour mettre la data et l'automatisation au service d'un projet │
│  concret. Mon background fullstack me permet d'aller de l'idée  │
│  au déploiement rapidement.                                     │
├─────────────────────────────────────────────────────────────────┤
│ → e-commerce & SEO · données produits · déploiement OVH         │
└─────────────────────────────────────────────────────────────────┘
```

---

## Fonctionnalités

- **Capture loopback WASAPI** — écoute uniquement le son de votre casque, sans toucher au micro
- **Segmentation automatique** — détecte le début et la fin de chaque phrase du recruteur
- **Analyse par Gemini** — transcription + détection de question + suggestion de réponse en un seul appel
- **Réponse en 2 à 5 phrases** naturelles à la première personne, en français ou en anglais
- **Mots-clés** pour développer (exemples du CV, chiffres, technologies)
- **Historique de session** — l'IA comprend les relances (« et pourquoi ? », « un exemple ? »)
- **Saisie manuelle** — tapez une question pour tester sans audio
- **Vumètre RMS** — réglez le seuil de détection en direct
- **Sélecteur de périphérique** — choisissez le bon casque si vous en avez plusieurs
- **Toujours au-dessus** — la fenêtre reste visible même quand Teams est en plein écran
- **Raccourcis clavier** — F9 pause, Ctrl+/- taille du texte
- **Journal Markdown** — chaque session est sauvegardée dans `sessions/`
- **Bascule de modèles** — si un modèle est indisponible (429/503), passe automatiquement au suivant

---

## Prérequis

| Élément | Détail |
|---|---|
| OS | Windows 10 ou 11 |
| Python | 3.11 ou supérieur |
| Matériel | Casque audio branché à l'ordinateur |
| Clé API | [Google AI Studio](https://aistudio.google.com/apikey) (gratuit) |

> **Pourquoi Windows uniquement ?** La capture loopback WASAPI (écoute du son système sans micro virtuel) n'est disponible que sous Windows via la bibliothèque PyAudioWPatch.

---

## Installation

### 1. Cloner le dépôt

```bash
git clone https://github.com/sofiane-cheriette/copilote-entretien.git
cd copilote-entretien
```

### 2. Créer les fichiers de configuration

```bash
# Copiez et remplissez le fichier de configuration
copy .env.example .env

# Copiez et adaptez votre CV
copy cv.txt.example cv.txt

# Copiez et remplissez le contexte de l'entretien
copy contexte.txt.example contexte.txt
```

### 3. Configurer `.env`

```env
GEMINI_API_KEY=AIza...votre_clé...   # Obtenez-la sur aistudio.google.com/apikey
USER_NAME=Votre prénom               # Utilisé dans les suggestions de l'IA
```

Les autres valeurs ont des défauts raisonnables. Voir la section [Configuration](#configuration) pour les détails.

### 4. Lancer (méthode simple)

Double-cliquez sur **`lancer.bat`** — il crée le venv, installe les dépendances et démarre le programme.

### 5. Lancer (méthode manuelle)

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python main.py
```

---

## Configuration

Toutes les options se trouvent dans `.env` :

| Variable | Défaut | Description |
|---|---|---|
| `GEMINI_API_KEY` | *(requis)* | Clé API Google AI Studio |
| `USER_NAME` | `le candidat` | Votre prénom, utilisé dans le prompt |
| `GEMINI_MODELS` | `gemini-3.6-flash,...` | Liste de modèles, essayés dans l'ordre |
| `RMS_THRESHOLD` | `350` | Seuil de détection vocale (réglez avec le vumètre) |
| `SILENCE_SEC` | `1.0` | Silence en secondes avant de clore un segment |
| `MIN_SPEECH_SEC` | `0.7` | Durée minimale de voix pour envoyer à l'IA |
| `MAX_SEGMENT_SEC` | `25` | Coupure forcée si le recruteur parle trop longtemps |
| `FONT_SIZE` | `22` | Taille de police de la réponse (points) |
| `HISTORY_TURNS` | `6` | Nombre d'échanges gardés en contexte |

### Choisir le bon périphérique audio

Le son de votre logiciel de visio sort dans votre casque. Il faut sélectionner le **loopback de ce casque** dans la liste déroulante de l'interface.

Pour voir les périphériques disponibles avant de lancer l'interface :

```bash
python main.py --devices
```

### Régler le seuil RMS

Pendant l'utilisation, le vumètre affiche le niveau RMS en temps réel. Lancez une vidéo dans votre casque et observez :
- **Trop de faux déclenchements** (bruit de fond capté) → augmentez `RMS_THRESHOLD`
- **La voix n'est pas détectée** → diminuez `RMS_THRESHOLD`

---

## Utilisation

### Lancer l'interface

```bash
python main.py
```

### Vérifier la clé et les modèles disponibles

```bash
python main.py --check
```

Affiche les modèles Flash disponibles sur votre compte, fait un appel test et mesure la latence.

### Lister les périphériques audio

```bash
python main.py --devices
```

### Pendant l'entretien

1. Lancez le programme **avant** l'appel
2. Sélectionnez le loopback de votre casque dans la liste déroulante
3. Déplacez la fenêtre sur votre second écran (hors partage)
4. Cochez **« Toujours au-dessus »** si nécessaire
5. La fenêtre se met à jour automatiquement quand le recruteur parle

### Raccourcis clavier

| Touche | Action |
|---|---|
| `F9` | Pause / Reprendre l'écoute |
| `Ctrl` + `+` | Augmenter la taille du texte |
| `Ctrl` + `-` | Réduire la taille du texte |
| `Entrée` (champ texte) | Envoyer une question manuelle |

---

## Architecture

```
copilote-entretien/
├── main.py                  # Point d'entrée (--check, --devices, interface)
├── copilote/
│   ├── config.py            # Variables .env + chemins (compatible PyInstaller)
│   ├── prompts.py           # Construction du prompt système Gemini
│   ├── ia.py                # Client Gemini : JSON structuré, bascule modèles
│   ├── audio.py             # Capture WASAPI + classe Segmenter pure
│   └── ui.py                # Interface PySide6
├── tests/
│   └── test_segmenter.py    # Tests unitaires de la segmentation audio
├── .env.example             # Modèle de configuration
├── cv.txt.example           # Modèle de CV
├── contexte.txt.example     # Modèle de contexte d'entretien
├── requirements.txt         # Dépendances de production
├── requirements-test.txt    # Dépendances de test (CI)
├── lancer.bat               # Lancement en un clic (Windows)
└── build_exe.bat            # Build PyInstaller → CopiloteEntretien.exe
```

### Flux de données

```
Casque (loopback WASAPI)
        │
        ▼
   AudioCapture          Thread de capture
   ┌──────────┐
   │ Callback │ ──► queue.Queue ──► Segmenter.feed() / tick()
   └──────────┘                          │
                                         │ segment WAV 16 kHz
                                         ▼
                                   ThreadPoolExecutor
                                         │
                                         ▼
                                   ClientIA.analyser_audio()
                                         │
                                         ▼
                                   API Gemini → Analyse (JSON)
                                         │
                                         ▼
                                   Signal Qt → UI (thread principal)
```

### Segmentation audio

La classe `Segmenter` est **pure** (pas d'I/O, testable sans carte son) :

- Reçoit des blocs mono 16 kHz via `feed(bloc, t)`
- Maintient une fenêtre de pré-roll (300 ms) pour ne pas couper le début des phrases
- Détecte la fin via `tick(t)` même en l'absence de nouvelles trames (loopback silencieux)
- Rejette les segments trop courts (`MIN_SPEECH_SEC`) pour éviter les bruits parasites

---

## Build (exécutable Windows)

```bash
build_exe.bat
```

Produit `dist/CopiloteEntretien.exe` avec `.env`, `cv.txt` et `contexte.txt` copiés à côté. L'exe est autonome — Python n'est pas requis sur la machine cible.

> Si le démarrage est lent, éditez `build_exe.bat` et remplacez `--onefile` par `--onedir`.

---

## Tests

```bash
pip install -r requirements-test.txt
pytest tests/ -v
```

Les tests couvrent la logique de segmentation audio sans dépendance matérielle :

| Test | Ce qui est vérifié |
|---|---|
| `test_segment_simple` | Un segment est produit après voix + silence |
| `test_segment_trop_court` | Les segments < `MIN_SPEECH_SEC` sont rejetés |
| `test_coupure_forcee` | La coupure à `MAX_SEGMENT_SEC` fonctionne |
| `test_tick_sans_trames` | `tick()` détecte la fin sans nouvelles trames |
| `test_silence_pur_sans_segment` | Le silence seul ne produit rien |
| `test_deux_phrases_successives` | Deux phrases distinctes → deux segments |
| `test_preroll_inclus` | Le pré-roll est bien inclus dans le segment |

---

## Dépendances

| Bibliothèque | Rôle |
|---|---|
| [`google-genai`](https://pypi.org/project/google-genai/) | SDK Gemini (transcription + réponse) |
| [`pydantic`](https://docs.pydantic.dev/) | Schéma JSON structuré pour les réponses IA |
| [`PySide6`](https://doc.qt.io/qtforpython/) | Interface graphique |
| [`PyAudioWPatch`](https://github.com/s0d3s/PyAudioWPatch) | Capture loopback WASAPI (Windows) |
| [`numpy`](https://numpy.org/) | Traitement du signal (RMS, rééchantillonnage) |
| [`python-dotenv`](https://pypi.org/project/python-dotenv/) | Chargement de `.env` |
| [`pyinstaller`](https://pyinstaller.org/) | Compilation en `.exe` |

---

## Contribuer

Les contributions sont les bienvenues. Pour proposer une amélioration :

1. Forkez le dépôt
2. Créez une branche (`git checkout -b feature/ma-feature`)
3. Committez vos changements (`git commit -m 'feat: ma feature'`)
4. Poussez la branche (`git push origin feature/ma-feature`)
5. Ouvrez une Pull Request

Assurez-vous que `pytest tests/ -v` passe avant de soumettre.

---

## Idées d'améliorations futures

- **Mode local** — transcription avec faster-whisper (GPU) + LLM local via Ollama
- **Capture du micro** — suivre ses propres réponses pour enrichir l'historique
- **Streaming** — afficher la transcription mot par mot en temps réel
- **Thèmes** — mode clair / mode sombre configurable

---

## Licence

MIT — voir [LICENSE](LICENSE).
