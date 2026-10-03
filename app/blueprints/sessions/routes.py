from flask import Blueprint, render_template, abort
from app.services.CourseService import CourseService
from app.services.ProgressService import ProgressService

sessions_bp = Blueprint('sessions', __name__, template_folder="templates")


@sessions_bp.route('/<int:session_id>', methods=['GET'])
def session_view(session_id):
	cs = CourseService()
	session = cs.getSessionById(session_id)
	if session is None:
		abort(404)
	paliers = [{"palier": p, "stars": ProgressService.starsOf(p.lessons)} for p in session.paliers]
	metadata = {"title": session.title, "pagename": "sessions"}
	return render_template('session.html', metadata=metadata, course=session, paliers=paliers, total=ProgressService.starsOf(session.lessons))
