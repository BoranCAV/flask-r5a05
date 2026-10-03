// Déroulé des exercices : saisie, correction (fetch JSON), indices, navigation, chronos, étoiles.
(function () {
	"use strict";
	const runner = document.getElementById("runner");
	if (!runner) return;

	const RUN_ID = runner.dataset.run;
	const LESSON_ID = runner.dataset.lesson;
	const MODE = runner.dataset.mode; // lesson | revision | exam
	const url = (kind, id) => runner.dataset[kind + "Url"].replace("__ID__", encodeURIComponent(id));
	const sections = Array.from(runner.querySelectorAll(".exercise"));
	const state = new Map(sections.map((s) => [s.dataset.id, { hints: 0, done: false, timerStart: null, inTime: true }]));
	let current = 0;

	// ---------- utilitaires ----------
	const el = (tag, cls, text) => { const e = document.createElement(tag); if (cls) e.className = cls; if (text != null) e.textContent = text; return e; };
	const codeBlock = (code) => {
		const pre = el("pre", "code-block mt-2"); const c = el("code", "language-python", code || "");
		pre.appendChild(c); if (window.hljs) hljs.highlightElement(c); return pre;
	};
	async function post(u, body) {
		const r = await fetch(u, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) });
		if (!r.ok) throw new Error("Erreur serveur " + r.status);
		return r.json();
	}
	const fmt = (s) => { const a = Math.abs(s); return (s < 0 ? "-" : "") + Math.floor(a / 60) + ":" + String(a % 60).padStart(2, "0"); };

	// ---------- navigation (mode leçon / révision) ----------
	function show(i) {
		if (MODE === "exam") return;
		current = Math.max(0, Math.min(i, sections.length - 1));
		sections.forEach((s, k) => { s.hidden = k !== current; });
		runner.querySelectorAll(".ex-dot").forEach((d, k) => { if (k === current) d.setAttribute("aria-current", "step"); else d.removeAttribute("aria-current"); });
		startPaperTimer(sections[current]);
		sections[current].querySelector("h2").focus({ preventScroll: true });
	}
	runner.querySelectorAll(".ex-dot").forEach((d) => d.addEventListener("click", () => show(+d.dataset.goto)));
	sections.forEach((s) => s.querySelector("h2").setAttribute("tabindex", "-1"));

	function updateProgress() {
		const done = [...state.values()].filter((s) => s.done).length;
		const bar = document.getElementById("run-progress");
		if (bar) { bar.style.width = (100 * done / sections.length) + "%"; bar.parentElement.setAttribute("aria-valuenow", done); }
	}

	// ---------- chronos ----------
	function startPaperTimer(section) {
		const t = section.querySelector("[data-timer]");
		const st = state.get(section.dataset.id);
		if (!t || st.timerStart) return;
		const duree = +section.dataset.duree;
		st.timerStart = Date.now();
		const span = t.querySelector("span");
		st.interval = setInterval(() => {
			const left = duree - Math.floor((Date.now() - st.timerStart) / 1000);
			span.textContent = fmt(left);
			if (left < 0) { t.classList.add("over"); st.inTime = false; }
		}, 1000);
	}
	const examTimer = document.getElementById("exam-timer");
	let examInTime = true;
	if (examTimer) {
		const start = Date.now(), dur = +examTimer.dataset.duration, span = examTimer.querySelector("span");
		examTimer._interval = setInterval(() => {
			const left = dur - Math.floor((Date.now() - start) / 1000);
			span.textContent = fmt(left);
			if (left < 0) { examTimer.classList.add("over"); examInTime = false; }
		}, 1000);
	} else if (sections.length) {
		startPaperTimer(sections[0]);
	}

	// ---------- lecture de la réponse selon le type ----------
	function readAnswer(section) {
		const type = section.dataset.type;
		if (type === "qcm") return [...section.querySelectorAll("input:checked")].map((i) => +i.value);
		if (type === "trous") return [...section.querySelectorAll("[data-blank]")].sort((a, b) => a.dataset.blank - b.dataset.blank).map((i) => i.value);
		if (type === "ordre") return [...section.querySelectorAll(".ordre li")].map((li) => +li.dataset.orig);
		if (type === "relier") return [...section.querySelectorAll("select[data-notion]")].map((s) => (s.value === "" ? null : +s.value));
		if (type === "bug") {
			const lines = [...section.querySelectorAll('.bug-line[aria-pressed="true"]')].map((b) => +b.dataset.line);
			const fixes = {};
			section.querySelectorAll("[data-fix]").forEach((i) => { fixes[i.dataset.fix] = i.value; });
			return { lines, fixes };
		}
		if (type === "code" || type === "papier") return section.querySelector("textarea").value;
		return null;
	}

	// ---------- affichage de la correction ----------
	function markDetails(section, res) {
		const type = section.dataset.type;
		if (type === "qcm") {
			section.querySelectorAll(".choice").forEach((c) => {
				const i = +c.dataset.choice, checked = c.querySelector("input").checked, good = res.details.includes(i);
				c.classList.toggle("is-correct", good);
				c.classList.toggle("is-wrong", checked && !good);
			});
		} else if (type === "trous") {
			section.querySelectorAll("[data-blank]").forEach((inp) => {
				const ok = res.details[+inp.dataset.blank];
				inp.classList.toggle("is-correct", ok); inp.classList.toggle("is-wrong", !ok);
				if (!ok && res.expected) inp.title = "Attendu : " + res.expected[+inp.dataset.blank][0];
			});
		} else if (type === "ordre") {
			section.querySelectorAll(".ordre li").forEach((li, k) => { li.classList.toggle("is-correct", res.details[k]); li.classList.toggle("is-wrong", !res.details[k]); });
		} else if (type === "relier") {
			section.querySelectorAll("select[data-notion]").forEach((s) => { const ok = res.details[+s.dataset.notion]; s.classList.toggle("is-correct", ok); s.classList.toggle("is-wrong", !ok); });
		} else if (type === "bug") {
			section.querySelectorAll(".bug-line").forEach((b) => b.classList.toggle("was-bug", res.details.bug_lines.includes(+b.dataset.line)));
		}
	}

	function renderFeedback(section, res) {
		const area = section.querySelector(".feedback-area");
		area.innerHTML = "";
		const box = el("div", "feedback reveal " + (res.correct ? "ok" : "ko"));
		const head = el("p", "fw-semibold mb-1", (res.correct ? "✓ " : "✗ ") + res.feedback);
		box.appendChild(head);
		if (res.score !== res.raw) box.appendChild(el("p", "small mb-1", `Score : ${res.score} % (${res.raw} % − pénalité d'indices)`));
		if (section.dataset.type === "code" && Array.isArray(res.details) && res.details.length) {
			const ul = el("ul", "tests");
			res.details.forEach((t) => { const li = el("li", t.passed ? "pass" : "", t.doc + (t.passed ? "" : " → " + t.message)); ul.appendChild(li); });
			box.appendChild(ul);
		}
		if (section.dataset.type === "bug" && res.expected) {
			box.appendChild(el("p", "small mb-1 mt-2", "Corrections attendues :"));
			Object.entries(res.expected).forEach(([n, line]) => box.appendChild(codeBlock(`# ligne ${n}\n${line}`)));
		}
		area.appendChild(box);
		const explainBtn = section.querySelector('[data-action="explain"]');
		if (res.explication || res.solution) {
			section._explain = res;
			explainBtn.hidden = false;
		}
	}

	function renderExplain(section) {
		const res = section._explain || {};
		const box = section.querySelector(".explain-area");
		box.innerHTML = "";
		if (res.explication) { const p = el("div", "feedback reveal"); p.appendChild(el("p", "mb-0", res.explication)); box.appendChild(p); }
		if (res.solution) { box.appendChild(el("p", "small fw-semibold mt-2 mb-0", "Corrigé :")); box.appendChild(codeBlock(res.solution)); }
		box.hidden = false;
	}

	function markDot(section, ok) {
		const i = sections.indexOf(section);
		const dot = runner.querySelectorAll(".ex-dot")[i];
		if (dot) { dot.classList.toggle("ok", ok); dot.classList.toggle("ko", !ok); }
	}

	// ---------- résultat de la leçon : étoiles ----------
	function showResult(summary) {
		if (!summary || !summary.finished) return;
		const panel = document.getElementById("result-panel");
		const stars = panel.querySelectorAll(".star");
		stars.forEach((s, k) => {
			s.classList.remove("on", "earned");
			if (k < summary.stars) { void s.offsetWidth; s.classList.add("on", "earned"); }
		});
		document.getElementById("result-stars").setAttribute("aria-label", `${summary.stars} étoile(s) sur 3`);
		document.getElementById("result-score").textContent = MODE === "exam" ? `Note : ${summary.note20} / 20` : `Score : ${summary.score} %`;
		let msg = summary.message;
		if (summary.new_stars > 0) msg = `+${summary.new_stars} étoile${summary.new_stars > 1 ? "s" : ""} ! ` + msg;
		else if (summary.best_stars > summary.stars) msg += ` (Ton record reste ${summary.best_stars} ★.)`;
		document.getElementById("result-msg").textContent = msg;
		const best = document.querySelectorAll("#best-stars .star");
		best.forEach((s, k) => s.classList.toggle("on", k < summary.best_stars));
		panel.hidden = false;
		if (MODE !== "exam") sections.forEach((s) => { s.hidden = true; });
		panel.scrollIntoView({ behavior: matchMedia("(prefers-reduced-motion: reduce)").matches ? "auto" : "smooth", block: "center" });
	}

	// ---------- actions ----------
	async function check(section, answerOverride) {
		const st = state.get(section.dataset.id);
		const btn = section.querySelector('[data-action="check"], [data-action="selfeval"]');
		const inTime = MODE === "exam" ? examInTime : st.inTime;
		try {
			if (btn) btn.disabled = true;
			const res = await post(url("check", section.dataset.id), {
				run_id: RUN_ID, lesson_id: LESSON_ID, hints: st.hints, in_time: inTime,
				answer: answerOverride !== undefined ? answerOverride : readAnswer(section),
			});
			st.done = true;
			markDetails(section, res);
			renderFeedback(section, res);
			markDot(section, res.correct);
			updateProgress();
			if (st.interval && section.dataset.type === "papier") clearInterval(st.interval);
			showResult(res.lesson);
			return res;
		} catch (e) {
			section.querySelector(".feedback-area").replaceChildren(el("div", "feedback ko", "Impossible de joindre le serveur : " + e.message));
		} finally {
			if (btn) btn.disabled = false;
		}
	}

	async function paper(section) {
		const st = state.get(section.dataset.id);
		if (st.interval) clearInterval(st.interval);   // copie rendue : le chrono s'arrête
		const btn = section.querySelector('[data-action="paper"]');
		if (btn) btn.disabled = true;
		const res = await post(url("run", section.dataset.id), { answer: readAnswer(section) });
		const corr = section.querySelector(".papier-correction");
		const sol = corr.querySelector("[data-solution]");
		sol.textContent = res.solution || "";
		if (window.hljs) { sol.removeAttribute("data-highlighted"); hljs.highlightElement(sol); }
		corr.querySelector("[data-papier-msg]").textContent = res.feedback;
		corr.querySelectorAll("[data-crit]").forEach((lab) => {
			const auto = res.auto_checked.includes(+lab.dataset.crit);
			lab.classList.toggle("auto", auto);
			const cb = lab.querySelector("input");
			if (auto) { cb.checked = true; cb.disabled = true; lab.title = "Validé automatiquement par les tests du serveur"; }
		});
		corr.hidden = false;
		corr.classList.add("reveal");
		section.querySelector("textarea").readOnly = true;
		if (btn) btn.hidden = true;
		return res;
	}

	function selfeval(section) {
		const checked = [...section.querySelectorAll(".grille input:checked")].map((c) => +c.value);
		section.querySelector('[data-action="selfeval"]').hidden = true;
		section.querySelectorAll(".grille input").forEach((c) => { c.disabled = true; });
		return check(section, { checked });
	}

	function hint(section) {
		const st = state.get(section.dataset.id);
		const tpls = section.querySelectorAll("template[data-hint]");
		if (st.hints >= tpls.length) return;
		const h = el("div", "hint reveal", "💡 " + tpls[st.hints].content.textContent.trim());
		section.querySelector(".hints").appendChild(h);
		st.hints++;
		const btn = section.querySelector('[data-action="hint"]');
		const left = tpls.length - st.hints;
		btn.querySelector("span").textContent = `(−20 %, ${left} dispo)`;
		if (!left) btn.disabled = true;
	}

	async function giveup(section) {
		const r = await fetch(url("solution", section.dataset.id));
		section._explain = await r.json();
		renderExplain(section);
	}

	runner.addEventListener("click", (e) => {
		const btn = e.target.closest("[data-action]");
		if (!btn) return;
		const section = btn.closest(".exercise");
		const a = btn.dataset.action;
		if (a === "check") check(section);
		else if (a === "hint") hint(section);
		else if (a === "explain") renderExplain(section);
		else if (a === "next") show(sections.indexOf(section) + 1);
		else if (a === "paper") paper(section);
		else if (a === "selfeval") selfeval(section);
		else if (a === "giveup") giveup(section);
	});

	// ---------- remettre dans l'ordre : glisser-déposer + clavier ----------
	runner.querySelectorAll(".ordre").forEach((list) => {
		let dragged = null;
		list.addEventListener("dragstart", (e) => { dragged = e.target.closest("li"); dragged.classList.add("dragging"); e.dataTransfer.effectAllowed = "move"; });
		list.addEventListener("dragend", () => { if (dragged) dragged.classList.remove("dragging"); dragged = null; });
		list.addEventListener("dragover", (e) => {
			e.preventDefault();
			const over = e.target.closest("li");
			if (!dragged || !over || over === dragged) return;
			const r = over.getBoundingClientRect();
			list.insertBefore(dragged, e.clientY > r.top + r.height / 2 ? over.nextSibling : over);
		});
		list.addEventListener("click", (e) => {
			const b = e.target.closest("[data-move]");
			if (!b) return;
			const li = b.closest("li");
			if (+b.dataset.move < 0 && li.previousElementSibling) list.insertBefore(li, li.previousElementSibling);
			else if (+b.dataset.move > 0 && li.nextElementSibling) list.insertBefore(li.nextElementSibling, li);
			b.focus();
		});
	});

	// ---------- trouver le bug : sélection des lignes + champ de correction ----------
	runner.querySelectorAll(".bug-lines").forEach((list) => {
		const fixes = list.parentElement.querySelector(".bug-fixes");
		list.addEventListener("click", (e) => {
			const b = e.target.closest(".bug-line");
			if (!b) return;
			const on = b.getAttribute("aria-pressed") !== "true";
			b.setAttribute("aria-pressed", on);
			const n = b.dataset.line;
			const existing = fixes.querySelector(`[data-fix-wrap="${n}"]`);
			if (on && !existing) {
				const wrap = el("div", "mb-2 reveal"); wrap.dataset.fixWrap = n;
				const lab = el("label", "small fw-semibold d-block mb-1", `Correction de la ligne ${n}`);
				const inp = el("input", "form-control font-code"); inp.dataset.fix = n; inp.value = b.textContent; inp.spellcheck = false; inp.autocomplete = "off";
				inp.id = `fix-${list.closest(".exercise").dataset.id}-${n}`; lab.htmlFor = inp.id;
				wrap.append(lab, inp); fixes.appendChild(wrap);
				[...fixes.children].sort((a, c) => a.dataset.fixWrap - c.dataset.fixWrap).forEach((c) => fixes.appendChild(c));
			} else if (!on && existing) existing.remove();
		});
	});

	// trous : la largeur du champ suit la saisie
	runner.querySelectorAll("[data-blank]").forEach((i) => i.addEventListener("input", () => { i.size = Math.max(10, i.value.length + 1); }));

	// ---------- contrôle blanc : rendre la copie ----------
	const submit = document.getElementById("exam-submit");
	if (submit) {
		submit.addEventListener("click", async () => {
			if (!confirm("Rendre la copie ? Tu ne pourras plus modifier tes réponses.")) return;
			submit.disabled = true;
			clearInterval(examTimer._interval);
			runner.querySelectorAll("input, select, textarea").forEach((x) => { if (!x.closest(".grille")) x.disabled = true; });
			for (const s of sections) {
				if (s.dataset.type === "papier") await paper(s);
				else await check(s);
			}
			submit.textContent = "Copie rendue : auto-évalue tes exercices de code";
			const firstPaper = sections.find((s) => s.dataset.type === "papier");
			if (firstPaper) firstPaper.scrollIntoView({ block: "start" });
		});
	}
})();
