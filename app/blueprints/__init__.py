from app.blueprints.index import index_bp
from app.blueprints.sessions import sessions_bp
from app.blueprints.lessons import lessons_bp
from app.blueprints.exercises import exercises_bp
from app.blueprints.progress import progress_bp
from app.blueprints.exam import exam_bp

__all__ = [
	'index_bp',
	'sessions_bp',
	'lessons_bp',
	'exercises_bp',
	'progress_bp',
	'exam_bp',
]
