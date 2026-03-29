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
        const username = document.getElementById('input-username').value.trim();
        const title = document.getElementById('input-title').value.trim();
        if (!username) return;

        const data = await api('/api/sources', 'POST', { username, title });
        if (data.ok) {
            location.reload();
        } else {
            alert(data.error || 'Failed to add');
        }
    });
}

async function deleteSource(id) {
    if (!confirm('Remove this source?')) return;
    await api(`/api/sources/${id}`, 'DELETE');
    const row = document.querySelector(`tr[data-id="${id}"]`);
    if (row) row.remove();
}

async function toggleSource(id) {
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

// queue
async function approveItem(id) {
    await api(`/api/queue/${id}/approve`, 'POST');
    const el = document.querySelector(`div[data-id="${id}"]`);
    if (el) el.remove();
}

async function rejectItem(id) {
    await api(`/api/queue/${id}/reject`, 'POST');
    const el = document.querySelector(`div[data-id="${id}"]`);
    if (el) el.remove();
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

// auto-refresh stats on dashboard (every 30s)
if (document.getElementById('stat-published')) {
    showUpdatedTime();

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
