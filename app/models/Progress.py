from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, Boolean, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from app.models.base import Base, BaseModelMixin


class Attempt(Base, BaseModelMixin):
	"""
	une tentative sur un exercice, rattachée à un "run" (un passage complet de la leçon)
	N-1 avec Exercise
	"""
	__tablename__ = 'attempts'

	id = Column(Integer, primary_key=True, autoincrement=True)
	exercise_id = Column(String(40), ForeignKey('exercises.id', ondelete='CASCADE'), nullable=False, index=True)
	run_id = Column(String(40), nullable=False, index=True)
	score = Column(Float, nullable=False, default=0.0)  # 0..1, pénalité d'indices déjà appliquée
	hints_used = Column(Integer, default=0)
	first_try = Column(Boolean, default=False)  # 100 % du premier coup (et dans le temps)
	# callable sans parenthèses : évalué à chaque insertion (piège classique du cours)
	created_at = Column(DateTime, default=datetime.now)

	exercise = relationship('Exercise', back_populates='attempts')

	def __init__(self, exercise_id=None, run_id=None, score=0.0, hints_used=0, first_try=False):
		self.exercise_id = exercise_id
		self.run_id = run_id
		self.score = score
		self.hints_used = hints_used
		self.first_try = first_try


class Progress(Base, BaseModelMixin):
	"""
	meilleur résultat sur une leçon
	1-1 avec Lesson (FK unique + uselist=False côté Lesson)
	"""
	__tablename__ = 'progress'

	id = Column(Integer, primary_key=True, autoincrement=True)
	lesson_id = Column(String(20), ForeignKey('lessons.id', ondelete='CASCADE'), unique=True, nullable=False, index=True)
	best_score = Column(Float, default=0.0)
	stars = Column(Integer, default=0)
	updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

	lesson = relationship('Lesson', back_populates='progress')

	def __init__(self, lesson_id=None, best_score=0.0, stars=0):
		self.lesson_id = lesson_id
		self.best_score = best_score
		self.stars = stars
