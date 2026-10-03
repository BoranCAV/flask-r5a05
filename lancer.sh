#!/bin/sh
# macOS / Linux : installe au premier lancement, puis démarre le site sur http://localhost:8000
cd "$(dirname "$0")" || exit 1

if ! command -v python3 >/dev/null 2>&1; then
    echo "Python 3 est introuvable : installe-le depuis https://www.python.org/downloads/"
    exit 1
fi

if [ ! -x .venv/bin/python ]; then
    echo "Premier lancement : installation, ça prend une minute..."
    python3 -m venv .venv && .venv/bin/python -m pip install --quiet -r requirements.txt && .venv/bin/python seed.py || {
        echo "L'installation a échoué (connexion internet ? Python 3.10 ou plus ?)"
        exit 1
    }
fi

echo "Le site démarre sur http://localhost:8000 (Ctrl+C pour l'arrêter)"
( sleep 3; open http://localhost:8000 2>/dev/null || xdg-open http://localhost:8000 2>/dev/null ) &
exec .venv/bin/python main.py
