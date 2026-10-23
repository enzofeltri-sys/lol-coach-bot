import os
import importlib.util
from pathlib import Path

from riot_api import get_puuid, get_ranked_match_ids, get_match, get_timeline
from analysis import analyze_matches
from report import build_report

spec = importlib.util.spec_from_file_location('lol_site_renderer', Path(__file__).with_name('site.py'))
renderer = importlib.util.module_from_spec(spec)
spec.loader.exec_module(renderer)

RIOT_ID = 'Kyoraku#1707'
GAME_NAME, TAG_LINE = RIOT_ID.split('#')

REFRESH_UI = '''
<section class="panel" aria-label="Actualisation"><button type="button" id="refresh-page">Actualiser la page ↻</button><p id="refresh-status" role="status">Au sommet de la page, tire vers le bas pour actualiser. Cela recharge le dernier rapport publié, sans lancer une analyse Riot ni effacer tout le cache du navigateur.</p></section>
<script>
(() => {
  const button = document.getElementById('refresh-page');
  const status = document.getElementById('refresh-status');
  let busy = false;
  function refresh() {
    if (busy) return;
    if (!navigator.onLine) {
      status.textContent = 'Hors ligne : reconnecte-toi puis réessaie.';
      return;
    }
    busy = true;
    button.disabled = true;
    status.textContent = 'Chargement du dernier rapport publié…';
    const url = new URL(window.location.href);
    url.searchParams.set('_refresh', Date.now().toString());
    window.location.replace(url.toString());
  }
  button.addEventListener('click', refresh);
  let startY = null;
  let distance = 0;
  document.addEventListener('touchstart', event => {
    startY = window.scrollY <= 0 && event.touches.length === 1 && !event.target.closest('button,a,input,select,textarea') ? event.touches[0].clientY : null;
    distance = 0;
  }, {passive: true});
  document.addEventListener('touchmove', event => {
    if (startY === null || event.touches.length !== 1) return;
    distance = event.touches[0].clientY - startY;
    if (distance > 0 && window.scrollY <= 0) {
      if (event.cancelable) event.preventDefault();
      status.textContent = distance >= 100 ? 'Relâche pour actualiser.' : 'Tire encore pour actualiser.';
    }
  }, {passive: false});
  document.addEventListener('touchend', () => {
    const ready = startY !== null && distance >= 100 && window.scrollY <= 0;
    startY = null;
    distance = 0;
    if (ready) refresh();
  }, {passive: true});
  document.addEventListener('touchcancel', () => {startY = null; distance = 0;}, {passive: true});
})();
</script>
'''


def main():
    print(f'Analyse des games de {RIOT_ID}...')
    puuid = get_puuid(GAME_NAME, TAG_LINE)
    match_ids = get_ranked_match_ids(puuid, count=10)
    if not match_ids:
        raise RuntimeError('Aucune ranked récente trouvée.')
    matches = [get_match(match_id) for match_id in match_ids]
    timelines = {}
    timeline_errors = []
    for match in matches:
        match_id = match['metadata']['matchId']
        try:
            timelines[match_id] = get_timeline(match_id)
        except Exception as error:
            detail = getattr(error, 'response', None)
            status = getattr(detail, 'status_code', None)
            timeline_errors.append(f'{match_id} : {type(error).__name__}' + (f' (HTTP {status})' if status else ''))
            print(f'Timeline indisponible pour {match_id} : {type(error).__name__}' + (f' HTTP {status}' if status else ''))
    analysis = analyze_matches(matches, puuid, timelines, timeline_errors)
    os.makedirs('site', exist_ok=True)
    Path('rapport.md').write_text(build_report(RIOT_ID, analysis), encoding='utf-8')
    html = renderer.build_html(RIOT_ID, analysis)
    html = html.replace('<main>', '<main>' + REFRESH_UI, 1)
    Path('site/index.html').write_text(html, encoding='utf-8')
    print('Rapport et site générés.')


if __name__ == '__main__':
    main()
