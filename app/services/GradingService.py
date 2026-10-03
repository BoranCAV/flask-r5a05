import re
from typing import Dict, List, Any, Optional

from app.services.executor import run_code


def normalize(code: str) -> str:
	"""normalise une réponse : guillemets doubles → simples, espaces supprimés, ; final ignoré"""
	code = (code or "").replace('"', "'")
	code = re.sub(r"\s+", "", code)
	return code.rstrip(";")


def matches(answer: str, accepted: List[str]) -> bool:
	"""vrai si la réponse correspond à l'une des réponses acceptées"""
	return normalize(answer) in {normalize(a) for a in accepted}


class GradingService:
	"""
	correction des exercices ; chaque méthode retourne
	{"score": 0..1 (avant pénalité d'indices), "details": [...], "feedback": str}
	"""

	def grade(self, ex_type: str, data: Dict[str, Any], answer: Any) -> Dict[str, Any]:
		"""aiguille vers la bonne méthode selon le type d'exercice"""
		method = getattr(self, f"grade_{ex_type}", None)
		if method is None:
			raise ValueError(f"type d'exercice inconnu : {ex_type}")
		return method(data, answer)

	def grade_qcm(self, data: Dict[str, Any], answer: List[int]) -> Dict[str, Any]:
		expected = set(data["answer"])
		chosen = set(int(a) for a in (answer or []))
		ok = chosen == expected
		return {"score": 1.0 if ok else 0.0, "details": sorted(expected), "feedback": "Bonne réponse !" if ok else "Ce n'est pas ça."}

	def grade_trous(self, data: Dict[str, Any], answer: List[str]) -> Dict[str, Any]:
		blanks = data["blanks"]
		answer = list(answer or []) + [""] * len(blanks)
		details = [matches(answer[i], accepted) for i, accepted in enumerate(blanks)]
		score = sum(details) / len(blanks)
		return {"score": score, "details": details, "feedback": f"{sum(details)} trou(s) correct(s) sur {len(blanks)}."}

	def grade_ordre(self, data: Dict[str, Any], answer: List[int]) -> Dict[str, Any]:
		"""answer = indices des lignes (dans l'ordre correct d'origine) tels que placés par l'étudiant"""
		n = len(data["lines"])
		order = [int(i) for i in (answer or [])]
		details = [i < len(order) and order[i] == i for i in range(n)]
		score = sum(details) / n
		return {"score": score, "details": details, "feedback": "Ordre parfait !" if score == 1 else f"{sum(details)} ligne(s) bien placée(s) sur {n}."}

	def grade_relier(self, data: Dict[str, Any], answer: List[Optional[int]]) -> Dict[str, Any]:
		"""answer[i] = indice de la définition choisie pour la notion i (indices d'origine)"""
		n = len(data["pairs"])
		answer = list(answer or []) + [None] * n
		details = [answer[i] is not None and int(answer[i]) == i for i in range(n)]
		return {"score": sum(details) / n, "details": details, "feedback": f"{sum(details)} association(s) correcte(s) sur {n}."}

	def grade_bug(self, data: Dict[str, Any], answer: Dict[str, Any]) -> Dict[str, Any]:
		"""
		answer = {"lines": [numéros de lignes cliquées], "fixes": {"3": "ligne corrigée"}}
		moitié des points pour localiser, moitié pour corriger
		"""
		bugs = {int(k): v for k, v in data["fixes"].items()}
		selected = set(int(x) for x in (answer or {}).get("lines", []))
		fixes = {int(k): v for k, v in (answer or {}).get("fixes", {}).items()}
		found = selected & set(bugs)
		locate = len(found) / max(len(selected), len(bugs))
		fixed = [n for n in bugs if n in fixes and matches(fixes[n], bugs[n])]
		repair = len(fixed) / len(bugs)
		score = (locate + repair) / 2
		details = {"bug_lines": sorted(bugs), "found": sorted(found), "fixed": sorted(fixed)}
		feedback = f"Lignes fautives trouvées : {len(found)}/{len(bugs)} · corrections justes : {len(fixed)}/{len(bugs)}."
		return {"score": score, "details": details, "feedback": feedback}

	def grade_code(self, data: Dict[str, Any], answer: str) -> Dict[str, Any]:
		res = run_code(answer, data.get("tests", ""), data.get("setup", ""))
		score = res["passed"] / res["total"] if res["total"] and not res["error"] else 0.0
		if res["error"]:
			feedback = res["error"]
		elif score == 1:
			feedback = f"Tous les tests passent ({res['total']}/{res['total']}) !"
		else:
			first_fail = next(t for t in res["tests"] if not t["passed"])
			feedback = f"{res['passed']}/{res['total']} tests réussis. Premier test qui échoue : « {first_fail['doc']} » → {first_fail['message']}"
		return {"score": score, "details": res["tests"], "feedback": feedback, "error": res["error"]}

	def run_papier(self, data: Dict[str, Any], answer: str) -> Dict[str, Any]:
		"""mode papier, étape 1 : si des tests existent, ils cochent d'office les critères 'auto' réussis"""
		auto_checked: List[int] = []
		feedback = "Compare ta copie au corrigé et coche honnêtement les critères respectés."
		if data.get("tests"):
			res = run_code(answer, data["tests"], data.get("setup", ""))
			passed = {t["name"] for t in res["tests"] if t["passed"]}
			auto_checked = [i for i, c in enumerate(data["grille"]) if c.get("auto") and c["auto"] in passed]
			if res["error"]:
				feedback = f"Le serveur n'a pas pu valider ta copie ({res['error']}). Auto-évalue-toi avec la grille."
			elif auto_checked:
				feedback = f"Le serveur a validé {len(auto_checked)} critère(s) automatiquement. Coche les autres toi-même."
		return {"auto_checked": auto_checked, "feedback": feedback}

	def grade_papier(self, data: Dict[str, Any], answer: Dict[str, Any]) -> Dict[str, Any]:
		"""mode papier, étape 2 : score = points des critères cochés / total"""
		grille = data["grille"]
		checked = set(int(i) for i in (answer or {}).get("checked", []))
		total = sum(c.get("points", 1) for c in grille)
		got = sum(c.get("points", 1) for i, c in enumerate(grille) if i in checked)
		return {"score": got / total if total else 0.0, "details": sorted(checked), "feedback": f"{got:g} / {total:g} points selon la grille."}
