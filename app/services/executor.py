import json
import os
import shutil
import subprocess
import sys
import tempfile
from typing import Dict, Any

RUNNER = os.path.join(os.path.dirname(os.path.abspath(__file__)), "runner_template.py")

# disponible dans le setup des exercices : fake_module('app.services.BookService', BookService=FakeService)
PRELUDE = """
import sys, types
def fake_module(name, **attrs):
	parts = name.split('.')
	for i in range(1, len(parts) + 1):
		sub = '.'.join(parts[:i])
		if sub not in sys.modules:
			sys.modules[sub] = types.ModuleType(sub)
			sys.modules[sub].__path__ = []
		if i > 1:
			setattr(sys.modules['.'.join(parts[:i - 1])], parts[i - 1], sys.modules[sub])
	for k, v in attrs.items():
		setattr(sys.modules[name], k, v)
	return sys.modules[name]
"""


def run_code(student_code: str, tests_code: str, setup_code: str = "", timeout: float = 5.0) -> Dict[str, Any]:
	"""
	exécute le code de l'étudiant + les tests cachés dans un sous-processus isolé :
	dossier temporaire, python -I (isolé) -B (pas de .pyc), timeout, audit hook (voir runner_template.py)
	retourne {"error", "tests": [{name, doc, passed, message}], "passed", "total", "timeout"}
	"""
	tmp = tempfile.mkdtemp(prefix="flask_ex_")
	try:
		shutil.copy(RUNNER, os.path.join(tmp, "runner.py"))
		with open(os.path.join(tmp, "student.py"), "w", encoding="utf-8") as f:
			f.write(student_code or "")
		with open(os.path.join(tmp, "tests.py"), "w", encoding="utf-8") as f:
			f.write(tests_code or "")
		with open(os.path.join(tmp, "setup.py"), "w", encoding="utf-8") as f:
			f.write(PRELUDE + (setup_code or ""))

		env = {"PYTHONIOENCODING": "utf-8", "SYSTEMROOT": os.environ.get("SYSTEMROOT", "")}
		try:
			proc = subprocess.run(
				[sys.executable, "-I", "-B", os.path.join(tmp, "runner.py")],
				cwd=tmp, env=env, capture_output=True, text=True, timeout=timeout
			)
		except subprocess.TimeoutExpired:
			return {"error": f"Temps dépassé ({timeout:.0f} s) : boucle infinie ?", "tests": [], "passed": 0, "total": 0, "timeout": True}

		result_path = os.path.join(tmp, "result.json")
		if not os.path.exists(result_path):
			err = (proc.stderr or "").strip().splitlines()
			return {"error": "L'exécution a échoué : " + (err[-1] if err else "raison inconnue"), "tests": [], "passed": 0, "total": 0, "timeout": False}
		with open(result_path, encoding="utf-8") as f:
			result = json.load(f)
	finally:
		shutil.rmtree(tmp, ignore_errors=True)

	result["passed"] = sum(1 for t in result["tests"] if t["passed"])
	result["total"] = len(result["tests"])
	result["timeout"] = False
	return result
