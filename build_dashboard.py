#!/usr/bin/env python3
"""Build the enriched intern decision dashboard HTML."""
import json, os, glob, subprocess

# Load scores
with open('docs/scores.json') as f:
    scores = json.load(f)

# Load contributor JSONs
contributors = {}
for fp in glob.glob('contributors/*.json'):
    try:
        with open(fp) as fh:
            data = json.load(fh)
            key = os.path.basename(fp).replace('.json', '')
            contributors[key] = data
    except:
        pass

# Get PRs from GitHub
result = subprocess.run(
    ['gh', 'pr', 'list', '--repo', 'Life-Atlas/lpi-developer-kit',
     '--state', 'all', '--limit', '500',
     '--json', 'number,title,author,state'],
    capture_output=True, text=True
)
prs_data = json.loads(result.stdout)
login_prs = {}
for pr in prs_data:
    login = pr['author']['login']
    login_prs.setdefault(login, []).append({
        'number': pr['number'], 'state': pr['state'], 'title': pr['title']
    })

def find_contributor(score_key, score_name):
    if score_key in contributors:
        return contributors[score_key]
    for ck, cv in contributors.items():
        if cv.get('name', '').lower() == score_name.lower():
            return cv
    return None

def find_prs(github_login):
    if not github_login:
        return []
    login = github_login.replace('https://github.com/', '').strip('/')
    return login_prs.get(login, [])

# Sort entries
entries = list(scores.items())
entries.sort(key=lambda x: (
    x[1].get('level', 0),
    x[1].get('score', 0),
    x[1].get('pct', 0)
), reverse=True)

# Build JS data
js_items = []
for rank, (key, val) in enumerate(entries, 1):
    name = val.get('name', '')
    contrib = find_contributor(key, name)
    github = (contrib.get('github', '') if contrib else '').replace('https://github.com/', '').strip('/')
    prs = find_prs(github)
    l3_prs = [p['number'] for p in prs if 'level-3' in p['title'].lower() or 'level 3' in p['title'].lower()][:3]
    l4_prs = [p['number'] for p in prs if 'level-4' in p['title'].lower() or 'level 4' in p['title'].lower()][:2]
    all_prs = [p['number'] for p in prs][:5]

    lv = val.get('level', 0)
    pct = val.get('pct', 0)
    if lv == 4:
        t, tl, tc, dec = 'core-crew', 'Core Crew (L4)', '#3fb950', 'ACCEPT'
    elif lv == 2:
        t, tl, tc, dec = 'released', 'L2 Only', '#f85149', 'RELEASE'
    elif pct >= 92:
        t, tl, tc, dec = 'core-crew', 'Core Crew', '#3fb950', 'ACCEPT'
    elif pct >= 85:
        t, tl, tc, dec = 'fast-track', 'Fast Track', '#58a6ff', 'ACCEPT'
    elif pct >= 77:
        t, tl, tc, dec = 'proving', 'Proving Ground', '#d2a8ff', 'ACCEPT'
    elif pct >= 69:
        t, tl, tc, dec = 'bench', 'Bench', '#ffa657', 'BENCH'
    elif pct >= 46:
        t, tl, tc, dec = 'waitlist', 'Waitlist', '#8b949e', 'WAITLIST'
    else:
        t, tl, tc, dec = 'released', 'Released', '#f85149', 'RELEASE'

    note = val.get('note', '')
    fl = 'FLAG' in note.upper() or 'Most complete' in note

    js_items.append({
        'r': rank, 'k': key, 'n': name, 'lv': lv,
        's': val.get('score', 0), 'm': val.get('max', 13), 'p': pct,
        't': t, 'tl': tl, 'tc': tc, 'd': dec,
        'gh': github,
        'prog': (contrib.get('program', '') if contrib else ''),
        'camp': (contrib.get('campus', '') if contrib else ''),
        'tr': (contrib.get('track', '') if contrib else ''),
        'sk': ', '.join((contrib.get('skills', []) if contrib else [])[:8]),
        'int': ', '.join((contrib.get('interests', []) if contrib else [])[:6]),
        'tw': (contrib.get('my_twin', '') if contrib else ''),
        'l3': l3_prs, 'l4': l4_prs, 'ap': all_prs,
        'nt': note, 'fl': fl
    })

js_json = json.dumps(js_items, ensure_ascii=False)

# Read template
with open('docs/profiles_template.html', 'r', encoding='utf-8') as f:
    template = f.read()

html = template.replace('/*__DATA__*/', js_json)

with open('docs/profiles.html', 'w', encoding='utf-8') as f:
    f.write(html)

# Also copy to OneDrive
import shutil
shutil.copy('docs/profiles.html', os.path.expanduser('~/OneDrive/Documents/Intern_Profiles_Complete.html'))

print(f"Built dashboard: {len(html)} bytes, {len(js_items)} candidates")
for item in js_items[:5]:
    print(f"  #{item['r']} {item['n']} L{item['lv']} {item['s']}/{item['m']}")
