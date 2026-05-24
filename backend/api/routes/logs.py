from __future__ import annotations

import json
from pathlib import Path

from fastapi import APIRouter, Query
from fastapi.responses import HTMLResponse

router = APIRouter(prefix="/logs", tags=["logs"])

_PROJECT_ROOT = Path(__file__).resolve().parents[3]
_LOG_FILE = _PROJECT_ROOT / "data" / "logs" / "operations.jsonl"


def _read_logs(limit: int, offset: int, intent_filter: str | None) -> list[dict]:
    if not _LOG_FILE.exists():
        return []

    entries: list[dict] = []
    with open(_LOG_FILE, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                entry = json.loads(line)
                if intent_filter and entry.get("intent") != intent_filter:
                    continue
                entries.append(entry)
            except json.JSONDecodeError:
                continue

    entries.reverse()
    return entries[offset : offset + limit]


@router.get("", summary="操作ログ一覧 (JSON)")
async def get_logs(
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    intent: str | None = Query(None, description="Intent でフィルタ"),
) -> dict:
    entries = _read_logs(limit, offset, intent)
    return {"count": len(entries), "offset": offset, "entries": entries}


@router.get("/view", response_class=HTMLResponse, summary="操作ログ ビューア")
async def log_viewer() -> HTMLResponse:
    return HTMLResponse(_LOG_VIEWER_HTML)


_LOG_VIEWER_HTML = r"""<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>AI秘書 — 操作ログ</title>
<style>
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body { font-family: 'Segoe UI', system-ui, sans-serif; background: #0f1117; color: #e2e8f0; min-height: 100vh; }
  header { background: #1a1d2e; border-bottom: 1px solid #2d3748; padding: 16px 24px; display: flex; align-items: center; gap: 12px; }
  header h1 { font-size: 18px; font-weight: 600; color: #a78bfa; }
  header span { font-size: 13px; color: #64748b; }
  .toolbar { padding: 16px 24px; display: flex; gap: 12px; flex-wrap: wrap; background: #13151f; border-bottom: 1px solid #1e2235; }
  .toolbar input, .toolbar select { background: #1e2235; border: 1px solid #2d3748; color: #e2e8f0; padding: 8px 12px; border-radius: 6px; font-size: 13px; }
  .toolbar input { flex: 1; min-width: 200px; }
  .toolbar button { background: #7c3aed; color: #fff; border: none; padding: 8px 16px; border-radius: 6px; cursor: pointer; font-size: 13px; font-weight: 500; }
  .toolbar button:hover { background: #6d28d9; }
  .stats { padding: 12px 24px; font-size: 12px; color: #64748b; background: #13151f; }
  .table-wrap { overflow-x: auto; padding: 0 24px 24px; }
  table { width: 100%; border-collapse: collapse; font-size: 13px; margin-top: 16px; }
  th { background: #1a1d2e; color: #94a3b8; font-weight: 600; text-align: left; padding: 10px 12px; border-bottom: 2px solid #2d3748; white-space: nowrap; }
  td { padding: 10px 12px; border-bottom: 1px solid #1e2235; vertical-align: top; }
  tr:hover td { background: #1a1d2e; }
  .badge { display: inline-block; padding: 2px 8px; border-radius: 9999px; font-size: 11px; font-weight: 600; white-space: nowrap; }
  .badge-local { background: #1e3a5f; color: #60a5fa; }
  .badge-cloud { background: #2d1b4e; color: #c084fc; }
  .badge-rule { background: #1a2e1a; color: #4ade80; }
  .badge-hitl  { background: #3b1f1f; color: #f87171; }
  .badge-success { background: #1a2e1a; color: #4ade80; }
  .badge-error { background: #3b1f1f; color: #f87171; }
  .tools { color: #64748b; font-size: 11px; }
  .ts { color: #64748b; white-space: nowrap; font-size: 11px; }
  .empty { text-align: center; color: #475569; padding: 48px; font-size: 14px; }
  .loader { text-align: center; padding: 48px; color: #64748b; }
  .pager { display: flex; gap: 8px; padding: 16px 24px; }
  .pager button { background: #1e2235; border: 1px solid #2d3748; color: #e2e8f0; padding: 6px 14px; border-radius: 6px; cursor: pointer; font-size: 13px; }
  .pager button:disabled { opacity: 0.4; cursor: default; }
  .pager span { line-height: 32px; font-size: 13px; color: #64748b; }
</style>
</head>
<body>
<header>
  <h1>🗂 操作ログ</h1>
  <span id="subtitle">読み込み中...</span>
</header>
<div class="toolbar">
  <input id="search" type="text" placeholder="サマリ・セッションIDで絞り込み..." oninput="debounceFilter()">
  <select id="intent-filter" onchange="load(0)">
    <option value="">すべての Intent</option>
    <option value="chat">chat</option>
    <option value="task_add">task_add</option>
    <option value="task_list">task_list</option>
    <option value="task_update">task_update</option>
    <option value="reminder_add">reminder_add</option>
    <option value="reminder_list">reminder_list</option>
    <option value="memo_add">memo_add</option>
    <option value="memo_list">memo_list</option>
    <option value="knowledge_search">knowledge_search</option>
    <option value="schedule_check_calendar">schedule_check_calendar</option>
    <option value="briefing">briefing</option>
  </select>
  <select id="route-filter" onchange="applyFilters()">
    <option value="">すべての Route</option>
    <option value="local">local</option>
    <option value="cloud">cloud</option>
    <option value="rule_based">rule_based</option>
    <option value="hitl">hitl</option>
  </select>
  <button onclick="load(0)">更新</button>
</div>
<div class="stats" id="stats">-</div>
<div class="table-wrap">
  <div class="loader" id="loader">読み込み中...</div>
  <table id="table" style="display:none">
    <thead>
      <tr>
        <th>日時</th>
        <th>Intent</th>
        <th>Route</th>
        <th>サマリ</th>
        <th>ツール</th>
        <th>結果</th>
      </tr>
    </thead>
    <tbody id="tbody"></tbody>
  </table>
  <div class="empty" id="empty" style="display:none">ログがありません</div>
</div>
<div class="pager">
  <button id="prev" onclick="prevPage()" disabled>← 前へ</button>
  <span id="page-info"></span>
  <button id="next" onclick="nextPage()">次へ →</button>
</div>
<script>
const PER_PAGE = 50;
let offset = 0;
let allEntries = [];
let filteredEntries = [];
let debounceTimer;

async function load(newOffset = 0) {
  offset = newOffset;
  const intent = document.getElementById('intent-filter').value;
  const params = new URLSearchParams({ limit: 500, offset: 0 });
  if (intent) params.set('intent', intent);

  document.getElementById('loader').style.display = 'block';
  document.getElementById('table').style.display = 'none';
  document.getElementById('empty').style.display = 'none';

  try {
    const res = await fetch('/api/logs?' + params);
    const data = await res.json();
    allEntries = data.entries || [];
    applyFilters();
  } catch(e) {
    document.getElementById('loader').textContent = 'エラー: ' + e.message;
  }
}

function applyFilters() {
  const q = document.getElementById('search').value.toLowerCase();
  const route = document.getElementById('route-filter').value;
  filteredEntries = allEntries.filter(e => {
    if (route && e.llm_route !== route) return false;
    if (q && !JSON.stringify(e).toLowerCase().includes(q)) return false;
    return true;
  });
  renderPage(0);
}

function renderPage(page) {
  offset = page * PER_PAGE;
  const pageEntries = filteredEntries.slice(offset, offset + PER_PAGE);
  const tbody = document.getElementById('tbody');
  tbody.innerHTML = '';

  document.getElementById('loader').style.display = 'none';
  document.getElementById('subtitle').textContent = filteredEntries.length + ' 件';
  document.getElementById('stats').textContent =
    `合計 ${filteredEntries.length} 件 | ページ ${page + 1} / ${Math.max(1, Math.ceil(filteredEntries.length / PER_PAGE))}`;

  if (pageEntries.length === 0) {
    document.getElementById('empty').style.display = 'block';
    document.getElementById('table').style.display = 'none';
  } else {
    document.getElementById('table').style.display = 'table';
    document.getElementById('empty').style.display = 'none';
    for (const e of pageEntries) {
      const tr = document.createElement('tr');
      tr.innerHTML = \`
        <td class="ts">\${fmtTs(e.timestamp)}</td>
        <td><span class="badge" style="background:#1e2235;color:#e2e8f0">\${e.intent || '-'}</span></td>
        <td>\${routeBadge(e.llm_route)}</td>
        <td>\${esc(e.input_summary || '')}</td>
        <td class="tools">\${(e.tools_called || []).join('<br>')}</td>
        <td>\${resultBadge(e.result)}</td>
      \`;
      tbody.appendChild(tr);
    }
  }

  document.getElementById('prev').disabled = page === 0;
  document.getElementById('next').disabled = offset + PER_PAGE >= filteredEntries.length;
  document.getElementById('page-info').textContent =
    \`\${offset + 1}–\${Math.min(offset + PER_PAGE, filteredEntries.length)} / \${filteredEntries.length}\`;

  window._currentPage = page;
}

function prevPage() { if (window._currentPage > 0) renderPage(window._currentPage - 1); }
function nextPage() { renderPage((window._currentPage || 0) + 1); }

function fmtTs(ts) {
  if (!ts) return '-';
  const d = new Date(ts);
  return d.toLocaleString('ja-JP', { month:'2-digit', day:'2-digit', hour:'2-digit', minute:'2-digit', second:'2-digit' });
}

function routeBadge(r) {
  const cls = { local:'badge-local', cloud:'badge-cloud', rule_based:'badge-rule', hitl:'badge-hitl' }[r] || '';
  return \`<span class="badge \${cls}">\${r || '-'}</span>\`;
}

function resultBadge(r) {
  const cls = r === 'success' ? 'badge-success' : 'badge-error';
  return \`<span class="badge \${cls}">\${r || '-'}</span>\`;
}

function esc(s) {
  return s.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');
}

function debounceFilter() {
  clearTimeout(debounceTimer);
  debounceTimer = setTimeout(applyFilters, 200);
}

window._currentPage = 0;
load(0);
setInterval(() => load(window._currentPage * PER_PAGE), 30000);
</script>
</body>
</html>"""
