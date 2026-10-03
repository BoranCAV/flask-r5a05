import re
from markupsafe import Markup, escape


def mini_markdown(text):
	"""
	markdown minimal pour les énoncés et fiches : `code`, **gras**, listes "- ", paragraphes
	(pas de dépendance markdown : le contenu est écrit par nous)
	"""
	if not text:
		return ""
	html, in_list = [], False
	for line in str(text).strip().split("\n"):
		s = str(escape(line.rstrip()))
		s = re.sub(r"`([^`]+)`", r"<code>\1</code>", s)
		s = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", s)
		if s.lstrip().startswith("- "):
			if not in_list:
				html.append("<ul>")
				in_list = True
			html.append(f"<li>{s.lstrip()[2:]}</li>")
			continue
		if in_list:
			html.append("</ul>")
			in_list = False
		if s.strip():
			html.append(f"<p>{s}</p>")
	if in_list:
		html.append("</ul>")
	return Markup("".join(html))


def register_filters(app):
	app.jinja_env.filters['md'] = mini_markdown
