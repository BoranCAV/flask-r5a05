from sqlalchemy import Column, Integer, String, Text, ForeignKey
from sqlalchemy.orm import relationship
from app.models.base import Base, BaseModelMixin


class Lesson(Base, BaseModelMixin):
	"""
	une leçon : fiche mémo + exemple commenté + exercices
	N-1 avec Palier, 1-N avec Exercise, 1-1 avec Progress
	"""
	__tablename__ = 'lessons'

	id = Column(String(20), primary_key=True)  # ex : "1.4"
	palier_id = Column(Integer, ForeignKey('paliers.id', ondelete='CASCADE'), nullable=False, index=True)
	position = Column(Integer, nullable=False, default=1)
	title = Column(String(200), nullable=False)
	memo = Column(Text, nullable=True)
	example = Column(Text, nullable=True)
	duration = Column(Integer, nullable=True)  # en secondes, pour le contrôle blanc
	bonus = Column(Integer, default=0)  # 1 = hors contrôle

	palier = relationship('Palier', back_populates='lessons')
	exercises = relationship(
		'Exercise',
		back_populates='lesson',
		cascade='all, delete-orphan',
		order_by='Exercise.position'
	)
	progress = relationship(
		'Progress',
		back_populates='lesson',
		uselist=False,
		cascade='all, delete-orphan'
	)

	def __init__(self, id=None, palier_id=None, position=1, title=None, memo=None, example=None, duration=None, bonus=0):
		self.id = id
		self.palier_id = palier_id
		self.position = position
		self.title = title
		self.memo = memo
		self.example = example
		self.duration = duration
		self.bonus = bonus

	@property
	def stars(self):
		"""meilleur nombre d'étoiles obtenu (0 si jamais faite)"""
		return self.progress.stars if self.progress else 0
