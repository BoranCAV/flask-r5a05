import uuid
from flask import Blueprint, render_template
from app.services.CourseService import CourseService
from app.services.ProgressService import ProgressService

progress_bp = Blueprint('progress', __name__, template_folder="templates")


@progress_bp.route('/', methods=['GET'])
def dashboard():
	cs = CourseService()
	ps = ProgressService()
	sessions = cs.getAllSessions()
	rows = [
		{
			"session": s,
			"stars": ps.starsOf(s.lessons),
			"paliers": [{"palier": p, "stars": ps.starsOf(p.lessons)} for p in s.paliers],
		}
		for s in sessions
	]
	metadata = {"title": "Ma progression", "pagename": "progress"}
	return render_template('progress.html', metadata=metadata, rows=rows, weak=ps.weakTags())


@progress_bp.route('/revision', methods=['GET'])
def revision():
	"""série d'exercices générée sur les notions les plus ratées"""
	cs = CourseService()
	ps = ProgressService()
	weak = ps.weakTags(3)
	exercises = [cs.exerciseView(ex) for ex in ps.revisionExercises()]
	metadata = {"title": "Réviser mes points faibles", "pagename": "progress"}
	return render_template('revision.html', metadata=metadata, exercises=exercises, weak=weak, run_id=uuid.uuid4().hex, mode="revision")
