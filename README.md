# Escola Sabatina — Estudo da Lição (PWA)

Lição do trimestre com leitura bíblica ao toque, grifos, áudio, quiz semanal com ranking e uso offline.

## Publicar no GitHub Pages
1. Envie **todos** os arquivos (inclusive `data/`, `tools/`, `apps-script/` e `.github/`) para um repositório.
2. Settings → Pages → *Deploy from a branch* → `main` / `(root)`.
3. Settings → Actions → General → *Workflow permissions* → **Read and write**.
4. Abra `https://SEU-USUARIO.github.io/NOME-DO-REPO/` e use "Adicionar à tela inicial".

## Atualização automática
- **No app:** a cada abertura com internet ele busca o trimestre vigente no repositório Adventech/sabbath-school-lessons.
- **Capas e áudios (CPB mais):** o workflow `.github/workflows/atualizar.yml` roda todo dia e atualiza `data/capas.json` e `data/audios.json`. Rode-o uma vez em *Actions → Atualizar lição e capas → Run workflow*.

## Áudio dentro do app
- Se o workflow encontrar os arquivos de áudio na página da CPB, cada dia mostra um player e toca ali mesmo.
- Se não encontrar (por exemplo, se a CPB exigir login), o botão "▶ Ouvir aqui no app" abre a página de áudio da CPB numa janela *dentro* do app. Se a CPB bloquear esse uso, a janela traz um link para abrir no site.

## Quiz e ranking semanal
Depois de Sexta há a aba **Quiz** 🏆: **uma pergunta por dia de estudo**, gerada do texto daquele dia (no sábado, o verso para memorizar). As perguntas são iguais para todos e só se responde uma vez.

- **Pontuação para todos:** o ranking (pódio, barras, "Esta semana" e "Trimestre", filtro por classe) aparece para qualquer pessoa que use o app.
- **Respostas só para quem respondeu:** a revisão das respostas e os acertos (●) de cada colega só aparecem depois de responder o quiz.

Para escrever perguntas à mão, use `data/quiz.json` (tem prioridade sobre as automáticas):
```json
{"2026-04-04":[{"h":"Domingo · Título","q":"Pergunta?","o":["A","B","C","D"],"a":1,"e":"Explicação"}]}
```

### Ligar o ranking com o Google Apps Script (gratuito)
1. Crie uma planilha em sheets.google.com (pode ficar vazia).
2. **Extensões → Apps Script**, apague o conteúdo, cole o arquivo `apps-script/Code.gs` e salve.
3. **Implantar → Nova implantação → App da Web**. Executar como: **Eu**. Quem pode acessar: **Qualquer pessoa**. Implante e autorize o acesso.
4. Copie a URL que termina em `/exec` e cole em `config.js`, no campo `apiUrl`. Envie ao GitHub.
5. Ao editar o código depois: *Implantar → Gerenciar implantações → editar → Nova versão*.

Os dados ficam na aba `respostas` da sua planilha, onde você pode ver e apagar linhas.

### Limites do ranking
A nota é calculada no aparelho e o servidor aceita um envio por nome em cada quiz. Quem usar outro nome pode responder de novo, e alguém com conhecimento técnico pode enviar notas falsas. Serve para grupos de confiança, como uma classe da Escola Sabatina.

## Uso offline
Aa → ⤓ Offline: baixe a lição e as versões da Bíblia (ACF, AA, NVI). Os áudios exigem internet.

## Aviso
O texto da lição, as capas e os áudios pertencem à Associação Geral e à CPB. Verifique as condições de uso antes de divulgar publicamente.
