/* Lembretes da Escola Sabatina — Cloudflare Worker (plano GRATUITO, sem cartão).
 *
 * O que faz: a cada hora, a partir das 7h (no fuso de cada pessoa), envia uma notificação
 * para quem ainda NÃO marcou como estudada a lição do dia. Quem já estudou não recebe nada.
 *
 * Como funciona (resumo): o app avisa este Worker quando a pessoa liga o lembrete e quando ela
 * marca um dia como estudado. Um cron do Cloudflare acorda o Worker e ele manda um "push vazio"
 * (assinado com chaves VAPID, geradas sozinhas na 1ª vez); o service worker do app mostra o aviso.
 * Nenhum nome, texto ou resposta do aluno sai do aparelho: só endereço de push, fuso e quais dias foram lidos.
 *
 * Configuração: veja push/LEIA-ME.md  (um KV chamado SUBS + um cron a cada 10 minutos)
 */
const HORA_INICIO = 7;      // primeira notificação do dia (hora local de cada pessoa)
const HORA_FIM = 21;        // última (para não acordar ninguém de noite). Use 23 se quiser mais tarde.
const POR_EXECUCAO = 40;    // limite do plano gratuito: 50 chamadas por execução
const HOSTS_PUSH = [/^fcm\.googleapis\.com$/, /(^|\.)push\.services\.mozilla\.com$/, /(^|\.)push\.apple\.com$/, /(^|\.)notify\.windows\.com$/];

const CORS = { 'Access-Control-Allow-Origin': '*', 'Access-Control-Allow-Methods': 'GET,POST,OPTIONS', 'Access-Control-Allow-Headers': 'Content-Type' };
const enc = new TextEncoder();
const b64u = buf => btoa(String.fromCharCode(...new Uint8Array(buf))).replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/, '');
const b64uJson = o => b64u(enc.encode(JSON.stringify(o)));
const resp = (txt, status = 200) => new Response(txt, { status, headers: { ...CORS, 'Content-Type': 'text/plain; charset=utf-8' } });

let VAPID; // cache em memória
async function getVapid(env) {
  if (VAPID) return VAPID;
  const salvo = await env.SUBS.get('cfg:vapid', 'json');
  if (salvo) return (VAPID = salvo);
  const par = await crypto.subtle.generateKey({ name: 'ECDSA', namedCurve: 'P-256' }, true, ['sign', 'verify']);
  VAPID = { priv: await crypto.subtle.exportKey('jwk', par.privateKey), pub: b64u(await crypto.subtle.exportKey('raw', par.publicKey)) };
  await env.SUBS.put('cfg:vapid', JSON.stringify(VAPID));
  return VAPID;
}

async function cabecalhoVapid(endpoint, env) {
  const v = await getVapid(env);
  const head = b64uJson({ typ: 'JWT', alg: 'ES256' });
  const body = b64uJson({ aud: new URL(endpoint).origin, exp: Math.floor(Date.now() / 1000) + 12 * 3600, sub: env.CONTATO || 'mailto:lembrete@example.com' });
  const chave = await crypto.subtle.importKey('jwk', v.priv, { name: 'ECDSA', namedCurve: 'P-256' }, false, ['sign']);
  const sig = await crypto.subtle.sign({ name: 'ECDSA', hash: 'SHA-256' }, chave, enc.encode(head + '.' + body));
  return `vapid t=${head}.${body}.${b64u(sig)}, k=${v.pub}`;
}

function endpointValido(e) {
  if (typeof e !== 'string' || e.length > 480) return false;
  try { const u = new URL(e); return u.protocol === 'https:' && HOSTS_PUSH.some(r => r.test(u.hostname)); } catch { return false; }
}

function local(agora, tz) {
  let f;
  try { f = new Intl.DateTimeFormat('en-CA', { timeZone: tz, year: 'numeric', month: '2-digit', day: '2-digit', hour: '2-digit', hourCycle: 'h23' }); }
  catch { f = new Intl.DateTimeFormat('en-CA', { timeZone: 'America/Sao_Paulo', year: 'numeric', month: '2-digit', day: '2-digit', hour: '2-digit', hourCycle: 'h23' }); }
  const p = Object.fromEntries(f.formatToParts(agora).map(x => [x.type, x.value]));
  return { y: +p.year, m: +p.month, d: +p.day, h: +p.hour };
}

const hash = s => { let h = 2166136261; for (let i = 0; i < s.length; i++) { h ^= s.charCodeAt(i); h = Math.imul(h, 16777619); } return h >>> 0; };

/** Já estudou o dia de hoje? null = fora do trimestre (não notifica). */
export function precisaLembrar(meta, agora) {
  if (!meta || !/^\d{2}\/\d{2}\/\d{4}$/.test(meta.q || '') || !/^[01]+$/.test(meta.r || '')) return false;
  const t = local(agora, meta.t);
  if (t.h < HORA_INICIO || t.h > HORA_FIM) return false;
  const [qd, qm, qy] = meta.q.split('/').map(Number);
  const idx = Math.round((Date.UTC(t.y, t.m - 1, t.d) - Date.UTC(qy, qm - 1, qd)) / 864e5);
  if (idx < 0 || idx >= meta.r.length) return false;
  return meta.r[idx] !== '1';
}

export async function rodar(env, agora = new Date(), enviar = fetch) {
  let gastos = 1;
  const subs = []; let cursor;
  do {
    const l = await env.SUBS.list({ prefix: 's:', cursor });
    subs.push(...l.keys); cursor = l.list_complete ? null : l.cursor;
    if (cursor) gastos++;
  } while (cursor && gastos < 5);
  // Poucos inscritos: todos no minuto :00. Muitos: espalha em até 6 faixas de 10 min (limite de 50 chamadas por execução).
  const faixas = Math.min(6, Math.max(1, Math.ceil(subs.length / POR_EXECUCAO)));
  const faixaAgora = Math.floor(agora.getUTCMinutes() / 10);
  if (faixaAgora >= faixas) return { enviados: 0, inscritos: subs.length };
  let enviados = 0;
  for (const k of subs) {
    if (hash(k.name) % faixas !== faixaAgora) continue;
    if (!precisaLembrar(k.metadata, agora)) continue;
    if (gastos >= 48) break;
    const endpoint = k.name.slice(2); gastos++;
    try {
      const r = await enviar(endpoint, { method: 'POST', headers: { Authorization: await cabecalhoVapid(endpoint, env), TTL: '3000', Urgency: 'normal' } });
      if (r.status === 404 || r.status === 410) { await env.SUBS.delete(k.name); gastos++; }
      else if (r.ok) enviados++;
      else console.log('push recusado', r.status, endpoint.slice(0, 40));
    } catch (e) { console.log('erro de envio', String(e)); }
  }
  return { enviados, inscritos: subs.length, faixas };
}

export default {
  async scheduled(ev, env, ctx) { ctx.waitUntil(rodar(env, new Date(ev.scheduledTime))); },

  async fetch(req, env) {
    const { pathname } = new URL(req.url);
    if (req.method === 'OPTIONS') return new Response(null, { status: 204, headers: CORS });
    if (pathname === '/chave') return resp((await getVapid(env)).pub);
    if (req.method === 'POST' && (pathname === '/inscrever' || pathname === '/cancelar')) {
      let d; try { const t = await req.text(); if (t.length > 4000) throw 0; d = JSON.parse(t); } catch { return resp('json inválido', 400); }
      if (!endpointValido(d.endpoint)) return resp('endpoint inválido', 400);
      const chave = 's:' + d.endpoint;
      if (pathname === '/cancelar') { await env.SUBS.delete(chave); return resp('ok'); }
      if (!/^\d{2}\/\d{2}\/\d{4}$/.test(d.qs || '') || !/^[01]{7,140}$/.test(d.r || '') || !/^[A-Za-z0-9_\/+\-]{1,40}$/.test(d.tz || '')) return resp('dados inválidos', 400);
      await env.SUBS.put(chave, '1', { metadata: { t: d.tz, q: d.qs, r: d.r } });
      return resp('ok');
    }
    return resp('Lembretes da Escola Sabatina: no ar.');
  }
};
