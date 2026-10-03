"""correction des exercices (hors exécution de code)"""
from app.services.GradingService import GradingService, normalize, matches

g = GradingService()


def test_normalisation_trous():
	assert normalize("Blueprint( 'movies' ,  __name__ )") == normalize('Blueprint("movies", __name__)')
	assert matches(" url_prefix ", ["url_prefix"])
	assert matches('"templates"', ["'templates'"])
	assert not matches("template", ["'templates'"])


def test_trous_plusieurs_reponses_acceptees():
	data = {"code": "x = [[0]]", "blanks": [["(id,)", "[id]"]]}
	assert g.grade_trous(data, ["[id]"])["score"] == 1
	assert g.grade_trous(data, ["(id)"])["score"] == 0


def test_trous_score_partiel():
	data = {"code": "[[0]] [[1]]", "blanks": [["a"], ["b"]]}
	res = g.grade_trous(data, ["a", "z"])
	assert res["score"] == 0.5 and res["details"] == [True, False]


def test_trous_reponse_manquante():
	data = {"code": "[[0]] [[1]]", "blanks": [["a"], ["b"]]}
	assert g.grade_trous(data, ["a"])["score"] == 0.5


def test_qcm_simple_et_multiple():
	assert g.grade_qcm({"choices": ["a", "b"], "answer": [1]}, [1])["score"] == 1
	assert g.grade_qcm({"choices": ["a", "b", "c"], "answer": [0, 2]}, [0])["score"] == 0
	assert g.grade_qcm({"choices": ["a", "b", "c"], "answer": [0, 2]}, [2, 0])["score"] == 1


def test_ordre():
	data = {"lines": ["a", "b", "c", "d"]}
	assert g.grade_ordre(data, [0, 1, 2, 3])["score"] == 1
	assert g.grade_ordre(data, [1, 0, 2, 3])["score"] == 0.5


def test_relier():
	data = {"pairs": [["x", "1"], ["y", "2"], ["z", "3"]]}
	assert g.grade_relier(data, [0, 1, 2])["score"] == 1
	assert round(g.grade_relier(data, [0, 2, None])["score"], 2) == 0.33


def test_bug_localiser_et_corriger():
	data = {"code": "a\nb = 1\nc", "fixes": {"2": ["b = 2"]}}
	assert g.grade_bug(data, {"lines": [2], "fixes": {"2": "b=2"}})["score"] == 1
	assert g.grade_bug(data, {"lines": [2], "fixes": {"2": "b = 1"}})["score"] == 0.5    # trouvée, mal corrigée
	assert g.grade_bug(data, {"lines": [1, 2], "fixes": {"2": "b = 2"}})["score"] == 0.75  # une ligne en trop


def test_papier_grille():
	data = {"grille": [{"critere": "a", "points": 1}, {"critere": "b", "points": 3}]}
	assert g.grade_papier(data, {"checked": [1]})["score"] == 0.75
	assert g.grade_papier(data, {"checked": []})["score"] == 0
