#!/usr/bin/env python3
"""Lê as páginas de áudio do CPB mais e grava data/audios.json (um arquivo por dia, na ordem Sáb→Sex)."""
import re, json, os, html as H, urllib.request
from urllib.parse import urljoin
UA = {'User-Agent': 'Mozilla/5.0'}
BASE = 'https://mais.cpb.com.br'
def get(u): return urllib.request.urlopen(urllib.request.Request(u, headers=UA), timeout=30).read().decode('utf8', 'ignore').replace('\\/', '/')
def arquivos(page):
    f = []
    for blk in re.findall(r'<audio\b.*?</audio>|<audio\b[^>]*/?>', page, re.S | re.I):      # players <audio>/<source>
        f += re.findall(r'\bsrc=["\']([^"\']+)["\']', blk, re.I)
    if not f:                                                                                  # qualquer link de áudio
        f = re.findall(r'(?:https?:)?//[^"\'\s<>()]+?\.(?:mp3|m4a|aac|ogg|wav)(?:\?[^"\'\s<>()]*)?', page, re.I)
        f += re.findall(r'(?:src|data-src|href)=["\'](/[^"\']+?\.(?:mp3|m4a|aac|ogg|wav)[^"\']*)["\']', page, re.I)
    return list(dict.fromkeys(urljoin(BASE, H.unescape(u)) for u in f))
aud = json.load(open('data/audios.json', encoding='utf8')) if os.path.exists('data/audios.json') else {}
index = get(BASE + '/audios/')
for url in dict.fromkeys(re.findall(r'https://mais\.cpb\.com\.br/audio/[^"\'\s<>]+', index)):
    try: page = get(url)
    except Exception as e: print('falhou', url, e); continue
    m = re.search(r'Lição\s*(\d+).*?(\d)º\s*Trimestre\s*(\d{4})', re.search(r'<title>(.*?)</title>', page, re.S).group(1), re.S)
    if not m: print('sem título reconhecido:', url); continue
    n, q, y = m.groups(); qid = f'{y}-0{q}'
    files = arquivos(page)
    aud.setdefault(qid, {})[str(int(n))] = {'page': url, 'files': files}
    print(f'lição {int(n)}: {len(files)} arquivo(s) de áudio')
json.dump(aud, open('data/audios.json', 'w', encoding='utf8'), ensure_ascii=False, indent=1)
