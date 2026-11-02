"""Build the public website version of Chevy from the Claude artifact's index.html.

Published entries come from content.json (Maggie's entries, read-only on the site).
Visitors can add their own sandbox entries, saved only in their browser.
Usage: python3 build_site.py <claude index.html> <output index.html>
"""
import sys
src, dst = sys.argv[1], sys.argv[2]
s = open(src).read()
def r(a, b):
    global s
    assert a in s, "MISSING: " + a[:90]
    s = s.replace(a, b, 1)

# ---------- CSS ----------
s = s.replace('</style>', '''
/* Public site: published entries are read-only; visitor entries are a sandbox */
.site-banner { max-width: 1120px; margin: 0 auto; padding: 14px 20px 0; }
.site-banner > div { display: flex; flex-wrap: wrap; align-items: center; justify-content: space-between; gap: 8px 14px; background: var(--panel); border: 1px solid var(--panel-line); border-radius: 10px; padding: 9px 14px; font-size: 13px; color: var(--ink); }
.site-banner .btn { padding: 3px 10px; font-size: 12px; }
.mine-tag { font-size: 10px; font-weight: 700; letter-spacing: .05em; text-transform: uppercase; color: var(--hold); background: var(--hold-soft); border-radius: 4px; padding: 1px 6px; flex: none; }
.ro-note { font-size: 12px; color: var(--muted); }
.ro-note[hidden] { display: none; }
.dialog.ro #ed-addlink, .dialog.ro [data-unlink], .dialog.ro #bodyToggle, .dialog.ro #deleteBtn,
.dialog.ro button[type="submit"], .dialog.ro .md-hint { display: none !important; }
.dialog.ro .md { cursor: default; }
.dialog.ro input:disabled, .dialog.ro select:disabled { opacity: 1; color: var(--ink); -webkit-text-fill-color: var(--ink); }
select.pill:disabled { cursor: default; opacity: 1; }
</style>''', 1)

# ---------- Banner ----------
r('<div class="notice-wrap"><div class="notice" id="notice" hidden></div></div>',
  '''<div class="site-banner"><div><span id="bannerText">You're viewing Maggie's Chevy. You can add your own entries to try it out. They stay only on this device.</span><button type="button" class="btn" id="clearSandbox" hidden>Clear my entries</button></div></div>
<div class="notice-wrap"><div class="notice" id="notice" hidden></div></div>''')
r('''<span class="dlg-kind" id="dlgTitle">New project</span>''',
  '''<span class="dlg-kind" id="dlgTitle">New project</span>
      <span class="ro-note" id="roNote" hidden>Read-only · published by Maggie</span>''')

# ---------- Table cells ----------
r('''${e.subtitle ? `<span class="t-sub">${esc(e.subtitle)}</span>` : ""}</span></span>`;''',
  '''${e.subtitle ? `<span class="t-sub">${esc(e.subtitle)}</span>` : ""}</span>${e._pub ? "" : '<span class="mine-tag">Yours</span>'}</span>`;''')
r('''cell: (e, P, T) => `<select class="pill ${statusOf(e.status).cls}" data-status-for="${esc(e.id)}" aria-label''',
  '''cell: (e, P, T) => `<select class="pill ${statusOf(e.status).cls}" data-status-for="${esc(e.id)}"${e._pub ? " disabled" : ""} aria-label''')

# ---------- Saving: only sandbox entries can change ----------
r('''    if (local || !db) {
      const list = data[type], i = list.findIndex(x => x.id === id);
      if (i >= 0) list[i] = e; else list.push(e);
      renderAll(); return;
    }''', '''    if (local || !db) {
      if (published.has(id)) throw new Error("This entry is published by Maggie and can't be changed here.");
      const list = data[type], i = list.findIndex(x => x.id === id);
      if (i >= 0) list[i] = e; else list.push(e);
      persistSandbox(); renderAll(); return;
    }''')
r('''    if (local || !db) { data[type] = data[type].filter(x => x.id !== id); renderAll(); return; }''',
  '''    if (local || !db) {
      if (published.has(id)) throw new Error("This entry is published by Maggie and can't be deleted here.");
      data[type] = data[type].filter(x => x.id !== id); persistSandbox(); renderAll(); return;
    }''')
r('const o = byId.get(oid); if (!o) continue;', 'const o = byId.get(oid); if (!o || o.e._pub) continue;')
r('const others = [...byId.values()].filter(o => o.e.id !== id &&', 'const others = [...byId.values()].filter(o => !o.e._pub && o.e.id !== id &&')
r('''  async function saveCurrent() {''', '''  async function saveCurrent() {
    if (editing && editing.ro) return true;''')

# ---------- Read-only view for published entries ----------
r('''    $("overlay").hidden = false;''', '''    editing.ro = !!(e && e._pub);
    $("editForm").classList.toggle("ro", editing.ro);
    $("roNote").hidden = !editing.ro;
    $("cancelBtn").textContent = editing.ro ? "Close" : "Cancel";
    if (editing.ro) $("edFields").querySelectorAll("input, select, textarea").forEach(el => { el.disabled = true; });
    $("overlay").hidden = false;''')
r('''  $("bodyView").addEventListener("click", e => {''', '''  $("bodyView").addEventListener("click", e => {
    if (editing && editing.ro && !e.target.closest("a")) return;''')

# ---------- Data: published content + this visitor's sandbox ----------
start = s.index('  // ---------- Connect to saved data ----------')
end = s.index('\n  showView();\n')
s = s[:start] + '''  // ---------- Data: Maggie's published entries + this visitor's sandbox ----------
  const published = new Set();
  let sandbox = Object.fromEntries(TYPES.map(T => [T.key, []]));
  function persistSandbox() {
    TYPES.forEach(T => { sandbox[T.key] = data[T.key].filter(e => !published.has(e.id)); });
    try { localStorage.setItem("chevy.sandbox", JSON.stringify(sandbox)); }
    catch (e) { notice("Your browser wouldn't save your entry. Private browsing can cause this."); }
    $("clearSandbox").hidden = !TYPES.some(T => sandbox[T.key].length);
  }
  local = true; clearTimeout(loadTimer);
  try {
    const saved = JSON.parse(localStorage.getItem("chevy.sandbox") || "null");
    if (saved) TYPES.forEach(T => { if (Array.isArray(saved[T.key])) sandbox[T.key] = saved[T.key].map(e => { const c = { ...e }; delete c._pub; return c; }); });
  } catch (e) {}
  $("clearSandbox").hidden = !TYPES.some(T => sandbox[T.key].length);
  $("clearSandbox").addEventListener("click", () => {
    if ($("clearSandbox").dataset.confirm !== "1") { $("clearSandbox").dataset.confirm = "1"; $("clearSandbox").textContent = "Tap again to clear"; return; }
    $("clearSandbox").dataset.confirm = ""; $("clearSandbox").textContent = "Clear my entries";
    TYPES.forEach(T => { data[T.key] = data[T.key].filter(e => published.has(e.id)); });
    persistSandbox(); renderAll();
  });
  TYPES.forEach(T => { data[T.key] = [...sandbox[T.key]]; });
  fetch("content.json", { cache: "no-cache" })
    .then(res => { if (!res.ok) throw new Error(res.status); return res.json(); })
    .then(content => {
      TYPES.forEach(T => {
        const pub = (Array.isArray(content[T.key]) ? content[T.key] : []).map(e => ({ ...e, _pub: true }));
        pub.forEach(e => published.add(e.id));
        data[T.key] = [...pub, ...sandbox[T.key].filter(e => !published.has(e.id))];
      });
    })
    .catch(() => notice("Maggie's entries couldn't be loaded. Check your connection and reload the page."))
    .finally(() => { TYPES.forEach(T => { loaded[T.key] = true; }); renderAll(); });
''' + s[end:]
open(dst, 'w').write(s)
print("built", dst)

# ---------- Send entries to Maggie (Netlify Forms) ----------
s = open(dst).read()
def r2(a, b):
    global s
    assert a in s, "MISSING: " + a[:90]
    s = s.replace(a, b, 1)

s = s.replace('</style>', '''
.site-banner .actions { display: flex; gap: 6px; flex-wrap: wrap; }
.btn.small-primary { background: var(--accent); color: var(--on-accent); border-color: var(--accent); font-weight: 600; }
.send-list { display: grid; gap: 4px; max-height: 220px; overflow-y: auto; border: 1px solid var(--line); border-radius: 8px; padding: 6px 8px; }
.dialog .send-list input { width: auto; flex: none; padding: 0; }
.send-list label { display: flex; align-items: center; gap: 8px; font-size: 14px; cursor: pointer; padding: 2px 0; }
.send-list .sent { font-size: 11px; color: var(--good); font-weight: 600; }
.send-ok { background: var(--good-soft); color: var(--good); border-radius: 8px; padding: 10px 12px; font-size: 14px; }
.send-ok[hidden] { display: none; }
.dialog .f textarea { padding: 9px 10px; border: 1px solid var(--line); border-radius: 7px; background: var(--bg); width: 100%; min-height: 70px; resize: vertical; font: inherit; }
.sent-tag { font-size: 10px; font-weight: 700; letter-spacing: .05em; text-transform: uppercase; color: var(--good); background: var(--good-soft); border-radius: 4px; padding: 1px 6px; flex: none; }
</style>''', 1)

r2('''<button type="button" class="btn" id="clearSandbox" hidden>Clear my entries</button>''',
   '''<span class="actions"><button type="button" class="btn small-primary" id="openSend" hidden>Send my entries to Maggie</button><button type="button" class="btn" id="clearSandbox" hidden>Clear my entries</button></span>''')

r2('<script src="https://cdnjs.cloudflare.com/ajax/libs/d3/7.8.5/d3.min.js"></script>', '''<!-- Netlify reads this hidden form at deploy time so submissions are accepted -->
<form name="chevy-submissions" data-netlify="true" netlify-honeypot="bot-field" hidden>
  <input name="bot-field"><input name="name"><input name="email"><textarea name="message"></textarea><textarea name="summary"></textarea><textarea name="entries"></textarea>
</form>

<div class="overlay" id="sendOverlay" hidden>
  <form class="dialog" id="sendForm" role="dialog" aria-modal="true" aria-labelledby="sendTitle">
    <h2 id="sendTitle">Send entries to Maggie</h2>
    <p style="margin:0;color:var(--muted);font-size:14px">Pick the entries you'd like Maggie to consider. She decides what gets added to her Chevy.</p>
    <div class="f"><span class="flabel">Entries to send</span><div class="send-list" id="sendList"></div></div>
    <div class="f"><label for="sendName">Your name (optional)</label><input id="sendName" type="text" autocomplete="name"></div>
    <div class="f"><label for="sendEmail">Your email (optional, so she can reply)</label><input id="sendEmail" type="email" autocomplete="email"></div>
    <div class="f"><label for="sendMsg">Note to Maggie (optional)</label><textarea id="sendMsg"></textarea></div>
    <p hidden><label>Leave this empty <input id="sendBot" type="text" tabindex="-1" autocomplete="off"></label></p>
    <div class="send-ok" id="sendOk" hidden></div>
    <div class="err" id="sendErr"></div>
    <div class="dialog-actions"><div class="right"><button class="btn" type="button" id="sendCancel">Cancel</button><button class="btn primary" type="submit" id="sendSubmit">Send</button></div></div>
  </form>
</div>

<script src="https://cdnjs.cloudflare.com/ajax/libs/d3/7.8.5/d3.min.js"></script>''')

# show a "Sent" tag on entries already sent
r2('''${e._pub ? "" : '<span class="mine-tag">Yours</span>'}</span>`;''',
   '''${e._pub ? "" : '<span class="mine-tag">Yours</span>'}${!e._pub && e.sentAt ? '<span class="sent-tag">Sent</span>' : ""}</span>`;''')

# show the send button whenever there are sandbox entries
s = s.replace('''$("clearSandbox").hidden = !TYPES.some(T => sandbox[T.key].length);''',
              '''$("clearSandbox").hidden = $("openSend").hidden = !TYPES.some(T => sandbox[T.key].length);''')

r2('''  TYPES.forEach(T => { data[T.key] = [...sandbox[T.key]]; });''', r'''  TYPES.forEach(T => { data[T.key] = [...sandbox[T.key]]; });

  // ---------- Send entries to Maggie ----------
  const mine = () => TYPES.flatMap(T => data[T.key].filter(e => !published.has(e.id)).map(e => ({ type: T.key, e })));
  function describe({ type, e }) {
    const T = TYPE[type], lines = [`${T.singular.toUpperCase()}: ${e.title || "Untitled"}`];
    T.props.forEach(P => {
      if (P.kind === "title") return;
      let v = "";
      if (P.kind === "text") v = e[P.field] || "";
      else if (P.kind === "date") v = e[P.field] ? fmt(e[P.field]) + (P.withTime && fmtTime(e[P.field]) ? ", " + fmtTime(e[P.field]) : "") : "";
      else if (P.kind === "status") v = e.status || "Not started";
      else if (P.kind === "daterange") v = fmtRange(e[P.start], e[P.end]);
      else if (P.kind === "links") v = linksOf(e.id).map(x => x.e.title + (x.e._pub ? "" : " (theirs)")).join(", ");
      if (v) lines.push(`${P.label}: ${v}`);
    });
    if ((e.body || "").trim()) lines.push("Notes:", e.body.trim());
    return lines.join("\n");
  }
  function openSend() {
    const list = mine().sort(titleSort);
    $("sendList").innerHTML = list.map(x => `<label><input type="checkbox" value="${esc(x.e.id)}" ${x.e.sentAt ? "" : "checked"}><i class="tdot t-${x.type}" aria-hidden="true"></i>${esc(x.e.title || "Untitled")}${x.e.sentAt ? ' <span class="sent">sent before</span>' : ""}</label>`).join("");
    $("sendOk").hidden = true; $("sendErr").textContent = "";
    $("sendSubmit").hidden = false; $("sendSubmit").disabled = false; $("sendSubmit").textContent = "Send";
    $("sendCancel").textContent = "Cancel";
    $("sendOverlay").hidden = false;
  }
  const closeSend = () => { $("sendOverlay").hidden = true; };
  $("openSend").addEventListener("click", openSend);
  $("sendCancel").addEventListener("click", closeSend);
  $("sendOverlay").addEventListener("click", e => { if (e.target.id === "sendOverlay") closeSend(); });
  $("sendForm").addEventListener("submit", async ev => {
    ev.preventDefault();
    const ids = [...$("sendList").querySelectorAll("input:checked")].map(i => i.value);
    if (!ids.length) { $("sendErr").textContent = "Tick at least one entry to send."; return; }
    const chosen = mine().filter(x => ids.includes(x.e.id));
    const payload = chosen.map(({ type, e }) => { const c = { ...e }; delete c.sentAt; return { type, ...c }; });
    const body = new URLSearchParams({
      "form-name": "chevy-submissions",
      "bot-field": $("sendBot").value,
      name: $("sendName").value.trim(),
      email: $("sendEmail").value.trim(),
      message: $("sendMsg").value.trim(),
      summary: chosen.map(describe).join("\n\n----------\n\n"),
      entries: JSON.stringify(payload),
    });
    $("sendSubmit").disabled = true; $("sendSubmit").textContent = "Sending…"; $("sendErr").textContent = "";
    try {
      const res = await fetch("/", { method: "POST", headers: { "Content-Type": "application/x-www-form-urlencoded" }, body: body.toString() });
      if (!res.ok) throw new Error(res.status);
      const now = new Date().toISOString();
      TYPES.forEach(T => { data[T.key] = data[T.key].map(e => ids.includes(e.id) ? { ...e, sentAt: now } : e); });
      persistSandbox(); renderAll();
      $("sendOk").textContent = `Sent ${ids.length} entr${ids.length === 1 ? "y" : "ies"} to Maggie. Thank you! Your copies stay here on this device.`;
      $("sendOk").hidden = false; $("sendSubmit").hidden = true; $("sendCancel").textContent = "Close";
    } catch (err) {
      $("sendErr").textContent = /^\d+$/.test(err.message)
        ? `That didn't send (error ${err.message}). Maggie's site isn't accepting messages yet. Please try again later.`
        : "That didn't send. Check your connection and try again.";
      $("sendSubmit").disabled = false; $("sendSubmit").textContent = "Send";
    }
  });''')
open(dst, 'w').write(s)
print("send feature added")
