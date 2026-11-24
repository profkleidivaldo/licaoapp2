# Lembrete de hora em hora (grátis)

A partir das 7h (no fuso de cada pessoa) e até as 21h, quem **ainda não marcou o dia como estudado** recebe uma notificação a cada hora. Quem já estudou não recebe nada, e o aviso some sozinho quando o dia é marcado.

Tudo roda no plano gratuito do Cloudflare (sem cartão). Leva uns 10 minutos, uma vez só.

## Passo a passo
1. Crie a conta em **dash.cloudflare.com** (grátis).
2. **Workers & Pages → Create → Create Worker**, nome `licao-lembrete` → **Deploy** → **Edit code**. Apague tudo, cole o conteúdo de `push/worker.js` e clique em **Deploy**.
3. **Storage & Databases → KV → Create** um namespace chamado `licao-subs`.
4. Volte ao Worker → **Settings → Bindings → Add → KV namespace**. Em *Variable name* escreva exatamente `SUBS` e escolha o namespace criado. Salve.
5. **Settings → Trigger Events → Cron Triggers → Add** e use `*/10 * * * *` (a cada 10 minutos; o Worker decide sozinho quem recebe em cada rodada).
6. (Opcional) **Settings → Variables**: `CONTATO` = `mailto:seuemail@exemplo.com`.
7. Copie o endereço do Worker (`https://licao-lembrete.SEU-USUARIO.workers.dev`). Abra-o no navegador com `/chave` no fim: deve aparecer um texto comprido (a chave pública, criada sozinha na 1ª vez). Cole o endereço em `config.js`, no campo `pushUrl`, e envie ao GitHub.
8. No app: **Aa → 🔔 Lembrete** e permita as notificações.

## Detalhes
- **iPhone:** precisa do iOS 16.4 ou mais novo e do app **adicionado à tela inicial** (abrir pelo ícone, não pelo Safari).
- **Privacidade:** o Worker guarda só o endereço de push do aparelho, o fuso e quais dias foram marcados. Nomes, respostas e grifos não saem do aparelho.
- **Horários:** `HORA_INICIO` e `HORA_FIM` no topo do `worker.js`.
- **Limites do plano gratuito:** funciona até ~240 inscritos. Até ~40 pessoas todas recebem na hora cheia; acima disso o Worker espalha os envios em faixas de 10 minutos (7h00, 7h10…), por causa do limite de 50 chamadas por execução.
- **Textos:** a notificação chega sem texto do servidor; as frases ficam no `sw.js` e são fáceis de trocar.
