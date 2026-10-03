from sqlalchemy import Column, Integer, String, Text
from sqlalchemy.orm import relationship
from app.models.base import Base, BaseModelMixin


class Session(Base, BaseModelMixin):
	"""
	une session du cours (1, 2, 3) ou le contrôle blanc (4)
	1-N avec Palier
	(à ne pas confondre avec la session ORM, qu'on obtient toujours via le DAO)
	"""
	__tablename__ = 'sessions'

	id = Column(Integer, primary_key=True)
	title = Column(String(150), nullable=False)
	subtitle = Column(String(255), nullable=True)
	is_exam = Column(Integer, default=0)

	paliers = relationship(
		'Palier',
		back_populates='session',
		cascade='all, delete-orphan',
		order_by='Palier.number'
	)

	def __init__(self, id=None, title=None, subtitle=None, is_exam=0):
		self.id = id
		self.title = title
		self.subtitle = subtitle
		self.is_exam = is_exam

	@property
	def lessons(self):
		"""toutes les leçons de la session, palier par palier"""
		return [lesson for palier in self.paliers for lesson in palier.lessons]
