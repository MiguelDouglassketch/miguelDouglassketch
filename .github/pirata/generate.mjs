// Gera um SVG animado: um navio pirata navega pelo mar e coleta
// um tesouro para cada dia em que você fez commits.
//
// Uso no GitHub Actions: node .github/pirata/generate.mjs
// Teste com dados de exemplo:  node .github/pirata/generate.mjs --demo

import { mkdirSync, writeFileSync } from "node:fs";

const USER = process.env.GH_USER || process.env.GITHUB_REPOSITORY_OWNER;
const TOKEN = process.env.GITHUB_TOKEN;
const DEMO = process.argv.includes("--demo");

// ---------- 1. Buscar os dias de contribuição ----------
async function getWeeks() {
  if (DEMO) {
    return Array.from({ length: 53 }, () => ({
      contributionDays: Array.from({ length: 7 }, (_, weekday) => ({
        weekday,
        contributionCount: Math.random() < 0.3 ? Math.ceil(Math.random() * 9) : 0,
      })),
    }));
  }

  const query = `query($login:String!){
    user(login:$login){
      contributionsCollection{
        contributionCalendar{ weeks{ contributionDays{ contributionCount weekday } } }
      }
    }
  }`;

  const res = await fetch("https://api.github.com/graphql", {
    method: "POST",
    headers: {
      Authorization: `bearer ${TOKEN}`,
      "Content-Type": "application/json",
      "User-Agent": "navio-pirata",
    },
    body: JSON.stringify({ query, variables: { login: USER } }),
  });
  const json = await res.json();
  if (!res.ok || json.errors || !json.data?.user) {
    throw new Error("Erro ao buscar contribuições: " + JSON.stringify(json));
  }
  return json.data.user.contributionsCollection.contributionCalendar.weeks;
}

// ---------- 2. Medidas do desenho ----------
const weeks = await getWeeks();
const CELL = 15; // distância entre um dia e outro
const MX = 40; // margem lateral
const MY = 40; // margem de cima e de baixo
const W = MX * 2 + weeks.length * CELL;
const H = MY * 2 + 7 * CELL;

const cx = (w) => MX + w * CELL + CELL / 2;
const cy = (d) => MY + d * CELL + CELL / 2;

// guarda a quantidade de commits de cada dia: counts["semana,dia"]
const counts = {};
let max = 1;
weeks.forEach((week, w) => {
  week.contributionDays.forEach((day) => {
    counts[`${w},${day.weekday}`] = day.contributionCount;
    max = Math.max(max, day.contributionCount);
  });
});

// ---------- 3. Rota do navio (sobe uma coluna, desce a próxima...) ----------
const route = [];
weeks.forEach((_, w) => {
  const days = [0, 1, 2, 3, 4, 5, 6];
  if (w % 2 === 1) days.reverse();
  days.forEach((d) => route.push({ w, d }));
});
const N = route.length;
const DUR = Math.max(20, N * 0.1); // duração de uma volta completa (segundos)
const shipPath = route
  .map((p, i) => `${i === 0 ? "M" : "L"}${cx(p.w)} ${cy(p.d)}`)
  .join(" ");

// ---------- 4. Ondas ----------
function wave(y, amp, wl, color, opacity, dur, dir = -1) {
  const half = wl / 2;
  // a onda começa antes da borda e termina depois, para nunca deixar vãos
  const n = Math.ceil((W + wl * 3) / half);
  let d = `M${-wl} ${y} q${wl / 4} ${-amp} ${half} 0`;
  for (let i = 1; i < n; i++) d += ` t${half} 0`;
  d += ` L${-wl + n * half} ${H} L${-wl} ${H} Z`;
  return `<path d="${d}" fill="${color}" opacity="${opacity}">
    <animateTransform attributeName="transform" type="translate" from="0 0" to="${dir * wl} 0" dur="${dur}s" repeatCount="indefinite"/>
  </path>`;
}

// ---------- 5. Tesouros ----------
function treasure(count, k, x, y) {
  const level = Math.max(1, Math.ceil((4 * count) / max));
  // o tesouro some quando o navio chega nele
  const t = Math.min(k / (N - 1), 0.99);
  const hide = `<animate attributeName="opacity" dur="${DUR}s" repeatCount="indefinite"
      keyTimes="0;${t.toFixed(4)};${(t + 0.004).toFixed(4)};1" values="1;1;0;0"/>`;

  if (level <= 2) {
    const r = level === 1 ? 4 : 5.2;
    return `<g>${hide}
      <circle cx="${x}" cy="${y}" r="${r}" fill="#FFD54F" stroke="#F9A825" stroke-width="1"/>
      <circle cx="${x - 1.2}" cy="${y - 1.2}" r="${r / 3}" fill="#FFF8E1" opacity=".8"/>
    </g>`;
  }
  // baú para dias com muitos commits
  return `<g>${hide}
    <rect x="${x - 6}" y="${y - 4.5}" width="12" height="9" rx="2" fill="#8D6E63" stroke="#4E342E" stroke-width="1"/>
    <rect x="${x - 6}" y="${y - 4.5}" width="12" height="3.5" rx="2" fill="#A1887F" stroke="#4E342E" stroke-width="1"/>
    <rect x="${x - 1.3}" y="${y - 2}" width="2.6" height="3.2" fill="#FFD54F"/>
  </g>`;
}

let items = "";
route.forEach((p, k) => {
  const count = counts[`${p.w},${p.d}`] ?? 0;
  const x = cx(p.w);
  const y = cy(p.d);
  if (count > 0) {
    items += treasure(count, k, x, y);
  } else {
    // dia sem commit: só um brilhinho na água, para manter o desenho do gráfico
    items += `<rect x="${x - 4.5}" y="${y - 4.5}" width="9" height="9" rx="2" fill="#ffffff" opacity=".07"/>`;
  }
});

// ---------- 6. Navio pirata (desenho original e genérico) ----------
const ship = `
<g>
  <animateMotion path="${shipPath}" dur="${DUR}s" repeatCount="indefinite" rotate="0"/>
  <g>
    <animateTransform attributeName="transform" type="translate" values="0 0;0 -1.6;0 0" dur="1.4s" repeatCount="indefinite"/>
    <g transform="translate(0 -9) scale(1.25)">
      <rect x="-1" y="-26" width="2" height="26" fill="#3E2723"/>
      <path d="M1.5 -22 Q15 -14 1.5 -5 Z" fill="#FFF8E1" stroke="#BCAAA4" stroke-width=".8"/>
      <path d="M-1.5 -20 Q-12 -13 -1.5 -6 Z" fill="#FFFDE7" stroke="#BCAAA4" stroke-width=".8"/>
      <rect x="1" y="-30" width="10" height="6.5" fill="#111"/>
      <circle cx="6" cy="-27" r="1.8" fill="#fff"/>
      <rect x="1" y="-30" width="1" height="30" fill="#3E2723"/>
      <path d="M-15 0 L15 0 L10.5 8 L-10.5 8 Z" fill="#6D4C41" stroke="#3E2723" stroke-width="1"/>
      <rect x="-12" y="2.2" width="24" height="1.6" fill="#8D6E63"/>
      <circle cx="-6" cy="5.4" r="1" fill="#212121"/>
      <circle cx="0" cy="5.4" r="1" fill="#212121"/>
      <circle cx="6" cy="5.4" r="1" fill="#212121"/>
    </g>
  </g>
</g>`;

// ---------- 7. Montar o SVG ----------
const svg = `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 ${W} ${H}" width="${W}" height="${H}" role="img" aria-label="Navio pirata coletando os commits como tesouros">
  <defs>
    <linearGradient id="mar" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0" stop-color="#29A3F0"/>
      <stop offset="1" stop-color="#0B3D91"/>
    </linearGradient>
    <clipPath id="borda"><rect width="${W}" height="${H}" rx="14"/></clipPath>
  </defs>
  <g clip-path="url(#borda)">
    <rect width="${W}" height="${H}" fill="url(#mar)"/>
    ${wave(H * 0.3, 7, 90, "#ffffff", 0.1, 7, -1)}
    ${wave(H * 0.52, 9, 120, "#ffffff", 0.1, 9, 1)}
    ${wave(H * 0.74, 8, 80, "#0B3D91", 0.35, 6, -1)}
    ${wave(H * 0.9, 6, 100, "#082a66", 0.45, 8, 1)}
    ${items}
    ${ship}
  </g>
</svg>`;

mkdirSync("dist", { recursive: true });
writeFileSync("dist/navio-pirata.svg", svg);
console.log(`navio-pirata.svg gerado: ${weeks.length} semanas, ${N} dias, volta de ${DUR.toFixed(0)}s`);
