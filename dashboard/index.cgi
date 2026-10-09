#!/bin/sh
# Renders the stats page from the proxy's log: its hourly "In the last 1h0m0s,
# there were N completed successful connections. Traffic Relayed ↓ X KB (…),
# ↑ Y KB (…)." summaries, the NAT type it detects, and its start line.
#
# awk only extracts the data; every figure on the page (rolling windows,
# trends, daily totals, the weekday x hour heatmap) is computed by the page's
# script from that one list of hourly summaries, so they always agree.
LOG_FILE="${LOG_FILE:-/data/snowflake.log}"

printf 'Content-Type: text/html; charset=utf-8\r\n\r\n'

cat <<'HTML'
<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta http-equiv="refresh" content="300">
<link rel="icon" href="/favicon.svg">
<title>Snowflake Proxy Stats</title>
<style>
  :root {
    color-scheme: dark;
    --bg: #07090c; --panel: #0d1117; --panel2: #10151c; --line: #1c2430;
    --fg: #d7dde5; --dim: #6b7685; --faint: #2a3340;
    --cyan: #22d3ee; --magenta: #e879f9; --green: #4ade80; --amber: #fbbf24;
    --koamaru: #333366; --koamaru-light: #9999d6;
    --mono: ui-monospace, SFMono-Regular, Menlo, Consolas, "Liberation Mono", monospace;
  }
  * { box-sizing: border-box; }
  body {
    margin: 0; background: var(--bg); color: var(--fg); min-height: 100vh;
    font: 14px/1.4 system-ui, -apple-system, "Segoe UI", sans-serif;
    background-image: radial-gradient(circle at 15% -10%, rgba(34,211,238,.08), transparent 40%),
                      radial-gradient(circle at 110% 10%, rgba(232,121,249,.06), transparent 35%);
  }
  body::after { content: ""; position: fixed; inset: 0; pointer-events: none;
    background: repeating-linear-gradient(to bottom, rgba(255,255,255,.018) 0 1px, transparent 1px 3px); }
  .wrap { max-width: 1120px; margin: 0 auto; padding: 20px 16px 40px; }

  .strip { display: flex; flex-wrap: wrap; gap: 6px 18px; align-items: center;
    font: 600 11px/1 var(--mono); letter-spacing: .08em; text-transform: uppercase; color: var(--dim);
    border: 1px solid var(--line); background: var(--panel); padding: 9px 12px; margin-bottom: 18px; }
  .strip b { color: var(--fg); font-weight: 600; }
  .dot { display: inline-block; width: 7px; height: 7px; border-radius: 50%; background: var(--green);
    box-shadow: 0 0 8px var(--green); margin-right: 6px; animation: pulse 2s ease-in-out infinite; }
  .dot.stale { background: var(--amber); box-shadow: 0 0 8px var(--amber); }
  @keyframes pulse { 50% { opacity: .35; } }
  @media (prefers-reduced-motion: reduce) { .dot { animation: none; } }
  .strip .sep { color: var(--faint); }
  .strip .right { margin-left: auto; }

  h1 { margin: 0 0 4px; font: 700 20px/1.2 var(--mono); letter-spacing: .02em; display: flex; align-items: center; gap: 8px; }
  h1 svg { color: var(--cyan); filter: drop-shadow(0 0 6px rgba(34,211,238,.5)); }
  h1 .acc { color: var(--cyan); }
  .sub { color: var(--dim); font: 12px var(--mono); margin-bottom: 18px; }

  .grid { display: grid; gap: 12px; grid-template-columns: repeat(auto-fit, minmax(190px, 1fr)); margin-bottom: 12px; }
  .card { position: relative; background: linear-gradient(180deg, var(--panel2), var(--panel));
    border: 1px solid var(--line); border-left: 2px solid var(--rail, var(--cyan)); padding: 12px 14px; min-height: 108px; }
  .card::before, .card::after { content: ""; position: absolute; width: 10px; height: 10px;
    border-color: var(--rail, var(--cyan)); opacity: .8; }
  .card::before { top: -1px; right: -1px; border-top: 1px solid; border-right: 1px solid; }
  .card::after { bottom: -1px; right: -1px; border-bottom: 1px solid; border-right: 1px solid; }
  .lbl { display: flex; justify-content: space-between; font: 600 10.5px/1 var(--mono);
    letter-spacing: .12em; text-transform: uppercase; color: var(--dim); margin-bottom: 10px; }
  .lbl i { font-style: normal; color: var(--faint); }
  .val { font: 700 26px/1.1 var(--mono); font-variant-numeric: tabular-nums; }
  .val small { font-size: 13px; color: var(--dim); font-weight: 600; margin-left: 3px; }
  .glow-c { color: var(--cyan); text-shadow: 0 0 14px rgba(34,211,238,.45); }
  .glow-g { text-shadow: 0 0 14px rgba(74,222,128,.45); }
  .meta { margin-top: 6px; font: 11.5px var(--mono); color: var(--dim); display: flex; gap: 10px; flex-wrap: wrap; }
  .up { color: var(--green); } .down { color: var(--amber); }
  .card.has-spark { padding-bottom: 40px; }
  .spark { position: absolute; left: 14px; bottom: 8px; width: calc(100% - 28px); height: 26px; opacity: .9; }
  .ud { margin-top: 4px; }
  .ud b { font-weight: 600; color: var(--fg); }
  .ud .dn { color: var(--cyan); } .ud .upl { color: var(--magenta); }

  .grid.compact { grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); }
  .card.mini { min-height: 0; padding: 9px 12px; }
  .card.mini .lbl { margin-bottom: 6px; }
  .card.mini .val { font-size: 18px; }
  .card.mini .val small { font-size: 11px; }
  .card.mini .row { display: flex; justify-content: space-between; align-items: baseline; gap: 8px; }
  .card.mini .meta { margin: 0; }
  .card.mini::before, .card.mini::after { width: 7px; height: 7px; }

  .panel { position: relative; background: var(--panel); border: 1px solid var(--line); padding: 14px; margin-bottom: 12px; }
  .panel::before { content: ""; position: absolute; top: -1px; left: -1px; width: 14px; height: 14px;
    border-top: 1px solid var(--magenta); border-left: 1px solid var(--magenta); }
  .phead { display: flex; justify-content: space-between; align-items: baseline; gap: 10px; flex-wrap: wrap; margin-bottom: 10px; }
  .ptitle { font: 600 11px var(--mono); letter-spacing: .12em; text-transform: uppercase; }
  .ptitle span { color: var(--magenta); margin-right: 6px; }
  .pmeta { font: 11px var(--mono); color: var(--dim); }
  .empty { font: 12px var(--mono); color: var(--dim); padding: 24px 0; text-align: center; }
  svg text { font: 10px var(--mono); fill: var(--dim); }

  .heat { display: grid; grid-template-columns: 34px repeat(24, 1fr); gap: 3px; }
  .heat div { aspect-ratio: 1; min-width: 0; border-radius: 1px; }
  .heat .rl { aspect-ratio: auto; font: 10px/1 var(--mono); color: var(--dim); align-self: center; }
  .heat .na { outline: 1px dashed var(--line); outline-offset: -1px; }
  .legend { display: flex; gap: 3px; align-items: center; font: 10px var(--mono); color: var(--dim); margin-top: 8px; justify-content: flex-end; }
  .legend div { width: 11px; height: 11px; }

  footer { font: 11px var(--mono); color: var(--faint); margin-top: 16px; display: flex; justify-content: space-between; flex-wrap: wrap; gap: 8px; }
</style>
</head>
<body>
<div class="wrap">
  <div class="strip">
    <span><span class="dot" id="dot"></span><b id="state">—</b></span>
    <span class="sep">│</span><span>NAT <b id="nat-strip">—</b></span>
    <span class="sep">│</span><span>Uptime <b id="uptime-strip">—</b></span>
    <span class="right">Gen <b id="gen">—</b></span>
  </div>

  <h1><svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" aria-hidden="true"><line x1="20.23" y1="16.75" x2="3.77" y2="7.25"/><line x1="12" y1="21.5" x2="12" y2="2.5"/><line x1="3.77" y1="16.75" x2="20.23" y2="7.25"/><line x1="17.2" y1="15" x2="20.57" y2="11.25"/><line x1="17.2" y1="15" x2="15.63" y2="19.79"/><line x1="12" y1="18" x2="16.93" y2="19.04"/><line x1="12" y1="18" x2="7.07" y2="19.04"/><line x1="6.8" y1="15" x2="8.37" y2="19.79"/><line x1="6.8" y1="15" x2="3.43" y2="11.25"/><line x1="6.8" y1="9" x2="3.43" y2="12.75"/><line x1="6.8" y1="9" x2="8.37" y2="4.21"/><line x1="12" y1="6" x2="7.07" y2="4.96"/><line x1="12" y1="6" x2="16.93" y2="4.96"/><line x1="17.2" y1="9" x2="15.63" y2="4.21"/><line x1="17.2" y1="9" x2="20.57" y2="12.75"/></svg><span>SNOWFLAKE<span class="acc">://</span>PROXY</span></h1>
  <div class="sub">tor pluggable-transport relay · hourly telemetry · Snowflake Dashboard powered by ruxal</div>

  <div class="grid">
    <div class="card has-spark">
      <div class="lbl">Bandwidth · last 24h <i>01</i></div>
      <div class="val glow-c" id="last24">—</div>
      <div class="meta"><span id="d24"></span><span id="c24"></span></div>
      <div class="meta ud" id="ud24"></div>
      <svg class="spark" id="spark-24h" preserveAspectRatio="none"></svg>
    </div>
    <div class="card has-spark">
      <div class="lbl">Bandwidth · 7d <i>02</i></div>
      <div class="val" id="w7">—</div>
      <div class="meta"><span id="d7"></span><span id="c7"></span></div>
      <div class="meta ud" id="ud7"></div>
      <svg class="spark" id="spark-7d" preserveAspectRatio="none"></svg>
    </div>
    <div class="card has-spark" style="--rail: var(--magenta)">
      <div class="lbl">Avg / day <i>03</i></div>
      <div class="val" id="avgday">—</div>
      <div class="meta" id="days">—</div>
      <div class="meta ud" id="udavg"></div>
      <svg class="spark" id="spark-avg" preserveAspectRatio="none"></svg>
    </div>
    <div class="card has-spark" style="--rail: var(--magenta)">
      <div class="lbl">All-time <i>04</i></div>
      <div class="val" id="all">—</div>
      <div class="meta" id="call">—</div>
      <div class="meta ud" id="udall"></div>
      <svg class="spark" id="spark-all" preserveAspectRatio="none"></svg>
    </div>
  </div>

  <div class="grid compact">
    <div class="card mini">
      <div class="lbl">Conn · last hour <i>05</i></div>
      <div class="row"><span class="val" id="c1">—</span><span class="meta" id="c1m"></span></div>
    </div>
    <div class="card mini">
      <div class="lbl">Peak throughput <i>06</i></div>
      <div class="row"><span class="val" id="peakmbps">—</span><span class="meta">hourly avg, 24h</span></div>
    </div>
    <div class="card mini">
      <div class="lbl">Telemetry <i>07</i></div>
      <div class="row"><span class="val" id="nsum">—</span><span class="meta">hourly summaries</span></div>
    </div>
  </div>

  <div class="panel">
    <div class="phead">
      <div class="ptitle"><span>▸</span>Bandwidth · last 24h</div>
      <div class="pmeta" id="chartmeta"></div>
    </div>
    <svg id="chart" width="100%" height="190"></svg>
  </div>

  <div class="panel">
    <div class="phead">
      <div class="ptitle"><span>▸</span>Activity · hour × weekday</div>
      <div class="pmeta">UTC · summary hour ending · avg MB per hour</div>
    </div>
    <div class="heat" id="heat"></div>
    <div class="legend">less <div style="background:#141429"></div><div style="background:#1f1f3d"></div><div style="background:#333366"></div><div style="background:#5c5ca3"></div><div style="background:#9999d6"></div> more</div>
  </div>

  <footer><span id="src">—</span><span>// end of transmission</span></footer>
</div>
<script>
HTML

# Data block. Only digits, '-', ':', 'T', 'Z' and a sanitised NAT word reach
# the script, so nothing from the log can break out of it.
awk -v generated="$(date -u +%Y-%m-%dT%H:%M:%SZ)" -v logfile="$LOG_FILE" '
function iso(d, t) { gsub("/", "-", d); return d "T" t "Z" }
BEGIN { n = 0; nat = "unknown" }
/NAT type:/ { nat = $0; sub(/.*NAT type: */, "", nat); gsub(/[^A-Za-z0-9 _-]/, "", nat); nat_ts = iso($1, $2) }
/Proxy starting/ { start_ts = iso($1, $2) }
# Each summary is logged through two loggers, so drop exact repeats.
# The proxy reports decimal kilobytes (bytes / 1000).
/completed successful connections/ && !seen[$0]++ {
  n++; row[n] = sprintf("[\"%s\",%d,%d,%d]", iso($1, $2), $9 + 0, $16 + 0, $21 + 0)
}
END {
  gsub(/[^A-Za-z0-9\/._-]/, "", logfile)
  printf "const GENERATED = \"%s\", STARTED = \"%s\", NAT = \"%s\", NAT_TS = \"%s\", LOG = \"%s\";\n", generated, start_ts, nat, nat_ts, logfile
  printf "// [hour ending (UTC), connections, KB down, KB up], oldest first\nconst HOURS = ["
  for (i = 1; i <= n; i++) printf "%s%s", (i > 1 ? "," : ""), row[i]
  print "];"
}' "$( [ -f "$LOG_FILE" ] && printf %s "$LOG_FILE" || printf /dev/null )"

cat <<'HTML'
const H = 36e5, NS = "http://www.w3.org/2000/svg";
const $ = id => document.getElementById(id);
const el = (t, a, p) => { const e = document.createElementNS(NS, t); for (const k in a) e.setAttribute(k, a[k]); if (p) p.appendChild(e); return e; };
const gbHtml = kb => (kb / 1e6).toFixed(2) + "<small>GB</small>";
const sum = (a, k) => a.reduce((s, r) => s + r[k], 0);
const loggedDays = hours => hours / 24;

const now = Date.parse(GENERATED);
const rows = HOURS.map(([iso, c, dn, up]) => ({ t: Date.parse(iso), iso, c, dn, up, kb: dn + up }));
const firstT = rows.length ? rows[0].t : now, lastT = rows.length ? rows[rows.length - 1].t : 0;
const win = (from, to) => rows.filter(r => r.t > now - from * H && r.t <= now - to * H);
const bucketIndex = (t, count, duration) => count - 1 - Math.floor((now - t) / duration);

// A trend is only shown once the log covers the whole previous window.
function trend(id, cur, prev, hours, label) {
  const e = $(id);
  if (!prev || firstT > now - 2 * hours * H + H) { e.textContent = "no prior " + label; return; }
  const p = Math.round((cur - prev) / prev * 100);
  e.textContent = `${p < 0 ? "▼" : "▲"} ${Math.abs(p)}% vs prev ${label}`;
  e.className = p < 0 ? "down" : "up";
}

// header + NAT
const fresh = rows.length && now - lastT < 2 * H;
$("dot").classList.toggle("stale", !fresh);
$("state").textContent = !rows.length ? "Waiting for first summary" : fresh ? "Relay up" : "No recent summary";
const natOk = /^unrestricted$/i.test(NAT), natWarn = /^restricted$/i.test(NAT);
const natColor = natOk ? "var(--green)" : natWarn ? "var(--amber)" : "var(--dim)";
$("nat-strip").textContent = NAT.toLowerCase(); $("nat-strip").style.color = natColor;
if (NAT_TS) $("nat-strip").title = "detected " + NAT_TS.replace("T", " ");
$("gen").textContent = GENERATED.replace("T", " ");
$("uptime-strip").title = STARTED ? "proxy started " + STARTED.replace("T", " ") : "start not logged";
$("src").textContent = `${rows.length} hourly summaries parsed from ${LOG}`;

// rolling windows, anchored to now so a stopped proxy shows as quiet, not stale data
const d24 = win(24, 0), p24 = win(48, 24), w7 = win(168, 0), p7 = win(336, 168);
$("last24").innerHTML = gbHtml(sum(d24, "kb"));
$("c24").textContent = sum(d24, "c") + " conn";
trend("d24", sum(d24, "kb"), sum(p24, "kb"), 24, "24h");
$("w7").innerHTML = gbHtml(sum(w7, "kb"));
$("c7").textContent = sum(w7, "c") + " conn";
const gbs = kb => (kb / 1e6).toFixed(2) + " GB";
const ud = (id, a, div = 1) => { $(id).innerHTML =
  `<span class="dn">↓</span> <b>${gbs(sum(a, "dn") / div)}</b> <span class="upl">↑</span> <b>${gbs(sum(a, "up") / div)}</b>`; };
trend("d7", sum(w7, "kb"), sum(p7, "kb"), 168, "7d");

$("all").innerHTML = gbHtml(sum(rows, "kb"));
$("call").textContent = sum(rows, "c") + " conn · cumulative";
ud("ud24", d24); ud("ud7", w7); ud("udall", rows);
const days = loggedDays(rows.length);
if (rows.length) ud("udavg", rows, days);
$("avgday").innerHTML = rows.length ? gbHtml(sum(rows, "kb") / days) : "—";
$("days").textContent = days.toFixed(1) + " days logged";
$("nsum").textContent = rows.length;
const lastC = fresh ? rows[rows.length - 1].c : null;
$("c1").textContent = lastC == null ? "—" : lastC;
$("c1m").textContent = lastC == null ? "no summary this hour" : "≈ " + (lastC / 60).toFixed(2) + " / min";

// 24 hourly slots ending now; a slot without a summary stays empty
const slots = Array(24).fill(null);
for (const r of d24) { const i = bucketIndex(r.t, 24, H); if (i >= 0 && i < 24) slots[i] = (slots[i] || 0) + r.kb / 1e3; }
const filled = slots.filter(v => v != null), peakMB = filled.length ? Math.max(...filled) : 0;
$("peakmbps").innerHTML = (peakMB * 8 / 3600).toFixed(2) + "<small>Mbit/s</small>";
const totalMB = filled.reduce((a, b) => a + b, 0);
$("chartmeta").textContent = filled.length
  ? `Σ ${(totalMB / 1e3).toFixed(2)} GB · peak ${peakMB.toFixed(1)} MB · avg ${(totalMB / filled.length).toFixed(0)} MB/h`
  : "";

const weekSlots = Array(7).fill(0);
for (const r of w7) weekSlots[bucketIndex(r.t, 7, 24 * H)] += r.kb / 1e6;

// daily totals (UTC dates) for the avg / all-time sparklines
const byDay = new Map();
for (const r of rows) {
  const k = r.iso.slice(0, 10), day = byDay.get(k) || { gb: 0, hours: 0 };
  day.gb += r.kb / 1e6; day.hours++;
  byDay.set(k, day);
}
let totalGB = 0, totalHours = 0;
const cumulative = [], dailyAverage = [];
for (const day of byDay.values()) {
  totalGB += day.gb; totalHours += day.hours;
  cumulative.push(totalGB);
  dailyAverage.push(totalGB / loggedDays(totalHours));
}

function spark(id, data, color) {
  if (data.length < 2) return;
  const svg = $(id), w = 100, h = 26, mx = Math.max(1e-9, ...data);
  svg.setAttribute("viewBox", `0 0 ${w} ${h}`);
  const d = data.map((v, i) => (i ? "L" : "M") + (i / (data.length - 1) * w).toFixed(1) + " " + (h - 2 - v / mx * (h - 4)).toFixed(1)).join(" ");
  const g = el("linearGradient", { id: id + "g", x1: 0, y1: 0, x2: 0, y2: 1 }, el("defs", {}, svg));
  el("stop", { offset: 0, "stop-color": color, "stop-opacity": .35 }, g); el("stop", { offset: 1, "stop-color": color, "stop-opacity": 0 }, g);
  el("path", { d: d + ` L${w} ${h} L0 ${h} Z`, fill: `url(#${id}g)` }, svg);
  el("path", { d, fill: "none", stroke: color, "stroke-width": 1.4, "vector-effect": "non-scaling-stroke" }, svg);
}
if (filled.length) spark("spark-24h", slots.map(v => v || 0), "#22d3ee");
spark("spark-7d", weekSlots, "#e879f9");
spark("spark-avg", dailyAverage, "#e879f9");
spark("spark-all", cumulative, "#e879f9");

function drawChart() {
  const svg = $("chart"); svg.innerHTML = "";
  if (!filled.length) {
    el("text", { x: "50%", y: 95, "text-anchor": "middle" }, svg).textContent =
      rows.length ? "no summaries in the last 24 hours" : "no hourly summaries logged yet — the first arrives after a full hour";
    return;
  }
  const W = svg.clientWidth, Ht = 190, L = 44, B = 22, T = 8, cw = (W - L) / 24;
  const step = peakMB > 400 ? 100 : peakMB > 40 ? 10 : 1, top = Math.max(step, Math.ceil(peakMB / step) * step);
  for (let i = 0; i <= 4; i++) {
    const y = T + (Ht - T - B) * i / 4;
    el("line", { x1: L, x2: W, y1: y, y2: y, stroke: "#1c2430", "stroke-dasharray": i === 4 ? "" : "2 4" }, svg);
    el("text", { x: L - 8, y: y + 3, "text-anchor": "end" }, svg).textContent = +(top * (1 - i / 4)).toFixed(1) + "M";
  }
  const g = el("linearGradient", { id: "bg", x1: 0, y1: 0, x2: 0, y2: 1 }, el("defs", {}, svg));
  el("stop", { offset: 0, "stop-color": "#22d3ee" }, g); el("stop", { offset: 1, "stop-color": "#0e7490", "stop-opacity": .6 }, g);
  slots.forEach((v, i) => {
    const x = L + i * cw + cw * .18;
    if (i % 6 === 0 || i === 23)
      el("text", { x: i === 23 ? W - 2 : x + cw * .32, y: Ht - 6, "text-anchor": i === 23 ? "end" : "middle" }, svg).textContent = i === 23 ? "now" : `-${24 - i}h`;
    if (v == null) return;
    const h = (Ht - T - B) * v / top, isPeak = v === peakMB;
    const r = el("rect", { x, y: Ht - B - h, width: cw * .64, height: Math.max(h, 1), fill: isPeak ? "#9999d6" : "url(#bg)" }, svg);
    if (isPeak) r.setAttribute("style", "filter: drop-shadow(0 0 6px rgba(153,153,214,.75))");
    const end = new Date(now - (23 - i) * H).toISOString().slice(11, 13);
    el("title", {}, r).textContent = `hour ending ~${end}:00 UTC · ${v.toFixed(1)} MB · ${(v * 8 / 3600).toFixed(2)} Mbit/s`;
  });
}
drawChart(); addEventListener("resize", drawChart);

// heatmap: average MB per weekday x hour (UTC); Deep Koamaru ramp
const sumH = Array.from({ length: 7 }, () => Array(24).fill(0)), cnt = Array.from({ length: 7 }, () => Array(24).fill(0));
for (const r of rows) { const d = new Date(r.t), w = (d.getUTCDay() + 6) % 7, h = d.getUTCHours(); sumH[w][h] += r.kb / 1e3; cnt[w][h]++; }
const heat = sumH.map((row, w) => row.map((v, h) => cnt[w][h] ? v / cnt[w][h] : null));
const hmax = Math.max(1, ...heat.flat().filter(v => v != null));
const ramp = ["#141429", "#1f1f3d", "#333366", "#5c5ca3", "#9999d6"];
const hm = $("heat");
["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"].forEach((d, w) => {
  const l = document.createElement("div"); l.className = "rl"; l.textContent = d; hm.appendChild(l);
  heat[w].forEach((v, h) => {
    const c = document.createElement("div");
    if (v == null) c.className = "na"; else c.style.background = ramp[Math.min(4, Math.floor(v / hmax * 5))];
    c.title = `${d} ${String(h).padStart(2, "0")}:00–${String(h).padStart(2, "0")}:59 UTC summary ending · ${v == null ? "no data" : v.toFixed(1) + " MB avg"}`;
    hm.appendChild(c);
  });
});

// live uptime counter from the proxy's last start
function fmt(s) { const h = Math.floor(s / 3600), m = Math.floor(s % 3600 / 60), x = Math.floor(s % 60);
  return `${h}h ${String(m).padStart(2, "0")}m ${String(x).padStart(2, "0")}s`; }
const base = STARTED ? (now - Date.parse(STARTED)) / 1000 : NaN, t0 = Date.now();
function tick() {
  if (isNaN(base)) return;
  const s = Math.max(0, base + (Date.now() - t0) / 1000);
  $("uptime-strip").textContent = fmt(s);
}
tick(); setInterval(tick, 1000);
</script>
</body>
</html>
HTML
