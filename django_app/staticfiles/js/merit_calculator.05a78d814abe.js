/* merit_calculator.js  — fixed version */
let allColleges = [];
let _lastMerit   = null;
let _lastPayload = null;

const $ = (id) => document.getElementById(id);

const PROB_BADGE = {
    high:     '<span class="badge bg-success">High</span>',
    medium:   '<span class="badge bg-warning text-dark">Medium</span>',
    low:      '<span class="badge bg-danger">Low</span>',
    unlikely: '<span class="badge bg-secondary">Unlikely</span>',
    unknown:  '<span class="badge bg-light text-muted">—</span>',
};

document.addEventListener("DOMContentLoaded", () => {
    $("calculateBtn")?.addEventListener("click", doCalculate);
    $("resetBtn")?.addEventListener("click", doReset);

    // Use event delegation for saveResultBtn — it lives inside #resultsPanel
    // which is hidden at DOMContentLoaded, so a direct addEventListener misses it.
    document.addEventListener("click", (e) => {
        if (e.target.closest("#saveResultBtn")) doSave();
    });

    ["filterCity", "filterCourse", "sortBy"].forEach((id) => {
        $(id)?.addEventListener("change", renderTable);
    });
});

/* ── Calculate ── */
async function doCalculate() {
    const btn = $("calculateBtn");
    btn.disabled = true;
    btn.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Calculating...';

    const payload = {
        category:           CATEGORY,
        theory_obtained:    parseFloat($("theoryObtained")?.value  || 0),
        theory_total:       parseInt($("theoryTotal")?.value        || 300),
        gujcet_marks:       parseFloat($("gujcetMarks")?.value      || 0),
        student_category:   $("studentCategory")?.value             || "OPEN",
        farming_background: $("farmingBonus")?.checked              || false,
    };

    if (!payload.theory_obtained || !payload.gujcet_marks) {
        showError("Please enter your marks.");
        btn.disabled = false;
        btn.innerHTML = '<i class="bi bi-calculator me-2"></i>Calculate Merit';
        return;
    }

    try {
        const resp = await fetch("/api/predict/calculate/", {
            method: "POST",
            headers: { "Content-Type": "application/json", "X-CSRFToken": CSRF },
            body: JSON.stringify(payload),
        });
        const data = await resp.json();

        if (!resp.ok || data.error) {
            showError(data.error || data.details || "Calculation failed.");
            return;
        }

        // Cache for saving — store the raw merit value (number)
        _lastMerit   = data.merit;
        _lastPayload = payload;

        displayResults(data);
        allColleges = data.colleges || [];
        populateFilters(allColleges);
        renderTable();

        $("resultsPanel")?.classList.remove("d-none");
        $("emptyState")?.classList.add("d-none");

        window.scrollTo({ top: $("resultsPanel").offsetTop - 100, behavior: "smooth" });

    } catch (e) {
        showError("Network error. Please try again.");
        console.error(e);
    } finally {
        btn.disabled = false;
        btn.innerHTML = '<i class="bi bi-calculator me-2"></i>Calculate Merit';
    }
}

/* ── Display results ──
   API returns: merit, theory_comp, gujcet_comp, bonus_comp  */
function displayResults(data) {
    if ($("meritDisplay")) $("meritDisplay").textContent = parseFloat(data.merit).toFixed(2);

    // Support both key conventions (theory_comp  OR  theory_component)
    const tc = data.theory_comp   ?? data.theory_component  ?? "—";
    const gc = data.gujcet_comp   ?? data.gujcet_component  ?? "—";
    const bc = data.bonus_comp    ?? (data.farming_bonus_applied ? "+5%" : "0");

    if ($("theoryComp")) $("theoryComp").textContent = isNaN(tc) ? tc : parseFloat(tc).toFixed(2);
    if ($("gujcetComp")) $("gujcetComp").textContent = isNaN(gc) ? gc : parseFloat(gc).toFixed(2);
    if ($("bonusComp"))  $("bonusComp").textContent  = isNaN(bc) ? bc : parseFloat(bc).toFixed(2);
}

/* ── College table ── */
function renderTable() {
    const cityFilter   = $("filterCity")?.value   || "";
    const courseFilter = $("filterCourse")?.value || "";
    const sortBy       = $("sortBy")?.value       || "probability";
    const tbody        = $("collegeTableBody");
    if (!tbody) return;

    const ORDER = { high: 0, medium: 1, low: 2, unlikely: 3, unknown: 4 };

    let filtered = allColleges.filter(c =>
        (!cityFilter   || (c.city || c.location) === cityFilter) &&
        (!courseFilter || (c.course_name || c.course) === courseFilter)
    );

    filtered.sort((a, b) => {
        if (sortBy === "merit") return (b.last_cutoff ?? b.cutoff ?? 0) - (a.last_cutoff ?? a.cutoff ?? 0);
        // probability sort — chance_label takes priority if probability key is a string label
        const probA = ORDER[a.probability] ?? (ORDER[a.chance_label?.toLowerCase()] ?? 4);
        const probB = ORDER[b.probability] ?? (ORDER[b.chance_label?.toLowerCase()] ?? 4);
        return probA - probB;
    });

    if (!filtered.length) {
        tbody.innerHTML = `<tr><td colspan="5" class="text-center text-muted py-4">No colleges match your filters.</td></tr>`;
        $("collegeCount") && ($("collegeCount").textContent = "0");
        return;
    }

    tbody.innerHTML = filtered.map(c => {
        const name    = escHtml(c.college_name || c.name       || "N/A");
        const course  = escHtml(c.course_name  || c.course     || "N/A");
        const loc     = escHtml(c.city         || c.location   || "");
        const cutoff  = c.last_cutoff ?? c.cutoff ?? "—";
        const cutoffFmt = (cutoff !== "—") ? parseFloat(cutoff).toFixed(2) : "—";
        const prob    = c.probability  ?? 0;
        const rnd     = escHtml(c.round_prediction || "—");
        const ch      = (c.chance_label || "low").toLowerCase();
        const bc      = ch === "high" ? "bg-success" : ch === "medium" ? "bg-warning text-dark" : "bg-danger";
        const colLink = c.college_code ? `/colleges/${c.college_code}/` : "#";

        return `<tr>
          <td><div class="fw-bold">${name}</div>${loc ? `<small class="text-muted">${loc}</small>` : ""}</td>
          <td>${course}</td>
          <td class="fw-semibold">${cutoffFmt}</td>
          <td><span class="badge ${bc}">${rnd} (${prob}%)</span></td>
          <td><a href="${colLink}" class="text-success"><i class="bi bi-info-circle"></i></a></td>
        </tr>`;
    }).join("");

    $("collegeCount") && ($("collegeCount").textContent = filtered.length);
}

/* ── Filters ── */
function populateFilters(colleges) {
    const cityEl   = $("filterCity");
    const courseEl = $("filterCourse");
    if (!cityEl) return;

    const cities   = [...new Set(colleges.map(c => c.city    || c.location    || "").filter(Boolean))].sort();
    const courses  = [...new Set(colleges.map(c => c.course_name || c.course  || "").filter(Boolean))].sort();

    cityEl.innerHTML   = '<option value="">All Cities</option>'   + cities.map(v  => `<option value="${escHtml(v)}">${escHtml(v)}</option>`).join("");
    courseEl.innerHTML = '<option value="">All Courses</option>'  + courses.map(v => `<option value="${escHtml(v)}">${escHtml(v)}</option>`).join("");
}

/* ── Save ── */
async function doSave() {
    if (!IS_AUTH) {
        showAlertBox("Please log in to save results.", "warning");
        return;
    }
    if (_lastMerit === null || _lastPayload === null) {
        showAlertBox("Please calculate your merit first.", "warning");
        return;
    }

    const btn = $("saveResultBtn");
    if (btn) { btn.disabled = true; btn.innerHTML = '<span class="spinner-border spinner-border-sm me-1"></span>Saving...'; }

    try {
        const resp = await fetch("/api/predict/save/", {
            method: "POST",
            headers: { "Content-Type": "application/json", "X-CSRFToken": CSRF },
            body: JSON.stringify({
                category:           _lastPayload.category,
                merit:              _lastMerit,
                theory_obtained:    _lastPayload.theory_obtained,
                theory_total:       _lastPayload.theory_total,
                gujcet_marks:       _lastPayload.gujcet_marks,
                student_category:   _lastPayload.student_category,
                farming_background: _lastPayload.farming_background,
            }),
        });

        const data = await resp.json();

        if (resp.ok && data.saved) {
            if (btn) {
                btn.innerHTML  = '<i class="bi bi-check-lg me-1"></i>Saved!';
                btn.className  = btn.className.replace("btn-outline-success", "btn-success")
                                              .replace("btn-outline-info",    "btn-info");
                btn.disabled   = true;
            }
            showAlertBox("Result saved to your profile!", "success");
        } else {
            throw new Error(data.error || "Save failed");
        }
    } catch (err) {
        showAlertBox("Save failed: " + err.message, "danger");
        if (btn) { btn.disabled = false; btn.innerHTML = '<i class="bi bi-bookmark me-1"></i>Save Result'; }
    }
}

/* ── Helpers ── */
function escHtml(s) {
    return String(s ?? "")
        .replace(/&/g, "&amp;").replace(/</g, "&lt;")
        .replace(/>/g, "&gt;").replace(/"/g, "&quot;");
}

function showAlertBox(msg, type) {
    const panel = $("resultsPanel");
    if (!panel) { alert(msg); return; }
    const div = document.createElement("div");
    div.className = `alert alert-${type} alert-dismissible fade show mt-2`;
    div.innerHTML = `${msg}<button type="button" class="btn-close" data-bs-dismiss="alert"></button>`;
    panel.prepend(div);
    setTimeout(() => div.remove(), 4000);
}

function showError(msg) {
    const fa = $("formAlert");
    if (fa) {
        fa.innerHTML = `<div class="alert alert-danger alert-dismissible fade show py-2 mb-3">
            ${escHtml(msg)}<button type="button" class="btn-close" data-bs-dismiss="alert"></button></div>`;
    } else {
        alert(msg);
    }
}

function doReset() { location.reload(); }