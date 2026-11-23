#!/usr/bin/env python3
"""Gera os quizzes semanais com IA (Groq + gpt-oss) e grava em data/quiz.json.

O arquivo vai para o repositório, então TODOS veem as mesmas perguntas (o ranking depende disso).
A chave da Groq nunca vai para o app: ela fica só no GitHub (Settings → Secrets → GROQ_API_KEY).

Uso:
  export GROQ_API_KEY=gsk_...
  python tools/gerar_quiz.py              # gera só as semanas que ainda não têm quiz
  python tools/gerar_quiz.py --semana 3   # só a lição 3 (se já existir, precisa de --refazer)
  python tools/gerar_quiz.py --refazer    # regera mesmo as que já existem (muda as perguntas do ranking!)

Semanas que já têm quiz em data/quiz.json NUNCA são sobrescritas sem --refazer: trocar as perguntas
no meio da semana invalidaria as notas já enviadas ao ranking.
"""
import json, os, sys, time, random, argparse, urllib.request, urllib.error

URL = 'https://api.groq.com/openai/v1/chat/completions'
MODEL = os.environ.get('GROQ_MODEL', 'openai/gpt-oss-120b')
DAYS = ['Sábado', 'Domingo', 'Segunda', 'Terça', 'Quarta', 'Quinta', 'Sexta']
QTD = 7  # uma pergunta por dia de estudo (o app e o ranking foram feitos para isso)

SISTEMA = """Você é um professor experiente de Escola Sabatina e cria quizzes interessantes, justos e variados \
em português do Brasil, baseados SOMENTE no texto da lição fornecido (nunca use conhecimento externo para a resposta certa)."""

INSTRUCOES = f"""Crie exatamente {QTD} perguntas de múltipla escolha sobre a lição abaixo: UMA para cada dia (dia 0 = Sábado, \
1 = Domingo, 2 = Segunda, 3 = Terça, 4 = Quarta, 5 = Quinta, 6 = Sexta), na ordem.

Deixe o quiz interessante, variando o TIPO das perguntas ao longo da semana (use pelo menos 5 tipos diferentes):
- "compreensao": ideia central do dia, em palavras diferentes das do texto (sem "complete a lacuna");
- "versiculo": qual texto bíblico / o que o versículo ensina / a quem foi dito;
- "verdadeiro_falso": afirmação para julgar; opções exatamente "Verdadeiro" e "Falso";
- "incorreta": "Qual das alternativas NÃO está de acordo com o estudo?";
- "aplicacao": como o princípio do dia se aplica a uma situação cotidiana concreta (resposta defendida pelo texto);
- "conexao": relacionar duas ideias, personagens ou textos do estudo;
- "quem_onde_quando": detalhe concreto (pessoa, lugar, evento) citado no dia.
O dia 0 (Sábado) deve ser sobre o versículo para memorizar ou a ideia principal da semana.

Regras de qualidade:
- Cada pergunta deve ser respondível só com o texto do dia indicado e fazer sentido sozinha (sem "segundo o texto acima").
- Alternativas erradas plausíveis, do mesmo tamanho e estilo da certa, sem pegadinhas bobas, sem "todas/nenhuma das anteriores".
- Não repita a mesma pergunta/ideia entre dias. Não use a palavra da resposta na pergunta.
- Perguntas com no máximo 220 caracteres; alternativas com no máximo 110 caracteres.
- "explicacao": 1 ou 2 frases curtas que ensinam o porquê, citando o dia (ex.: "Veja o estudo de domingo…").
- Dê a alternativa certa em "certa" e as erradas em "erradas" (3 erradas; no verdadeiro_falso, 1 errada). Não embaralhe: eu embaralho.

Responda APENAS com JSON no formato:
{{"perguntas":[{{"dia":0,"tipo":"compreensao","pergunta":"...","certa":"...","erradas":["...","...","..."],"explicacao":"..."}}]}}

TEXTO DA LIÇÃO:
"""

SCHEMA = {
    'type': 'object',
    'properties': {'perguntas': {'type': 'array', 'items': {
        'type': 'object',
        'properties': {
            'dia': {'type': 'integer'}, 'tipo': {'type': 'string'}, 'pergunta': {'type': 'string'},
            'certa': {'type': 'string'}, 'erradas': {'type': 'array', 'items': {'type': 'string'}},
            'explicacao': {'type': 'string'}},
        'required': ['dia', 'tipo', 'pergunta', 'certa', 'erradas', 'explicacao'],
        'additionalProperties': False}}},
    'required': ['perguntas'], 'additionalProperties': False}


def texto_semana(w):
    partes = [f"Lição {w['n']}: {w['title']}"]
    if w.get('reads'): partes.append('Leituras da semana: ' + w['reads'])
    for i, d in enumerate(w['days']):
        partes.append(f"\n=== DIA {i} ({DAYS[i]}): {d['t']} ===\n{d['md'].strip()}")
    return '\n'.join(partes)


def chamar(prompt, chave, json_schema=True):
    corpo = {
        'model': MODEL, 'temperature': 0.7, 'max_completion_tokens': 6000, 'reasoning_effort': 'low',
        'messages': [{'role': 'system', 'content': SISTEMA}, {'role': 'user', 'content': prompt}],
        'response_format': {'type': 'json_schema', 'json_schema': {'name': 'quiz', 'schema': SCHEMA}}
        if json_schema else {'type': 'json_object'}}
    req = urllib.request.Request(URL, json.dumps(corpo).encode(), {
        'Authorization': 'Bearer ' + chave, 'Content-Type': 'application/json', 'User-Agent': 'licaoapp-quiz/1.0'})
    try:
        with urllib.request.urlopen(req, timeout=120) as r:
            return json.loads(r.read())['choices'][0]['message']['content']
    except urllib.error.HTTPError as e:
        detalhe = e.read().decode('utf8', 'ignore')[:300]
        if e.code == 400 and json_schema:           # modelo/conta sem json_schema: tenta modo JSON simples
            print('  json_schema recusado, tentando json_object:', detalhe)
            return chamar(prompt, chave, json_schema=False)
        e.detalhe = detalhe
        raise


def validar(dados, w):
    """Devolve a lista final de perguntas no formato do app, ou levanta ValueError."""
    if isinstance(dados, str): dados = json.loads(dados)
    ps = dados['perguntas']
    if len(ps) != QTD: raise ValueError(f'veio {len(ps)} perguntas, esperado {QTD}')
    ps = sorted(ps, key=lambda p: p['dia'])
    if [p['dia'] for p in ps] != list(range(QTD)): raise ValueError('dias fora de 0..6')
    rnd = random.Random(f"{w['n']}-{w['title']}")  # embaralhamento estável
    out = []
    for p in ps:
        q, c, e = p['pergunta'].strip(), p['certa'].strip(), p['explicacao'].strip()
        err = [x.strip() for x in p['erradas'] if x.strip()]
        vf = p['tipo'] == 'verdadeiro_falso'
        if not (q and c and e): raise ValueError(f"dia {p['dia']}: campo vazio")
        if vf:
            if {c, *err} != {'Verdadeiro', 'Falso'} or len(err) != 1: raise ValueError(f"dia {p['dia']}: V/F inválida")
            o = ['Verdadeiro', 'Falso']
        else:
            if len(err) != 3 or len({c, *err}) != 4: raise ValueError(f"dia {p['dia']}: precisa de 1 certa + 3 erradas distintas")
            if any(t.lower().startswith(('todas as', 'nenhuma das')) for t in err + [c]): raise ValueError(f"dia {p['dia']}: 'todas/nenhuma'")
            o = [c, *err]; rnd.shuffle(o)
        if len(q) > 320 or any(len(t) > 160 for t in o): raise ValueError(f"dia {p['dia']}: texto longo demais")
        out.append({'h': f"{DAYS[p['dia']]} · {w['days'][p['dia']]['t']}", 'q': q, 'o': o, 'a': o.index(c), 'e': e})
    return out


def gerar_semana(w, chave, tentativas=3):
    prompt = INSTRUCOES + texto_semana(w)
    for t in range(1, tentativas + 1):
        try:
            return validar(chamar(prompt, chave), w)
        except urllib.error.HTTPError as e:
            print(f'  HTTP {e.code} (tentativa {t}): {getattr(e, "detalhe", "")}')
            if e.code in (401, 403): raise SystemExit('Chave da Groq recusada: confira o secret GROQ_API_KEY.')
            time.sleep(min(60, 8 * t * (3 if e.code == 429 else 1)))
        except (ValueError, KeyError, TypeError, json.JSONDecodeError) as e:
            print(f'  resposta inválida (tentativa {t}): {e}')
    return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--semana', type=int, help='número da lição (1-13)')
    ap.add_argument('--refazer', action='store_true', help='sobrescreve quizzes já existentes')
    a = ap.parse_args()
    chave = os.environ.get('GROQ_API_KEY', '').strip()
    if not chave:
        print('GROQ_API_KEY não definida: nada a fazer.'); return
    lic = json.load(open('data/licao.json', encoding='utf8'))
    arq = 'data/quiz.json'
    quiz = json.load(open(arq, encoding='utf8')) if os.path.exists(arq) else {}
    feitos = 0
    for w in lic['weeks']:
        if a.semana and w['n'] != a.semana: continue
        qid = f"{lic['id']}-{w['n']:02d}"
        if quiz.get(qid) and not a.refazer: print(f'lição {w["n"]}: já tem quiz, pulando'); continue
        print(f'lição {w["n"]}: gerando com {MODEL}…')
        qs = gerar_semana(w, chave)
        if not qs: print('  falhou; fica o quiz automático do app'); continue
        quiz[qid] = qs; feitos += 1
        json.dump(quiz, open(arq, 'w', encoding='utf8'), ensure_ascii=False, indent=1)  # grava a cada semana
        time.sleep(2)
    print(f'{feitos} quiz(zes) novo(s) em {arq}')


if __name__ == '__main__':
    main()
