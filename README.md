# Escola Sabatina — Estudo da Lição (PWA)

Lição do trimestre com leitura bíblica ao toque, grifos, áudio da CPB mais, quiz semanal com ranking e uso offline.

## Publicar no GitHub Pages
1. Envie **todos** os arquivos (inclusive `data/`, `tools/` e `.github/`) para um repositório.
2. Settings → Pages → *Deploy from a branch* → `main` / `(root)`.
3. Settings → Actions → General → *Workflow permissions* → **Read and write**.
4. Abra `https://SEU-USUARIO.github.io/NOME-DO-REPO/` e use "Adicionar à tela inicial".

## Atualização automática
- **No app:** a cada abertura com internet ele busca o trimestre vigente no repositório Adventech/sabbath-school-lessons. Ao mudar de trimestre, progresso e grifos do anterior são arquivados.
- **Capas e áudios (CPB mais):** o workflow `.github/workflows/atualizar.yml` roda todo dia e atualiza `data/capas.json` e `data/audios.json`. Rode-o uma vez em *Actions → Atualizar lição e capas → Run workflow*.

## Áudio
Cada dia mostra o player com o áudio da CPB mais (quando o workflow encontrar o arquivo) e um link para a página de áudio da lição. Os áudios tocam direto do site da CPB e **não** ficam salvos offline. Se a CPB mudar a estrutura do site e os arquivos não forem encontrados, o app mostra só o link "Ouvir no CPB mais".

## Quiz e ranking semanal
Depois de Sexta há a aba **Quiz** (🏆) com até 10 perguntas geradas do texto da semana: verso para memorizar, referência bíblica de um texto, completar versículos, tema de cada dia e leituras da semana. As perguntas são iguais para todos. Cada pessoa responde **uma vez** e vê o resultado, a revisão e o ranking (empate decidido pelo menor tempo). Há um campo opcional de "código da classe" para filtrar o ranking.

Para quizzes escritos à mão, preencha `data/quiz.json` (ele tem prioridade sobre o automático):
```json
{"2026-04-04":[{"q":"Pergunta?","o":["A","B","C","D"],"a":1,"e":"Explicação mostrada após responder"}]}
```

### Ligar o ranking (Firebase, gratuito)
O GitHub Pages não guarda dados, então o ranking usa o Firestore. Sem isso o quiz funciona, mas só mostra o resultado no aparelho.
1. Em console.firebase.google.com, crie um projeto (pode desativar o Analytics).
2. *Build → Firestore Database → Criar banco de dados* (modo produção, região `southamerica-east1`).
3. Aba **Regras**: cole o conteúdo de `firestore.rules` e publique.
4. ⚙ *Configurações do projeto → Seus apps → Web (`</>`)*: registre o app e copie `apiKey` e `projectId`.
5. Cole os dois valores em `config.js` e envie ao GitHub.

### Limites do ranking
A nota é calculada no aparelho e a regra do servidor garante um envio por nome em cada quiz. Quem limpar os dados do navegador e usar outro nome pode responder de novo, e alguém com conhecimento técnico pode enviar notas falsas. Serve para grupos de confiança, como uma classe da Escola Sabatina.

## Uso offline
Toque em Aa → ⤓ Offline: baixe a lição e as versões da Bíblia (ACF, AA, NVI). Capas e versículos já vistos também ficam guardados.

## Aviso
O texto da lição, as capas e os áudios pertencem à Associação Geral e à CPB. Verifique as condições de uso antes de divulgar publicamente.
