import os
from flask import Flask


def create_app(db_uri=None):
	"""
	application factory : crée et configure l'app, puis enregistre les blueprints
	db_uri permet aux tests d'utiliser une autre base
	"""
	app = Flask(__name__, static_url_path='/static')

	app.config['DATABASE_PATH'] = os.path.join(app.root_path, 'training.db')
	app.config['SQLALCHEMY_DATABASE_URI'] = db_uri or 'sqlite:///' + app.config['DATABASE_PATH']
	app.secret_key = 'entrainement-r5a05-local'

	# import ici (et pas en haut du fichier) pour éviter les imports circulaires
	from app.blueprints import index_bp, sessions_bp, lessons_bp, exercises_bp, progress_bp, exam_bp
	app.register_blueprint(index_bp)
	app.register_blueprint(sessions_bp, url_prefix='/sessions')
	app.register_blueprint(lessons_bp, url_prefix='/lessons')
	app.register_blueprint(exercises_bp, url_prefix='/exercises')
	app.register_blueprint(progress_bp, url_prefix='/progress')
	app.register_blueprint(exam_bp, url_prefix='/exam')

	from app.blueprints.filters import register_filters
	register_filters(app)

	return app
