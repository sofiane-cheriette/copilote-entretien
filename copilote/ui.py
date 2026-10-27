from concurrent.futures import ThreadPoolExecutor
from datetime import datetime

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QComboBox, QTextEdit, QLineEdit, QPushButton, QProgressBar,
    QFrame, QCheckBox, QSizePolicy,
)
from PySide6.QtCore import Qt, Signal, QObject
from PySide6.QtGui import QFont, QKeySequence, QShortcut

from copilote.config import FONT_SIZE, SESSIONS_DIR
from copilote.ia import ClientIA, Analyse
from copilote.audio import AudioCapture

_STYLE = """
QMainWindow, QWidget {
    background: #1a1a2e;
    color: #e0e0e0;
    font-family: "Segoe UI", sans-serif;
}
QLabel { color: #e0e0e0; }
QLineEdit, QTextEdit {
    background: #16213e;
    color: #e0e0e0;
    border: 1px solid #0f3460;
    border-radius: 4px;
    padding: 4px;
}
QPushButton {
    background: #0f3460;
    color: #e0e0e0;
    border: none;
    border-radius: 4px;
    padding: 6px 14px;
}
QPushButton:hover { background: #1a4f8a; }
QPushButton:pressed { background: #0a2a4a; }
QComboBox {
    background: #16213e;
    color: #e0e0e0;
    border: 1px solid #0f3460;
    border-radius: 4px;
    padding: 4px;
}
QComboBox QAbstractItemView {
    background: #16213e;
    color: #e0e0e0;
    selection-background-color: #0f3460;
}
QScrollBar:vertical {
    background: #16213e;
    width: 8px;
    border-radius: 4px;
}
QScrollBar::handle:vertical {
    background: #0f3460;
    border-radius: 4px;
    min-height: 20px;
}
QProgressBar {
    background: #16213e;
    border-radius: 4px;
    border: none;
}
QProgressBar::chunk {
    background: #4caf50;
    border-radius: 4px;
}
QCheckBox { color: #888; font-size: 11px; }
"""


class _Signaux(QObject):
    rms_recu = Signal(float)
    analyse_recue = Signal(object, float, str, int)
    erreur = Signal(str)
    etat = Signal(str)


class FenetreUI(QMainWindow):
    def __init__(self, ia: ClientIA):
        super().__init__()
        self._ia = ia
        self._sig = _Signaux()
        self._executor = ThreadPoolExecutor(max_workers=2)
        self._seq = 0
        self._seq_dernier = -1
        self._capture: AudioCapture | None = None
        self._en_pause = False
        self._font_size = FONT_SIZE
        self._devs: list[dict] = []

        SESSIONS_DIR.mkdir(exist_ok=True)
        nom = datetime.now().strftime("entretien_%Y-%m-%d_%H%M.md")
        self._journal = SESSIONS_DIR / nom
        with open(self._journal, "w", encoding="utf-8") as f:
            f.write(f"# Session du {datetime.now().strftime('%d/%m/%Y %H:%M')}\n\n")

        self._init_ui()
        self._connecter_signaux()
        self._demarrer_capture()

    # ------------------------------------------------------------------ UI --

    def _init_ui(self):
        self.setWindowTitle("Copilote d'entretien")
        self.setMinimumSize(720, 540)
        self.setStyleSheet(_STYLE)

        central = QWidget()
        self.setCentralWidget(central)
        root = QVBoxLayout(central)
        root.setSpacing(8)
        root.setContentsMargins(12, 12, 12, 12)

        # Barre supérieure
        top = QHBoxLayout()

        self._lbl_etat = QLabel("En attente…")
        self._lbl_etat.setStyleSheet("font-weight: bold; color: #69f0ae; font-size: 13px;")
        top.addWidget(self._lbl_etat)

        self._barre_rms = QProgressBar()
        self._barre_rms.setRange(0, 1000)
        self._barre_rms.setValue(0)
        self._barre_rms.setMaximumWidth(110)
        self._barre_rms.setFixedHeight(14)
        self._barre_rms.setTextVisible(False)
        top.addWidget(self._barre_rms)

        self._lbl_rms = QLabel("RMS: 0")
        self._lbl_rms.setStyleSheet("color: #666; font-size: 11px;")
        self._lbl_rms.setMinimumWidth(60)
        top.addWidget(self._lbl_rms)

        top.addStretch()

        self._combo_devs = QComboBox()
        self._combo_devs.setMaximumWidth(220)
        self._combo_devs.setToolTip("Périphérique audio loopback")
        self._remplir_periph()
        self._combo_devs.currentIndexChanged.connect(self._changer_periph)
        top.addWidget(self._combo_devs)

        self._lbl_modele = QLabel("")
        self._lbl_modele.setStyleSheet("color: #666; font-size: 11px;")
        top.addWidget(self._lbl_modele)

        self._lbl_latence = QLabel("")
        self._lbl_latence.setStyleSheet("color: #666; font-size: 11px;")
        top.addWidget(self._lbl_latence)

        self._chk_dessus = QCheckBox("Toujours au-dessus")
        self._chk_dessus.stateChanged.connect(self._toggle_dessus)
        top.addWidget(self._chk_dessus)

        root.addLayout(top)
        root.addWidget(_separateur())

        # Transcription
        self._lbl_il_a_dit = QLabel("Il a dit :")
        self._lbl_il_a_dit.setStyleSheet("color: #888; font-size: 12px;")
        root.addWidget(self._lbl_il_a_dit)

        self._lbl_transcription = QLabel("")
        self._lbl_transcription.setWordWrap(True)
        self._lbl_transcription.setStyleSheet(
            "color: #999; font-style: italic; font-size: 13px; padding: 4px 4px 2px 4px;"
        )
        root.addWidget(self._lbl_transcription)

        # Réponse
        lbl_rep_titre = QLabel("Réponse :")
        lbl_rep_titre.setStyleSheet("color: #ccc; font-size: 12px;")
        root.addWidget(lbl_rep_titre)

        self._lbl_reponse = QLabel("")
        self._lbl_reponse.setWordWrap(True)
        self._lbl_reponse.setFont(QFont("Segoe UI", self._font_size))
        self._lbl_reponse.setStyleSheet(
            "color: #ffffff; padding: 10px; background: #16213e; border-radius: 6px;"
        )
        self._lbl_reponse.setMinimumHeight(90)
        self._lbl_reponse.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        root.addWidget(self._lbl_reponse)

        # Mots-clés
        self._lbl_mots_cles = QLabel("")
        self._lbl_mots_cles.setWordWrap(True)
        self._lbl_mots_cles.setStyleSheet(
            "color: #e94560; font-size: 14px; font-weight: bold; padding: 4px;"
        )
        root.addWidget(self._lbl_mots_cles)

        root.addWidget(_separateur())

        # Historique
        lbl_hist = QLabel("Historique")
        lbl_hist.setStyleSheet("color: #666; font-size: 11px;")
        root.addWidget(lbl_hist)

        self._txt_hist = QTextEdit()
        self._txt_hist.setReadOnly(True)
        self._txt_hist.setMaximumHeight(110)
        self._txt_hist.setStyleSheet("font-size: 11px; color: #888;")
        root.addWidget(self._txt_hist)

        root.addWidget(_separateur())

        # Barre basse
        bas = QHBoxLayout()

        self._saisie = QLineEdit()
        self._saisie.setPlaceholderText("Tapez une question et appuyez sur Entrée…")
        self._saisie.returnPressed.connect(self._soumettre_texte)
        bas.addWidget(self._saisie)

        self._btn_pause = QPushButton("Pause  F9")
        self._btn_pause.clicked.connect(self._toggle_pause)
        bas.addWidget(self._btn_pause)

        btn_effacer = QPushButton("Effacer")
        btn_effacer.clicked.connect(self._effacer)
        bas.addWidget(btn_effacer)

        btn_test = QPushButton("Tester API")
        btn_test.clicked.connect(self._tester_api)
        bas.addWidget(btn_test)

        root.addLayout(bas)

        # Raccourcis
        QShortcut(QKeySequence("F9"), self).activated.connect(self._toggle_pause)
        QShortcut(QKeySequence("Ctrl++"), self).activated.connect(self._agrandir_police)
        QShortcut(QKeySequence("Ctrl+-"), self).activated.connect(self._reduire_police)
        QShortcut(QKeySequence("Ctrl+="), self).activated.connect(self._agrandir_police)

    def _connecter_signaux(self):
        self._sig.rms_recu.connect(self._maj_rms)
        self._sig.analyse_recue.connect(self._maj_analyse)
        self._sig.erreur.connect(self._afficher_erreur)
        self._sig.etat.connect(self._maj_etat)

    # --------------------------------------------------------------- Audio --

    def _remplir_periph(self):
        self._combo_devs.blockSignals(True)
        self._combo_devs.clear()
        self._devs = AudioCapture.lister_peripheriques()
        for d in self._devs:
            self._combo_devs.addItem(d.get("name", "?")[:42])
        self._combo_devs.blockSignals(False)

    def _changer_periph(self, idx: int):
        if not self._devs or idx < 0 or idx >= len(self._devs):
            return
        dev_idx = self._devs[idx].get("index")
        if self._capture:
            self._capture.arreter()
        self._demarrer_capture(device_index=dev_idx)

    def _demarrer_capture(self, device_index=None):
        self._capture = AudioCapture(
            on_segment=self._sur_segment,
            on_rms=lambda v: self._sig.rms_recu.emit(v),
            device_index=device_index,
        )
        self._capture.demarrer()
        self._sig.etat.emit("Écoute en cours…")

    def _sur_segment(self, wav: bytes):
        if self._en_pause:
            return
        self._seq += 1
        seq = self._seq
        self._sig.etat.emit("Analyse en cours…")
        self._executor.submit(self._analyser_audio, wav, seq)

    def _analyser_audio(self, wav: bytes, seq: int):
        try:
            analyse, latence, modele = self._ia.analyser_audio(wav)
            self._sig.analyse_recue.emit(analyse, latence, modele, seq)
        except Exception as e:
            self._sig.erreur.emit(f"Analyse audio : {e}")

    def _soumettre_texte(self):
        question = self._saisie.text().strip()
        if not question:
            return
        self._saisie.clear()
        self._seq += 1
        seq = self._seq
        self._sig.etat.emit("Analyse en cours…")
        self._executor.submit(self._analyser_texte, question, seq)

    def _analyser_texte(self, question: str, seq: int):
        try:
            analyse, latence, modele = self._ia.analyser_texte(question)
            self._sig.analyse_recue.emit(analyse, latence, modele, seq)
        except Exception as e:
            self._sig.erreur.emit(f"Saisie manuelle : {e}")

    # ------------------------------------------------------------ Slots Qt --

    def _maj_rms(self, valeur: float):
        self._barre_rms.setValue(int(min(valeur, 1000)))
        self._lbl_rms.setText(f"RMS: {int(valeur)}")

    def _maj_analyse(self, analyse_obj, latence: float, modele: str, seq: int):
        if seq < self._seq_dernier:
            return
        self._seq_dernier = seq
        analyse: Analyse = analyse_obj

        nom_modele = modele.split("/")[-1]
        self._lbl_modele.setText(nom_modele)
        self._lbl_latence.setText(f"{latence:.1f}s")
        self._lbl_transcription.setText(analyse.transcription)

        if analyse.est_question:
            self._lbl_reponse.setText(analyse.reponse)
            self._lbl_mots_cles.setText(" · ".join(analyse.mots_cles))
        else:
            # Ne pas effacer la dernière réponse affichée
            if analyse.mots_cles:
                self._lbl_mots_cles.setText(" · ".join(analyse.mots_cles))

        self._ajouter_historique(analyse)
        self._enregistrer(analyse, latence)
        self._sig.etat.emit("Écoute en cours…")

    def _ajouter_historique(self, analyse: Analyse):
        if not analyse.transcription:
            return
        txt = f"[{analyse.langue}] {analyse.transcription}"
        if analyse.est_question and analyse.reponse:
            txt += f"\n→ {analyse.reponse[:90]}{'…' if len(analyse.reponse) > 90 else ''}"
        self._txt_hist.append(txt)

    def _enregistrer(self, analyse: Analyse, latence: float):
        ts = datetime.now().strftime("%H:%M:%S")
        lignes = [f"\n## {ts} — {latence:.1f}s\n\n"]
        lignes.append(f"**Recruteur :** {analyse.transcription}\n\n")
        if analyse.est_question and analyse.reponse:
            lignes.append(f"**Réponse :** {analyse.reponse}\n\n")
        if analyse.mots_cles:
            lignes.append(f"**Mots-clés :** {', '.join(analyse.mots_cles)}\n")
        try:
            with open(self._journal, "a", encoding="utf-8") as f:
                f.writelines(lignes)
        except OSError:
            pass

    def _afficher_erreur(self, msg: str):
        self._lbl_etat.setText(f"Erreur : {msg[:90]}")
        self._lbl_etat.setStyleSheet("font-weight: bold; color: #ff5252; font-size: 13px;")

    def _maj_etat(self, msg: str):
        self._lbl_etat.setText(msg)
        if "erreur" in msg.lower():
            couleur = "#ff5252"
        elif "analyse" in msg.lower():
            couleur = "#ffd740"
        else:
            couleur = "#69f0ae"
        self._lbl_etat.setStyleSheet(f"font-weight: bold; color: {couleur}; font-size: 13px;")

    # ------------------------------------------------------------ Commandes --

    def _toggle_pause(self):
        self._en_pause = not self._en_pause
        if self._en_pause:
            self._btn_pause.setText("Reprendre  F9")
            self._sig.etat.emit("En pause")
        else:
            self._btn_pause.setText("Pause  F9")
            self._sig.etat.emit("Écoute en cours…")

    def _effacer(self):
        self._lbl_transcription.setText("")
        self._lbl_reponse.setText("")
        self._lbl_mots_cles.setText("")
        self._txt_hist.clear()
        self._ia.effacer_historique()

    def _tester_api(self):
        self._sig.etat.emit("Test API…")
        def _test():
            try:
                msg, _ = self._ia.test_connexion()
                self._sig.etat.emit(f"Test OK : {msg[:70]}")
            except Exception as e:
                self._sig.erreur.emit(f"Test API : {e}")
        self._executor.submit(_test)

    def _toggle_dessus(self, state: int):
        flags = self.windowFlags()
        if state:
            self.setWindowFlags(flags | Qt.WindowStaysOnTopHint)
        else:
            self.setWindowFlags(flags & ~Qt.WindowStaysOnTopHint)
        self.show()

    def _agrandir_police(self):
        self._font_size = min(self._font_size + 2, 48)
        self._lbl_reponse.setFont(QFont("Segoe UI", self._font_size))

    def _reduire_police(self):
        self._font_size = max(self._font_size - 2, 10)
        self._lbl_reponse.setFont(QFont("Segoe UI", self._font_size))

    def closeEvent(self, event):
        if self._capture:
            self._capture.arreter()
        self._executor.shutdown(wait=False)
        event.accept()


def _separateur() -> QFrame:
    sep = QFrame()
    sep.setFrameShape(QFrame.HLine)
    sep.setStyleSheet("background: #0f3460; max-height: 1px;")
    return sep
