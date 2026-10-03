from flask import Blueprint, request, jsonify, abort
from app.services.CourseService import CourseService
from app.services.ProgressService import ProgressService
from app.services.GradingService import GradingService

exercises_bp = Blueprint('exercises', __name__)


def _exercise_or_404(ex_id):
	ex = CourseService().getExerciseById(ex_id)
	if ex is None:
		abort(404)
	return ex


@exercises_bp.route('/<string:ex_id>/check', methods=['POST'])
def check(ex_id):
	"""
	corrige une réponse (JSON : answer, hints, run_id, lesson_id, in_time)
	enregistre la tentative et renvoie la correction + l'état de la leçon
	"""
	ex = _exercise_or_404(ex_id)
	payload = request.get_json(silent=True) or {}
	run_id = str(payload.get("run_id") or "")[:40]
	if not run_id:
		return jsonify({"error": "run_id manquant"}), 400
	hints = max(0, min(int(payload.get("hints", 0)), len(ex.indices or [])))

	result = GradingService().grade(ex.type, ex.data, payload.get("answer"))
	ps = ProgressService()
	attempt = ps.recordAttempt(ex, run_id, result["score"], hints, bool(payload.get("in_time", True)))

	response = {
		"raw": round(result["score"] * 100),
		"score": round(attempt.score * 100),
		"correct": result["score"] >= 0.999,
		"details": result["details"],
		"feedback": result["feedback"],
		"explication": ex.explication,
	}
	# la solution n'est montrée qu'une fois l'exercice réussi (ou abandonné via /solution) pour le code
	if ex.type != "code" or response["correct"]:
		response["solution"] = ex.solution
	if ex.type in ("trous", "bug"):
		response["expected"] = ex.data.get("blanks") if ex.type == "trous" else {k: v[0] for k, v in ex.data["fixes"].items()}

	lesson_id = payload.get("lesson_id")
	if lesson_id:
		lesson = CourseService().getLessonById(lesson_id)
		if lesson is not None:
			response["lesson"] = ps.lessonRunSummary(lesson, run_id)
	return jsonify(response)


@exercises_bp.route('/<string:ex_id>/run', methods=['POST'])
def run_papier(ex_id):
	"""mode papier, étape 1 : validation automatique éventuelle + corrigé + grille"""
	ex = _exercise_or_404(ex_id)
	if ex.type != "papier":
		abort(400)
	payload = request.get_json(silent=True) or {}
	result = GradingService().run_papier(ex.data, payload.get("answer", ""))
	result.update({"solution": ex.solution, "explication": ex.explication})
	return jsonify(result)


@exercises_bp.route('/<string:ex_id>/solution', methods=['GET'])
def solution(ex_id):
	"""corrigé à la demande (abandon d'un exercice de code)"""
	ex = _exercise_or_404(ex_id)
	return jsonify({"solution": ex.solution, "explication": ex.explication})
