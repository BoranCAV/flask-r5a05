import random
from typing import Dict, List, Any, Optional
from flask import current_app

from app.models.TrainingDAO import TrainingSqliteORM as TrainingDAO
from app.models.Session import Session
from app.models.Lesson import Lesson
from app.models.Exercise import Exercise


class CourseService:
	"""
	accès au contenu pédagogique et préparation des exercices pour l'affichage
	(on n'envoie jamais les réponses au navigateur)
	"""

	def __init__(self, db_uri: Optional[str] = None):
		if db_uri is None:
			try:
				db_uri = current_app.config.get('SQLALCHEMY_DATABASE_URI')
			except RuntimeError:
				pass
		self.dao = TrainingDAO(db_uri=db_uri)

	def getAllSessions(self) -> List[Session]:
		return self.dao.findAllSessions()

	def getSessionById(self, id: int) -> Optional[Session]:
		return self.dao.findSessionById(id)

	def getLessonById(self, id: str) -> Optional[Lesson]:
		return self.dao.findLessonById(id)

	def getExerciseById(self, id: str) -> Optional[Exercise]:
		return self.dao.findExerciseById(id)

	@staticmethod
	def _shuffled(n: int, seed: str) -> List[int]:
		"""permutation déterministe de range(n), jamais identique à l'ordre correct si n > 1"""
		order = list(range(n))
		rng = random.Random(seed)
		while n > 1 and order == list(range(n)):
			rng.shuffle(order)
		return order

	def exerciseView(self, ex: Exercise) -> Dict[str, Any]:
		"""données d'affichage d'un exercice, sans les réponses"""
		d = ex.data or {}
		view: Dict[str, Any] = {
			"id": ex.id, "type": ex.type, "enonce": ex.enonce, "indices": ex.indices or [],
			"tags": [t.name for t in ex.tags], "points": ex.points,
		}
		if ex.type == "qcm":
			view["choices"] = d["choices"]
			view["multiple"] = len(d["answer"]) > 1
			view["code"] = d.get("code")
		elif ex.type == "trous":
			view["segments"] = self._split_blanks(d["code"])
		elif ex.type == "ordre":
			view["lines"] = [(i, d["lines"][i]) for i in self._shuffled(len(d["lines"]), ex.id)]
		elif ex.type == "relier":
			view["notions"] = [p[0] for p in d["pairs"]]
			view["definitions"] = [(i, d["pairs"][i][1]) for i in self._shuffled(len(d["pairs"]), ex.id)]
		elif ex.type == "bug":
			view["lines"] = d["code"].rstrip("\n").split("\n")
			view["nb_bugs"] = len(d["fixes"])
		elif ex.type in ("code", "papier"):
			view["starter"] = d.get("starter", "")
			view["duree"] = d.get("duree")
			if ex.type == "papier":
				view["grille"] = [c["critere"] for c in d["grille"]]
		return view

	@staticmethod
	def _split_blanks(code: str) -> List[Any]:
		"""découpe "a [[0]] b" en ["a ", 0, " b"] pour placer les champs de saisie"""
		import re
		parts: List[Any] = []
		for i, chunk in enumerate(re.split(r"\[\[(\d+)\]\]", code)):
			parts.append(int(chunk) if i % 2 else chunk)
		return parts
