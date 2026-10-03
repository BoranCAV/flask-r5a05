# Entraînement Flask R5.A.05

Un site d'entraînement interactif pour préparer le contrôle papier de R5.A.05 (Flask modulaire, ORM SQLAlchemy, mixins). Le contenu est tiré du cours (CM01, CM02, TD01 à TD03).

- 3 sessions × 4 paliers × 3 leçons, plus un contrôle blanc (2 sujets de 1 h 30 notés sur 20) et 2 leçons bonus hors contrôle.
- Environ 250 exercices de 7 types : QCM et vrai/faux, code à trous, remettre dans l'ordre, relier, trouver le bug, écrire du code (tests cachés exécutés dans un sous-processus isolé), mode papier (chronomètre et grille de barème).
- Étoiles par leçon, tableau de bord `/progress`, révision ciblée des notions ratées. **Tout est accessible, sans verrou.**

## Démarrage rapide (double-clic)

1. Installe **Python 3.10 ou plus** depuis https://www.python.org/downloads/. Sous Windows, coche « Add python.exe to PATH ».
2. Dézippe le dossier, puis double-clique sur **`lancer.bat`** (Windows). Sous macOS ou Linux, lance `sh lancer.sh` dans un terminal.
3. Le premier lancement installe tout (environ 1 minute, connexion internet nécessaire). Le site s'ouvre ensuite sur http://localhost:8000.

Chacun a sa propre progression, enregistrée dans `app/training.db` sur sa machine.

## Installation manuelle (Windows)

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python seed.py
```

Sous Linux ou macOS : `source .venv/bin/activate` à la place de la 2e ligne.

## Lancement

```bash
python main.py
```

Puis ouvrir <http://localhost:8000>.

## Commandes utiles

| Commande | Effet |
| --- | --- |
| `python seed.py` | Recharge le contenu de `content/*.yaml` en gardant la progression |
| `python seed.py --reset` | Recharge le contenu et efface la progression |
| `python -m pytest` | Lance tous les tests (dont les solutions officielles exécutées dans le bac à sable) |

## Ajouter un exercice

Ajoute une entrée dans la leçon voulue de `content/sessionN.yaml`, puis relance `python seed.py`. Tu n'as pas besoin de toucher au code. Les champs communs sont `type`, `tags`, `enonce`, `indices`, `explication` et `solution`. Selon le type, il faut en plus :

| Type | Champs |
| --- | --- |
| `qcm` / `vf` | `choices` + `answer` (indice ou liste d'indices) ; pour `vf` : `answer: true/false` |
| `trous` | `code` avec des `[[0]]`, `[[1]]`… + `blanks` (une liste de réponses acceptées par trou) |
| `ordre` | `lines` dans l'ordre correct (l'affichage les mélange) |
| `relier` | `pairs` : `[notion, définition]` |
| `bug` | `code` + `fixes` : `{numéro_de_ligne: [corrections acceptées]}` |
| `code` | `starter`, `tests` (des fonctions `test_*` avec une docstring en français), `solution`, `setup` facultatif |
| `papier` | `duree` (en secondes), `grille` (`critere`, `points`, `auto` = nom d'un test), `tests` / `setup` facultatifs |

Dans `setup`, `fake_module('app.services.X', X=Classe)` simule un module du projet. Ça permet de valider des copies réalistes, comme `from app.services.BookService import BookService`.

## Architecture

Le site applique les conventions du cours :

```
main.py                     create_app() + run(port=8000)
seed.py                     YAML → base SQLite (via l'ORM)
app/__init__.py             application factory
app/models/                 Base + BaseModelMixin, Session, Palier, Lesson, Exercise/Tag (N-N), Attempt, Progress,
                            TrainingDAOInterface + TrainingSqliteORM (_query_with_relations, try/finally)
app/services/               CourseService, ProgressService (étoiles), GradingService, executor (bac à sable)
app/blueprints/             index, sessions, lessons, exercises, progress, exam
content/                    un fichier YAML par session
tests/                      étoiles, correction, exécuteur, routes, cohérence du contenu, solutions officielles
```

**Limite de sécurité.** Le code soumis tourne dans un sous-processus (`python -I`), dans un dossier temporaire, avec un timeout de 5 s et un *audit hook* qui bloque le réseau, les processus, les suppressions et les écritures hors du dossier. C'est un garde-fou suffisant pour un usage local par une seule personne, **pas un vrai bac à sable**. Pour exposer le site, il faudrait exécuter le code dans un conteneur.
