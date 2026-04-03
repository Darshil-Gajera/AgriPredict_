// main.js — AgriPredict

// ── Dark mode ─────────────────────────────────────────────────
const html = document.documentElement;
const themeToggle = document.getElementById("themeToggle");
const themeIcon   = document.getElementById("themeIcon");

function applyTheme(theme) {
  html.setAttribute("data-bs-theme", theme);
  if (themeIcon) {
    themeIcon.className = theme === "dark" ? "bi bi-sun-fill" : "bi bi-moon-fill";
  }
  localStorage.setItem("theme", theme);
}

// Load saved theme
const savedTheme = localStorage.getItem("theme") ||
  (window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light");
applyTheme(savedTheme);

if (themeToggle) {
  themeToggle.addEventListener("click", () => {
    applyTheme(html.getAttribute("data-bs-theme") === "dark" ? "light" : "dark");
  });
}

// ── Merit Calculator ──────────────────────────────────────────
const calcForm   = document.getElementById("meritForm");
const resultArea = document.getElementById("resultArea");

if (calcForm) {
  calcForm.addEventListener("submit", async (e) => {
    e.preventDefault();
    const btn = calcForm.querySelector('[type="submit"]');
    btn.disabled = true;
    btn.innerHTML = '<span class="spinner-border spinner-border-sm"></span> Calculating…';

    const fd = new FormData(calcForm);
    const payload = {
      category:          fd.get("category"),
      theory_obtained:   parseFloat(fd.get("theory_obtained")),
      theory_total:      parseInt(fd.get("theory_total")),
      gujcet_marks:      parseFloat(fd.get("gujcet_marks")),
      student_category:  fd.get("student_category"),
      farming_background: fd.get("farming_background") === "on",
      subject_group:     fd.get("subject_group") || "",
      city:              fd.get("city") || "",
      district:          fd.get("district") || "",
    };

    try {
      const res = await fetch("/predict/calculate/", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-CSRFToken": getCookie("csrftoken"),
        },
        body: JSON.stringify(payload),
      });
      const data = await res.json();
      if (res.ok) {
        renderResults(data, payload);
        // Store merit context for chatbot
        window._meritContext = {
          category: payload.category,
          merit: data.merit,
          student_category: payload.student_category,
        };
      } else {
        showError(data.error || "Calculation failed");
      }
    } catch (err) {
      showError("Network error. Please try again.");
    } finally {
      btn.disabled = false;
      btn.innerHTML = 'Calculate Merit';
    }
  });
}

function renderResults(data, payload) {
  if (!resultArea) return;

  // Merit score header
  const scoreHtml = `
    <div class="text-center mb-4">
      <div class="merit-score-display">${data.merit.toFixed(2)}</div>
      <small class="text-muted">
        Theory: ${data.theory_component.toFixed(2)} + GUJCET: ${data.gujcet_component.toFixed(2)}
        ${data.farming_bonus_applied ? ' + Farming Bonus 5%' : ''}
      </small>
    </div>`;

  // Save button (only if logged in — injected by Django template)
  const saveBtn = window._userLoggedIn
    ? `<button class="btn btn-outline-success btn-sm mb-3" onclick="saveResult(${JSON.stringify(payload).replace(/"/g, '&quot;')}, ${data.merit})">
         <i class="bi bi-bookmark-plus"></i> Save Result
       </button>`
    : '';

  // Filter bar
  const filterBar = `
    <div class="d-flex flex-wrap gap-2 align-items-center mb-3">
      <input type="text" id="collegeSearch" class="form-control form-control-sm w-auto flex-grow-1"
             placeholder="Search college…" oninput="filterColleges()" />
      <select id="sortSelect" class="form-select form-select-sm w-auto" onchange="sortColleges()">
        <option value="prob">Sort by Probability</option>
        <option value="merit">Sort by Merit</option>
        <option value="college">Sort by College</option>
      </select>
    </div>`;

  // College cards
  const ORDER = { high: 0, medium: 1, low: 2, unlikely: 3, unknown: 4 };
  const colleges = [...data.colleges].sort((a, b) => ORDER[a.probability] - ORDER[b.probability]);
  window._collegeData = colleges;

  resultArea.innerHTML = scoreHtml + saveBtn + filterBar +
    `<div id="collegeList">${buildCollegeCards(colleges)}</div>`;
  resultArea.classList.remove("d-none");
  resultArea.scrollIntoView({ behavior: "smooth", block: "start" });
}

function buildCollegeCards(colleges) {
  if (!colleges.length) return `<p class="text-muted">No colleges found for your selection.</p>`;
  return colleges.map(c => `
    <div class="card college-card mb-2 p-3" data-name="${(c.college_name||'').toLowerCase()}" data-merit="${c.last_cutoff || 0}">
      <div class="d-flex justify-content-between align-items-start">
        <div>
          <strong>${c.college_name}</strong>
          <div class="text-muted small">${c.university || ''} &bull; ${c.city || ''}</div>
          <div class="text-muted small">Code: ${c.college_code} &bull; ${c.course_name}</div>
        </div>
        <div class="text-end">
          <span class="probability-badge prob-${c.probability}">${probLabel(c.probability)}</span>
          ${c.last_cutoff
            ? `<div class="text-muted small mt-1">Last cutoff: ${c.last_cutoff} (${c.cutoff_year})</div>`
            : `<div class="text-muted small mt-1">No cutoff data</div>`}
        </div>
      </div>
    </div>`).join("");
}

function probLabel(p) {
  return { high: "High Chance", medium: "Medium", low: "Low", unlikely: "Unlikely", unknown: "Unknown" }[p] || p;
}

function filterColleges() {
  const q = document.getElementById("collegeSearch").value.toLowerCase();
  const filtered = (window._collegeData || []).filter(c =>
    (c.college_name || "").toLowerCase().includes(q) ||
    (c.city || "").toLowerCase().includes(q) ||
    (c.course_name || "").toLowerCase().includes(q)
  );
  document.getElementById("collegeList").innerHTML = buildCollegeCards(filtered);
}

function sortColleges() {
  const mode = document.getElementById("sortSelect").value;
  const ORDER = { high: 0, medium: 1, low: 2, unlikely: 3, unknown: 4 };
  const sorted = [...(window._collegeData || [])].sort((a, b) => {
    if (mode === "merit")   return (b.last_cutoff || 0) - (a.last_cutoff || 0);
    if (mode === "college") return (a.college_name || "").localeCompare(b.college_name || "");
    return ORDER[a.probability] - ORDER[b.probability];
  });
  document.getElementById("collegeList").innerHTML = buildCollegeCards(sorted);
}

async function saveResult(payload, merit) {
  payload.merit = merit;
  const res = await fetch("/predict/save/", {
    method: "POST",
    headers: { "Content-Type": "application/json", "X-CSRFToken": getCookie("csrftoken") },
    body: JSON.stringify(payload),
  });
  if (res.ok) {
    showToast("Result saved!", "success");
  } else {
    showToast("Could not save result.", "danger");
  }
}

function showError(msg) {
  if (resultArea) {
    resultArea.innerHTML = `<div class="alert alert-danger">${msg}</div>`;
    resultArea.classList.remove("d-none");
  }
}

// ── Utilities ─────────────────────────────────────────────────
function getCookie(name) {
  const v = `; ${document.cookie}`;
  const parts = v.split(`; ${name}=`);
  if (parts.length === 2) return parts.pop().split(";").shift();
}

function showToast(msg, type = "info") {
  const toast = document.createElement("div");
  toast.className = `toast align-items-center text-bg-${type} border-0 show position-fixed bottom-0 start-50 translate-middle-x mb-4`;
  toast.style.zIndex = 9999;
  toast.innerHTML = `<div class="d-flex"><div class="toast-body">${msg}</div>
    <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button></div>`;
  document.body.appendChild(toast);
  setTimeout(() => toast.remove(), 3000);
}
