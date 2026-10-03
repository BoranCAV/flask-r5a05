from flask import Blueprint, render_template
from app.services.CourseService import CourseService
from app.services.ProgressService import ProgressService

index_bp = Blueprint('index', __name__, template_folder="templates")


@index_bp.route('/', methods=['GET'])
def index():
	cs = CourseService()
	sessions = cs.getAllSessions()
	cards = [{"session": s, "stars": ProgressService.starsOf(s.lessons)} for s in sessions]
	all_lessons = [l for s in sessions for l in s.lessons]
	metadata = {"title": "Accueil", "pagename": "index"}
	return render_template('index.html', metadata=metadata, cards=cards, total=ProgressService.starsOf(all_lessons))
