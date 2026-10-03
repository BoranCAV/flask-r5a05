from app import create_app

app = create_app()

if __name__ == '__main__':
	# notre méthode principale (main) pour lancer l'app
	app.run(host="localhost", port=8000, debug=True)
