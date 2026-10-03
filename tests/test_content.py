"""cohérence du contenu YAML (rapide, sans exécuter de code)"""
import re
from collections import Counter

import pytest

from conftest import all_exercises
from seed import load_content

EXERCISES = all_exercises()


def test_volume_minimum():
	"""au moins 12 leçons par session et 6 exercices par leçon (hors contrôle blanc et bonus)"""
	for doc in load_content():
		s = doc["session"]
		lessons = [l for l in doc["lessons"] if not l.get("bonus")]
		if s.get("is_exam"):
			assert len(lessons) >= 2
			continue
		assert len(lessons) >= 12, s["title"]
		assert Counter(l["palier"] for l in lessons) == {1: 3, 2: 3, 3: 3, 4: 3}, s["title"]
		for l in lessons:
			assert len(l["exercises"]) >= 6, l["id"]
			assert l.get("memo"), l["id"]


def test_identifiants_uniques():
	ids = [l["id"] for doc in load_content() for l in doc["lessons"]]
	assert len(ids) == len(set(ids))


@pytest.mark.parametrize("ex_id,ex", EXERCISES, ids=[e[0] for e in EXERCISES])
def test_structure_exercice(ex_id, ex):
	assert ex.get("enonce"), "énoncé manquant"
	assert ex.get("tags"), "tags manquants"
	t = ex["type"]
	if t == "qcm":
		assert ex["answer"] and all(0 <= a < len(ex["choices"]) for a in ex["answer"])
	elif t == "trous":
		found = sorted(int(n) for n in re.findall(r"\[\[(\d+)\]\]", ex["code"]))
		assert found == list(range(len(ex["blanks"]))), "trous mal numérotés"
		assert all(isinstance(b, list) and b for b in ex["blanks"])
	elif t == "ordre":
		assert len(ex["lines"]) >= 3 and len(set(ex["lines"])) == len(ex["lines"])
	elif t == "relier":
		defs = [p[1] for p in ex["pairs"]]
		assert len(ex["pairs"]) >= 3 and len(set(defs)) == len(defs)
	elif t == "bug":
		n = len(ex["code"].rstrip("\n").split("\n"))
		assert all(1 <= int(k) <= n for k in ex["fixes"]), "ligne de bug hors du code"
		lines = ex["code"].rstrip("\n").split("\n")
		for k, accepted in ex["fixes"].items():
			assert lines[int(k) - 1].strip() not in [a.strip() for a in accepted], f"la ligne {k} est déjà correcte"
	elif t == "code":
		assert ex.get("tests") and ex.get("solution")
	elif t == "papier":
		assert ex.get("grille") and ex.get("solution")
		if ex.get("tests"):
			names = set(re.findall(r"def (test_\w+)", ex["tests"]))
			for c in ex["grille"]:
				if c.get("auto"):
					assert c["auto"] in names, f"critère auto inconnu : {c['auto']}"
