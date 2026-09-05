const historyEl = document.getElementById("history");
const commandForm = document.getElementById("command-form");
const commandInput = document.getElementById("command-input");
const micButton = document.getElementById("mic-button");

const noteForm = document.getElementById("note-form");
const noteInput = document.getElementById("note-input");
const notesList = document.getElementById("notes-list");

const reminderForm = document.getElementById("reminder-form");
const reminderInput = document.getElementById("reminder-input");
const remindersList = document.getElementById("reminders-list");

const historyBody = document.getElementById("history-body");


// ============================================================
// BROWSER MICROPHONE
// ============================================================

let audioContext = null;
let mediaStream = null;
let sourceNode = null;
let processorNode = null;
let audioBuffers = [];
let isRecording = false;


// ============================================================
// START RECORDING
// ============================================================

async function startRecording() {

  try {

    mediaStream = await navigator.mediaDevices.getUserMedia({
      audio: true
    });

    audioContext = new AudioContext();

    sourceNode =
      audioContext.createMediaStreamSource(
        mediaStream
      );

    processorNode =
      audioContext.createScriptProcessor(
        4096,
        1,
        1
      );

    audioBuffers = [];

    processorNode.onaudioprocess = (event) => {

      if (!isRecording) return;

      const inputData =
        event.inputBuffer.getChannelData(0);

      audioBuffers.push(
        new Float32Array(inputData)
      );

    };

    sourceNode.connect(processorNode);

    processorNode.connect(
      audioContext.destination
    );

    isRecording = true;

    micButton.textContent =
      "🔴 Listening...";

    micButton.disabled = false;

  } catch (error) {

    console.error(
      "Microphone error:",
      error
    );

    micButton.textContent =
      "🎤 Talk";

    alert(
      "Microphone access nahi mil raha. Browser permission check karo."
    );

  }

}


// ============================================================
// STOP RECORDING
// ============================================================

async function stopRecording() {

  if (!isRecording) return;

  isRecording = false;

  micButton.textContent =
    "Processing...";

  micButton.disabled = true;

  if (processorNode) {
    processorNode.disconnect();
  }

  if (sourceNode) {
    sourceNode.disconnect();
  }

  if (mediaStream) {

    mediaStream
      .getTracks()
      .forEach(track => track.stop());

  }

  const sampleRate =
    audioContext.sampleRate;

  const wavBlob =
    createWavBlob(
      audioBuffers,
      sampleRate
    );

  await sendVoiceToServer(
    wavBlob
  );

  if (audioContext) {
    await audioContext.close();
  }

  audioContext = null;
  mediaStream = null;
  sourceNode = null;
  processorNode = null;
  audioBuffers = [];

  micButton.textContent =
    "🎤 Talk";

  micButton.disabled = false;

}


// ============================================================
// CREATE WAV FILE
// ============================================================

function createWavBlob(
  buffers,
  sampleRate
) {

  let totalLength = 0;

  buffers.forEach(
    buffer => {
      totalLength += buffer.length;
    }
  );

  const samples =
    new Float32Array(totalLength);

  let offset = 0;

  buffers.forEach(buffer => {

    samples.set(
      buffer,
      offset
    );

    offset += buffer.length;

  });

  const buffer =
    new ArrayBuffer(
      44 + samples.length * 2
    );

  const view =
    new DataView(buffer);


  function writeString(
    offset,
    string
  ) {

    for (
      let i = 0;
      i < string.length;
      i++
    ) {

      view.setUint8(
        offset + i,
        string.charCodeAt(i)
      );

    }

  }


  writeString(
    0,
    "RIFF"
  );

  view.setUint32(
    4,
    36 + samples.length * 2,
    true
  );

  writeString(
    8,
    "WAVE"
  );

  writeString(
    12,
    "fmt "
  );

  view.setUint32(
    16,
    16,
    true
  );

  view.setUint16(
    20,
    1,
    true
  );

  view.setUint16(
    22,
    1,
    true
  );

  view.setUint32(
    24,
    sampleRate,
    true
  );

  view.setUint32(
    28,
    sampleRate * 2,
    true
  );

  view.setUint16(
    32,
    2,
    true
  );

  view.setUint16(
    34,
    16,
    true
  );

  writeString(
    36,
    "data"
  );

  view.setUint32(
    40,
    samples.length * 2,
    true
  );


  let index = 44;

  for (
    let i = 0;
    i < samples.length;
    i++
  ) {

    let sample =
      Math.max(
        -1,
        Math.min(
          1,
          samples[i]
        )
      );

    sample =
      sample < 0
        ? sample * 0x8000
        : sample * 0x7FFF;

    view.setInt16(
      index,
      sample,
      true
    );

    index += 2;

  }


  return new Blob(
    [buffer],
    {
      type: "audio/wav"
    }
  );

}


// ============================================================
// SEND AUDIO TO PYTHON / VOSK
// ============================================================

async function sendVoiceToServer(
  audioBlob
) {

  try {

    const formData =
      new FormData();

    formData.append(
      "audio",
      audioBlob,
      "voice.wav"
    );

    const res =
      await fetch(
        "/api/voice",
        {
          method: "POST",
          body: formData
        }
      );

    const data =
      await res.json();

    console.log(
      "Voice server response:",
      data
    );

    if (data.error) {

      addMessage(
        "shiv",
        "Voice processing error: " +
        data.error
      );

      return;

    }

    const recognizedText =
      data.text || "";

    if (recognizedText) {

      addMessage(
        "user",
        recognizedText
      );

    }

    addMessage(
      "shiv",
      data.response ||
      "I couldn't understand that."
    );

    loadHistory();
    loadNotes();
    loadReminders();

  } catch (error) {

    console.error(
      "Voice request error:",
      error
    );

    addMessage(
      "shiv",
      "Voice server se connect nahi ho paya."
    );

  }

}


// ============================================================
// MIC BUTTON
// ============================================================

micButton.addEventListener(
  "click",
  () => {

    if (isRecording) {

      stopRecording();

    } else {

      startRecording();

    }

  }
);


// ============================================================
// ADD MESSAGE
// ============================================================

function addMessage(who, text) {

  const div =
    document.createElement("div");

  div.className =
    `msg ${who}`;

  div.innerHTML = `
    <div class="who">
      ${who === "user" ? "You" : "Shiv"}
    </div>

    <div class="bubble"></div>
  `;

  div.querySelector(
    ".bubble"
  ).textContent = text;

  historyEl.appendChild(div);

  historyEl.scrollTop =
    historyEl.scrollHeight;

}


// ============================================================
// TEXT COMMAND
// ============================================================

commandForm.addEventListener(
  "submit",
  async (e) => {

    e.preventDefault();

    const text =
      commandInput.value.trim();

    if (!text) return;

    addMessage(
      "user",
      text
    );

    commandInput.value = "";

    try {

      const res =
        await fetch(
          "/api/command",
          {
            method: "POST",

            headers: {
              "Content-Type":
                "application/json"
            },

            body: JSON.stringify({
              text: text
            })
          }
        );

      const data =
        await res.json();

      addMessage(
        "shiv",
        data.response ||
        "I don't have a response for that."
      );

    } catch (err) {

      console.error(
        "Command error:",
        err
      );

      addMessage(
        "shiv",
        "Dashboard backend se connect nahi ho paya."
      );

    }

    loadHistory();
    loadNotes();
    loadReminders();

  }
);


// ============================================================
// NOTES
// ============================================================

async function loadNotes() {

  try {

    const res =
      await fetch("/api/notes");

    const notes =
      await res.json();

    notesList.innerHTML = "";

    if (!notes.length) {

      notesList.innerHTML =
        '<li class="empty">No notes yet.</li>';

      return;

    }

    notes.forEach((n) => {

      const li =
        document.createElement("li");

      li.innerHTML = `
        <span>
          ${escapeHtml(n.content)}
        </span>

        <button
          class="remove"
          data-id="${n.id}">
          remove
        </button>
      `;

      li.querySelector(
        ".remove"
      ).addEventListener(
        "click",
        async () => {

          await fetch(
            `/api/notes/${n.id}`,
            {
              method: "DELETE"
            }
          );

          loadNotes();

        }
      );

      notesList.appendChild(li);

    });

  } catch (err) {

    console.log(
      "Could not load notes:",
      err
    );

  }

}


// ============================================================
// REMINDERS
// ============================================================

async function loadReminders() {

  try {

    const res =
      await fetch("/api/reminders");

    const reminders =
      await res.json();

    const pending =
      reminders.filter(
        (r) => !r.done
      );

    remindersList.innerHTML = "";

    if (!pending.length) {

      remindersList.innerHTML =
        '<li class="empty">No reminders set.</li>';

      return;

    }

    pending.forEach((r) => {

      const when =
        new Date(
          r.remind_at
        ).toLocaleString(
          [],
          {
            hour: "2-digit",
            minute: "2-digit",
            month: "short",
            day: "numeric"
          }
        );

      const li =
        document.createElement("li");

      li.innerHTML = `
        <span>
          ${escapeHtml(r.content)}

          <div class="meta">
            ${when}
          </div>
        </span>

        <button
          class="remove"
          data-id="${r.id}">
          remove
        </button>
      `;

      li.querySelector(
        ".remove"
      ).addEventListener(
        "click",
        async () => {

          await fetch(
            `/api/reminders/${r.id}`,
            {
              method: "DELETE"
            }
          );

          loadReminders();

        }
      );

      remindersList.appendChild(li);

    });

  } catch (err) {

    console.log(
      "Could not load reminders:",
      err
    );

  }

}


// ============================================================
// HISTORY
// ============================================================

async function loadHistory() {

  try {

    const res =
      await fetch("/api/history");

    const rows =
      await res.json();

    historyBody.innerHTML = "";

    rows.forEach((r) => {

      const tr =
        document.createElement("tr");

      const t =
        new Date(
          r.timestamp
        ).toLocaleString(
          [],
          {
            hour: "2-digit",
            minute: "2-digit",
            month: "short",
            day: "numeric"
          }
        );

      tr.innerHTML = `
        <td class="dim">
          ${t}
        </td>

        <td class="dim">
          ${escapeHtml(r.source)}
        </td>

        <td>
          ${escapeHtml(r.command_text)}
        </td>

        <td>
          ${escapeHtml(r.response_text)}
        </td>
      `;

      historyBody.appendChild(tr);

    });

  } catch (err) {

    console.log(
      "Could not load history:",
      err
    );

  }

}


// ============================================================
// ADD NOTE
// ============================================================

noteForm.addEventListener(
  "submit",
  async (e) => {

    e.preventDefault();

    const content =
      noteInput.value.trim();

    if (!content) return;

    await fetch(
      "/api/notes",
      {
        method: "POST",

        headers: {
          "Content-Type":
            "application/json"
        },

        body: JSON.stringify({
          content: content
        })
      }
    );

    noteInput.value = "";

    loadNotes();

  }
);


// ============================================================
// ADD REMINDER
// ============================================================

reminderForm.addEventListener(
  "submit",
  async (e) => {

    e.preventDefault();

    const text =
      reminderInput.value.trim();

    if (!text) return;

    await fetch(
      "/api/reminders",
      {
        method: "POST",

        headers: {
          "Content-Type":
            "application/json"
        },

        body: JSON.stringify({
          text: text
        })
      }
    );

    reminderInput.value = "";

    loadReminders();

  }
);


// ============================================================
// ESCAPE HTML
// ============================================================

function escapeHtml(str) {

  const div =
    document.createElement("div");

  div.textContent = str;

  return div.innerHTML;

}


// ============================================================
// INITIAL LOAD
// ============================================================

loadNotes();
loadReminders();
loadHistory();

addMessage(
  "shiv",
  "Hey Rajshree! Yahan se bhi mujhse baat kar sakti ho — type karke ya 🎤 Talk button se."
);