const adminTokenInput = document.getElementById("adminTokenInput");
const saveTokenBtn = document.getElementById("saveTokenBtn");
const bootstrapBtn = document.getElementById("bootstrapBtn");
const approveAllBtn = document.getElementById("approveAllBtn");
const refreshSummaryBtn = document.getElementById("refreshSummaryBtn");
const summaryText = document.getElementById("summaryText");
const bootstrapStatusText = document.getElementById("bootstrapStatusText");
const pendingList = document.getElementById("pendingList");
const changeLogList = document.getElementById("changeLogList");
const adminMessage = document.getElementById("adminMessage");

function getToken() {
  return localStorage.getItem("adminToken") || "";
}

function setToken(token) {
  localStorage.setItem("adminToken", token);
}

function adminHeaders() {
  return {
    "Content-Type": "application/json",
    "x-admin-token": getToken(),
  };
}

function setMessage(text, isError = false) {
  adminMessage.textContent = text;
  adminMessage.style.color = isError ? "#b91c1c" : "#065f46";
}

async function loadSummary() {
  try {
    const response = await fetch("/api/admin/summary", { headers: adminHeaders() });
    const data = await response.json();
    if (!response.ok) {
      throw new Error(data.error || "Could not load summary.");
    }
    summaryText.textContent = `Approved: ${data.approved} | Pending: ${data.pending} | Rejected: ${data.rejected}`;
  } catch (error) {
    summaryText.textContent = error.message;
  }
}

function formatScriptFailures(scripts) {
  const failed = scripts.filter((item) => !item.success);
  if (!failed.length) {
    return "All scripts succeeded.";
  }
  return `Failed scripts: ${failed.map((item) => item.script).join(", ")}`;
}

async function loadBootstrapStatus() {
  try {
    const response = await fetch("/api/admin/bootstrap-status", { headers: adminHeaders() });
    const data = await response.json();
    if (!response.ok) {
      throw new Error(data.error || "Could not load bootstrap status.");
    }
    const lastRun = data.lastRunAt ? `Last run: ${data.lastRunAt}` : "Last run: never";
    const success = data.success === null ? "Status: unknown" : `Status: ${data.success ? "success" : "partial failure"}`;
    const details = data.scripts && data.scripts.length ? formatScriptFailures(data.scripts) : "";
    bootstrapStatusText.textContent = `${lastRun} | ${success}${details ? ` | ${details}` : ""}`;
  } catch (error) {
    bootstrapStatusText.textContent = error.message;
  }
}

function renderPending(items) {
  if (!items.length) {
    pendingList.innerHTML = "<p>No pending submissions.</p>";
    return;
  }

  pendingList.innerHTML = "";
  items.forEach((camp) => {
    const card = document.createElement("article");
    card.className = "camp-card";
    card.innerHTML = `
      <h3>${camp.name}</h3>
      <p>${camp.type}</p>
      <p><strong>County:</strong> ${camp.county}</p>
      <p><strong>Location:</strong> ${camp.locationDetail || "Not listed"}</p>
      <p><strong>Source:</strong> ${camp.sourceUrl ? `<a href="${camp.sourceUrl}" target="_blank" rel="noopener noreferrer">Open link</a>` : "Not listed"}</p>
      <div class="results-row">
        <button data-action="approve" data-id="${camp.id}" type="button">Approve</button>
        <button data-action="reject" data-id="${camp.id}" type="button">Reject</button>
      </div>
    `;
    pendingList.appendChild(card);
  });
}

async function loadPending() {
  try {
    const response = await fetch("/api/admin/submissions", { headers: adminHeaders() });
    const data = await response.json();
    if (!response.ok) {
      throw new Error(data.error || "Could not load pending submissions.");
    }
    renderPending(data);
  } catch (error) {
    pendingList.innerHTML = `<p>${error.message}</p>`;
  }
}

function renderChangeLog(items) {
  if (!items.length) {
    changeLogList.innerHTML = "<p>No recent updates yet.</p>";
    return;
  }
  changeLogList.innerHTML = items
    .map(
      (item) =>
        `<p><strong>${item.name}</strong> | ${item.status} | ${item.sourceType} | ${item.updatedAt}</p>`
    )
    .join("");
}

async function loadChangeLog() {
  try {
    const response = await fetch("/api/admin/change-log", { headers: adminHeaders() });
    const data = await response.json();
    if (!response.ok) {
      throw new Error(data.error || "Could not load change log.");
    }
    renderChangeLog(data);
  } catch (error) {
    changeLogList.innerHTML = `<p>${error.message}</p>`;
  }
}

async function moderateSubmission(id, action) {
  try {
    const response = await fetch(`/api/admin/submissions/${id}/${action}`, {
      method: "POST",
      headers: adminHeaders(),
    });
    const data = await response.json();
    if (!response.ok) {
      throw new Error(data.error || `Could not ${action} submission.`);
    }
    setMessage(`Submission ${action}d.`);
    await Promise.all([loadPending(), loadSummary(), loadChangeLog()]);
  } catch (error) {
    setMessage(error.message, true);
  }
}

async function runBootstrap() {
  try {
    setMessage("Running bootstrap...");
    const response = await fetch("/api/admin/bootstrap-live-data", {
      method: "POST",
      headers: adminHeaders(),
    });
    const data = await response.json();
    if (!response.ok) {
      throw new Error(data.error || "Bootstrap failed.");
    }
    setMessage(`Bootstrap complete. Approved: ${data.approvedCount}, Total: ${data.totalCount}`);
    await Promise.all([loadPending(), loadSummary(), loadChangeLog(), loadBootstrapStatus()]);
  } catch (error) {
    setMessage(error.message, true);
    await loadBootstrapStatus();
  }
}

async function approveAllPending() {
  try {
    setMessage("Approving all pending submissions...");
    const response = await fetch("/api/admin/submissions/approve-all", {
      method: "POST",
      headers: adminHeaders(),
    });
    const data = await response.json();
    if (!response.ok) {
      throw new Error(data.error || "Approve all failed.");
    }
    setMessage(
      `Approved ${data.updatedRows} submissions. Approved total: ${data.approvedCount}`
    );
    await Promise.all([loadPending(), loadSummary(), loadChangeLog(), loadBootstrapStatus()]);
  } catch (error) {
    setMessage(error.message, true);
  }
}

saveTokenBtn.addEventListener("click", async () => {
  const token = adminTokenInput.value.trim();
  if (!token) {
    setMessage("Please enter an admin token.", true);
    return;
  }
  setToken(token);
  setMessage("Token saved.");
  await Promise.all([loadPending(), loadSummary(), loadChangeLog(), loadBootstrapStatus()]);
});

bootstrapBtn.addEventListener("click", runBootstrap);
approveAllBtn.addEventListener("click", approveAllPending);
refreshSummaryBtn.addEventListener("click", async () => {
  await Promise.all([loadPending(), loadSummary(), loadChangeLog(), loadBootstrapStatus()]);
});

pendingList.addEventListener("click", (event) => {
  const button = event.target.closest("button[data-action]");
  if (!button) {
    return;
  }
  moderateSubmission(button.dataset.id, button.dataset.action);
});

adminTokenInput.value = getToken();
loadSummary();
loadPending();
loadChangeLog();
loadBootstrapStatus();
