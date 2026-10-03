from sqlalchemy import Table, Column, Integer, String, ForeignKey
from app.models.base import Base

# N-N entre Exercise et Tag : un exercice a plusieurs tags, un tag regroupe plusieurs exercices
exercise_tags = Table(
	'exercise_tags',
	Base.metadata,
	Column('exercise_id', String(40), ForeignKey('exercises.id', ondelete='CASCADE'), primary_key=True),
	Column('tag_id', Integer, ForeignKey('tags.id', ondelete='CASCADE'), primary_key=True)
)
