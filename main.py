import sys
import argparse

sys.stdout.reconfigure(encoding="utf-8")


def cmd_check():
    from copilote.ia import ClientIA
    try:
        ia = ClientIA()
    except ValueError as e:
        print(f"[ERREUR] {e}")
        return

    print("Modèles Flash disponibles sur votre compte :")
    for m in ia.lister_modeles_flash():
        print(f"  {m}")

    print("\nTest de connexion avec « Pouvez-vous vous présenter ? »…")
    try:
        msg, latence = ia.test_connexion()
        print(f"[OK] {msg}")
        cible = "✓ En dessous de la cible 3s" if latence < 3 else "⚠ Au-dessus de la cible 3s"
        print(f"Latence : {latence:.2f}s  {cible}")
    except Exception as e:
        print(f"[ERREUR] {e}")


def cmd_devices():
    from copilote.audio import AudioCapture
    print("Périphériques loopback WASAPI disponibles :")
    devs = AudioCapture.lister_peripheriques()
    if not devs:
        print("  Aucun périphérique trouvé.")
        return
    for d in devs:
        idx = d.get("index", "?")
        nom = d.get("name", "?")
        rate = int(d.get("defaultSampleRate", 0))
        ch = int(d.get("maxInputChannels", 0))
        print(f"  [{idx}] {nom}  ({ch} canal(aux), {rate} Hz)")


def cmd_ui():
    from PySide6.QtWidgets import QApplication, QMessageBox
    from copilote.ia import ClientIA
    from copilote.ui import FenetreUI

    app = QApplication(sys.argv)
    app.setApplicationName("Copilote d'entretien")

    try:
        ia = ClientIA()
    except ValueError as e:
        QMessageBox.critical(None, "Clé API manquante", str(e))
        sys.exit(1)

    fenetre = FenetreUI(ia)
    fenetre.show()
    sys.exit(app.exec())


def main():
    parser = argparse.ArgumentParser(description="Copilote d'entretien – aide en temps réel")
    parser.add_argument("--check", action="store_true", help="Vérifie la clé API et mesure la latence")
    parser.add_argument("--devices", action="store_true", help="Liste les périphériques loopback WASAPI")
    args = parser.parse_args()

    if args.check:
        cmd_check()
    elif args.devices:
        cmd_devices()
    else:
        cmd_ui()


if __name__ == "__main__":
    main()
