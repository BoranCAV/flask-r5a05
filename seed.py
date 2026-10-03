"""
charge le contenu pédagogique (content/*.yaml) dans la base SQLite via l'ORM

    python seed.py           recharge le contenu, garde ta progression
    python seed.py --reset   efface aussi la progression
"""
import glob
import os
import sys
from typing import Any, Dict, List

import yaml
from sqlalchemy.orm import sessionmaker

from app.models import Base, get_engine, Session, Palier, Lesson, Exercise, Tag, Attempt, Progress, exercise_tags

ROOT = os.path.dirname(os.path.abspath(__file__))
CONTENT_DIR = os.path.join(ROOT, "content")
DB_URI = f"sqlite:///{os.path.join(ROOT, 'app', 'training.db')}"

# colonnes de Exercise ; tout le reste d'un exercice YAML part dans data (JSON)
COLUMNS = {"type", "enonce", "indices", "solution", "explication", "points"}
EXERCISE_TYPES = {"qcm", "trous", "ordre", "relier", "bug", "code", "papier"}


def normalize_exercise(raw: Dict[str, Any]) -> Dict[str, Any]:
	"""raccourci vf (vrai/faux) → qcm, et vérifications de base du contenu"""
	ex = dict(raw)
	if ex["type"] == "vf":
		ex["type"] = "qcm"
		ex["choices"] = ["Vrai", "Faux"]
		ex["answer"] = [0 if ex["answer"] else 1]
	if ex["type"] == "qcm" and isinstance(ex.get("answer"), int):
		ex["answer"] = [ex["answer"]]
	if ex["type"] not in EXERCISE_TYPES:
		raise ValueError(f"type inconnu : {ex['type']}")
	return ex


def load_content(content_dir: str = CONTENT_DIR) -> List[Dict[str, Any]]:
	"""lit tous les fichiers YAML du dossier content/ (un par session)"""
	docs = []
	for path in sorted(glob.glob(os.path.join(content_dir, "*.yaml"))):
		with open(path, encoding="utf-8") as f:
			docs.append(yaml.safe_load(f))
	return docs


def seed(db_uri: str = DB_URI, reset: bool = False, content_dir: str = CONTENT_DIR) -> Dict[str, int]:
	engine = get_engine(db_uri)
	content_tables = [exercise_tags, Tag.__table__, Exercise.__table__, Lesson.__table__, Palier.__table__, Session.__table__]
	if reset:
		Base.metadata.drop_all(engine)
	else:
		# on ne recrée que le contenu : tentatives et progression restent (mêmes identifiants d'exercices)
		Base.metadata.drop_all(engine, tables=content_tables)
	Base.metadata.create_all(engine)

	SessionFactory = sessionmaker(bind=engine)
	session = SessionFactory()
	tags: Dict[str, Tag] = {}
	counts = {"sessions": 0, "lessons": 0, "exercises": 0}
	try:
		for doc in load_content(content_dir):
			s = doc["session"]
			course = Session(id=s["id"], title=s["title"], subtitle=s.get("subtitle"), is_exam=int(s.get("is_exam", 0)))
			session.add(course)
			paliers: Dict[int, Palier] = {}
			for pos, l in enumerate(doc["lessons"], start=1):
				num = int(l.get("palier", 1))
				if num not in paliers:
					paliers[num] = Palier(number=num, name=s.get("palier_names", {}).get(num))
					course.paliers.append(paliers[num])
				lesson = Lesson(id=str(l["id"]), position=pos, title=l["title"], memo=l.get("memo"),
				                example=l.get("example"), duration=l.get("duration"), bonus=int(l.get("bonus", 0)))
				paliers[num].lessons.append(lesson)
				for i, raw in enumerate(l["exercises"], start=1):
					ex = normalize_exercise(raw)
					exercise = Exercise(
						id=f"{lesson.id}-{i}", position=i, type=ex["type"], enonce=ex["enonce"],
						indices=ex.get("indices", []), solution=ex.get("solution"), explication=ex.get("explication"),
						points=float(ex.get("points", 1)),
						data={k: v for k, v in ex.items() if k not in COLUMNS | {"tags"}}
					)
					for name in ex.get("tags", []):
						if name not in tags:
							tags[name] = Tag(name=name)
						exercise.tags.append(tags[name])
					lesson.exercises.append(exercise)
					counts["exercises"] += 1
				counts["lessons"] += 1
			counts["sessions"] += 1
		session.commit()
	except Exception:
		session.rollback()
		raise
	finally:
		session.close()
	return counts


if __name__ == "__main__":
	c = seed(reset="--reset" in sys.argv)
	print(f"Contenu chargé : {c['sessions']} sessions, {c['lessons']} leçons, {c['exercises']} exercices.")
