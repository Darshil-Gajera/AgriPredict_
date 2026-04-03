/* merit_calculator.js
   Works for all 3 categories. Category-specific fields are controlled
   by the inline <script> that sets CATEGORY before this file loads. */

let allColleges = [];

const $ = (id) => document.getElementById(id);

const PROB_BADGE = {
  high:     '<span class="badge bg-success">High</span>',
  medium:   '<span class="badge bg-warning text-dark">Medium</span>',
  low:      '<span class="badge bg-danger">Low</span>',
  unlikely: '<span class="badge bg-secondary">Unlikely</span>',
  unknown:  '<span class="badge bg-light text-muted">—</span>',
};

document.addEventListener("DOMContentLoaded", () => {
  const calcBtn  = $("calculateBtn");
  const resetBtn = $("resetBtn");
  const saveBtn  = $("saveResultBtn");

  if (calcBtn) calcBtn.addEventListener("click", doCalculate);
  if (resetBtn) resetBtn.addEventListener("click", doReset);
  if (saveBtn) saveBtn.addEventListener("click", doSave);

  ["filterCity", "filterCourse", "sortBy"].forEach((id) => {
    const el = $(id);
    if (el) el.addEventListener("change", renderTable);
  });
});

async function doCalculate() {
  const btn = $("calculateBtn");
  btn.disabled = true;
  btn.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Calculating…';

  const payload = {
    category: CATEGORY,
    theory_obtained: parseFloat($("theoryObtained")?.value || 0),
    theory_total:    parseInt($("theoryTotal")?.value || 300),
    gujcet_marks:    parseFloat($("gujcetMarks")?.value || 0),
    student_category: $("studentCategory")?.value || "OPEN",
    farming_background: $("farmingBonus")?.checked || false,
    subject_group:   $("subjectGroup")?.value || "",
    city:            $("cityInput")?.value || "",
  };

  // Basic validation
  if (!payload.theory_total || !payload.student_category) {
    showError("Please fill in all required fields.");
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

    if (data.error) { showError(data.error); return; }

    // Store in session via hidden field for chatbot context
    window._lastMerit = data.merit;
    window._lastPayload = payload;

    displayResults(data);
    populateFilters(data.colleges);
    allColleges = data.colleges;
    renderTable();

    $("resultsPanel")?.classList.remove("d-none");
    $("emptyState")?.classList.add("d-none");
  } catch (e) {
    showError("Network error. Please try again.");
  } finally {
    btn.disabled = false;
    btn.innerHTML = '<i class="bi bi-calculator me-2"></i>Calculate Merit';
  }
}

function displayResults(data) {
  if ($("meritDisplay")) $("meritDisplay").textContent = data.merit.toFixed(2);
  if ($("theoryComp"))   $("theoryComp").textContent   = data.theory_component?.toFixed(2) ?? "—";
  if ($("gujcetComp"))   $("gujcetComp").textContent   = data.gujcet_component?.toFixed(2) ?? "—";
  if ($("bonusComp"))    $("bonusComp").textContent     = data.farming_bonus_applied ? "+5%" : "None";
}

function populateFilters(colleges) {
  const cities   = [...new Set(colleges.map((c) => c.city).filter(Boolean))].sort();
  const courses  = [...new Set(colleges.map((c) => c.course_name).filter(Boolean))].sort();

  const cityEl   = $("filterCity");
  const courseEl = $("filterCourse");
  if (!cityEl || !courseEl) return;

  cityEl.innerHTML   = '<option value="">All cities</option>';
  courseEl.innerHTML = '<option value="">All courses</option>';

  cities.forEach((c)  => (cityEl.innerHTML   += `<option value="${c}">${c}</option>`));
  courses.forEach((c) => (courseEl.innerHTML += `<option value="${c}">${c}</option>`));
}

function renderTable() {
  const cityFilter   = $("filterCity")?.value   || "";
  const courseFilter = $("filterCourse")?.value || "";
  const sortBy       = $("sortBy")?.value       || "probability";
  const tbody        = $("collegeTableBody");
  if (!tbody) return;

  const ORDER = { high: 0, medium: 1, low: 2, unlikely: 3, unknown: 4 };

  let filtered = allColleges
    .filter((c) => (!cityFilter   || c.city        === cityFilter))
    .filter((c) => (!courseFilter || c.course_name === courseFilter));

  filtered.sort((a, b) => {
    if (sortBy === "probability") return (ORDER[a.probability] ?? 4) - (ORDER[b.probability] ?? 4);
    if (sortBy === "merit")       return (b.last_cutoff ?? 0) - (a.last_cutoff ?? 0);
    if (sortBy === "city")        return (a.city || "").localeCompare(b.city || "");
    return 0;
  });

  if ($("collegeCount")) $("collegeCount").textContent = filtered.length;

  tbody.innerHTML = filtered.map((c) => `
    <tr>
      <td>
        <div class="fw-semibold">${c.college_name}</div>
        <div class="text-muted small">${c.college_code} &bull; ${c.city || ""}</div>
      </td>
      <td class="small">${c.course_name}</td>
      <td class="small">${c.last_cutoff ? c.last_cutoff.toFixed(2) + " <span class='text-muted'>(" + c.cutoff_year + ")</span>" : "—"}</td>
      <td>${PROB_BADGE[c.probability] || PROB_BADGE.unknown}</td>
      <td><a href="/colleges/${c.college_code}/" class="btn btn-sm btn-outline-success">Details</a></td>
    </tr>
  `).join("");

  if (!filtered.length) {
    tbody.innerHTML = '<tr><td colspan="5" class="text-center text-muted py-4">No colleges match your filters.</td></tr>';
  }
}

async function doSave() {
  if (!IS_AUTH) return;
  const btn = $("saveResultBtn");
  btn.disabled = true;
  try {
    const payload = {
      ...window._lastPayload,
      merit: window._lastMerit,
    };
    const resp = await fetch("/api/predict/save/", {
      method: "POST",
      headers: { "Content-Type": "application/json", "X-CSRFToken": CSRF },
      body: JSON.stringify(payload),
    });
    const data = await resp.json();
    if (data.saved) {
      btn.innerHTML = '<i class="bi bi-bookmark-check-fill me-1"></i>Saved!';
      btn.classList.replace("btn-outline-success", "btn-success");
    }
  } catch (e) {
    btn.disabled = false;
    btn.textContent = "Save Result";
  }
}

function doReset() {
  ["theoryObtained", "gujcetMarks", "cityInput"].forEach((id) => {
    const el = $(id);
    if (el) el.value = "";
  });
  ["theoryTotal", "studentCategory", "subjectGroup"].forEach((id) => {
    const el = $(id);
    if (el) el.selectedIndex = 0;
  });
  const fb = $("farmingBonus");
  if (fb) fb.checked = false;

  allColleges = [];
  $("resultsPanel")?.classList.add("d-none");
  $("emptyState")?.classList.remove("d-none");
}

function showError(msg) {
  const existing = document.querySelector(".merit-error");
  if (existing) existing.remove();
  const div = document.createElement("div");
  div.className = "alert alert-danger alert-dismissible merit-error mt-3";
  div.innerHTML = `${msg}<button type="button" class="btn-close" data-bs-dismiss="alert"></button>`;
  $("calculateBtn")?.parentElement?.after(div);
}
