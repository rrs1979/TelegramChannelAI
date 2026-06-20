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
const titleInput = document.getElementById('input-title');
const titleCount = document.getElementById('input-title-count');
if (titleInput && titleCount) {
    const cap = titleInput.maxLength;
    const update = () => {
        const n = titleInput.value.length;
        titleCount.textContent = n ? `${n}/${cap}` : '';
        titleCount.classList.toggle('text-yellow-500', n > cap - 16);
    };
    titleInput.addEventListener('input', update);
    update();
}

const usernameInput = document.getElementById('input-username');
const usernameCount = document.getElementById('input-username-count');
if (usernameInput && usernameCount) {
    const cap = usernameInput.maxLength;
    const min = usernameInput.minLength;
    const update = () => {
        const n = usernameInput.value.length;
        usernameCount.textContent = n ? `${n}/${cap}` : '';
        usernameCount.classList.toggle('text-yellow-500', n > 0 && n < min);
    };
    usernameInput.addEventListener('input', update);
    update();
}

const addForm = document.getElementById('add-source-form');
if (addForm) {
    addForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        let username = document.getElementById('input-username').value.trim().replace(/^@/, '');
        const title = document.getElementById('input-title').value.trim();
        if (!username) return;
        if (!/^[A-Za-z][A-Za-z0-9_]{3,30}$/.test(username)) {
            alert("That's not a valid Telegram handle. Use 4-31 letters, digits, or underscores, starting with a letter.");
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

async function deleteSource(id, btn) {
    if (!confirm('Remove this source?')) return;
    var prev = btn.textContent;
    btn.disabled = true;
    btn.textContent = '';
    var dot = document.createElement('span');
    dot.className = 'spinner';
    btn.appendChild(dot);
    btn.appendChild(document.createTextNode('removing…'));
    btn.classList.add('opacity-50');
    try {
        await api(`/api/sources/${id}`, 'DELETE');
        const row = document.querySelector(`tr[data-id="${id}"]`);
        if (row) {
            row.classList.add('leaving');
            setTimeout(function () { row.remove(); }, 260);
        }
    } catch (e) {
        alert('Could not remove this source. Please try again.');
        btn.disabled = false;
        btn.textContent = prev;
        btn.classList.remove('opacity-50');
    }
}

async function toggleSource(id, isActive, btn) {
    const action = isActive ? 'Pause this source?' : 'Resume this source?';
    if (!confirm(action)) return;
    btn.disabled = true;
    btn.textContent = '';
    var dot = document.createElement('span');
    dot.className = 'spinner';
    btn.appendChild(dot);
    btn.appendChild(document.createTextNode('saving…'));
    btn.classList.add('opacity-50');
    try {
        await api(`/api/sources/${id}/toggle`, 'POST');
        location.reload();
    } catch (e) {
        alert('Could not update this source. Please try again.');
        btn.disabled = false;
        btn.textContent = 'toggle';
        btn.classList.remove('opacity-50');
    }
}

// copy text to clipboard
function copyText(btn) {
    const block = btn.closest('.relative').querySelector('.post-text');
    if (!block) return;
    navigator.clipboard.writeText(block.textContent.trim()).then(() => {
        btn.textContent = 'Copied!';
        popButton(btn);
        setTimeout(() => { btn.textContent = 'Copy'; }, 1500);
    });
}

function copyValue(text, btn) {
    navigator.clipboard.writeText(text).then(() => {
        var prev = btn.textContent;
        btn.textContent = 'Copied!';
        popButton(btn);
        setTimeout(() => { btn.textContent = prev; }, 1200);
    });
}

// replay the copy-pop animation; the reflow lets it restart on a quick re-copy
function popButton(btn) {
    btn.classList.remove('copied');
    void btn.offsetWidth;
    btn.classList.add('copied');
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
    // server timestamps come over naive (no tz) — tack on 'Z' so the browser
    // reads them as UTC instead of assuming the viewer's local zone
    var d = new Date(el.dataset.ts + 'Z');
    var diff = Math.floor((Date.now() - d.getTime()) / 1000);
    var ago;
    if (diff < 60) ago = 'just now';
    else if (diff < 3600) ago = Math.floor(diff / 60) + 'm ago';
    else if (diff < 86400) ago = Math.floor(diff / 3600) + 'h ago';
    else ago = Math.floor(diff / 86400) + 'd ago';
    el.textContent = 'Last run ' + ago;
    el.title = d.toLocaleString();
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
    var d = new Date(started + 'Z');
    var diff = Math.floor((Date.now() - d.getTime()) / 1000);
    if (diff < 60) el.textContent = 'Last: just now';
    else if (diff < 3600) el.textContent = 'Last: ' + Math.floor(diff / 60) + 'm ago';
    else if (diff < 86400) el.textContent = 'Last: ' + Math.floor(diff / 3600) + 'h ago';
    else el.textContent = 'Last: ' + Math.floor(diff / 86400) + 'd ago';
    el.title = d.toLocaleString();
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

// a little "?" cheatsheet so the shortcuts below are actually discoverable
function toggleShortcuts() {
    var open = document.getElementById('shortcuts-overlay');
    if (open) { open.remove(); return; }
    var rows = [
        ['?', 'show this help'],
        ['/', 'jump to the filter box'],
        ['n', 'new source (sources page)'],
        ['e', 'expand every panel'],
        ['Esc', 'clear filter / collapse panels'],
        ['Ctrl+R', 'run the pipeline (dashboard)'],
        ['Ctrl+S', 'save settings'],
    ].map(function (r) {
        return '<div class="flex justify-between gap-6 py-1">' +
            '<kbd class="px-1.5 py-0.5 rounded bg-dark-700 text-gray-200 text-xs">' + r[0] + '</kbd>' +
            '<span class="text-gray-400 text-sm">' + r[1] + '</span></div>';
    }).join('');
    var box = document.createElement('div');
    box.id = 'shortcuts-overlay';
    box.className = 'fixed inset-0 z-50 flex items-center justify-center bg-black/50';
    box.innerHTML = '<div class="card max-w-xs w-full mx-4">' +
        '<div class="font-semibold mb-2 text-white">Keyboard shortcuts</div>' + rows + '</div>';
    box.addEventListener('click', function () { box.remove(); });
    document.body.appendChild(box);
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

    // Escape — close the shortcuts overlay first, then search box, then panels
    if (e.key === 'Escape') {
        var overlay = document.getElementById('shortcuts-overlay');
        if (overlay) { overlay.remove(); return; }
        var active = document.activeElement;
        var searchBoxes = ['queue-search', 'published-search', 'sources-search'];
        if (active && searchBoxes.indexOf(active.id) !== -1 && active.value) {
            active.value = '';
            active.dispatchEvent(new Event('input'));
            return;
        }
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

    // "?" — toggle the keyboard shortcuts cheatsheet
    if (e.key === '?') {
        var qt = (e.target.tagName || '').toLowerCase();
        if (qt === 'input' || qt === 'textarea') return;
        e.preventDefault();
        toggleShortcuts();
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

    // "n" — jump to the add-source field on the sources page
    if (e.key === 'n' && !e.ctrlKey && !e.metaKey && !e.altKey) {
        var tag2 = (e.target.tagName || '').toLowerCase();
        if (tag2 === 'input' || tag2 === 'textarea') return;
        var newSrc = document.getElementById('input-username');
        if (newSrc) {
            e.preventDefault();
            newSrc.focus();
        }
    }

    // "e" — expand every details panel at once (Escape already collapses them)
    if (e.key === 'e' && !e.ctrlKey && !e.metaKey && !e.altKey) {
        var t = (e.target.tagName || '').toLowerCase();
        if (t === 'input' || t === 'textarea') return;
        var panels = document.querySelectorAll('details:not([open])');
        if (panels.length) {
            e.preventDefault();
            panels.forEach(function (d) { d.setAttribute('open', ''); });
        }
    }
});

// queue/published/analytics/sources all wire a checkbox to a full-page reload
// timer the same way — only the storage key and cadence differ
function wireReloadRefresh(toggleId, storageKey, intervalMs) {
    var toggle = document.getElementById(toggleId);
    if (!toggle) return;
    var timer = null;

    function start() {
        timer = setInterval(function () { if (!document.hidden) location.reload(); }, intervalMs);
    }

    if (localStorage.getItem(storageKey) === 'on') {
        toggle.checked = true;
        start();
    }

    toggle.addEventListener('change', function () {
        if (this.checked) {
            localStorage.setItem(storageKey, 'on');
            start();
        } else {
            localStorage.setItem(storageKey, 'off');
            clearInterval(timer);
            timer = null;
        }
    });
}

// queue reloads every 45s
wireReloadRefresh('queue-auto-refresh', 'queueAutoRefresh', 45000);

// filter queue items
var queueSearch = document.getElementById('queue-search');
if (queueSearch) {
    var queueCount = document.getElementById('queue-count');
    var queueSource = document.getElementById('queue-source');
    var queueRange = document.getElementById('queue-range');
    var queueCards = document.querySelectorAll('.space-y-4 > [data-id]');
    var queueNoMatch = document.getElementById('queue-no-match');
    var queueTotal = queueCards.length;

    function filterQueue() {
        var q = queueSearch.value.toLowerCase();
        var src = queueSource ? queueSource.value : '';
        var range = queueRange ? queueRange.value : '';
        var minDate = '';
        if (range) {
            var d = new Date();
            d.setDate(d.getDate() - parseInt(range, 10));
            minDate = d.toISOString().slice(0, 10);
        }
        var visible = 0;
        queueCards.forEach(function (card) {
            var textMatch = !q || card.textContent.toLowerCase().includes(q);
            var srcMatch = !src || card.dataset.source === src;
            var dateMatch = !minDate || (card.dataset.date && card.dataset.date >= minDate);
            var match = textMatch && srcMatch && dateMatch;
            card.style.display = match ? '' : 'none';
            if (match) visible++;
        });
        if (queueCount) {
            queueCount.textContent = (q || src || range) ? visible + ' of ' + queueTotal : queueTotal + ' items';
        }
        if (queueNoMatch) {
            queueNoMatch.classList.toggle('hidden', visible > 0 || (!q && !src && !range));
        }
    }

    queueSearch.addEventListener('input', filterQueue);
    if (queueSource) queueSource.addEventListener('change', filterQueue);
    if (queueRange) queueRange.addEventListener('change', filterQueue);
    filterQueue();
}

// published every 60s — slower than queue, archive moves less
wireReloadRefresh('published-auto-refresh', 'publishedAutoRefresh', 60000);

// analytics every 120s — daily rollup only ticks when a run completes,
// no point reloading as often as queue/published
wireReloadRefresh('analytics-auto-refresh', 'analyticsAutoRefresh', 120000);

// filter published posts
var searchInput = document.getElementById('published-search');
if (searchInput) {
    var countEl = document.getElementById('published-count');
    var sourceSel = document.getElementById('published-source');
    var rangeSel = document.getElementById('published-range');
    var allCards = document.querySelectorAll('.space-y-3 > details');
    var noMatch = document.getElementById('published-no-match');
    var total = allCards.length;

    function updateSearchCount() {
        var q = searchInput.value.toLowerCase();
        var src = sourceSel ? sourceSel.value : '';
        var range = rangeSel ? rangeSel.value : '';
        var minDate = '';
        if (range) {
            var d = new Date();
            d.setDate(d.getDate() - parseInt(range, 10));
            minDate = d.toISOString().slice(0, 10);
        }
        var visible = 0;
        allCards.forEach(function (el) {
            var textMatch = !q || el.textContent.toLowerCase().includes(q);
            var srcMatch = !src || el.dataset.source === src;
            var dateMatch = !minDate || (el.dataset.date && el.dataset.date >= minDate);
            var match = textMatch && srcMatch && dateMatch;
            el.style.display = match ? '' : 'none';
            if (match) visible++;
        });
        if (countEl) {
            countEl.textContent = (q || src || range) ? visible + ' of ' + total : total + ' posts';
        }
        if (noMatch) {
            noMatch.classList.toggle('hidden', visible > 0 || (!q && !src && !range));
        }
    }

    searchInput.addEventListener('input', updateSearchCount);
    if (sourceSel) sourceSel.addEventListener('change', updateSearchCount);
    if (rangeSel) rangeSel.addEventListener('change', updateSearchCount);
    updateSearchCount();
}

// sources every 90s — subscriber counts only tick when the pipeline scans
// channels, which is slower than queue/published activity
wireReloadRefresh('sources-auto-refresh', 'sourcesAutoRefresh', 90000);

// filter sources table
var srcSearch = document.getElementById('sources-search');
if (srcSearch) {
    var srcCount = document.getElementById('sources-count');
    var srcActiveOnly = document.getElementById('sources-active-only');
    var srcRows = document.querySelectorAll('#sources-table tbody tr');
    var srcNoMatch = document.getElementById('sources-no-match');
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
        if (srcNoMatch) {
            srcNoMatch.classList.toggle('hidden', visible > 0 || (!q && !onlyActive));
        }
    }

    var srcSort = document.getElementById('sources-sort');
    function sortSources() {
        var mode = srcSort ? srcSort.value : '';
        var tbody = document.querySelector('#sources-table tbody');
        if (!tbody) return;
        var rows = Array.prototype.slice.call(srcRows);
        if (mode === 'subs') {
            rows.sort(function (a, b) {
                return (parseInt(b.children[2].textContent, 10) || 0) -
                       (parseInt(a.children[2].textContent, 10) || 0);
            });
        } else if (mode === 'name') {
            rows.sort(function (a, b) {
                return a.querySelector('a').textContent.trim()
                    .localeCompare(b.querySelector('a').textContent.trim());
            });
        } else if (mode === 'added') {
            rows.sort(function (a, b) {
                return b.children[3].textContent.localeCompare(a.children[3].textContent);
            });
        }
        // empty mode falls through and re-appends in the original srcRows order
        rows.forEach(function (r) { tbody.appendChild(r); });
    }

    srcSearch.addEventListener('input', filterSources);
    if (srcActiveOnly) srcActiveOnly.addEventListener('change', filterSources);
    if (srcSort) srcSort.addEventListener('change', sortSources);
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
            if (document.hidden) return;
            var stamp = document.getElementById('last-updated');
            var prev = stamp ? stamp.textContent : '';
            if (stamp) stamp.textContent = 'Updating…';
            try {
                const s = await api('/api/stats');
                document.getElementById('stat-published').textContent = s.total_published;
                document.getElementById('stat-sources').textContent = s.total_sources;
                document.getElementById('stat-queue').textContent = s.queue_size;
                document.getElementById('stat-runs').textContent = s.total_runs;
                showUpdatedTime();
                var lr = s.last_run;
                updateLastRunAgo(lr ? lr.started_at : null);
            } catch (e) {
                // poll failed — drop the "Updating…" hint so it doesn't get stuck
                if (stamp) stamp.textContent = prev;
            }
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
