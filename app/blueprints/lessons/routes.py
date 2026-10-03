import uuid
from flask import Blueprint, render_template, abort
from app.services.CourseService import CourseService

lessons_bp = Blueprint('lessons', __name__, template_folder="templates")


@lessons_bp.route('/<string:lesson_id>', methods=['GET'])
def lesson_view(lesson_id):
	cs = CourseService()
	lesson = cs.getLessonById(lesson_id)
	if lesson is None:
		abort(404)
	session = lesson.palier.session
	# voisins pour la navigation précédent / suivant
	full = cs.getSessionById(session.id)
	ids = [l.id for l in full.lessons]
	i = ids.index(lesson.id)
	nav = {"prev": ids[i - 1] if i > 0 else None, "next": ids[i + 1] if i + 1 < len(ids) else None}

	exercises = [cs.exerciseView(ex) for ex in lesson.exercises]
	metadata = {"title": f"{lesson.id} · {lesson.title}", "pagename": "lessons"}
	return render_template(
		'lesson.html', metadata=metadata, lesson=lesson, course=session, exercises=exercises,
		run_id=uuid.uuid4().hex, nav=nav, mode="lesson"
	)
