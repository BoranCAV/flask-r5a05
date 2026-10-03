"""calcul des étoiles et de la progression"""
import uuid

from app.services.ProgressService import ProgressService

stars = ProgressService.stars_for


def test_trois_etoiles_parfait():
	assert stars(1.0, 0, True) == 3


def test_pas_trois_etoiles_si_indice_ou_deuxieme_essai():
	assert stars(1.0, 1, True) == 2      # un indice → 2 étoiles max
	assert stars(1.0, 0, False) == 2     # pas du premier coup → 2 étoiles max


def test_deux_etoiles():
	assert stars(0.8, 0, False) == 2
	assert stars(0.8, 1, False) == 2
	assert stars(0.85, 2, False) == 1    # plus d'un indice → 1 étoile


def test_une_etoile_et_zero():
	assert stars(0.5, 5, False) == 1
	assert stars(0.49, 0, False) == 0


def test_penalite_indice():
	assert ProgressService.apply_hints(1.0, 1) == 0.8
	assert ProgressService.apply_hints(0.3, 2) == 0.0   # plancher à 0


def test_run_complet_et_meilleur_score(app):
	"""une leçon entièrement réussie donne 3 étoiles, un passage moins bon ne fait pas baisser le record"""
	from app.services.CourseService import CourseService
	with app.app_context():
		cs, ps = CourseService(), ProgressService()
		lesson = cs.getLessonById("1.1")
		run = uuid.uuid4().hex
		summary = None
		for ex in lesson.exercises:
			ps.recordAttempt(ex, run, 1.0, 0)
			summary = ps.lessonRunSummary(cs.getLessonById("1.1"), run)
		assert summary["finished"] and summary["stars"] == 3 and summary["new_stars"] == 3

		run2 = uuid.uuid4().hex
		for ex in lesson.exercises:
			ps.recordAttempt(ex, run2, 0.0, 0)
		summary2 = ps.lessonRunSummary(cs.getLessonById("1.1"), run2)
		assert summary2["stars"] == 0 and summary2["best_stars"] == 3
		assert cs.getLessonById("1.1").stars == 3


def test_premier_essai_seul_compte(app):
	"""réussir au 2e essai ne donne pas le score plein (sauf exercices de code)"""
	from app.services.CourseService import CourseService
	with app.app_context():
		cs, ps = CourseService(), ProgressService()
		lesson = cs.getLessonById("1.1")
		run = uuid.uuid4().hex
		first = lesson.exercises[0]
		ps.recordAttempt(first, run, 0.0, 0)
		ps.recordAttempt(first, run, 1.0, 0)
		for ex in lesson.exercises[1:]:
			ps.recordAttempt(ex, run, 1.0, 0)
		summary = ps.lessonRunSummary(cs.getLessonById("1.1"), run)
		assert summary["score"] < 100 and summary["stars"] == 2


def test_points_faibles(app):
	from app.services.CourseService import CourseService
	with app.app_context():
		cs, ps = CourseService(), ProgressService()
		ex = cs.getLessonById("1.1").exercises[0]
		ps.recordAttempt(ex, "r", 0.0, 0)
		weak = ps.weakTags()
		assert weak and weak[0]["score"] == 0
		assert set(t.name for t in ex.tags) & {w["tag"] for w in weak}
		assert ps.revisionExercises()   # une série de révision est proposée
