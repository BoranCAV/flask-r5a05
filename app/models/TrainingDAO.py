import os
from typing import List, Optional
from sqlalchemy import func
from sqlalchemy.orm import sessionmaker, joinedload, selectinload

from app.models.TrainingDAOInterface import TrainingDAOInterface
from app.models.base import get_engine
from app.models.Session import Session
from app.models.Palier import Palier
from app.models.Lesson import Lesson
from app.models.Exercise import Exercise, Tag
from app.models.Progress import Attempt, Progress


class TrainingSqliteORM(TrainingDAOInterface):
	"""
	DAO du site utilisant l'ORM
	chaque méthode ouvre une session courte et la ferme dans finally (patron du TD02/TD03)
	"""

	def __init__(self, db_uri: Optional[str] = None):
		if db_uri is None:
			base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
			db_uri = f"sqlite:///{os.path.join(base_dir, 'training.db')}"
		self.db_uri = db_uri
		self.engine = get_engine(db_uri)
		# expire_on_commit=False : les objets restent lisibles après la fermeture de la session
		self.SessionFactory = sessionmaker(bind=self.engine, expire_on_commit=False)

	def connect(self):
		"""retourne une nouvelle session ORM"""
		return self.SessionFactory()

	def _query_sessions_with_relations(self, session):
		"""sessions → paliers → leçons → progression, chargés d'avance (pas de N+1)"""
		return session.query(Session).options(
			selectinload(Session.paliers)
			.selectinload(Palier.lessons)
			.joinedload(Lesson.progress)
		)

	def findAllSessions(self) -> List[Session]:
		session = self.connect()
		try:
			return self._query_sessions_with_relations(session).order_by(Session.id).all()
		finally:
			session.close()

	def findSessionById(self, id: int) -> Optional[Session]:
		session = self.connect()
		try:
			return self._query_sessions_with_relations(session).filter(Session.id == id).first()
		finally:
			session.close()

	def findLessonById(self, id: str) -> Optional[Lesson]:
		session = self.connect()
		try:
			return (
				session.query(Lesson)
				.options(
					joinedload(Lesson.palier).joinedload(Palier.session),
					joinedload(Lesson.progress),
					selectinload(Lesson.exercises).selectinload(Exercise.tags)
				)
				.filter(Lesson.id == id)
				.first()
			)
		finally:
			session.close()

	def findExerciseById(self, id: str) -> Optional[Exercise]:
		session = self.connect()
		try:
			return (
				session.query(Exercise)
				.options(
					joinedload(Exercise.lesson).joinedload(Lesson.palier),
					joinedload(Exercise.lesson).selectinload(Lesson.exercises),
					selectinload(Exercise.tags)
				)
				.filter(Exercise.id == id)
				.first()
			)
		finally:
			session.close()

	def findExercisesByTags(self, tag_names: List[str], limit: int = 10) -> List[Exercise]:
		session = self.connect()
		try:
			return (
				session.query(Exercise)
				.options(selectinload(Exercise.tags))
				.join(Exercise.tags)
				.filter(Tag.name.in_(tag_names))
				.filter(Exercise.type != 'papier')
				.distinct()
				.order_by(func.random())
				.limit(limit)
				.all()
			)
		finally:
			session.close()

	def addAttempt(self, attempt: Attempt) -> None:
		session = self.connect()
		try:
			session.add(attempt)
			session.commit()
		except Exception:
			session.rollback()
			raise
		finally:
			session.close()

	def findAttemptsByRun(self, run_id: str) -> List[Attempt]:
		session = self.connect()
		try:
			return session.query(Attempt).filter(Attempt.run_id == run_id).order_by(Attempt.id).all()
		finally:
			session.close()

	def saveBestProgress(self, lesson_id: str, score: float, stars: int) -> Progress:
		session = self.connect()
		try:
			progress = session.query(Progress).filter(Progress.lesson_id == lesson_id).first()
			if progress is None:
				progress = Progress(lesson_id=lesson_id)
				session.add(progress)
			progress.best_score = max(progress.best_score or 0.0, score)
			progress.stars = max(progress.stars or 0, stars)
			session.commit()
			return progress
		except Exception:
			session.rollback()
			raise
		finally:
			session.close()

	def findTagStats(self) -> List[tuple]:
		session = self.connect()
		try:
			return (
				session.query(Tag.name, func.avg(Attempt.score), func.count(Attempt.id))
				.join(Tag.exercises)
				.join(Exercise.attempts)
				.group_by(Tag.name)
				.all()
			)
		finally:
			session.close()
