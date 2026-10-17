fetch("jobs.json")
  .then(res => res.json())
  .then(jobs => renderJobs(jobs))
  .catch(err => {
    console.error(err);
    document.getElementById("job-list").innerHTML =
      '<p class="empty-state">Could not load deadlines. Try refreshing.</p>';
  });

function renderJobs(jobs) {
  const container = document.getElementById("job-list");
  container.innerHTML = "";

  if (!jobs || jobs.length === 0) {
    container.innerHTML =
      '<p class="empty-state">No deadlines found yet. The scraper runs daily at 06:00 UTC.</p>';
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

    const card = document.createElement("div");
    card.className = `job-card ${badgeClass}`;
    card.innerHTML = `
      <div class="badge ${badgeClass}">${label}</div>
      <h2>${escapeHtml(job.title)}</h2>
      <p class="meta">Last Date: ${formatDate(job.deadline)}</p>
      <a href="${job.link}" target="_blank" rel="noopener" class="apply-btn">Apply Now →</a>
    `;
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

  gsap.to(mascot, {
    y: -6, duration: 0.9, ease: "sine.inOut", repeat: -1, yoyo: true
  });
  gsap.fromTo(arm, { rotation: 0 },
    { rotation: -55, duration: 0.5, ease: "back.out(1.7)", delay: 0.2 }
  );
  gsap.fromTo(bubble, { scale: 0, opacity: 0 },
    { scale: 1, opacity: 1, duration: 0.4, ease: "back.out(2)", delay: 0.6 }
  );
}