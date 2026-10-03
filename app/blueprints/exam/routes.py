import uuid
from flask import Blueprint, render_template, abort
from app.services.CourseService import CourseService
from app.services.ProgressService import ProgressService

exam_bp = Blueprint('exam', __name__, template_folder="templates")

EXAM_SESSION_ID = 4


@exam_bp.route('/', methods=['GET'])
def exam_list():
	cs = CourseService()
	session = cs.getSessionById(EXAM_SESSION_ID)
	if session is None:
		abort(404)
	metadata = {"title": "Contrôle blanc", "pagename": "exam"}
	return render_template('exam_list.html', metadata=metadata, course=session, total=ProgressService.starsOf(session.lessons))


@exam_bp.route('/<string:lesson_id>', methods=['GET'])
def exam_view(lesson_id):
	"""un sujet complet : toutes les questions d'un coup, chrono global, copie rendue à la fin"""
	cs = CourseService()
	lesson = cs.getLessonById(lesson_id)
	if lesson is None or lesson.palier.session_id != EXAM_SESSION_ID:
		abort(404)
	exercises = [cs.exerciseView(ex) for ex in lesson.exercises]
	metadata = {"title": lesson.title, "pagename": "exam"}
	return render_template(
		'lesson.html', metadata=metadata, lesson=lesson, course=lesson.palier.session,
		exercises=exercises, run_id=uuid.uuid4().hex, nav={"prev": None, "next": None}, mode="exam"
	)
