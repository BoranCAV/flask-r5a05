from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from app.models.base import Base, BaseModelMixin

PALIER_NAMES = {1: "Découverte", 2: "Application", 3: "Maîtrise", 4: "Défi « papier »"}


class Palier(Base, BaseModelMixin):
	"""
	un palier d'une session
	N-1 avec Session, 1-N avec Lesson
	"""
	__tablename__ = 'paliers'

	id = Column(Integer, primary_key=True, autoincrement=True)
	session_id = Column(Integer, ForeignKey('sessions.id', ondelete='CASCADE'), nullable=False, index=True)
	number = Column(Integer, nullable=False)
	name = Column(String(100), nullable=False)

	session = relationship('Session', back_populates='paliers')
	lessons = relationship(
		'Lesson',
		back_populates='palier',
		cascade='all, delete-orphan',
		order_by='Lesson.position'
	)

	def __init__(self, session_id=None, number=1, name=None):
		self.session_id = session_id
		self.number = number
		self.name = name or PALIER_NAMES.get(number, f"Palier {number}")
