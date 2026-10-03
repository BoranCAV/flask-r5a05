# Script exécuté dans un sous-processus isolé (python -I -B), dans un dossier temporaire.
# Il lit student.py et tests.py, exécute le code de l'étudiant puis les fonctions test_*,
# et écrit le résultat dans result.json. Ce fichier n'est jamais importé par l'application.
import json, os, sys, io, traceback, contextlib

TMP = os.path.dirname(os.path.abspath(__file__))
RESULT = os.path.join(TMP, "result.json")


def write_result(data):
	with open(RESULT, "w", encoding="utf-8") as f:
		json.dump(data, f, ensure_ascii=False)


# 1) imports autorisés AVANT de verrouiller : flask, sqlalchemy, typing… restent utilisables
import typing, datetime, functools, sqlite3  # noqa: E401,F401
try:
	import flask, sqlalchemy, sqlalchemy.orm  # noqa: F401
except Exception:
	pass

student_code = open(os.path.join(TMP, "student.py"), encoding="utf-8").read()
tests_code = open(os.path.join(TMP, "tests.py"), encoding="utf-8").read()
setup_code = open(os.path.join(TMP, "setup.py"), encoding="utf-8").read()

# 2) verrou par audit hook : pas de réseau, pas de processus, pas d'écriture hors du dossier temporaire
# ponytail: audit hook = garde-fou, pas un vrai bac à sable (ctypes peut le contourner) ; un conteneur si le site est partagé
BLOCKED_PREFIXES = ("socket.", "subprocess.", "os.system", "os.exec", "os.spawn", "os.posix_spawn",
                    "os.fork", "os.kill", "os.remove", "os.unlink", "os.rmdir", "os.rename", "os.replace",
                    "os.truncate", "os.chmod", "os.chown", "os.link", "os.symlink", "shutil.rmtree",
                    "shutil.move", "urllib.", "http.", "ftplib.", "smtplib.", "webbrowser.", "winreg.", "ctypes.")
WRITE_FLAGS = os.O_WRONLY | os.O_RDWR | os.O_APPEND | os.O_CREAT | os.O_TRUNC


def _inside_tmp(path):
	try:
		return os.path.abspath(os.fsdecode(path)).startswith(TMP)
	except Exception:
		return False


def audit(event, args):
	if event.startswith(BLOCKED_PREFIXES):
		raise PermissionError(f"Action interdite dans l'exercice : {event}")
	if event == "open":
		path, mode, flags = args
		writing = (isinstance(mode, str) and any(c in mode for c in "wax+")) or (mode is None and isinstance(flags, int) and flags & WRITE_FLAGS)
		if writing and isinstance(path, (str, bytes, os.PathLike)) and not _inside_tmp(path):
			raise PermissionError("Écriture de fichier interdite dans l'exercice")
	if event == "sqlite3.connect":
		db = args[0]
		if str(db) not in (":memory:", "") and not _inside_tmp(db):
			raise PermissionError("Seule une base SQLite en mémoire est autorisée (sqlite:// ou :memory:)")


sys.addaudithook(audit)

# 3) préparation (faux modules du projet, ex. app.services.BookService) puis code de l'étudiant
ns = {"__name__": "student"}
out = io.StringIO()
result = {"error": None, "tests": [], "stdout": ""}
exec(compile(setup_code, "preparation.py", "exec"), ns)
try:
	with contextlib.redirect_stdout(out):
		exec(compile(student_code, "votre_code.py", "exec"), ns)
except SyntaxError as e:
	result["error"] = f"Erreur de syntaxe ligne {e.lineno} : {e.msg}"
except BaseException as e:  # noqa: BLE001 - on veut tout rapporter à l'étudiant
	tb = traceback.extract_tb(e.__traceback__)
	line = next((f.lineno for f in reversed(tb) if f.filename == "votre_code.py"), None)
	where = f" (ligne {line})" if line else ""
	result["error"] = f"Votre code plante à l'exécution{where} : {type(e).__name__} : {e}"

# 4) exécution des tests cachés, un par un
if result["error"] is None:
	tns = dict(ns)
	exec(compile(tests_code, "tests_caches.py", "exec"), tns)
	for name, fn in [(k, v) for k, v in tns.items() if k.startswith("test_") and callable(v)]:
		doc = (fn.__doc__ or name).strip()
		try:
			with contextlib.redirect_stdout(out):
				fn()
			result["tests"].append({"name": name, "doc": doc, "passed": True, "message": ""})
		except AssertionError as e:
			result["tests"].append({"name": name, "doc": doc, "passed": False, "message": str(e) or "condition non vérifiée"})
		except BaseException as e:  # noqa: BLE001
			result["tests"].append({"name": name, "doc": doc, "passed": False, "message": f"{type(e).__name__} : {e}"})

result["stdout"] = out.getvalue()[-2000:]
write_result(result)
