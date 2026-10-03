"""exécuteur isolé : résultats, timeout, code malveillant"""
import os

from app.services.executor import run_code

TEST_OK = 'def test_ok():\n    """toujours vrai"""\n    assert True\n'


def test_tests_passent_et_echouent():
	tests = (
		'def test_a():\n    """add(1, 2) vaut 3"""\n    assert add(1, 2) == 3\n'
		'def test_b():\n    """add(0, 0) vaut 1 (faux exprès)"""\n    assert add(0, 0) == 1, "message pédagogique"\n'
	)
	r = run_code("def add(a, b):\n    return a + b\n", tests)
	assert r["error"] is None and r["passed"] == 1 and r["total"] == 2
	failed = [t for t in r["tests"] if not t["passed"]][0]
	assert failed["doc"].startswith("add(0, 0)") and failed["message"] == "message pédagogique"


def test_erreur_de_syntaxe():
	r = run_code("def f(:\n    pass", TEST_OK)
	assert "syntaxe" in r["error"].lower()


def test_timeout_boucle_infinie():
	r = run_code("while True:\n    pass\n", TEST_OK, timeout=3)
	assert r["timeout"] and "Temps dépassé" in r["error"]


def test_os_remove_bloque(tmp_path):
	victim = tmp_path / "victime.txt"
	victim.write_text("intact")
	r = run_code(f"import os\nos.remove(r'{victim}')\n", TEST_OK)
	assert r["error"] and "interdite" in r["error"]
	assert victim.read_text() == "intact"


def test_ecriture_hors_dossier_bloquee(tmp_path):
	target = tmp_path / "pirate.txt"
	r = run_code(f"open(r'{target}', 'w').write('x')\n", TEST_OK)
	assert r["error"] and not target.exists()


def test_subprocess_et_reseau_bloques():
	assert run_code("import subprocess\nsubprocess.run(['echo', 'x'])\n", TEST_OK)["error"]
	assert run_code("import socket\nsocket.create_connection(('example.com', 80))\n", TEST_OK)["error"]
	assert run_code("import os\nos.system('echo x')\n", TEST_OK)["error"]


def test_sqlite_memoire_autorise_fichier_externe_refuse():
	ok = run_code("from sqlalchemy import create_engine\nwith create_engine('sqlite://').connect():\n    pass\n", TEST_OK)
	assert ok["error"] is None and ok["passed"] == 1
	path = os.path.join(os.path.expanduser("~"), "pirate.db")
	ko = run_code(f"import sqlite3\nsqlite3.connect(r'{path}')\n", TEST_OK)
	assert ko["error"] and not os.path.exists(path)


def test_faux_modules_du_projet():
	setup = "class _S:\n    def hello(self):\n        return 'ok'\nfake_module('app.services.X', X=_S)\n"
	r = run_code("from app.services.X import X\nres = X().hello()\n", 'def test_x():\n    """import du faux module"""\n    assert res == "ok"\n', setup)
	assert r["passed"] == 1
