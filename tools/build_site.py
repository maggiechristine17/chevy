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
r('''<span class="title-text">${esc(e.title || "Untitled")}</span></span>`;''',
  '''<span class="title-text">${esc(e.title || "Untitled")}</span>${e._pub ? "" : '<span class="mine-tag">Yours</span>'}</span>`;''')
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
  let sandbox = { projects: [], pages: [] };
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
