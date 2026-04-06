/**
 * merit_calculator.js  — AgriPredict  (unified v5.0)
 *
 * Works for ALL 3 categories.
 * Drop this file in BOTH locations:
 *   agripredict/static/js/merit_calculator.js
 *   predict/static/js/merit_calculator.js
 *
 * Required globals injected by Django template before this script:
 *   const CATEGORY = "1";          // "1" | "2" | "3"
 *   const CSRF     = "...token...";
 *   const IS_AUTH  = true;         // boolean
 */

console.log("✅ merit_calculator.js v5.0 loaded — category:", typeof CATEGORY !== 'undefined' ? CATEGORY : 'unknown');

// ─── Module-level state ──────────────────────────────────────────────────────
let allColleges   = [];
let _lastPayload  = null;   // full payload sent to /api/predict/calculate/
let _lastMerit    = null;   // numeric merit score from last successful calc

// ─── DOM shorthand ───────────────────────────────────────────────────────────
const $ = (id) => document.getElementById(id);

// ─── Bootstrap entry point ───────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
    $('calculateBtn')?.addEventListener('click', doCalculate);
    $('resetBtn')?.addEventListener('click', doReset);
    $('saveResultBtn')?.addEventListener('click', doSave);

    ['filterCity', 'filterCourse', 'sortBy'].forEach(id =>
        $(id)?.addEventListener('change', renderTable)
    );
});

// ─── Helpers ─────────────────────────────────────────────────────────────────
function getVal(id) {
    const el = $(id);
    return el ? el.value.trim() : '';
}
function getChecked(id) {
    const el = $(id);
    return el ? el.checked : false;
}
function getCsrf() {
    // Prefer the inline global, fall back to cookie
    if (typeof CSRF !== 'undefined' && CSRF) return CSRF;
    const v = document.cookie.match('(^|;)\\s*csrftoken\\s*=\\s*([^;]+)');
    return v ? v.pop() : '';
}
function escHtml(str) {
    if (str === null || str === undefined) return '—';
    return String(str)
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;');
}
function showAlert(msg, type = 'danger') {
    const box = $('formAlert');
    if (box) {
        box.innerHTML = `
            <div class="alert alert-${type} alert-dismissible fade show mb-0" role="alert">
                ${msg}
                <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
            </div>`;
    }
}
function clearAlert() {
    const box = $('formAlert');
    if (box) box.innerHTML = '';
}
function setLoading(on) {
    const btn = $('calculateBtn');
    if (!btn) return;
    btn.disabled = on;
    btn.innerHTML = on
        ? '<span class="spinner-border spinner-border-sm me-2"></span>Calculating…'
        : '<i class="bi bi-calculator me-2"></i>Calculate Merit';
}

// ─── Probability badge HTML ───────────────────────────────────────────────────
const PROB_BADGE = {
    high:     '<span class="badge bg-success">High Chance</span>',
    medium:   '<span class="badge bg-warning text-dark">Medium</span>',
    low:      '<span class="badge bg-danger">Low</span>',
    unlikely: '<span class="badge bg-secondary">Unlikely</span>',
    unknown:  '<span class="badge bg-light text-muted border">—</span>',
};

// ─── CALCULATE ────────────────────────────────────────────────────────────────
async function doCalculate() {
    clearAlert();

    // Build payload — use the correct backend key names every time
    const category = (typeof CATEGORY !== 'undefined') ? CATEGORY : '1';
    const payload = {
        category,
        theory_obtained:    parseFloat(getVal('theoryObtained')) || 0,
        theory_total:       parseInt(getVal('theoryTotal'))       || 300,
        gujcet_marks:       parseFloat(getVal('gujcetMarks'))     || 0,
        student_category:   getVal('studentCategory')             || 'OPEN',
        farming_background: getChecked('farmingBonus'),
        subject_group:      getVal('subjectGroup')                || '',
        city:               getVal('cityInput')                   || '',
    };

    console.log('📤 Calculate payload:', payload);

    // Validation
    if (!payload.theory_obtained) {
        showAlert('Please enter Theory Marks Obtained.', 'warning'); return;
    }
    if (!payload.gujcet_marks) {
        showAlert('Please enter GUJCET Marks.', 'warning'); return;
    }

    setLoading(true);

    try {
        const resp = await fetch('/api/predict/calculate/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCsrf(),
            },
            body: JSON.stringify(payload),
        });

        const data = await resp.json();
        console.log('📥 Calculate response:', data);

        if (!resp.ok || data.error) {
            throw new Error(data.details || data.error || `HTTP ${resp.status}`);
        }

        // ── Persist for save button ──────────────────────────────────────────
        _lastPayload = payload;
        _lastMerit   = typeof data.merit === 'number' ? data.merit : parseFloat(data.merit);

        // Also expose on window for chatbot integration
        window._meritContext = {
            category:         payload.category,
            merit:            _lastMerit,
            student_category: payload.student_category,
        };

        // ── Display merit breakdown ──────────────────────────────────────────
        displayMerit(data);

        // ── Handle colleges ──────────────────────────────────────────────────
        allColleges = Array.isArray(data.colleges) ? data.colleges : [];
        populateFilters(allColleges);
        renderTable();

        // ── Show results panel ───────────────────────────────────────────────
        $('resultsPanel')?.classList.remove('d-none');
        $('emptyState')?.classList.add('d-none');
        $('resultsPanel')?.scrollIntoView({ behavior: 'smooth' });

        // ── Reset save button state (in case previously saved) ───────────────
        resetSaveBtn();

    } catch (err) {
        console.error('❌ Calculate error:', err);
        showAlert('Error: ' + err.message, 'danger');
    } finally {
        setLoading(false);
    }
}

function displayMerit(data) {
    // Support both key naming conventions the backend might return
    const merit      = data.merit         ?? data.merit_score   ?? '—';
    const theoryComp = data.theory_comp   ?? data.theory_component   ?? '—';
    const gujcetComp = data.gujcet_comp   ?? data.gujcet_component   ?? '—';
    const bonusComp  = data.bonus_comp    ?? (data.farming_bonus_applied ? '+5%' : 'None');

    const fmt = (v) => (typeof v === 'number') ? v.toFixed(4) : v;

    const el = (id, val) => { if ($(id)) $(id).innerText = fmt(val); };
    el('meritDisplay', merit);
    el('theoryComp',   theoryComp);
    el('gujcetComp',   gujcetComp);
    if ($('bonusComp')) $('bonusComp').innerText = bonusComp;
}

// ─── FILTERS & TABLE ─────────────────────────────────────────────────────────
function populateFilters(colleges) {
    const cities   = [...new Set(colleges.map(c => c.city        || c.location).filter(Boolean))].sort();
    const courses  = [...new Set(colleges.map(c => c.course_name || c.course).filter(Boolean))].sort();

    const cityEl   = $('filterCity');
    const courseEl = $('filterCourse');
    if (!cityEl || !courseEl) return;

    cityEl.innerHTML   = '<option value="">All Cities</option>'   + cities.map(v => `<option value="${escHtml(v)}">${escHtml(v)}</option>`).join('');
    courseEl.innerHTML = '<option value="">All Courses</option>'  + courses.map(v => `<option value="${escHtml(v)}">${escHtml(v)}</option>`).join('');
}

function renderTable() {
    const cityFilter   = getVal('filterCity');
    const courseFilter = getVal('filterCourse');
    const sortBy       = getVal('sortBy') || 'probability';
    const tbody        = $('collegeTableBody');
    const countEl      = $('collegeCount');
    if (!tbody) return;

    const ORDER = { high: 0, medium: 1, low: 2, unlikely: 3, unknown: 4 };

    let filtered = allColleges
        .filter(c => !cityFilter   || (c.city        || c.location)   === cityFilter)
        .filter(c => !courseFilter || (c.course_name || c.course)     === courseFilter);

    filtered.sort((a, b) => {
        if (sortBy === 'probability') return (ORDER[a.probability] ?? 4) - (ORDER[b.probability] ?? 4);
        if (sortBy === 'cutoff_asc')  return (a.last_cutoff || a.cutoff || 0) - (b.last_cutoff || b.cutoff || 0);
        if (sortBy === 'merit')       return (b.last_cutoff || b.cutoff || 0) - (a.last_cutoff || a.cutoff || 0);
        if (sortBy === 'city')        return (a.city || a.location || '').localeCompare(b.city || b.location || '');
        return 0;
    });

    if (countEl) countEl.innerText = filtered.length;

    if (!filtered.length) {
        tbody.innerHTML = `<tr><td colspan="5" class="text-center text-muted py-4">No colleges match your filters.</td></tr>`;
        return;
    }

    tbody.innerHTML = filtered.map(c => {
        const name      = c.college_name || c.name || 'N/A';
        const course    = c.course_name  || c.course || 'N/A';
        const location  = c.city         || c.location || '';
        const code      = c.college_code || '';
        const cutoff    = c.last_cutoff  ?? c.cutoff;
        const cutoffYear= c.cutoff_year  || '';
        const prob      = c.probability  || 'unknown';
        const roundP    = c.round_prediction || '—';

        const cutoffHtml = cutoff != null
            ? `${parseFloat(cutoff).toFixed(4)} <small class="text-muted">(${cutoffYear})</small>`
            : '—';

        const detailUrl = code ? `/colleges/${code}/` : '#';

        return `
        <tr>
            <td>
                <div class="fw-semibold">${escHtml(name)}</div>
                ${location ? `<div class="text-muted small">${escHtml(location)}</div>` : ''}
                ${code     ? `<div class="text-muted small">Code: ${escHtml(code)}</div>` : ''}
            </td>
            <td class="small">${escHtml(course)}</td>
            <td class="small fw-semibold">${cutoffHtml}</td>
            <td>${PROB_BADGE[prob] || PROB_BADGE.unknown}</td>
            <td><a href="${detailUrl}" class="btn btn-sm btn-outline-success">Details</a></td>
        </tr>`;
    }).join('');
}

// ─── SAVE ─────────────────────────────────────────────────────────────────────
async function doSave() {
    // Auth guard
    const isAuth = (typeof IS_AUTH !== 'undefined') ? IS_AUTH : false;
    if (!isAuth) {
        showAlert('Please <a href="/accounts/login/?next=' + encodeURIComponent(window.location.pathname) + '">log in</a> to save results.', 'warning');
        return;
    }

    // Data guard — must have calculated first
    if (_lastMerit === null || !_lastPayload) {
        // Try reading from DOM as fallback (File 1 approach)
        const meritRaw = $('meritDisplay')?.innerText?.trim();
        const meritFromDom = parseFloat(meritRaw);
        if (!meritFromDom || isNaN(meritFromDom)) {
            showAlert('Please calculate your merit score first before saving.', 'warning');
            return;
        }
        // Reconstruct payload from DOM
        _lastMerit = meritFromDom;
        _lastPayload = {
            category:          (typeof CATEGORY !== 'undefined') ? CATEGORY : '1',
            theory_obtained:   parseFloat(getVal('theoryObtained')) || 0,
            theory_total:      parseInt(getVal('theoryTotal'))      || 300,
            gujcet_marks:      parseFloat(getVal('gujcetMarks'))    || 0,
            student_category:  getVal('studentCategory')            || 'OPEN',
            farming_background: getChecked('farmingBonus'),
        };
    }

    const btn = $('saveResultBtn');
    if (btn) {
        btn.disabled = true;
        btn.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Saving…';
    }

    // Build save payload — use CORRECT key names the backend expects
    const savePayload = {
        category:           _lastPayload.category,
        merit:              _lastMerit,
        theory_obtained:    _lastPayload.theory_obtained,
        theory_total:       _lastPayload.theory_total,
        gujcet_marks:       _lastPayload.gujcet_marks,
        student_category:   _lastPayload.student_category,
        farming_background: _lastPayload.farming_background,
    };

    console.log('💾 Save payload:', savePayload);

    try {
        const resp = await fetch('/api/predict/save/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCsrf(),
            },
            body: JSON.stringify(savePayload),
        });

        const data = await resp.json();
        console.log('💾 Save response:', data);

        if (resp.status === 401) {
            showAlert('Session expired. Please <a href="/accounts/login/">log in again</a>.', 'warning');
            resetSaveBtn();
            return;
        }

        if (!resp.ok || data.error) {
            throw new Error(data.error || data.detail || `HTTP ${resp.status}`);
        }

        if (data.saved) {
            if (btn) {
                btn.innerHTML = '<i class="bi bi-bookmark-check-fill me-1"></i>Saved!';
                btn.classList.remove('btn-outline-success');
                btn.classList.add('btn-success');
                // Keep disabled so user can't double-save same result
            }
            showAlert('Result saved to your profile! <a href="/profile/">View profile →</a>', 'success');
        } else {
            throw new Error(data.message || 'Unexpected response from server.');
        }

    } catch (err) {
        console.error('❌ Save error:', err);
        showAlert('Save failed: ' + err.message, 'danger');
        resetSaveBtn();
    }
}

function resetSaveBtn() {
    const btn = $('saveResultBtn');
    if (!btn) return;
    btn.disabled = false;
    btn.innerHTML = '<i class="bi bi-bookmark-plus me-1"></i>Save Result';
    btn.classList.remove('btn-success');
    btn.classList.add('btn-outline-success');
}

// ─── RESET ────────────────────────────────────────────────────────────────────
function doReset() {
    _lastPayload = null;
    _lastMerit   = null;
    allColleges  = [];

    ['theoryObtained', 'gujcetMarks', 'cityInput'].forEach(id => {
        const el = $(id);
        if (el) el.value = '';
    });
    ['theoryTotal', 'studentCategory', 'subjectGroup', 'filterCity', 'filterCourse', 'sortBy'].forEach(id => {
        const el = $(id);
        if (el) el.selectedIndex = 0;
    });
    const fb = $('farmingBonus');
    if (fb) fb.checked = false;

    $('resultsPanel')?.classList.add('d-none');
    $('emptyState')?.classList.remove('d-none');
    clearAlert();
    resetSaveBtn();
}

// ─── Expose calculate globally (called from some templates directly) ──────────
window.calculate = doCalculate;