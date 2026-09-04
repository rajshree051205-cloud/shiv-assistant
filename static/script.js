const historyEl = document.getElementById("history");
const commandForm = document.getElementById("command-form");
const commandInput = document.getElementById("command-input");

const noteForm = document.getElementById("note-form");
const noteInput = document.getElementById("note-input");
const notesList = document.getElementById("notes-list");

const reminderForm = document.getElementById("reminder-form");
const reminderInput = document.getElementById("reminder-input");
const remindersList = document.getElementById("reminders-list");

const historyBody = document.getElementById("history-body");

function addMessage(who, text) {
  const div = document.createElement("div");
  div.className = `msg ${who}`;
  div.innerHTML = `<div class="who">${who === "user" ? "You" : "Shiv"}</div><div class="bubble"></div>`;
  div.querySelector(".bubble").textContent = text;
  historyEl.appendChild(div);
  historyEl.scrollTop = historyEl.scrollHeight;
}

commandForm.addEventListener("submit", async (e) => {
  e.preventDefault();
  const text = commandInput.value.trim();
  if (!text) return;
  addMessage("user", text);
  commandInput.value = "";
  try {
    const res = await fetch("/api/command", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ text }),
    });
    const data = await res.json();
    addMessage("shiv", data.response || "...");
  } catch (err) {
    addMessage("shiv", "Dashboard backend se connect nahi ho paya.");
  }
  loadHistory();
  loadNotes();
  loadReminders();
});

async function loadNotes() {
  try {
    const res = await fetch("/api/notes");
    const notes = await res.json();
    notesList.innerHTML = "";
    if (!notes.length) {
      notesList.innerHTML = '<li class="empty">No notes yet.</li>';
      return;
    }
    notes.forEach((n) => {
      const li = document.createElement("li");
      li.innerHTML = `<span>${escapeHtml(n.content)}</span><button class="remove" data-id="${n.id}">remove</button>`;
      li.querySelector(".remove").addEventListener("click", async () => {
        await fetch(`/api/notes/${n.id}`, { method: "DELETE" });
        loadNotes();
      });
      notesList.appendChild(li);
    });
  } catch (err) {}
}

async function loadReminders() {
  try {
    const res = await fetch("/api/reminders");
    const reminders = await res.json();
    const pending = reminders.filter((r) => !r.done);
    remindersList.innerHTML = "";
    if (!pending.length) {
      remindersList.innerHTML = '<li class="empty">No reminders set.</li>';
      return;
    }
    pending.forEach((r) => {
      const when = new Date(r.remind_at).toLocaleString([], { hour: "2-digit", minute: "2-digit", month: "short", day: "numeric" });
      const li = document.createElement("li");
      li.innerHTML = `<span>${escapeHtml(r.content)}<div class="meta">${when}</div></span><button class="remove" data-id="${r.id}">remove</button>`;
      li.querySelector(".remove").addEventListener("click", async () => {
        await fetch(`/api/reminders/${r.id}`, { method: "DELETE" });
        loadReminders();
      });
      remindersList.appendChild(li);
    });
  } catch (err) {}
}

async function loadHistory() {
  try {
    const res = await fetch("/api/history");
    const rows = await res.json();
    historyBody.innerHTML = "";
    rows.forEach((r) => {
      const tr = document.createElement("tr");
      const t = new Date(r.timestamp).toLocaleString([], { hour: "2-digit", minute: "2-digit", month: "short", day: "numeric" });
      tr.innerHTML = `<td class="dim">${t}</td><td class="dim">${r.source}</td><td>${escapeHtml(r.command_text)}</td><td>${escapeHtml(r.response_text)}</td>`;
      historyBody.appendChild(tr);
    });
  } catch (err) {}
}

noteForm.addEventListener("submit", async (e) => {
  e.preventDefault();
  const content = noteInput.value.trim();
  if (!content) return;
  await fetch("/api/notes", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ content }),
  });
  noteInput.value = "";
  loadNotes();
});

reminderForm.addEventListener("submit", async (e) => {
  e.preventDefault();
  const text = reminderInput.value.trim();
  if (!text) return;
  await fetch("/api/reminders", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ text }),
  });
  reminderInput.value = "";
  loadReminders();
});

function escapeHtml(str) {
  const div = document.createElement("div");
  div.textContent = str;
  return div.innerHTML;
}

// initial load
loadNotes();
loadReminders();
loadHistory();
addMessage("shiv", "Hey Rajshree! Yahan se bhi mujhse baat kar sakti ho — type karke.");
