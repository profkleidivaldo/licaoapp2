#!/usr/bin/env python3
"""Lê as páginas de áudio do CPB mais e grava data/audios.json (um arquivo de áudio por dia)."""
import re, json, os, urllib.request
UA = {'User-Agent': 'Mozilla/5.0'}
def get(u): return urllib.request.urlopen(urllib.request.Request(u, headers=UA), timeout=30).read().decode('utf8', 'ignore').replace('\\/', '/')
BASE = 'https://mais.cpb.com.br'
EXT = r'(?:mp3|m4a|aac|ogg|wav)'
aud = json.load(open('data/audios.json', encoding='utf8')) if os.path.exists('data/audios.json') else {}
index = get(BASE + '/audios/')
pages = list(dict.fromkeys(re.findall(r'https://mais\.cpb\.com\.br/audio/[^"\'\s<>]+', index)))
for url in pages:
    try: html = get(url)
    except Exception as e: print('falhou', url, e); continue
    m = re.search(r'Lição\s*(\d+).*?(\d)º\s*Trimestre\s*(\d{4})', re.search(r'<title>(.*?)</title>', html, re.S).group(1), re.S)
    if not m: print('sem título reconhecido:', url); continue
    n, q, y = m.groups(); qid = f'{y}-0{q}'
    found = re.findall(r'(?:https?:)?//[^"\'\s<>()]+?\.' + EXT + r'(?:\?[^"\'\s<>()]*)?', html, re.I)
    found += [BASE + p for p in re.findall(r'(?:src|data-src|href)=["\'](/[^"\']+?\.' + EXT + r'(?:\?[^"\']*)?)["\']', html, re.I)]
    files = [('https:' + f if f.startswith('//') else f) for f in dict.fromkeys(found)]
    aud.setdefault(qid, {})[str(int(n))] = {'page': url, 'files': files}
    print(f'lição {int(n)}: {len(files)} arquivo(s) de áudio')
json.dump(aud, open('data/audios.json', 'w', encoding='utf8'), ensure_ascii=False, indent=1)
