/**
 * merit_calculator.js — AgriPredict (Unified v5.1)
 */

console.log("✅ merit_calculator.js loaded — category:", typeof CATEGORY !== 'undefined' ? CATEGORY : 'unknown');

let allColleges = [];
let _lastPayload = null;
let _lastMerit = null;

const $ = (id) => document.getElementById(id);

document.addEventListener("DOMContentLoaded", () => {
    $("calculateBtn")?.addEventListener("click", doCalculate);
    $("resetBtn")?.addEventListener("click", doReset);

    // EVENT DELEGATION: This fixes the Save button even if it starts hidden
    document.addEventListener("click", (e) => {
        if (e.target && e.target.id === "saveResultBtn") {
            doSave();
        }
    });

    ["filterCity", "filterCourse", "sortBy"].forEach(id => {
        $(id)?.addEventListener("change", renderTable);
    });
});

/* ─── CALCULATE ─── */
async function doCalculate() {
    clearAlert();
    const btn = $("calculateBtn");
    
    const payload = {
        category: typeof CATEGORY !== 'undefined' ? CATEGORY : "1",
        theory_obtained: parseFloat($("theoryObtained")?.value || 0),
        theory_total: parseInt($("theoryTotal")?.value || 300),
        gujcet_marks: parseFloat($("gujcetMarks")?.value || 0),
        student_category: $("studentCategory")?.value || "OPEN",
        farming_background: $("farmingBonus")?.checked || false,
    };

    if (!payload.theory_obtained || !payload.gujcet_marks) {
        showAlert("Please enter your marks.", "warning"); return;
    }

    setLoading(true);
    try {
        const resp = await fetch("/api/predict/calculate/", {
            method: "POST",
            headers: { "Content-Type": "application/json", "X-CSRFToken": CSRF },
            body: JSON.stringify(payload),
        });
        const data = await resp.json();

        if (!resp.ok) throw new Error(data.error || "Calculation failed");

        _lastMerit = data.merit;
        _lastPayload = payload;

        displayMerit(data);
        allColleges = data.colleges || [];
        populateFilters(allColleges);
        renderTable();

        $("resultsPanel")?.classList.remove("d-none");
        $("emptyState")?.classList.add("d-none");
        $("resultsPanel")?.scrollIntoView({ behavior: "smooth" });
        resetSaveBtn();

    } catch (err) {
        showAlert(err.message, "danger");
    } finally {
        setLoading(false);
    }
}

/* ─── SAVE ─── */
async function doSave() {
    if (typeof IS_AUTH !== 'undefined' && !IS_AUTH) {
        showAlert('Please <a href="/accounts/login/">log in</a> to save.', 'warning');
        return;
    }

    if (!_lastMerit) {
        showAlert("Calculate merit first!", "warning"); return;
    }

    const saveBtn = $("saveResultBtn");
    saveBtn.disabled = true;
    saveBtn.innerHTML = '<span class="spinner-border spinner-border-sm"></span> Saving...';

    try {
        const response = await fetch("/api/predict/save/", {
            method: "POST",
            headers: { "Content-Type": "application/json", "X-CSRFToken": CSRF },
            body: JSON.stringify({
                merit: _lastMerit,
                theory: _lastPayload.theory_obtained,
                theory_total: _lastPayload.theory_total,
                gujcet: _lastPayload.gujcet_marks,
                farming: _lastPayload.farming_background,
                category: _lastPayload.category,
                student_category: _lastPayload.student_category
            })
        });
        const result = await response.json();

        if (result.saved) {
            saveBtn.className = "btn btn-success btn-sm mt-3";
            saveBtn.innerHTML = '<i class="bi bi-check-circle"></i> Saved!';
            showAlert("Result saved successfully!", "success");
        } else {
            throw new Error(result.error);
        }
    } catch (err) {
        showAlert("Save failed: " + err.message, "danger");
        resetSaveBtn();
    }
}

/* ─── UTILITIES ─── */
function displayMerit(data) {
    const merit = data.merit ?? '—';
    const tc = data.theory_comp ?? data.theory_component ?? '—';
    const gc = data.gujcet_comp ?? data.gujcet_component ?? '—';
    const bc = data.bonus_comp ?? '0';

    if ($('meritDisplay')) $('meritDisplay').innerText = typeof merit === 'number' ? merit.toFixed(4) : merit;
    if ($('theoryComp')) $('theoryComp').innerText = tc;
    if ($('gujcetComp')) $('gujcetComp').innerText = gc;
    if ($('bonusComp')) $('bonusComp').innerText = bc;
}

function resetSaveBtn() {
    const btn = $("saveResultBtn");
    if (!btn) return;
    btn.disabled = false;
    btn.innerHTML = '<i class="bi bi-bookmark me-1"></i>Save Result';
    btn.className = "btn btn-outline-success btn-sm mt-3";
}

function showAlert(msg, type) {
    const box = $("formAlert");
    if (box) box.innerHTML = `<div class="alert alert-${type} alert-dismissible fade show">${msg}<button type="button" class="btn-close" data-bs-dismiss="alert"></button></div>`;
}

function clearAlert() { if ($("formAlert")) $("formAlert").innerHTML = ""; }

function setLoading(on) {
    const btn = $("calculateBtn");
    if (btn) {
        btn.disabled = on;
        btn.innerHTML = on ? '<span class="spinner-border spinner-border-sm me-2"></span>...' : '<i class="bi bi-calculator me-2"></i>Calculate Merit';
    }
}

function doReset() { window.location.reload(); }

// ... (keep your renderTable and populateFilters functions from your v5.0 version) ...