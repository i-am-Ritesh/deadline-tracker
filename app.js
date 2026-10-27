fetch("jobs.json")
  .then(res => res.json())
  .then(jobs => renderJobs(jobs))
  .catch(err => {
    console.error(err);
    document.getElementById("job-list").innerHTML =
      '<p class="empty-state">Could not load deadlines. Try refreshing.</p>';
  });

// Get saved states from the browser's memory
function getSavedStates() {
  return JSON.parse(localStorage.getItem("jobTrackerStates")) || {};
}

// Save states to the browser's memory
function saveState(link, state) {
  const states = getSavedStates();
  if (state) {
    states[link] = state;
  } else {
    delete states[link]; // Remove if unchecked
  }
  localStorage.setItem("jobTrackerStates", JSON.stringify(states));
}

function renderJobs(jobs) {
  const container = document.getElementById("job-list");
  container.innerHTML = "";
  const savedStates = getSavedStates();

  if (!jobs || jobs.length === 0) {
    container.innerHTML = '<p class="empty-state">No deadlines found yet.</p>';
    return;
  }

  jobs.sort((a, b) => new Date(a.deadline) - new Date(b.deadline));

  jobs.forEach((job, index) => {
    const days = job.days_left;
    let badgeClass = "safe";
    let label = `${days} day${days !== 1 ? "s" : ""} left`;

    if (days < 0) { badgeClass = "critical"; label = "Closed"; }
    else if (days <= 3) badgeClass = "critical";
    else if (days <= 7) badgeClass = "soon";

    // Check if this job has a saved status
    const currentStatus = savedStates[job.link] || "";
    const wantChecked = currentStatus === "want" ? "checked" : "";
    const doneChecked = currentStatus === "completed" ? "checked" : "";

    const card = document.createElement("div");
    // Add a class based on the status (want/apply, completed, or default)
    card.className = `job-card ${badgeClass} ${currentStatus ? 'status-' + currentStatus : ''}`;
    
    card.innerHTML = `
      <div class="job-content">
        <div class="badge ${badgeClass}">${label}</div>
        <h2>${escapeHtml(job.title)}</h2>
        <p class="meta">Last Date: ${formatDate(job.deadline)}</p>
        <a href="${job.link}" target="_blank" rel="noopener" class="apply-btn">Apply Now →</a>
      </div>
      
      <div class="job-actions">
        <label class="checkbox-label want-label">
          <input type="checkbox" class="cb-want" ${wantChecked}> 
          <span>Want to Apply</span>
        </label>
        <label class="checkbox-label done-label">
          <input type="checkbox" class="cb-done" ${doneChecked}> 
          <span>Completed</span>
        </label>
      </div>
    `;

    // Add event listeners for the checkboxes
    const cbWant = card.querySelector(".cb-want");
    const cbDone = card.querySelector(".cb-done");

    cbWant.addEventListener("change", (e) => {
      if (e.target.checked) {
        cbDone.checked = false; // Uncheck the other box
        card.className = `job-card ${badgeClass} status-want`;
        saveState(job.link, "want");
      } else {
        card.className = `job-card ${badgeClass}`;
        saveState(job.link, null);
      }
    });

    cbDone.addEventListener("change", (e) => {
      if (e.target.checked) {
        cbWant.checked = false; // Uncheck the other box
        card.className = `job-card ${badgeClass} status-completed`;
        saveState(job.link, "completed");
      } else {
        card.className = `job-card ${badgeClass}`;
        saveState(job.link, null);
      }
    });

    container.appendChild(card);

    if (index === 0 && days <= 3 && days >= 0) triggerMascot();
  });
}

function formatDate(iso) {
  const d = new Date(iso);
  return d.toLocaleDateString("en-IN", { day: "2-digit", month: "short", year: "numeric" });
}

function escapeHtml(s) {
  return s.replace(/[&<>"']/g, c => ({
    "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;"
  }[c]));
}

function triggerMascot() {
  const wrap = document.getElementById("mascot-wrap");
  const mascot = document.getElementById("mascot");
  const arm = document.getElementById("arm");
  const bubble = document.getElementById("mascot-bubble");

  wrap.classList.add("visible");

  gsap.to(mascot, { y: -6, duration: 0.9, ease: "sine.inOut", repeat: -1, yoyo: true });
  gsap.fromTo(arm, { rotation: 0 }, { rotation: -55, duration: 0.5, ease: "back.out(1.7)", delay: 0.2 });
  gsap.fromTo(bubble, { scale: 0, opacity: 0 }, { scale: 1, opacity: 1, duration: 0.4, ease: "back.out(2)", delay: 0.6 });
}