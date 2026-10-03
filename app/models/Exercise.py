from sqlalchemy import Column, Integer, String, Text, Float, ForeignKey, JSON
from sqlalchemy.orm import relationship
from app.models.base import Base, BaseModelMixin
from app.models.associations import exercise_tags


class Exercise(Base, BaseModelMixin):
	"""
	un exercice ; les champs propres à chaque type (choix, trous, lignes, tests…)
	sont rangés dans data (colonne JSON)
	N-1 avec Lesson, N-N avec Tag, 1-N avec Attempt
	"""
	__tablename__ = 'exercises'

	id = Column(String(40), primary_key=True)  # ex : "1.4-3"
	lesson_id = Column(String(20), ForeignKey('lessons.id', ondelete='CASCADE'), nullable=False, index=True)
	position = Column(Integer, nullable=False, default=1)
	type = Column(String(20), nullable=False, index=True)
	enonce = Column(Text, nullable=False)
	indices = Column(JSON, default=list)
	solution = Column(Text, nullable=True)
	explication = Column(Text, nullable=True)
	points = Column(Float, default=1.0)
	data = Column(JSON, default=dict)

	lesson = relationship('Lesson', back_populates='exercises')
	tags = relationship('Tag', secondary=exercise_tags, back_populates='exercises')
	attempts = relationship('Attempt', back_populates='exercise', cascade='all, delete-orphan')

	def __init__(self, id=None, lesson_id=None, position=1, type=None, enonce=None, indices=None, solution=None, explication=None, points=1.0, data=None):
		self.id = id
		self.lesson_id = lesson_id
		self.position = position
		self.type = type
		self.enonce = enonce
		self.indices = indices or []
		self.solution = solution
		self.explication = explication
		self.points = points
		self.data = data or {}

	@property
	def tags_str(self):
		return ", ".join(t.name for t in self.tags)

	def __getitem__(self, item):
		"""ex['choices'] va chercher dans data si ce n'est pas une colonne (polymorphisme par surcharge)"""
		if not hasattr(self, item) and item in (self.data or {}):
			return self.data[item]
		return super().__getitem__(item)


class Tag(Base, BaseModelMixin):
	"""notion travaillée (blueprint, relation-NN…) ; N-N avec Exercise"""
	__tablename__ = 'tags'

	id = Column(Integer, primary_key=True, autoincrement=True)
	name = Column(String(50), unique=True, nullable=False, index=True)

	exercises = relationship('Exercise', secondary=exercise_tags, back_populates='tags')

	def __init__(self, name=None):
		self.name = name
