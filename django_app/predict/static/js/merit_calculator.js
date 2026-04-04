console.log("🔥 merit_calculator.js v4 loaded");

// ─── Global store for filter/sort ───────────────────────────────────────────
let allColleges = [];

// ─── Utility: safely read a DOM element value ────────────────────────────────
function getVal(id) {
    const el = document.getElementById(id);
    return el ? el.value.trim() : "";
}
function getChecked(id) {
    const el = document.getElementById(id);
    return el ? el.checked : false;
}
function setEl(id, text) {
    const el = document.getElementById(id);
    if (el) el.innerText = (text !== null && text !== undefined) ? text : "—";
}

// ─── Main calculate function (global so onclick= works for Cat 2 & 3) ────────
window.calculate = async function (categoryOverride) {
    const category   = categoryOverride || (typeof CATEGORY !== 'undefined' ? CATEGORY : "1");
    const theoryTotal = getVal('theoryTotal') || "300";

    const payload = {
        category:           category,
        theory_obtained:    getVal('theoryObtained'),
        theory_total:       theoryTotal,
        gujcet_marks:       getVal('gujcetMarks'),
        student_category:   getVal('studentCategory') || "OPEN",
        farming_background: getChecked('farmingBonus'),
    };

    console.log("📤 Sending payload:", payload);

    // ── Validation ──
    if (!payload.theory_obtained || payload.theory_obtained === "0") {
        showAlert("Please enter Theory Marks Obtained.", "warning"); return;
    }
    if (!payload.gujcet_marks) {
        showAlert("Please enter GUJCET Marks.", "warning"); return;
    }

    setLoading(true);

    try {
        const response = await fetch('/api/predict/calculate/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': typeof CSRF !== 'undefined' ? CSRF : getCookie('csrftoken'),
            },
            body: JSON.stringify(payload),
        });

        const result = await response.json();

        // ── Full debug dump ──
        console.log("📥 Raw API response:", JSON.stringify(result, null, 2));

        if (!response.ok) {
            throw new Error(result.details || result.error || `HTTP ${response.status}`);
        }

        // ── Validate response structure ──
        if (typeof result.merit === 'undefined') {
            console.error("❌ 'merit' key missing from response:", result);
            throw new Error("Server returned unexpected data format. Check Django logs.");
        }

        allColleges = Array.isArray(result.colleges) ? result.colleges : [];

        console.log("✅ Colleges received:", allColleges.length);
        if (allColleges.length > 0) {
            console.log("📌 First college object:", allColleges[0]);
            console.log("📌 First college keys:", Object.keys(allColleges[0]));
        }

        // ── Update merit display ──
        setEl('meritDisplay',  result.merit);
        setEl('theoryComp',    result.theory_comp);
        setEl('gujcetComp',    result.gujcet_comp);
        setEl('bonusComp',     result.bonus_comp !== undefined ? result.bonus_comp : 0);

        // ── Show results panel ──
        const panel = document.getElementById('resultsPanel');
        const empty = document.getElementById('emptyState');
        if (panel) panel.classList.remove('d-none');
        if (empty) empty.classList.add('d-none');

        // ── Populate filter dropdowns ──
        populateFilters(allColleges);

        // ── Render table ──
        renderTable(allColleges);

        // ── Scroll to results ──
        if (panel) panel.scrollIntoView({ behavior: 'smooth' });

    } catch (err) {
        console.error("❌ calculate() error:", err);
        showAlert("Error: " + err.message, "danger");
    } finally {
        setLoading(false);
    }
};

// ─── Render table ────────────────────────────────────────────────────────────
function renderTable(colleges) {
    const tbody   = document.getElementById('collegeTableBody');
    const countEl = document.getElementById('collegeCount');
    if (!tbody) return;

    tbody.innerHTML = '';

    if (!colleges || colleges.length === 0) {
        tbody.innerHTML = `<tr><td colspan="5" class="text-center text-muted py-4">
            No colleges match your filters.</td></tr>`;
        if (countEl) countEl.innerText = 0;
        return;
    }

    colleges.forEach((col, idx) => {
        // ── Defensive field reads with multiple fallback key names ──
        // Handles both our normalized keys AND any raw CSV key variations
        const name        = col.name         || col['COLLEGE NAME'] || col['college name'] || col['college'] || "N/A";
        const course      = col.course       || col['COURSE']       || col['course']       || col['program'] || "N/A";
        const location    = col.location     || "";
        const cutoff      = col.cutoff       ?? col['cutoff']       ?? "—";
        const probability = col.probability  ?? col['probability']  ?? 0;
        const roundPred   = col.round_prediction || col['round_prediction'] || "—";
        const chanceLabel = col.chance_label || col['chance_label'] || "Low";

        // Debug first row
        if (idx === 0) {
            console.log("🔍 Rendering college[0]:", { name, course, cutoff, probability, chanceLabel });
        }

        let badgeClass = 'bg-secondary';
        if      (chanceLabel === 'High')   badgeClass = 'bg-success';
        else if (chanceLabel === 'Medium') badgeClass = 'bg-warning text-dark';
        else if (chanceLabel === 'Low')    badgeClass = 'bg-danger';

        const row = `
        <tr>
            <td>
                <div class="fw-bold">${escHtml(name)}</div>
                ${location ? `<small class="text-muted">${escHtml(location)}</small>` : ''}
            </td>
            <td>${escHtml(course)}</td>
            <td class="fw-semibold">${cutoff}</td>
            <td>
                <span class="badge ${badgeClass}">
                    ${escHtml(roundPred)} (${probability}%)
                </span>
            </td>
            <td>
                <a href="#" class="btn btn-sm btn-link text-success p-0">
                    <i class="bi bi-info-circle"></i>
                </a>
            </td>
        </tr>`;

        tbody.insertAdjacentHTML('beforeend', row);
    });

    if (countEl) countEl.innerText = colleges.length;
}

// ─── Filters ─────────────────────────────────────────────────────────────────
function populateFilters(colleges) {
    const cityEl   = document.getElementById('filterCity');
    const courseEl = document.getElementById('filterCourse');
    if (!cityEl || !courseEl) return;

    const cities  = [...new Set(colleges.map(c => c.location).filter(Boolean))].sort();
    const courses = [...new Set(colleges.map(c => c.course).filter(Boolean))].sort();

    cityEl.innerHTML   = '<option value="">All Cities</option>'   + cities.map(v => `<option value="${escHtml(v)}">${escHtml(v)}</option>`).join('');
    courseEl.innerHTML = '<option value="">All Courses</option>' + courses.map(v => `<option value="${escHtml(v)}">${escHtml(v)}</option>`).join('');
}

function applyFiltersAndSort() {
    const city   = getVal('filterCity');
    const course = getVal('filterCourse');
    const sortBy = getVal('sortBy') || 'probability';

    let filtered = [...allColleges];
    if (city)   filtered = filtered.filter(c => c.location === city);
    if (course) filtered = filtered.filter(c => c.course === course);

    filtered.sort((a, b) => {
        if (sortBy === 'probability') return b.probability - a.probability;
        if (sortBy === 'merit')       return a.cutoff - b.cutoff;
        if (sortBy === 'city')        return (a.location || '').localeCompare(b.location || '');
        return 0;
    });

    renderTable(filtered);
}

// ─── Loading state ────────────────────────────────────────────────────────────
function setLoading(on) {
    const btn = document.getElementById('calculateBtn');
    if (!btn) return;
    btn.disabled = on;
    btn.innerHTML = on
        ? '<span class="spinner-border spinner-border-sm me-2"></span>Calculating...'
        : '<i class="bi bi-calculator me-2"></i>Calculate Merit';
}

// ─── Alert helper ─────────────────────────────────────────────────────────────
function showAlert(msg, type = 'danger') {
    const old = document.getElementById('jsAlert');
    if (old) old.remove();

    const div = document.createElement('div');
    div.id = 'jsAlert';
    div.className = `alert alert-${type} alert-dismissible fade show mt-2`;
    div.innerHTML = `${msg} <button type="button" class="btn-close" data-bs-dismiss="alert"></button>`;

    const btn = document.getElementById('calculateBtn');
    if (btn) btn.closest('.card-body')?.prepend(div);
}

// ─── HTML escape ──────────────────────────────────────────────────────────────
function escHtml(str) {
    if (str === null || str === undefined) return '';
    return String(str)
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;');
}

// ─── CSRF cookie helper (fallback if CSRF var not set) ─────────────────────
function getCookie(name) {
    const v = document.cookie.match('(^|;)\\s*' + name + '\\s*=\\s*([^;]+)');
    return v ? v.pop() : '';
}

// ─── Event listeners ──────────────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {

    // Category 1 button (Cat 2 & 3 use onclick= attribute)
    const calcBtn = document.getElementById('calculateBtn');
    if (calcBtn && !calcBtn.hasAttribute('onclick')) {
        calcBtn.addEventListener('click', () =>
            calculate(typeof CATEGORY !== 'undefined' ? CATEGORY : '1')
        );
    }

    // Reset
    const resetBtn = document.getElementById('resetBtn');
    if (resetBtn) {
        resetBtn.addEventListener('click', () => {
            ['theoryObtained', 'gujcetMarks', 'cityInput'].forEach(id => {
                const el = document.getElementById(id);
                if (el) el.value = '';
            });
            ['theoryTotal', 'studentCategory', 'filterCity', 'filterCourse'].forEach(id => {
                const el = document.getElementById(id);
                if (el) el.selectedIndex = 0;
            });
            const cb = document.getElementById('farmingBonus');
            if (cb) cb.checked = false;

            allColleges = [];
            const panel = document.getElementById('resultsPanel');
            const empty = document.getElementById('emptyState');
            if (panel) panel.classList.add('d-none');
            if (empty) empty.classList.remove('d-none');
        });
    }

    // Filter/sort dropdowns
    ['filterCity', 'filterCourse', 'sortBy'].forEach(id => {
        const el = document.getElementById(id);
        if (el) el.addEventListener('change', applyFiltersAndSort);
    });

    // Save result
    const saveBtn = document.getElementById('saveResultBtn');
    if (saveBtn) {
        saveBtn.addEventListener('click', async () => {
            try {
                const res = await fetch('/api/predict/save/', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': typeof CSRF !== 'undefined' ? CSRF : getCookie('csrftoken'),
                    },
                    body: JSON.stringify({ merit: document.getElementById('meritDisplay')?.innerText }),
                });
                const d = await res.json();
                showAlert(d.saved ? 'Result saved!' : 'Could not save.', d.saved ? 'success' : 'warning');
            } catch (e) {
                showAlert('Save failed: ' + e.message, 'danger');
            }
        });
    }
});