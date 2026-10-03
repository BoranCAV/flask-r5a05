"""routes de l'application (tout est accessible, aucun verrou)"""
from app.services.CourseService import CourseService


def test_pages_principales(client):
	for url in ["/", "/sessions/1", "/sessions/2", "/sessions/3", "/exam/", "/progress/", "/progress/revision"]:
		assert client.get(url).status_code == 200, url


def test_toutes_les_lecons_sont_ouvertes(app, client):
	with app.app_context():
		sessions = CourseService().getAllSessions()
	for s in sessions:
		for lesson in s.lessons:
			url = f"/exam/{lesson.id}" if s.is_exam else f"/lessons/{lesson.id}"
			r = client.get(url)
			assert r.status_code == 200, url
			assert b"__ID__" in r.data  # le runner JS est présent


def test_404(client):
	assert client.get("/lessons/9.99").status_code == 404
	assert client.get("/sessions/42").status_code == 404
	assert client.post("/exercises/zz/check", json={"run_id": "x"}).status_code == 404


def test_reponses_non_divulguees(client):
	"""la page d'une leçon n'envoie pas les tests cachés ni les corrections"""
	html = client.get("/lessons/1.7").get_data(as_text=True)
	assert "def test_init_defaut" not in html
	assert "return f\"&lt;Book id" not in html and 'return f"<Book id' not in html


def test_check_qcm_et_progression(client):
	r = client.post("/exercises/1.1-1/check", json={"run_id": "abc", "lesson_id": "1.1", "answer": [2], "hints": 0})
	data = r.get_json()
	assert r.status_code == 200 and data["correct"] and data["score"] == 100
	assert data["lesson"]["done"] == 1 and not data["lesson"]["finished"]


def test_check_avec_indice(client):
	data = client.post("/exercises/1.1-1/check", json={"run_id": "def", "answer": [2], "hints": 1}).get_json()
	assert data["raw"] == 100 and data["score"] == 80


def test_code_ne_donne_pas_la_solution_en_cas_d_echec(client):
	data = client.post("/exercises/1.7-5/check", json={"run_id": "c", "answer": "class Book:\n    pass\n"}).get_json()
	assert not data["correct"] and "solution" not in data
	assert "Premier test qui échoue" in data["feedback"] or "plante" in data["feedback"]


def test_papier_auto_validation(client):
	sol = "from app import create_app\n\napp = create_app()\n\nif __name__ == '__main__':\n    app.run(host='localhost', port=8000, debug=True)\n"
	data = client.post("/exercises/1.10-2/run", json={"answer": sol}).get_json()
	assert data["auto_checked"] == [0, 1, 2, 3] and data["solution"]
	res = client.post("/exercises/1.10-2/check", json={"run_id": "p", "lesson_id": "1.10", "answer": {"checked": [0, 1, 2, 3]}}).get_json()
	assert res["score"] == 100
