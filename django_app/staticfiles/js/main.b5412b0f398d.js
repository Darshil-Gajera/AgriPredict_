/**
 * main.js — AgriPredict  (v2.0)
 * Global utilities: dark mode, toast, chatbot bridge.
 * The merit calculator logic lives in merit_calculator.js.
 */

// ── Dark mode ─────────────────────────────────────────────────────────────────
(function initTheme() {
    const html        = document.documentElement;
    const themeToggle = document.getElementById('themeToggle');
    const themeIcon   = document.getElementById('themeIcon');

    function applyTheme(theme) {
        html.setAttribute('data-bs-theme', theme);
        if (themeIcon) {
            themeIcon.className = theme === 'dark' ? 'bi bi-sun-fill' : 'bi bi-moon-fill';
        }
        localStorage.setItem('theme', theme);
    }

    const saved = localStorage.getItem('theme') ||
        (window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light');
    applyTheme(saved);

    if (themeToggle) {
        themeToggle.addEventListener('click', () => {
            applyTheme(html.getAttribute('data-bs-theme') === 'dark' ? 'light' : 'dark');
        });
    }
})();

// ── Utilities ─────────────────────────────────────────────────────────────────
function getCookie(name) {
    const v = `; ${document.cookie}`;
    const parts = v.split(`; ${name}=`);
    if (parts.length === 2) return parts.pop().split(';').shift();
    return '';
}

function showToast(msg, type = 'info') {
    const toast = document.createElement('div');
    toast.className = `toast align-items-center text-bg-${type} border-0 show position-fixed bottom-0 start-50 translate-middle-x mb-4`;
    toast.style.zIndex = 9999;
    toast.innerHTML = `
        <div class="d-flex">
            <div class="toast-body">${msg}</div>
            <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
        </div>`;
    document.body.appendChild(toast);
    setTimeout(() => toast.remove(), 3500);
}

// Expose globally so templates can call them
window.getCookie  = getCookie;
window.showToast  = showToast;

// ── Chatbot bridge ────────────────────────────────────────────────────────────
// After a successful merit calculation (in merit_calculator.js),
// window._meritContext is set. The chatbot widget reads this to
// personalise answers automatically.
//
// If you want to pre-populate the chatbot from the server side
// (e.g. user visits their profile page), inject it like:
//   <script>window._meritContext = { category:"1", merit:78.5, student_category:"GENERAL" };</script>

// ── Legacy calcForm handler (kept for pages that still use the old form) ──────
(function legacyCalcForm() {
    const calcForm   = document.getElementById('meritForm');
    const resultArea = document.getElementById('resultArea');
    if (!calcForm) return;  // Not on a calculator page — skip

    calcForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const btn = calcForm.querySelector('[type="submit"]');
        btn.disabled = true;
        btn.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Calculating…';

        const fd = new FormData(calcForm);
        const payload = {
            category:           fd.get('category'),
            theory_obtained:    parseFloat(fd.get('theory_obtained'))   || 0,
            theory_total:       parseInt(fd.get('theory_total'))         || 300,
            gujcet_marks:       parseFloat(fd.get('gujcet_marks'))      || 0,
            student_category:   fd.get('student_category')              || 'OPEN',
            farming_background: fd.get('farming_background') === 'on',
            subject_group:      fd.get('subject_group') || '',
            city:               fd.get('city')          || '',
            district:           fd.get('district')      || '',
        };

        try {
            const res = await fetch('/api/predict/calculate/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCookie('csrftoken'),
                },
                body: JSON.stringify(payload),
            });

            const data = await res.json();

            if (!res.ok || data.error) {
                throw new Error(data.error || data.details || `HTTP ${res.status}`);
            }

            // Store for chatbot
            window._meritContext = {
                category:         payload.category,
                merit:            data.merit,
                student_category: payload.student_category,
            };

            // Store for legacy save
            window.__legacyPayload = payload;
            window.__legacyMerit   = data.merit;

            renderLegacyResults(data, payload);

        } catch (err) {
            if (resultArea) {
                resultArea.innerHTML = `<div class="alert alert-danger">${escHtml(err.message)}</div>`;
                resultArea.classList.remove('d-none');
            }
        } finally {
            btn.disabled = false;
            btn.innerHTML = 'Calculate Merit';
        }
    });

    function escHtml(str) {
        return String(str || '')
            .replace(/&/g, '&amp;').replace(/</g, '&lt;')
            .replace(/>/g, '&gt;').replace(/"/g, '&quot;');
    }

    function renderLegacyResults(data, payload) {
        if (!resultArea) return;

        const ORDER = { high: 0, medium: 1, low: 2, unlikely: 3, unknown: 4 };
        const colleges = [...(data.colleges || [])].sort((a, b) =>
            (ORDER[a.probability] ?? 4) - (ORDER[b.probability] ?? 4)
        );
        window._collegeData = colleges;

        const isAuth = (typeof window._userLoggedIn !== 'undefined') ? window._userLoggedIn : false;
        const saveBtn = isAuth
            ? `<button class="btn btn-outline-success btn-sm mb-3" id="legacySaveBtn">
                   <i class="bi bi-bookmark-plus me-1"></i>Save Result
               </button>`
            : '';

        resultArea.innerHTML = `
            <div class="text-center mb-4">
                <div class="merit-score-display">${data.merit?.toFixed ? data.merit.toFixed(4) : data.merit}</div>
                <small class="text-muted">
                    Theory: ${(data.theory_component ?? data.theory_comp ?? 0).toFixed ? (data.theory_component ?? data.theory_comp ?? 0).toFixed(4) : '—'}
                    + GUJCET: ${(data.gujcet_component ?? data.gujcet_comp ?? 0).toFixed ? (data.gujcet_component ?? data.gujcet_comp ?? 0).toFixed(4) : '—'}
                    ${data.farming_bonus_applied ? ' + Farming Bonus' : ''}
                </small>
            </div>
            ${saveBtn}
            <div class="d-flex flex-wrap gap-2 align-items-center mb-3">
                <input type="text" id="collegeSearch" class="form-control form-control-sm w-auto flex-grow-1"
                       placeholder="Search college…" oninput="filterLegacyColleges()" />
                <select id="sortSelect" class="form-select form-select-sm w-auto" onchange="sortLegacyColleges()">
                    <option value="prob">Sort by Probability</option>
                    <option value="merit">Sort by Cutoff (high→low)</option>
                    <option value="college">Sort by College Name</option>
                </select>
            </div>
            <div id="collegeList">${buildLegacyCards(colleges)}</div>`;

        resultArea.classList.remove('d-none');
        resultArea.scrollIntoView({ behavior: 'smooth', block: 'start' });

        // Attach save handler
        document.getElementById('legacySaveBtn')?.addEventListener('click', legacySave);
    }

    function buildLegacyCards(colleges) {
        if (!colleges.length) return '<p class="text-muted">No colleges found for your selection.</p>';
        const PROB_LABEL = { high: 'High Chance', medium: 'Medium', low: 'Low', unlikely: 'Unlikely', unknown: '—' };
        const PROB_COLOR = { high: 'success', medium: 'warning', low: 'danger', unlikely: 'secondary', unknown: 'light' };

        return colleges.map(c => {
            const prob = c.probability || 'unknown';
            const cutoff = c.last_cutoff ?? c.cutoff;
            return `
            <div class="card college-card mb-2 p-3"
                 data-name="${escHtml((c.college_name || '').toLowerCase())}"
                 data-merit="${cutoff || 0}">
                <div class="d-flex justify-content-between align-items-start flex-wrap gap-2">
                    <div>
                        <strong>${escHtml(c.college_name || c.name || '—')}</strong>
                        <div class="text-muted small">
                            ${escHtml(c.university || '')}
                            ${c.city ? '&bull; ' + escHtml(c.city) : ''}
                        </div>
                        <div class="text-muted small">
                            Code: ${escHtml(c.college_code || '—')} &bull; ${escHtml(c.course_name || c.course || '—')}
                        </div>
                    </div>
                    <div class="text-end">
                        <span class="badge bg-${PROB_COLOR[prob]}${prob === 'medium' ? ' text-dark' : ''}">
                            ${PROB_LABEL[prob] || prob}
                        </span>
                        <div class="text-muted small mt-1">
                            ${cutoff != null ? `Last cutoff: ${parseFloat(cutoff).toFixed(4)} (${c.cutoff_year || '—'})` : 'No cutoff data'}
                        </div>
                    </div>
                </div>
            </div>`;
        }).join('');
    }

    window.filterLegacyColleges = function () {
        const q = document.getElementById('collegeSearch')?.value.toLowerCase() || '';
        const filtered = (window._collegeData || []).filter(c =>
            (c.college_name || '').toLowerCase().includes(q) ||
            (c.city         || '').toLowerCase().includes(q) ||
            (c.course_name  || '').toLowerCase().includes(q)
        );
        document.getElementById('collegeList').innerHTML = buildLegacyCards(filtered);
    };

    window.sortLegacyColleges = function () {
        const mode   = document.getElementById('sortSelect')?.value || 'prob';
        const ORDER  = { high: 0, medium: 1, low: 2, unlikely: 3, unknown: 4 };
        const sorted = [...(window._collegeData || [])].sort((a, b) => {
            if (mode === 'merit')   return (b.last_cutoff ?? b.cutoff ?? 0) - (a.last_cutoff ?? a.cutoff ?? 0);
            if (mode === 'college') return (a.college_name || '').localeCompare(b.college_name || '');
            return (ORDER[a.probability] ?? 4) - (ORDER[b.probability] ?? 4);
        });
        document.getElementById('collegeList').innerHTML = buildLegacyCards(sorted);
    };

    async function legacySave() {
        const merit   = window.__legacyMerit;
        const payload = window.__legacyPayload;
        if (!merit || !payload) {
            showToast('Please calculate first.', 'warning'); return;
        }
        const btn = document.getElementById('legacySaveBtn');
        if (btn) { btn.disabled = true; btn.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Saving…'; }

        try {
            const resp = await fetch('/api/predict/save/', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json', 'X-CSRFToken': getCookie('csrftoken') },
                body: JSON.stringify({ ...payload, merit }),
            });
            const data = await resp.json();
            if (data.saved) {
                showToast('Result saved to your profile!', 'success');
                if (btn) { btn.innerHTML = '<i class="bi bi-bookmark-check-fill me-1"></i>Saved!'; btn.classList.replace('btn-outline-success', 'btn-success'); }
            } else {
                throw new Error(data.error || 'Save failed');
            }
        } catch (e) {
            showToast('Save failed: ' + e.message, 'danger');
            if (btn) { btn.disabled = false; btn.innerHTML = '<i class="bi bi-bookmark-plus me-1"></i>Save Result'; }
        }
    }
})();