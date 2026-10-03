from typing import Dict, List, Any, Optional
from flask import current_app

from app.models.TrainingDAO import TrainingSqliteORM as TrainingDAO
from app.models.Progress import Attempt

HINT_PENALTY = 0.2

ENCOURAGEMENTS = {
	0: "Pas grave : relis la fiche mémo et retente, c'est comme ça qu'on apprend.",
	1: "Première étoile ! Les bases sont là, vise la deuxième.",
	2: "Deux étoiles, solide ! Encore un passage sans indice pour la troisième ?",
	3: "Trois étoiles, sans faute. Tu es prêt·e pour le papier !",
}


class ProgressService:
	"""
	logique de progression : score des exercices, étoiles des leçons, points faibles
	"""

	def __init__(self, db_uri: Optional[str] = None):
		if db_uri is None:
			try:
				db_uri = current_app.config.get('SQLALCHEMY_DATABASE_URI')
			except RuntimeError:
				pass
		self.dao = TrainingDAO(db_uri=db_uri)

	@staticmethod
	def apply_hints(raw: float, hints: int) -> float:
		"""chaque indice coûte 20 % du score de l'exercice (plancher 0)"""
		return max(0.0, raw - HINT_PENALTY * hints)

	@staticmethod
	def stars_for(score: float, hints: int, perfect_first_try: bool) -> int:
		"""
		★ score ≥ 50 % · ★★ score ≥ 80 % et ≤ 1 indice
		★★★ 100 % du premier coup, sans indice (et dans le temps pour le mode papier)
		"""
		if score >= 0.999 and hints == 0 and perfect_first_try:
			return 3
		if score >= 0.8 and hints <= 1:
			return 2
		if score >= 0.5:
			return 1
		return 0

	def recordAttempt(self, exercise, run_id: str, raw: float, hints: int, in_time: bool = True) -> Attempt:
		"""enregistre une tentative ; first_try = première tentative du run, parfaite, dans le temps"""
		previous = [a for a in self.dao.findAttemptsByRun(run_id) if a.exercise_id == exercise.id]
		score = self.apply_hints(raw, hints)
		attempt = Attempt(
			exercise_id=exercise.id,
			run_id=run_id,
			score=score,
			hints_used=hints,
			first_try=(not previous and raw >= 0.999 and hints == 0 and in_time)
		)
		self.dao.addAttempt(attempt)
		return attempt

	def lessonRunSummary(self, lesson, run_id: str) -> Dict[str, Any]:
		"""
		état du passage de la leçon : exercices faits, score courant
		si tous les exercices ont été tentés, calcule les étoiles et garde le meilleur résultat
		"""
		attempts = self.dao.findAttemptsByRun(run_id)
		by_ex: Dict[str, List[Attempt]] = {}
		for a in attempts:
			by_ex.setdefault(a.exercise_id, []).append(a)

		done = [ex for ex in lesson.exercises if ex.id in by_ex]
		summary = {"done": len(done), "total": len(lesson.exercises), "finished": False}
		if len(done) < len(lesson.exercises):
			return summary

		total_points, got, hints, perfect = 0.0, 0.0, 0, True
		for ex in lesson.exercises:
			tries = by_ex[ex.id]
			# on garde la 1re tentative ; pour le code (tests relancés) et le papier, la dernière
			counted = tries[-1] if ex.type in ("code", "papier") else tries[0]
			total_points += ex.points or 1
			got += (ex.points or 1) * counted.score
			hints += max(t.hints_used for t in tries)
			perfect = perfect and tries[0].first_try
		score = got / total_points if total_points else 0.0
		stars = self.stars_for(score, hints, perfect)
		before = lesson.progress.stars if lesson.progress else 0
		progress = self.dao.saveBestProgress(lesson.id, score, stars)
		summary.update({
			"finished": True,
			"score": round(score * 100),
			"note20": round(score * 20, 1),
			"stars": stars,
			"best_stars": progress.stars,
			"new_stars": max(0, stars - before),
			"message": ENCOURAGEMENTS[stars],
		})
		return summary

	def weakTags(self, limit: int = 5) -> List[Dict[str, Any]]:
		"""notions les plus ratées (score moyen le plus bas)"""
		stats = sorted(self.dao.findTagStats(), key=lambda s: s[1])
		return [{"tag": name, "score": round(avg * 100), "count": n} for name, avg, n in stats[:limit] if avg < 0.999]

	def revisionExercises(self, limit: int = 10) -> List:
		"""série d'exercices sur les 3 notions les plus faibles"""
		tags = [w["tag"] for w in self.weakTags(3)]
		return self.dao.findExercisesByTags(tags, limit) if tags else []

	@staticmethod
	def starsOf(lessons) -> Dict[str, int]:
		"""total d'étoiles obtenues / maximum possible pour une liste de leçons"""
		lessons = [l for l in lessons if not l.bonus]
		got = sum(l.stars for l in lessons)
		return {"got": got, "max": 3 * len(lessons), "avg": got / len(lessons) if lessons else 0.0}
