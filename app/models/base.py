from datetime import datetime
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base

# base déclarative partagée par tous les modèles ORM (comme dans le TD02)
Base = declarative_base()


class BaseModelMixin:
	"""
	mixin (héritage partiel) : jamais instancié directement, il apporte
	- l'accès type dictionnaire obj['title'] via __getitem__
	- la sérialisation to_dict()
	"""

	def __getitem__(self, item):
		if hasattr(self, item):
			return getattr(self, item)
		raise KeyError(f"L'objet '{self.__class__.__name__}' n'a pas l'attribut '{item}'")

	def to_dict(self):
		"""retourne les colonnes de l'objet sous forme de dictionnaire"""
		result = {}
		for col in self.__table__.columns:
			val = getattr(self, col.name)
			if isinstance(val, datetime):
				val = val.strftime("%Y-%m-%d %H:%M:%S")
			result[col.name] = val
		return result


def get_engine(db_uri=None):
	"""crée le moteur SQLAlchemy ; par défaut la base est app/training.db"""
	if db_uri is None:
		base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
		db_uri = f"sqlite:///{os.path.join(base_dir, 'training.db')}"
	return create_engine(db_uri, echo=False)
