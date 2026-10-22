"""Tracking feed for the desk. Read-only, no keys. Run from repo root:
  python3 tools/tracking_update.py [--registry /workspace/registry/distrokid_streaming_registry.csv]
Writes data/tracking.json: public channel subs + uploads + live streams (yt-dlp, public pages),
Earn hours from data/latest.json (Studio read), Morntide rows of the DistroKid registry CSV."""
import json, csv, argparse, subprocess, datetime
p = argparse.ArgumentParser()
p.add_argument('--channel', default='@morntidemusic')
p.add_argument('--artist', default='Morntide')
p.add_argument('--registry', default='/workspace/registry/distrokid_streaming_registry.csv')
a = p.parse_args()
def tab(t):
    out = subprocess.run(['yt-dlp', '--flat-playlist', '-J', f'https://www.youtube.com/{a.channel}/{t}'],
                         capture_output=True, text=True, check=True).stdout
    return json.loads(out)
V, S = tab('videos'), tab('streams')
row = lambda e: {"id": e['id'], "title": e.get('title'), "views": e.get('view_count'),
                 "duration": e.get('duration'), "live": e.get('live_status')}
L = json.load(open('data/latest.json'))
k = L.get('kpis', L)
links = ['Spotify URL', 'Apple Music URL', 'YouTube Music URL', 'Amazon Music URL']
rel = []
for r in csv.DictReader(open(a.registry, encoding='utf-8')):
    if r['Artist/Channel'] != a.artist: continue
    st = {c.split()[0]: r[c] for c in links if r[c].startswith('http')}
    for part in r['Other (Tidal/Deezer)'].split('|'):
        n, _, u = part.strip().partition(': ')
        if u.startswith('http'): st[n.split()[0]] = u
    rel.append({"title": r['Release title'], "type": r['Type'], "date": r['Release date'],
                "status": r['Distro status'], "upc": r['UPC'], "stores": st, "checked": r['Last checked (ET)']})
streams = [row(e) for e in S['entries']]
d = {"fetched": datetime.datetime.now().astimezone().isoformat(timespec='minutes'),
     "channel": a.channel, "channel_id": V.get('channel_id'),
     "subs_public": V.get('channel_follower_count'),
     "earn": k.get('earn'), "earn_source": "data/latest.json (Studio Earn, " + str(L.get('day')) + ")",
     "uploads": [row(e) for e in V['entries']], "streams": streams,
     "focus_radio": [s for s in streams if 'radio' in (s['title'] or '').lower()],
     "releases": sorted(rel, key=lambda r: r['date'], reverse=True),
     "sources": {"youtube": "yt-dlp public /videos and /streams tabs", "releases": "DistroKid Streaming Link Registry CSV (Morntide rows)"}}
json.dump(d, open('data/tracking.json', 'w'), ensure_ascii=False, indent=1)
print('ok', d['subs_public'], len(d['uploads']), len(d['streams']), len(d['focus_radio']), len(rel))
