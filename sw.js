/* Service worker da Escola Sabatina
   Guarda a própria página (e ícones) no aparelho para o site abrir sem internet.
   Os textos das versões (ACF/AA/NVI) e a lição são guardados pela página no Cache Storage
   (caches "ess-biblia-v1" e "ess-licoes-v1"), que este arquivo não toca. */

const SHELL = "ess-shell-v11";
const ASSETS = [
  "./",
  "./index.html",
  "./manifest.webmanifest",
  "./icon-192.png",
  "./icon-512.png",
  "./apple-touch-icon.png",
  "./icon-maskable-512.png",
  "./icon.svg",
  "./data/licao.json",
  "./data/capas.json",
  "./data/audios.json",
  "./data/quiz.json",
  "./config.js"
];

const CORE = ["./", "./index.html", "./manifest.webmanifest", "./config.js"];

self.addEventListener("install", event => {
  event.waitUntil((async () => {
    const cache = await caches.open(SHELL);
    // Arquivos essenciais: se falharem (sinal ruim), a instalação é cancelada e o
    // service worker antigo, que já funciona offline, continua valendo.
    await Promise.all(CORE.map(a => cache.add(new Request(a, { cache: "reload" }))));
    // O resto é opcional.
    await Promise.all(ASSETS.filter(a => !CORE.includes(a)).map(a => cache.add(a).catch(() => {})));
    await self.skipWaiting();
  })());
});

self.addEventListener("activate", event => {
  event.waitUntil(
    caches.keys()
      .then(keys => Promise.all(
        keys.filter(k => k.startsWith("ess-shell-") && k !== SHELL).map(k => caches.delete(k))
      ))
      .then(() => self.clients.claim())
  );
});

self.addEventListener("fetch", event => {
  const req = event.request;
  if (req.method !== "GET") return;

  const url = new URL(req.url);
  // Só cuida de arquivos do próprio site. Os JSON das versões e o VLibras
  // (outros domínios) seguem o caminho normal.
  if (url.origin !== self.location.origin) {
    // Imagens de outros sites (capas da CPB / repositório): guarda para ver offline.
    if (/\.(png|jpe?g|webp|gif)$/i.test(url.pathname)) {
      event.respondWith(caches.open("ess-img-v1").then(c => c.match(req).then(hit => {
        const net = fetch(req).then(res => { if (res && (res.ok || res.type === "opaque")) c.put(req, res.clone()); return res; }).catch(() => hit);
        return hit || net;
      })));
    }
    return;
  }

  // Dados da lição: rede primeiro (para pegar atualizações), mas sem esperar à toa:
  // se a internet estiver fraca/travada, usa em até 3,5 s a cópia guardada.
  if (url.pathname.includes("/data/") || url.pathname.endsWith("/config.js")) {
    event.respondWith((async () => {
      const cached = await caches.match(req);
      const net = fetch(req, { cache: "no-cache" }).then(res => {
        if (res && res.ok) { const copy = res.clone(); caches.open(SHELL).then(c => c.put(req, copy)); }
        return res;
      });
      if (!cached) return net;
      event.waitUntil(net.catch(() => {}));
      return Promise.race([net.catch(() => cached), new Promise(r => setTimeout(() => r(cached), 3500))]);
    })());
    return;
  }

  // Abrir o site: responde na hora com a página guardada e atualiza em segundo plano.
  if (req.mode === "navigate") {
    event.respondWith(
      caches.match("./index.html").then(cached => {
        const refresh = fetch(req)
          .then(res => {
            if (res && res.ok && !res.redirected) {
              const copy = res.clone();
              caches.open(SHELL).then(c => c.put("./index.html", copy));
            }
            return res;
          })
          .catch(() => cached || caches.match("./") );
        return cached || refresh.then(r => r || caches.match("./"));
      })
    );
    return;
  }

  // Demais arquivos do site: usa o guardado e, se não houver, busca e guarda.
  event.respondWith(
    caches.match(req).then(hit =>
      hit || fetch(req).then(res => {
        if (res && res.ok) {
          const copy = res.clone();
          caches.open(SHELL).then(c => c.put(req, copy));
        }
        return res;
      })
    )
  );
});

/* ===== Lembrete: o servidor (push/worker.js) só envia o aviso a quem ainda não estudou o dia ===== */
const MSGS = [
  "Que tal reservar uns minutos para a lição de hoje?",
  "A lição de hoje ainda está esperando por você.",
  "Um passo de cada vez: abra a lição de hoje e estude agora.",
  "Ainda dá tempo de estudar a lição de hoje."
];

self.addEventListener("push", event => {
  const agora = new Date();
  const dia = agora.toLocaleDateString("pt-BR", { weekday: "long" });
  event.waitUntil(self.registration.showNotification("📖 Escola Sabatina · " + dia, {
    body: MSGS[agora.getHours() % MSGS.length],
    icon: "./icon-192.png",
    badge: "./icon-192.png",
    tag: "licao-hoje",      // substitui o aviso anterior em vez de empilhar
    renotify: true,
    data: { url: "./?hoje=1" }
  }));
});

self.addEventListener("notificationclick", event => {
  event.notification.close();
  event.waitUntil(
    self.clients.matchAll({ type: "window", includeUncontrolled: true }).then(list => {
      for (const c of list) {
        if (c.url.startsWith(self.registration.scope) && "focus" in c) {
          c.postMessage({ hoje: true });
          return c.focus();
        }
      }
      return self.clients.openWindow("./?hoje=1");
    })
  );
});
