// ChannelAI dashboard JS

async function api(url, method = 'GET', body = null) {
    const opts = { method, headers: { 'Content-Type': 'application/json' } };
    if (body) opts.body = JSON.stringify(body);
    const res = await fetch(url, opts);
    return res.json();
}

// dashboard - run pipeline
async function runPipeline() {
    const btn = document.getElementById('btn-run');
    if (!btn) return;
    btn.disabled = true;
    btn.textContent = 'Running...';
    btn.classList.add('opacity-50');

    try {
        const data = await api('/api/pipeline/run', 'POST');
        if (data.error) {
            alert(data.error);
        } else {
            btn.textContent = 'Started!';
            setTimeout(() => location.reload(), 3000);
        }
    } catch (e) {
        alert('Failed: ' + e.message);
    } finally {
        setTimeout(() => {
            btn.disabled = false;
            btn.textContent = 'Run Pipeline';
            btn.classList.remove('opacity-50');
        }, 5000);
    }
}

// sources
const addForm = document.getElementById('add-source-form');
if (addForm) {
    addForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        let username = document.getElementById('input-username').value.trim().replace(/^@/, '');
        const title = document.getElementById('input-title').value.trim();
        if (!username) return;
        if (!/^[a-zA-Z][a-zA-Z0-9_]{3,31}$/.test(username)) {
            alert('Invalid username — use letters, digits and underscores (5-32 chars)');
            return;
        }

        const btn = addForm.querySelector('button[type="submit"]');
        btn.disabled = true;
        var dot = document.createElement('span');
        dot.className = 'spinner';
        btn.textContent = '';
        btn.appendChild(dot);
        btn.appendChild(document.createTextNode('Adding\u2026'));
        btn.classList.add('opacity-50');

        try {
            const data = await api('/api/sources', 'POST', { username, title });
            if (data.ok) {
                location.reload();
            } else {
                alert(data.error || 'Failed to add');
            }
        } catch (err) {
            alert('Network error: ' + err.message);
        } finally {
            btn.disabled = false;
            btn.textContent = 'Add Source';
            btn.classList.remove('opacity-50');
        }
    });
}

async function deleteSource(id) {
    if (!confirm('Remove this source?')) return;
    await api(`/api/sources/${id}`, 'DELETE');
    const row = document.querySelector(`tr[data-id="${id}"]`);
    if (row) row.remove();
}

async function toggleSource(id, isActive) {
    const action = isActive ? 'Pause this source?' : 'Resume this source?';
    if (!confirm(action)) return;
    await api(`/api/sources/${id}/toggle`, 'POST');
    location.reload();
}

// copy text to clipboard
function copyText(btn) {
    const block = btn.closest('.relative').querySelector('.post-text');
    if (!block) return;
    navigator.clipboard.writeText(block.textContent.trim()).then(() => {
        btn.textContent = 'Copied!';
        setTimeout(() => { btn.textContent = 'Copy'; }, 1500);
    });
}

function copyValue(text, btn) {
    navigator.clipboard.writeText(text).then(() => {
        var prev = btn.textContent;
        btn.textContent = 'Copied!';
        setTimeout(() => { btn.textContent = prev; }, 1200);
    });
}

// queue
async function approveItem(id, btn) {
    var wrap = btn.parentElement;
    wrap.querySelectorAll('button').forEach(function (b) { b.disabled = true; });
    var prev = btn.textContent;
    btn.textContent = '';
    var dot = document.createElement('span');
    dot.className = 'spinner';
    btn.appendChild(dot);
    btn.appendChild(document.createTextNode('Approving\u2026'));

    try {
        await api(`/api/queue/${id}/approve`, 'POST');
        var el = document.querySelector(`div[data-id="${id}"]`);
        if (el) el.remove();
    } catch (e) {
        alert('Could not approve: ' + e.message);
        wrap.querySelectorAll('button').forEach(function (b) { b.disabled = false; });
        btn.textContent = prev;
    }
}

async function rejectItem(id, btn) {
    if (!confirm('Reject this post? It will be discarded.')) return;
    var wrap = btn.parentElement;
    wrap.querySelectorAll('button').forEach(function (b) { b.disabled = true; });
    var prev = btn.textContent;
    btn.textContent = '';
    var dot = document.createElement('span');
    dot.className = 'spinner';
    btn.appendChild(dot);
    btn.appendChild(document.createTextNode('Rejecting\u2026'));

    try {
        await api(`/api/queue/${id}/reject`, 'POST');
        var el = document.querySelector(`div[data-id="${id}"]`);
        if (el) el.remove();
    } catch (e) {
        alert('Could not reject: ' + e.message);
        wrap.querySelectorAll('button').forEach(function (b) { b.disabled = false; });
        btn.textContent = prev;
    }
}

// show relative time for last pipeline run
function updateLastRunAgo(ts) {
    var el = document.getElementById('last-run-ago');
    if (!el) return;
    if (ts) el.dataset.ts = ts;
    var started = el.dataset.ts;
    if (!started) return;
    var diff = Math.floor((Date.now() - new Date(started + 'Z').getTime()) / 1000);
    if (diff < 60) el.textContent = 'Last: just now';
    else if (diff < 3600) el.textContent = 'Last: ' + Math.floor(diff / 60) + 'm ago';
    else if (diff < 86400) el.textContent = 'Last: ' + Math.floor(diff / 3600) + 'h ago';
    else el.textContent = 'Last: ' + Math.floor(diff / 86400) + 'd ago';
}

// show last-updated timestamp
function showUpdatedTime() {
    const el = document.getElementById('last-updated');
    if (!el) return;
    const now = new Date();
    const hh = String(now.getHours()).padStart(2, '0');
    const mm = String(now.getMinutes()).padStart(2, '0');
    const ss = String(now.getSeconds()).padStart(2, '0');
    el.textContent = 'Updated at ' + hh + ':' + mm + ':' + ss;
}

// keyboard shortcuts
document.addEventListener('keydown', function (e) {
    // Ctrl+S on settings page — submit the form
    if ((e.ctrlKey || e.metaKey) && e.key === 's') {
        var form = document.querySelector('form[action="/settings"]');
        if (form) {
            e.preventDefault();
            form.submit();
        }
    }

    // Escape — collapse open details panels (queue page)
    if (e.key === 'Escape') {
        document.querySelectorAll('details[open]').forEach(function (d) {
            d.removeAttribute('open');
        });
    }

    // Ctrl+R on dashboard — run pipeline instead of reloading the page
    if ((e.ctrlKey || e.metaKey) && e.key === 'r') {
        var runBtn = document.getElementById('btn-run');
        if (runBtn && !runBtn.disabled) {
            e.preventDefault();
            runPipeline();
        }
    }
});

// queue auto-refresh (reload page every 45s)
var queueToggle = document.getElementById('queue-auto-refresh');
if (queueToggle) {
    var queueTimer = null;

    function startQueueRefresh() {
        queueTimer = setInterval(function () { location.reload(); }, 45000);
    }

    if (localStorage.getItem('queueAutoRefresh') === 'on') {
        queueToggle.checked = true;
        startQueueRefresh();
    }

    queueToggle.addEventListener('change', function () {
        if (this.checked) {
            localStorage.setItem('queueAutoRefresh', 'on');
            startQueueRefresh();
        } else {
            localStorage.setItem('queueAutoRefresh', 'off');
            clearInterval(queueTimer);
            queueTimer = null;
        }
    });
}

// filter published posts
var searchInput = document.getElementById('published-search');
if (searchInput) {
    searchInput.addEventListener('input', function () {
        var q = this.value.toLowerCase();
        document.querySelectorAll('.space-y-3 > details').forEach(function (el) {
            var text = el.textContent.toLowerCase();
            el.style.display = text.includes(q) ? '' : 'none';
        });
    });
}

// auto-refresh stats on dashboard (every 30s)
if (document.getElementById('stat-published')) {
    showUpdatedTime();
    updateLastRunAgo();

    var refreshTimer = null;
    var toggleBox = document.getElementById('auto-refresh-toggle');

    function refreshStats() {
        refreshTimer = setInterval(async () => {
            try {
                const s = await api('/api/stats');
                document.getElementById('stat-published').textContent = s.total_published;
                document.getElementById('stat-sources').textContent = s.total_sources;
                document.getElementById('stat-queue').textContent = s.queue_size;
                document.getElementById('stat-runs').textContent = s.total_runs;
                showUpdatedTime();
                var lr = s.last_run;
                updateLastRunAgo(lr ? lr.started_at : null);
            } catch (e) {}
        }, 30000);
    }

    if (localStorage.getItem('autoRefresh') === 'off') {
        toggleBox.checked = false;
    } else {
        refreshStats();
    }

    toggleBox.addEventListener('change', function () {
        if (this.checked) {
            localStorage.setItem('autoRefresh', 'on');
            refreshStats();
        } else {
            localStorage.setItem('autoRefresh', 'off');
            clearInterval(refreshTimer);
            refreshTimer = null;
        }
    });
}
