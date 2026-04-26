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
    if (!confirm('Run the pipeline now? New posts will be fetched and queued.')) return;
    btn.disabled = true;
    btn.textContent = '';
    var dot = document.createElement('span');
    dot.className = 'spinner';
    btn.appendChild(dot);
    btn.appendChild(document.createTextNode('Running…'));
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
        alert('Could not start the pipeline. Check your connection and try again.');
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
            alert('Username has to start with a letter, then letters, digits or underscores (5-32 chars)');
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
                alert(data.error || 'Could not add this source. Please try again.');
            }
        } catch (err) {
            alert('Could not reach the server. Check your connection and try again.');
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
function fadeOutCard(id) {
    var el = document.querySelector(`div[data-id="${id}"]`);
    if (!el) return;
    el.classList.add('leaving');
    setTimeout(function () { el.remove(); }, 260);
}

async function approveItem(id, btn) {
    if (!confirm('Publish this post to the channel?')) return;
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
        fadeOutCard(id);
    } catch (e) {
        alert('Could not approve this post. Please refresh the page and try again.');
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
        fadeOutCard(id);
    } catch (e) {
        alert('Could not reject this post. Please refresh the page and try again.');
        wrap.querySelectorAll('button').forEach(function (b) { b.disabled = false; });
        btn.textContent = prev;
    }
}

// nav bar: show when pipeline last ran (visible on all pages)
function updateNavLastRun() {
    var el = document.getElementById('nav-last-run');
    if (!el || !el.dataset.ts) return;
    var diff = Math.floor((Date.now() - new Date(el.dataset.ts + 'Z').getTime()) / 1000);
    var ago;
    if (diff < 60) ago = 'just now';
    else if (diff < 3600) ago = Math.floor(diff / 60) + 'm ago';
    else if (diff < 86400) ago = Math.floor(diff / 3600) + 'h ago';
    else ago = Math.floor(diff / 86400) + 'd ago';
    el.textContent = 'Last run ' + ago;
}
updateNavLastRun();
setInterval(updateNavLastRun, 60000);

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

    // "/" — jump to the filter box on whichever list page we're on
    if (e.key === '/' && !e.ctrlKey && !e.metaKey && !e.altKey) {
        var tag = (e.target.tagName || '').toLowerCase();
        if (tag === 'input' || tag === 'textarea') return;
        var box = document.getElementById('queue-search') ||
                  document.getElementById('published-search') ||
                  document.getElementById('sources-search');
        if (box) {
            e.preventDefault();
            box.focus();
            box.select();
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

// filter queue items
var queueSearch = document.getElementById('queue-search');
if (queueSearch) {
    var queueCount = document.getElementById('queue-count');
    var queueCards = document.querySelectorAll('.space-y-4 > [data-id]');
    var queueTotal = queueCards.length;

    function filterQueue() {
        var q = queueSearch.value.toLowerCase();
        var visible = 0;
        queueCards.forEach(function (card) {
            var match = !q || card.textContent.toLowerCase().includes(q);
            card.style.display = match ? '' : 'none';
            if (match) visible++;
        });
        if (queueCount) {
            queueCount.textContent = q ? visible + ' of ' + queueTotal : queueTotal + ' items';
        }
    }

    queueSearch.addEventListener('input', filterQueue);
    filterQueue();
}

// filter published posts
var searchInput = document.getElementById('published-search');
if (searchInput) {
    var countEl = document.getElementById('published-count');
    var allCards = document.querySelectorAll('.space-y-3 > details');
    var total = allCards.length;

    function updateSearchCount() {
        if (!countEl) return;
        var q = searchInput.value.toLowerCase();
        var visible = 0;
        allCards.forEach(function (el) {
            var match = !q || el.textContent.toLowerCase().includes(q);
            el.style.display = match ? '' : 'none';
            if (match) visible++;
        });
        countEl.textContent = q ? visible + ' of ' + total : total + ' posts';
    }

    searchInput.addEventListener('input', updateSearchCount);
    updateSearchCount();
}

// filter sources table
var srcSearch = document.getElementById('sources-search');
if (srcSearch) {
    var srcCount = document.getElementById('sources-count');
    var srcActiveOnly = document.getElementById('sources-active-only');
    var srcRows = document.querySelectorAll('#sources-table tbody tr');
    var srcTotal = srcRows.length;

    function filterSources() {
        var q = srcSearch.value.toLowerCase();
        var onlyActive = srcActiveOnly && srcActiveOnly.checked;
        var visible = 0;
        srcRows.forEach(function (row) {
            var text = row.children[0].textContent.toLowerCase() +
                       ' ' + row.children[1].textContent.toLowerCase();
            var match = (!q || text.includes(q)) &&
                        (!onlyActive || row.dataset.active === '1');
            row.style.display = match ? '' : 'none';
            if (match) visible++;
        });
        if (srcCount) {
            var label = onlyActive ? ' active' : ' sources';
            srcCount.textContent = (q || onlyActive)
                ? visible + ' of ' + srcTotal
                : srcTotal + label;
        }
    }

    srcSearch.addEventListener('input', filterSources);
    if (srcActiveOnly) srcActiveOnly.addEventListener('change', filterSources);
    filterSources();
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
