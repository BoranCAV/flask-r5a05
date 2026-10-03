import os
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from seed import load_content, normalize_exercise, seed  # noqa: E402


def all_exercises():
	"""(id, exercice normalisé) pour tout le contenu YAML"""
	out = []
	for doc in load_content():
		for lesson in doc["lessons"]:
			for i, raw in enumerate(lesson["exercises"], start=1):
				out.append((f"{lesson['id']}-{i}", normalize_exercise(raw)))
	return out


@pytest.fixture()
def app(tmp_path):
	"""application branchée sur une base temporaire remplie avec le vrai contenu"""
	from app import create_app
	uri = f"sqlite:///{tmp_path / 'test.db'}"
	seed(uri, reset=True)
	return create_app(uri)


@pytest.fixture()
def client(app):
	return app.test_client()
