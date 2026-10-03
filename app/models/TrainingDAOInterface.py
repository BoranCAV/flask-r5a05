from typing import List, Optional


class TrainingDAOInterface:
	"""
	interface du DAO du site d'entraînement
	définit les méthodes obligatoires à implémenter
	"""

	def connect(self):
		"""retourne une session de connexion ORM"""
		pass

	def findAllSessions(self) -> List:
		"""toutes les sessions avec leurs paliers, leçons et progression"""
		pass

	def findSessionById(self, id: int):
		"""une session avec ses paliers, leçons et progression (ou None)"""
		pass

	def findLessonById(self, id: str):
		"""une leçon avec ses exercices et leurs tags (ou None)"""
		pass

	def findExerciseById(self, id: str):
		"""un exercice avec sa leçon (ou None)"""
		pass

	def findExercisesByTags(self, tag_names: List[str], limit: int = 10) -> List:
		"""exercices portant au moins un des tags (hors mode papier)"""
		pass

	def addAttempt(self, attempt) -> None:
		"""enregistre une tentative"""
		pass

	def findAttemptsByRun(self, run_id: str) -> List:
		"""tentatives d'un passage de leçon, de la plus ancienne à la plus récente"""
		pass

	def saveBestProgress(self, lesson_id: str, score: float, stars: int):
		"""garde le meilleur résultat de la leçon ; retourne le Progress à jour"""
		pass

	def findTagStats(self) -> List:
		"""(nom du tag, score moyen, nombre de tentatives) pour chaque tag tenté"""
		pass
