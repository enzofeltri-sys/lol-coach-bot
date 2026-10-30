from html import escape

STYLE = """<style>
.notes textarea,.notes input[type=text],.notes select{width:100%;background:#0d1827;color:var(--text);border:1px solid var(--line);border-radius:12px;padding:10px;font:inherit;margin:6px 0 10px}
.notes label{display:block;color:var(--muted);font-size:13px}
.notes .actions{display:flex;gap:8px;flex-wrap:wrap;align-items:center}
.notes button,.notes .file-btn{border:1px solid var(--line);border-radius:999px;padding:8px 14px;background:var(--panel);color:var(--text);cursor:pointer;font:inherit;font-size:13px}
.notes .file-btn input{display:none}
.notes ul{padding-left:20px}
</style>"""

SESSION_HTML = """<section class="section panel notes"><h2>Ma séance</h2>
<label for="session-goal">Objectif de la séance</label>
<input type="text" id="session-goal" maxlength="200" autocomplete="off">
<p class="hint" id="session-since"></p>
<div class="actions"><button type="button" id="session-close">Clôturer la séance</button></div>
<div id="session-closing" hidden>
<label for="session-result">Objectif atteint ?</label>
<select id="session-result"><option value="yes">Oui</option><option value="partial">En partie</option><option value="no">Non</option></select>
<label for="session-comment">Bilan de séance</label>
<textarea id="session-comment" rows="3" maxlength="500"></textarea>
<div class="actions"><button type="button" id="session-save">Enregistrer le bilan</button><button type="button" id="session-cancel">Annuler</button></div>
</div>
<p class="hint" id="session-status"></p>
<h3>Séances passées</h3><ul id="session-history"></ul></section>
<section class="section panel notes"><h2>Mes notes et mes données</h2>
<p class="hint">Tes notes restent dans ce navigateur : elles ne sont ni publiées ni envoyées. Elles ne passent pas d’un appareil à l’autre. Safari peut effacer les données d’un site après 7 jours sans visite : ajoute le site à l’écran d’accueil et exporte tes notes de temps en temps.</p>
<div class="actions"><button type="button" id="notes-export">Exporter</button><label class="file-btn">Importer<input type="file" id="notes-import" accept="application/json,.json"></label><button type="button" id="notes-clear">Tout effacer</button></div>
<p class="hint" id="notes-status"></p></section>
"""

OPPONENT_ANCHOR = '<p id="classic-versus-note" class="hint"></p>'
OPPONENT_HTML = OPPONENT_ANCHOR + """<div id="opp-notes" class="notes" hidden><label for="opp-text">Mes notes contre <b id="opp-name"></b></label><textarea id="opp-text" rows="3" maxlength="1000"></textarea><p class="hint" id="opp-status"></p></div>"""

SCRIPT = r"""<script>
(() => {
  const KEY = 'lolcoach.notes.v1';
  const $ = id => document.getElementById(id);
  const FORBIDDEN = ['__proto__', 'constructor', 'prototype'];
  const RESULTS = {yes: 'Objectif atteint', partial: 'Atteint en partie', no: 'Non atteint'};
  const str = (value, max) => typeof value === 'string' ? value.slice(0, max) : '';
  const key = value => { const k = str(value, 60); return k && !FORBIDDEN.includes(k) ? k : null; };
  const empty = () => ({version: 1, opponents: {}, games: {}, session: {goal: '', startedAt: null}, history: []});
  const entries = value => value && typeof value === 'object' && !Array.isArray(value) ? Object.entries(value) : [];
  function sanitize(raw) {
    if (!raw || typeof raw !== 'object' || raw.version !== 1) return null;
    const out = empty();
    entries(raw.opponents).slice(0, 300).forEach(([k, v]) => { const name = key(k), text = str(v, 1000); if (name && text) out.opponents[name] = text; });
    entries(raw.games).slice(0, 500).forEach(([k, v]) => {
      const id = key(k);
      if (!id || !v || typeof v !== 'object') return;
      const note = {problem: str(v.problem, 500), regret: str(v.regret, 500), goal: str(v.goal, 500)};
      if (note.problem || note.regret || note.goal) out.games[id] = note;
    });
    if (raw.session && typeof raw.session === 'object') {
      out.session.goal = str(raw.session.goal, 200);
      out.session.startedAt = out.session.goal && raw.session.startedAt ? str(raw.session.startedAt, 40) : null;
    }
    if (Array.isArray(raw.history)) {
      out.history = raw.history.slice(-50).filter(h => h && typeof h === 'object').map(h => ({goal: str(h.goal, 200), startedAt: str(h.startedAt, 40) || null, endedAt: str(h.endedAt, 40) || null, result: RESULTS[h.result] ? h.result : '', comment: str(h.comment, 500)}));
    }
    return out;
  }
  let storageOk = true;
  function load() {
    try {
      const text = localStorage.getItem(KEY);
      return text ? (sanitize(JSON.parse(text)) || empty()) : empty();
    } catch (error) { storageOk = false; return empty(); }
  }
  let state = load();
  function save() {
    try { localStorage.setItem(KEY, JSON.stringify(state)); return true; } catch (error) { storageOk = false; return false; }
  }
  let timer = null;
  function touch(status) {
    clearTimeout(timer);
    timer = setTimeout(() => { const ok = save(); if (status) status.textContent = ok ? 'Enregistré sur cet appareil.' : 'Stockage indisponible : note non enregistrée.'; }, 250);
  }
  const fmtDate = iso => { const d = new Date(iso); return isNaN(d) ? '' : d.toLocaleDateString('fr-FR'); };

  document.querySelectorAll('.note-form').forEach(form => {
    const id = key(form.dataset.matchId);
    if (!id) return;
    const status = form.querySelector('.note-status');
    form.querySelectorAll('textarea[data-field]').forEach(area => {
      area.value = (state.games[id] || {})[area.dataset.field] || '';
      area.addEventListener('input', () => {
        const note = state.games[id] || (state.games[id] = {problem: '', regret: '', goal: ''});
        note[area.dataset.field] = area.value.slice(0, 500);
        if (!note.problem && !note.regret && !note.goal) delete state.games[id];
        touch(status);
      });
    });
  });

  const select = $('classic-opponent'), box = $('opp-notes');
  if (select && box) {
    const area = $('opp-text'), name = $('opp-name'), status = $('opp-status');
    const show = () => {
      const opponent = key(select.value);
      box.hidden = !opponent;
      if (!opponent) return;
      name.textContent = select.options[select.selectedIndex].textContent;
      area.value = state.opponents[opponent] || '';
      status.textContent = '';
    };
    select.addEventListener('change', show);
    const champion = $('classic-champion');
    if (champion) champion.addEventListener('change', () => setTimeout(show, 0));
    area.addEventListener('input', () => {
      const opponent = key(select.value);
      if (!opponent) return;
      if (area.value.trim()) state.opponents[opponent] = area.value.slice(0, 1000); else delete state.opponents[opponent];
      touch(status);
    });
    show();
  }

  const goal = $('session-goal');
  if (goal) {
    const since = $('session-since'), closing = $('session-closing'), result = $('session-result'), comment = $('session-comment'), list = $('session-history'), status = $('session-status');
    const renderSince = () => { since.textContent = state.session.startedAt ? 'Séance commencée le ' + fmtDate(state.session.startedAt) + '.' : 'Aucune séance en cours : écris un objectif pour en démarrer une.'; };
    const renderHistory = () => {
      list.replaceChildren();
      state.history.slice().reverse().forEach(item => {
        const li = document.createElement('li');
        const label = document.createElement('b'); label.textContent = item.goal || 'Séance sans objectif';
        li.append(label, ' — ' + [fmtDate(item.endedAt), RESULTS[item.result] || 'Résultat non précisé'].filter(Boolean).join(' · ') + (item.comment ? ' : ' + item.comment : ''));
        list.append(li);
      });
      if (!state.history.length) { const li = document.createElement('li'); li.textContent = 'Aucune séance enregistrée.'; list.append(li); }
    };
    goal.value = state.session.goal;
    renderSince(); renderHistory();
    goal.addEventListener('input', () => {
      state.session.goal = goal.value.slice(0, 200);
      state.session.startedAt = state.session.goal.trim() ? (state.session.startedAt || new Date().toISOString()) : null;
      renderSince(); touch(status);
    });
    $('session-close').addEventListener('click', () => {
      if (!state.session.goal.trim()) { status.textContent = 'Écris d’abord un objectif de séance.'; return; }
      closing.hidden = false;
    });
    $('session-cancel').addEventListener('click', () => { closing.hidden = true; });
    $('session-save').addEventListener('click', () => {
      state.history.push({goal: state.session.goal, startedAt: state.session.startedAt, endedAt: new Date().toISOString(), result: result.value, comment: comment.value.slice(0, 500)});
      state.history = state.history.slice(-50);
      state.session = {goal: '', startedAt: null};
      goal.value = ''; comment.value = ''; closing.hidden = true;
      status.textContent = save() ? 'Bilan enregistré sur cet appareil.' : 'Stockage indisponible : bilan non enregistré.';
      renderSince(); renderHistory();
    });
  }

  const notesStatus = $('notes-status');
  if (notesStatus) {
    if (!storageOk) notesStatus.textContent = 'Le stockage du navigateur est indisponible : les notes ne seront pas conservées.';
    $('notes-export').addEventListener('click', () => {
      const blob = new Blob([JSON.stringify(state, null, 2)], {type: 'application/json'});
      const link = document.createElement('a');
      link.href = URL.createObjectURL(blob);
      link.download = 'lol-coach-notes-' + new Date().toISOString().slice(0, 10) + '.json';
      document.body.append(link); link.click(); link.remove();
      setTimeout(() => URL.revokeObjectURL(link.href), 1000);
      notesStatus.textContent = 'Export créé.';
    });
    $('notes-import').addEventListener('change', event => {
      const file = event.target.files[0];
      if (!file) return;
      if (file.size > 1000000) { notesStatus.textContent = 'Fichier trop volumineux.'; return; }
      const reader = new FileReader();
      reader.onload = () => {
        let next = null;
        try { next = sanitize(JSON.parse(reader.result)); } catch (error) { next = null; }
        if (!next) { notesStatus.textContent = 'Fichier invalide : aucune note modifiée.'; return; }
        if (!confirm('Remplacer toutes tes notes actuelles par le contenu de ce fichier ?')) return;
        state = next;
        if (!save()) { notesStatus.textContent = 'Stockage indisponible : import non enregistré.'; return; }
        location.reload();
      };
      reader.readAsText(file);
      event.target.value = '';
    });
    $('notes-clear').addEventListener('click', () => {
      if (!confirm('Effacer toutes tes notes de ce navigateur ?')) return;
      try { localStorage.removeItem(KEY); } catch (error) { notesStatus.textContent = 'Stockage indisponible.'; return; }
      state = empty();
      location.reload();
    });
  }
})();
</script>"""


def game_form(match_id):
    e = escape(str(match_id), quote=True)
    fields = ''.join(f'<label>{label}<textarea data-field="{field}" rows="2" maxlength="500"></textarea></label>' for field, label in [('problem', 'Ce qui m’a posé problème'), ('regret', 'Une décision que je regrette'), ('goal', 'L’objectif que j’ai travaillé')])
    return f'<details class="drawer notes note-form" data-match-id="{e}"><summary>Mon retour sur cette partie</summary>{fields}<p class="hint note-status"></p></details>'


def attach_notes(html, games):
    plan = html.find('<div id="plan"')
    matchups = html.find('<div id="matchups"', plan) if plan >= 0 else -1
    close = html.rfind('</div>', plan, matchups) if matchups >= 0 else -1
    if close >= 0:
        html = html[:close] + SESSION_HTML + html[close:]
    else:
        print('::warning::Notes : onglet Plan introuvable, séance et export ignorés')

    marker = "<article class='match "
    starts = []
    position = html.find(marker)
    while position >= 0:
        starts.append(position)
        position = html.find(marker, position + 1)
    if len(starts) == len(games):
        for start, game in reversed(list(zip(starts, games))):
            end = html.index('</article>', start)
            debrief = html.find("<section class='debrief'>", start, end)
            insert_at = html.index('</section>', debrief) + len('</section>') if debrief >= 0 else end
            html = html[:insert_at] + game_form(game['match_id']) + html[insert_at:]
    else:
        print(f'::warning::Notes : {len(starts)} cartes de parties pour {len(games)} parties, formulaires ignorés')

    if OPPONENT_ANCHOR in html:
        html = html.replace(OPPONENT_ANCHOR, OPPONENT_HTML, 1)
    else:
        print('::warning::Notes : zone du versus introuvable, notes par adversaire ignorées')

    html = html.replace('</head>', STYLE + '</head>', 1)
    return html.replace('</body>', SCRIPT + '</body>', 1)
