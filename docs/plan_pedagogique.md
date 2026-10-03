# Plan pédagogique — site d'entraînement « Flask R5.A.05 »

> Étape 1 du prompt : le plan est à valider **avant** de passer au code.
> Sources lues : CM01, TD01 (+ `TD01_correction`, `TD01_correction_simple`), CM02, TD02
> (+ `films.py`, `TD02_correction`), TD03 (+ `TD03_correction`, schéma `prepa_db.py`).
> Périmètre du contrôle : tout **sauf Jinja et la gestion des utilisateurs** (login, sessions Flask,
> bcrypt, `reqlogged`). Ces sujets n'apparaissent qu'en bonus marqué « hors contrôle ».

---

## 0. Ce qu'il faut retenir des sources (conventions du prof à reproduire)

| Élément | Convention du cours | Source |
| --- | --- | --- |
| Lancement | `main.py` : `app = create_app()` puis `app.run(host="localhost", port=8000, debug=True)` | TD01–03 |
| Factory | `create_app()` dans `app/__init__.py`, `app.config['DATABASE_PATH']`, `SQLALCHEMY_DATABASE_URI`, import des blueprints **dans** la fonction | TD01 |
| Blueprint | `xxx_bp = Blueprint('xxx', __name__, template_folder="templates")` dans `blueprints/xxx/routes.py` | TD01 |
| Export | `blueprints/xxx/__init__.py` : `from .routes import xxx_bp` + `__all__ = ['xxx_bp']` ; `blueprints/__init__.py` réexporte tout | TD01 |
| Enregistrement | `app.register_blueprint(movies_bp, url_prefix='/movies')` | TD02/03 |
| Routes | `@bp.route('/<int:movie_id>', methods=['GET'])`, `request.args.get('myear')`, `request.form['index']` | TD01 |
| Modèle classique | `__init__` avec valeurs `None`, `to_dict()`, `__getitem__` (getattr), `__contains__`, `__repr__` | TD01 `Movie.py` |
| DAO sqlite3 | `MovieSqliteDAO(MovieDAOInterface)`, `connect()` + `row_factory = sqlite3.Row`, requêtes paramétrées `?`, `conn.close()` | TD01 |
| Interface | classe avec méthodes `pass` + docstring : `connect`, `findAll(limit)`, `findById`, `findByYear`… | TD01/02 |
| Service | `MovieService`, DAO instancié dans `__init__` via `current_app.config[...]`, noms `getMoviesYears`, `getAllMovies(limit=100)` | TD01/02 |
| ORM base | `base.py` : `Base = declarative_base()`, `BaseModelMixin` (`__getitem__` qui lève `KeyError`, `to_dict()` sur `self.__table__.columns`), `get_engine()` | TD02 |
| Associations | `associations.py` : `Table('movie_genres', Base.metadata, Column(..., ForeignKey('movies.id', ondelete='CASCADE'), primary_key=True), ...)` | TD02 |
| Modèle ORM | `class Actor(Base, BaseModelMixin)` (**cet ordre**), `__tablename__`, `Column(String(150), unique=True, nullable=False, index=True)` | TD02 |
| Relations | `relationship('Movie', back_populates='director')`, 1-1 avec `uselist=False`, `cascade='all, delete-orphan'`, N-N avec `secondary=` | TD02/03 |
| DAO ORM | `MovieSqliteORM` : `sessionmaker(bind=engine, expire_on_commit=False)`, `connect()`, `_query_with_relations(session)` (joinedload to-one / selectinload to-many), méthodes en `try / finally: session.close()` | TD02/03 |
| Service ORM | `getMoviesYears()` = `query(Movie.year).filter(...isnot(None)).distinct().order_by(...)` ; `getStatsSummary()` = `.count()` | TD02/03 |
| Filtres | `heroes()` lit `universe`, `city`, `power`, `team` dans `request.args` et choisit la méthode du service | TD03 |

**Écarts relevés dans les corrections du prof.** Ils ne seront **pas** reproduits dans le contenu. Certains peuvent servir d'exercices « trouver le bug » :
- `MovieService.getMoviesByActor` appelle `findByActor`, qui n'existe pas dans `MovieSqliteORM` (TD02).
- `models/__init__.py` (TD02) cite `'UserDAOInterface'` dans `__all__` sans l'importer.
- `infos_bp` déclare `url_prefix='/infos'` dans `Blueprint(...)` **et** dans `register_blueprint` (TD01). C'est redondant, et le second l'emporte.

---

## 1. Système de progression (règles exactes proposées)

- **Score d'un exercice** (0 à 1) = résultat de la **1ʳᵉ** tentative validée − 0,2 par indice utilisé (plancher 0). On peut retenter pour apprendre, mais ça ne change pas le score.
  Exception : les exercices « écrire du code » sont notés selon la part de tests réussis à la dernière soumission. Le « premier coup » veut dire que la 1ʳᵉ soumission réussit tout.
- **Score d'une leçon** = moyenne des scores de ses exercices.
- **Étoiles** : ★ si ≥ 50 % · ★★ si ≥ 80 % et ≤ 1 indice · ★★★ si 100 % du premier coup, sans indice, et dans le temps imparti pour le palier 4. On garde le meilleur résultat.
- **Aucun verrou** (décision de l'utilisateur, remplace les règles de déverrouillage du prompt) : toutes les sessions, tous les paliers, toutes les leçons et le contrôle blanc sont accessibles dès le départ. Les étoiles servent uniquement à suivre la progression. Le palier 2 de la session N affiche « validé » quand sa moyenne atteint 2★, à titre indicatif.
- **Mode papier** : une grille de critères (cases à cocher) donne le %. Les critères vérifiables automatiquement sont cochés d'office si la version testée par le serveur réussit.

## 2. Types d'exercices et répartition par palier

| Code | Type | P1 | P2 | P3 | P4 |
| --- | --- | :-: | :-: | :-: | :-: |
| `qcm` | QCM / vrai-faux | 4 | 1 | 1 | – |
| `trous` | Code à trous (réponses multiples, normalisation des espaces et des guillemets) | 1 | 2 | 1 | – |
| `ordre` | Remettre des lignes dans l'ordre (glisser-déposer, + clavier ↑/↓) | 1 | 2 | – | – |
| `relier` | Relier notion ↔ définition | – | 1 | – | – |
| `bug` | Trouver la ligne fautive puis corriger | – | – | 2 | – |
| `code` | Écrire du code, validé par des tests cachés en sous-processus | – | – | 2 | – |
| `papier` | Mode papier : chrono, pas de coloration, grille de barème | – | – | – | 6 |

Au moins **6 exercices par leçon**, 12 leçons par session : **≥ 216 exercices**, plus 2 contrôles blancs.
`relier` est cité au palier 2 du prompt mais absent de la liste des 6 types, je l'ajoute comme 7ᵉ type (léger).
Au palier 4, chaque « mini-sujet » est découpé en 6 questions papier (une par fichier ou partie), chacune avec sa grille.

**Domaines** : P1–P2 restent sur les **films** et les **super-héros** du cours, pour ancrer. P3–P4 et le contrôle blanc passent à de **nouveaux domaines** pour apprendre à transposer : 📚 bibliothèque (livres / auteurs / tags), 🎵 musique (artistes / albums / genres), 🏫 école (élèves / classes / matières), plus 🍳 recettes et 🏀 club de sport pour le contrôle blanc.

---

## 3. Session 1 — Flask modulaire

| # | Palier | Leçon | Notions | Tags |
| --- | --- | --- | --- | --- |
| 1.1 | 1 Découverte | MVC-S : qui fait quoi ? | Model / DAO / Service / Controller (= blueprint) / View, pourquoi le service est typé et indépendant des données | `mvcs`, `dao`, `service` |
| 1.2 | 1 | Modules, packages et `__init__.py` | module = fichier `.py`, package = dossier + `__init__.py`, `__all__`, arborescence `app/blueprints, models, services, static, templates` | `module-package`, `init-all`, `arborescence` |
| 1.3 | 1 | L'application factory | `create_app()`, `Flask(__name__)`, `app.config[...]`, `app.root_path`, `main.py` port 8000, import des blueprints dans la factory (imports circulaires) | `factory`, `config`, `main` |
| 1.4 | 2 Application | Créer et enregistrer un blueprint | `Blueprint('movies', __name__, template_folder=...)`, `@bp.route`, `register_blueprint`, `url_prefix` (dans `Blueprint` vs à l'enregistrement) | `blueprint`, `register-bp`, `url-prefix`, `template-folder` |
| 1.5 | 2 | Routes, méthodes, paramètres | `methods=['GET','POST']`, `<int:id>`, `<string:name>`, `request.args.get`, `request.form[...]`, conversion `int(...)` | `route-methods`, `route-params`, `request-args`, `request-form` |
| 1.6 | 2 | Réponses et contexte | `render_template`, `jsonify`, `redirect(url_for('movies.movies'))` (nom `bp.fonction`), `current_app.config` | `url-for`, `redirect`, `jsonify`, `current-app` |
| 1.7 | 3 Maîtrise | Le modèle classique | `__init__` à valeurs par défaut, `to_dict`, `__getitem__`, `__contains__`, `__repr__`, `from_dict` → domaine **Book** | `modele-classique`, `dunder` |
| 1.8 | 3 | DAO sqlite3 avec interface | `XxxDAOInterface`, `XxxSqliteDAO(Interface)`, `connect()`, `row_factory`, `?` paramétré, `fetchall`, `close` → domaine **Album** | `dao-interface`, `dao-sqlite3`, `sql-injection` |
| 1.9 | 3 | Le service typé | `List[Dict]`, `Optional`, `getMoviesYears` en `sorted(set(...))`, valeurs de retour homogènes (`[]` / `[obj]`) → domaine **Élève** | `service`, `typing` |
| 1.10 | 4 Défi papier | Sujet A — Bibliothèque modulaire | arborescence + `main.py` + `create_app` + blueprint `books` (`/books/`, `/books/<int:id>`) + `__init__` / `__all__` | `factory`, `blueprint`, `init-all` |
| 1.11 | 4 | Sujet B — Musique : Model + DAO | `Album` classique + `AlbumDAOInterface` + `AlbumSqliteDAO` (`findAll`, `findById`, `findByYear`) | `modele-classique`, `dao-sqlite3` |
| 1.12 | 4 | Sujet C — École : Service + routes filtrées | `StudentService` + blueprint `students` avec `?classe=` et `jsonify` | `service`, `request-args`, `jsonify` |

## 4. Session 2 — ORM et mixins

| # | Palier | Leçon | Notions | Tags |
| --- | --- | --- | --- | --- |
| 2.1 | 1 | Pourquoi un ORM ? | table ↔ classe, ligne ↔ instance, approche déclarative vs impérative, `create_engine("sqlite:///...", echo=True)`, `Base = declarative_base()` | `orm-principe`, `engine`, `declarative-base` |
| 2.2 | 1 | Le modèle déclaratif | `__tablename__`, `Column(Integer, primary_key=True)`, `nullable`, `unique`, `index`, `default` (dont `func.current_timestamp()`), `Base.metadata.create_all(engine)` | `column-options`, `tablename`, `create-all` |
| 2.3 | 1 | Les sessions | `sessionmaker(bind=engine)`, `Session()`, `add` / `add_all`, `commit`, `rollback`, `close`, sessions courtes (films.py : `creation / remplir / explorer`) | `session-orm`, `commit`, `close` |
| 2.4 | 2 | Requêter sans SQL | `query`, `filter(Movie.year == y)`, `order_by`, `limit`, `first`, `all`, `count`, `distinct`, `ilike(f"%{x}%")`, `isnot(None)` | `query`, `filter`, `ilike`, `distinct` |
| 2.5 | 2 | Relations 1-N / N-1 | `ForeignKey('directors.id')` (**nom de table**), `relationship('Movie', back_populates=...)` des **deux** côtés, collection au pluriel | `relation-1N`, `foreign-key`, `back-populates` |
| 2.6 | 2 | Relations 1-1 et N-N | `uselist=False` + `unique=True` sur la FK, `Table` d'association dans `associations.py`, `secondary=`, clé primaire composée | `relation-11`, `relation-NN`, `association-table` |
| 2.7 | 3 | Cascades et suppressions | `ondelete='CASCADE'` / `'SET NULL'` (niveau BDD) vs `cascade='all, delete-orphan'` (niveau ORM), `default=datetime.utcnow` sans `()` | `cascade`, `ondelete`, `default-callable` |
| 2.8 | 3 | Charger efficacement | lazy vs eager, problème N+1, `joinedload` (to-one) vs `selectinload` (to-many), `options(...)`, `.join(Movie.genres)` | `loading`, `n-plus-1`, `join` |
| 2.9 | 3 | Mixins et POO avancée | `BaseModelMixin`, héritage multiple et ordre `(Base, BaseModelMixin)`, MRO / C3, `@property`, `@staticmethod`, surcharge de `__getitem__` avec `super()` | `mixin`, `mro`, `property`, `super` |
| 2.10 | 4 | Sujet A — Bibliothèque ORM | `Author` 1-N `Book`, `Book` N-N `Tag` (`book_tags`), `BookDetail` 1-1, `ForeignKey(..., ondelete=...)` | `relation-1N`, `relation-NN`, `relation-11` |
| 2.11 | 4 | Sujet B — Musique : base + mixin | `base.py` (`Base`, `BaseModelMixin`, `get_engine`) + `associations.py` + `Artist` / `Album` / `Genre` + `@property` | `mixin`, `association-table`, `property` |
| 2.12 | 4 | Sujet C — DAO ORM | `AlbumSqliteORM(AlbumDAOInterface)` : `__init__` (engine + `sessionmaker`), `connect`, `_query_with_relations`, `findAll`, `findByGenre` (`join` + `ilike`) | `dao-orm`, `loading`, `try-finally` |

## 5. Session 3 — Tout assembler (patron « super-héros »)

| # | Palier | Leçon | Notions | Tags |
| --- | --- | --- | --- | --- |
| 3.1 | 1 | Du schéma SQL aux modèles | `REFERENCES t(id) ON DELETE ...` → `ForeignKey`, `NOT NULL UNIQUE` → options, `DEFAULT` → `default=`, repérer les tables d'association (PK composée) | `schema-to-model`, `foreign-key` |
| 3.2 | 1 | Organiser un projet complet | ordre des imports dans `models/__init__.py` (base → associations → modèles → DAO), `__all__`, un blueprint par page, `services/` | `arborescence`, `init-all`, `module-package` |
| 3.3 | 1 | Des user stories aux routes | « en tant qu'utilisateur… » → URL, méthode, paramètre, méthode de service | `user-story`, `route-params`, `request-args` |
| 3.4 | 2 | Le DAO ORM complet | `connect()`, `try / finally: session.close()`, `_query_with_relations`, retour `[hero]` ou `[]`, `expire_on_commit=False` | `dao-orm`, `try-finally`, `loading` |
| 3.5 | 2 | Le service : stats et calculs | `getStatsSummary` (`count`), `getUniverses` (`distinct` + `order_by`), `@property` `average_danger`, `completed_missions_count` | `service-stats`, `count`, `distinct`, `property` |
| 3.6 | 2 | Blueprints avec filtres | `request.args.get('universe')`, cascade `if / elif`, routes `/city/<string:city_name>`, `url_prefix` à l'enregistrement | `filters`, `request-args`, `route-params` |
| 3.7 | 3 | Débugger une appli complète | bugs multi-fichiers (blueprint non enregistré, `back_populates` incohérent, FK vers le nom de classe, `commit` oublié, session jamais fermée) → domaine **école** | `debug`, `back-populates`, `register-bp` |
| 3.8 | 3 | Modèles depuis un schéma inconnu | écrire 4 modèles + associations, validés par introspection SQLAlchemy (colonnes, FK, `secondary`, `back_populates`) → **bibliothèque** | `schema-to-model`, `relation-NN` |
| 3.9 | 3 | DAO + service + blueprint testés | `findByTag`, `getStatsSummary`, puis `create_app` testé avec `app.test_client()` (`/books/` → 200) → **musique** | `dao-orm`, `service-stats`, `factory` |
| 3.10 | 4 | Sujet A — Bibliothèque complète | schéma fourni → modèles, DAO, service, blueprint filtré | tous |
| 3.11 | 4 | Sujet B — Festival de musique | idem (artistes, scènes, concerts, genres) | tous |
| 3.12 | 4 | Sujet C — Gestion d'école | idem (élèves, classes, matières, notes) + statistiques | tous |

## 6. Contrôle blanc (2 sujets, 1 h 30, /20)

| Sujet | Domaine | Barème |
| --- | --- | --- |
| A | 🍳 Recettes (recettes / ingrédients N-N / catégorie N-1 / fiche nutrition 1-1) | Cours 5 pts (QCM + questions ouvertes courtes) · Ex. 1 modèles ORM 6 pts · Ex. 2 DAO ORM 5 pts · Ex. 3 service + blueprint + factory 4 pts |
| B | 🏀 Club de sport (joueurs / équipes N-1 / entraînements N-N / licence 1-1) | même structure |

Le corrigé est détaillé question par question, avec une grille de barème cochable et une note sur 20 convertie en étoiles (≥ 10 → ★, ≥ 16 → ★★, 20 → ★★★).

**Bonus hors contrôle** (badge gris, sans étoiles) : 1 leçon « Jinja : `extends` / `block` / `include` / filtres » et 1 leçon « Utilisateurs : sessions Flask, bcrypt, `reqlogged` ».

---

## 7. Référentiel des tags

`mvcs` `dao` `service` `module-package` `init-all` `arborescence` `factory` `config` `main` `blueprint` `register-bp` `url-prefix` `template-folder` `route-methods` `route-params` `request-args` `request-form` `url-for` `redirect` `jsonify` `current-app` `modele-classique` `dunder` `dao-interface` `dao-sqlite3` `sql-injection` `typing` · `orm-principe` `engine` `declarative-base` `column-options` `tablename` `create-all` `session-orm` `commit` `close` `query` `filter` `ilike` `distinct` `relation-1N` `relation-11` `relation-NN` `foreign-key` `back-populates` `association-table` `cascade` `ondelete` `default-callable` `loading` `n-plus-1` `join` `mixin` `mro` `property` `super` · `schema-to-model` `user-story` `dao-orm` `try-finally` `service-stats` `count` `filters` `debug`

Le tableau de bord `/progress` agrège les scores par tag. « Réviser mes points faibles » tire jusqu'à 10 exercices sur les 3 tags les plus faibles, parmi les leçons déjà ouvertes.

## 8. Choix techniques à valider

1. **Contenu en YAML** (`content/session1.yaml`…) plutôt qu'en JSON : les blocs de code multi-lignes y restent lisibles et éditables à la main. Ça ajoute `PyYAML` comme seule dépendance de contenu. Dépendances totales : `flask`, `sqlalchemy`, `pyyaml`, `pytest`.
2. **Exécuteur de code** : `subprocess.run([sys.executable, "-I", runner.py], timeout=5, cwd=tmpdir)`, SQLite `:memory:`, et un `sys.addaudithook` qui bloque `socket`, `subprocess`, `os.remove` / `unlink` / `rmdir`, et `open` en écriture hors du dossier temporaire. **Limite honnête** : sous Windows, ce n'est pas un vrai bac à sable (il faudrait un conteneur). C'est suffisant pour un usage local mono-utilisateur. Le test `import os; os.remove(...)` sera bien couvert.
3. **Éditeur** : CodeMirror 6 via CDN (`esm.sh`), coloration Python. En mode papier, coloration, autocomplétion et fermeture automatique des parenthèses sont désactivées.
4. **API SQLAlchemy** : on garde le style `session.query(...)` du cours (toujours supporté en 2.x), pas `select()`.
5. Python local détecté : 3.14. Flask et SQLAlchemy ne sont pas installés, ils iront dans un `venv`.

## 9. Direction visuelle (skill `ui-ux-pro-max`)

- **Recherche** : le design system « éducation gamifiée » a proposé *Claymorphism + Baloo 2 / Comic Neue*. **Écarté**, car c'est conçu pour des enfants et ce public est en BUT3. Le pilotage par domaines a donné la paire **« Developer Mono »** et une palette « Developer Tool ».
- **Style** : interface sobre, orientée code, avec des touches de jeu réservées à la progression : chemin vertical des paliers, pastilles étoilées, petite animation sur une étoile gagnée.
- **Typo** : IBM Plex Sans (interface) + JetBrains Mono (code, titres de leçons).
- **Palette (tokens CSS sur `:root`, redéfinis en sombre)** : primaire indigo `#4F46E5` · progression vert `#16A34A` · étoile or `#F59E0B` · erreur `#DC2626` · fond clair `#F8FAFC` / sombre `#0F172A` · cartes `#FFFFFF` / `#1B2336`.
- **Garde-fous** : contraste ≥ 4,5:1, focus visible, `prefers-reduced-motion`, cibles ≥ 44 px, icônes SVG (pas d'emoji comme icône dans l'interface), responsive dès 375 px.
- **Skills prévus pendant le développement** : `ui-ux-pro-max` (tokens) · `emil-design-eng` (finitions des composants) · `animate` (étoile gagnée, chemin des paliers) · `design:accessibility-review` (audit WCAG avant livraison) · `break-ui` (titres longs, 0 étoile, données vides).

---

## Décisions prises

1. **Aucun verrou** : tout est ouvert (demande de l'utilisateur).
2. Contenu en **YAML** (choix par défaut).
3. Pénalité d'indice : **−20 %** du score de l'exercice (choix par défaut).
