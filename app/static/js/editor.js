// CodeMirror 6 (CDN) sur les textarea[data-cm] ; si le CDN ne répond pas, le textarea reste utilisable.
// Le textarea reste la source de vérité : lesson.js lit toujours textarea.value.
try {
	const { EditorView, basicSetup } = await import("https://esm.sh/codemirror@6.0.1");
	const { python } = await import("https://esm.sh/@codemirror/lang-python@6.1.6");
	const { Compartment } = await import("https://esm.sh/@codemirror/state@6");
	const { oneDark } = await import("https://esm.sh/@codemirror/theme-one-dark@6");
	const { indentUnit } = await import("https://esm.sh/@codemirror/language@6");

	const isDark = () => document.documentElement.getAttribute("data-bs-theme") === "dark";
	const views = [];

	document.querySelectorAll("textarea[data-cm]").forEach((ta) => {
		const theme = new Compartment();
		const view = new EditorView({
			doc: ta.value,
			extensions: [
				basicSetup,
				python(),
				indentUnit.of("    "),
				theme.of(isDark() ? oneDark : []),
				EditorView.contentAttributes.of({ "aria-label": "Éditeur de code Python" }),
				EditorView.updateListener.of((u) => { if (u.docChanged) ta.value = u.state.doc.toString(); }),
			],
		});
		ta.after(view.dom);
		ta.hidden = true;
		views.push({ view, theme });
	});

	document.addEventListener("themechange", () => {
		views.forEach(({ view, theme }) => view.dispatch({ effects: theme.reconfigure(isDark() ? oneDark : []) }));
	});
} catch (e) {
	console.warn("CodeMirror indisponible, éditeur texte simple utilisé.", e);
}
