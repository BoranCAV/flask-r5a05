"""chaque solution officielle passe ses propres tests cachés (exécutés dans le vrai bac à sable)"""
from concurrent.futures import ThreadPoolExecutor

import pytest

from conftest import all_exercises
from app.services.executor import run_code

TESTED = [(i, e) for i, e in all_exercises() if e["type"] in ("code", "papier") and e.get("tests")]


@pytest.fixture(scope="module")
def results():
	# exécution en parallèle : chaque exercice lance son propre sous-processus
	with ThreadPoolExecutor(max_workers=6) as pool:
		futures = {i: pool.submit(run_code, e["solution"], e["tests"], e.get("setup", ""), 20) for i, e in TESTED}
	return {i: f.result() for i, f in futures.items()}


@pytest.mark.parametrize("ex_id", [i for i, _ in TESTED])
def test_solution_officielle(results, ex_id):
	r = results[ex_id]
	assert r["error"] is None, r["error"]
	failed = [f"{t['doc']} → {t['message']}" for t in r["tests"] if not t["passed"]]
	assert r["total"] > 0 and not failed, failed


@pytest.mark.parametrize("ex_id,ex", [(i, e) for i, e in TESTED if e["type"] == "code" and e.get("starter")], ids=lambda v: v if isinstance(v, str) else "")
def test_starter_ne_passe_pas(ex_id, ex):
	"""le code de départ ne doit pas déjà réussir tous les tests"""
	r = run_code(ex["starter"], ex["tests"], ex.get("setup", ""), 20)
	assert r["error"] or r["passed"] < r["total"]
