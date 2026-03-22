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

// auto-refresh stats on dashboard (every 30s)
if (document.getElementById('stat-published')) {
    setInterval(async () => {
        try {
            const s = await api('/api/stats');
            document.getElementById('stat-published').textContent = s.total_published;
            document.getElementById('stat-sources').textContent = s.total_sources;
            document.getElementById('stat-queue').textContent = s.queue_size;
            document.getElementById('stat-runs').textContent = s.total_runs;
        } catch (e) {
            // silently fail, not critical
        }
    }, 30000);
}
