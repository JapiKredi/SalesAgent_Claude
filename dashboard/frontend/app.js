// Page is served at /d/<token>/ ; read the token from the path.
const TOKEN = location.pathname.split("/").filter(Boolean)[1] || "";
const API = "/api";
const headers = { "Content-Type": "application/json", "X-Dashboard-Token": TOKEN };

const COMMANDS = [
  ["prospect","Full prospect audit","url"],
  ["quick","60-second snapshot","url"],
  ["research","Company research","url"],
  ["qualify","Lead qualification (BANT/MEDDIC)","url"],
  ["contacts","Find decision makers","url"],
  ["outreach","Cold outreach emails","prospect"],
  ["followup","Follow-up emails","prospect"],
  ["prep","Meeting prep brief","url"],
  ["proposal","Client proposal","client"],
  ["objections","Objection playbook","topic"],
  ["icp","Ideal Customer Profile","description"],
  ["competitors","Competitive intel","url"],
  ["report","Pipeline report","none"],
  ["report-pdf","Pipeline report (PDF)","none"],
];
const PLACEHOLDER = {
  url:"Paste a company or LinkedIn URL (https://…)",
  prospect:"Prospect or company name",
  client:"Client name",
  topic:"Objection topic (e.g. pricing)",
  description:"Describe your ideal customer",
};

const $ = (id) => document.getElementById(id);
const select = $("command"), argRow = $("argRow"), argInput = $("arg"), runBtn = $("run");

COMMANDS.forEach(([name, label]) => {
  const o = document.createElement("option");
  o.value = name; o.textContent = label; select.appendChild(o);
});

function syncArgRow() {
  const kind = COMMANDS.find(c => c[0] === select.value)[2];
  if (kind === "none") { argRow.classList.add("hidden"); }
  else { argRow.classList.remove("hidden"); argInput.placeholder = PLACEHOLDER[kind]; argInput.value = ""; }
}
select.addEventListener("change", syncArgRow);
syncArgRow();

async function refreshUsage() {
  try {
    const r = await fetch(`${API}/usage`, { headers });
    if (!r.ok) return;
    const u = await r.json();
    $("usage").textContent = `${u.remaining} of ${u.limit} runs left today`;
  } catch (_) {}
}
refreshUsage();

function show(id) { $(id).classList.remove("hidden"); }
function hide(id) { $(id).classList.add("hidden"); }

runBtn.addEventListener("click", async () => {
  hide("errorBox"); hide("outputBox"); show("statusBox");
  $("statusText").textContent = "Starting…";
  runBtn.disabled = true;

  let res;
  try {
    res = await fetch(`${API}/run`, {
      method: "POST", headers,
      body: JSON.stringify({ command: select.value, arg: argInput.value }),
    });
  } catch (e) { return fail("Network error — please try again."); }

  if (res.status === 429) return fail((await res.json()).detail || "Please try again later.");
  if (res.status === 400) return fail((await res.json()).detail || "Please check your input.");
  if (!res.ok) return fail("Something went wrong — please try again.");

  const { run_id } = await res.json();
  const ev = new EventSource(`${API}/status/${run_id}?token=${encodeURIComponent(TOKEN)}`);
  let finished = false;
  let reconnects = 0;
  ev.onmessage = (m) => {
    reconnects = 0;                       // a message = the connection is healthy
    const data = JSON.parse(m.data);
    if (data.kind === "status") { $("statusText").textContent = data.text; }
    else if (data.kind === "error") { finished = true; ev.close(); fail(data.message || "Something went wrong."); }
    else if (data.kind === "result") {
      finished = true; ev.close(); hide("statusBox"); show("outputBox");
      $("output").innerHTML = marked.parse(data.output || "_No output._");
      setupDownload(data);
      runBtn.disabled = false; refreshUsage();
    }
  };
  // EventSource auto-reconnects when the connection drops, and the server replays
  // the run's events on reconnect — so a long run survives a flaky network/tunnel.
  // Don't close on a transient error; only give up after many failed retries.
  ev.onerror = () => {
    if (finished) return;                 // expected close after result/error
    reconnects += 1;
    if (reconnects > 40) { ev.close(); fail("Connection lost — reload the page; your run may still be finishing."); return; }
    $("statusText").textContent = "Reconnecting…";
  };
});

function setupDownload(data) {
  const dl = $("download");
  const pdf = (data.files || []).find(f => f.endsWith(".pdf"));
  if (pdf) {
    dl.href = `${API}/download/${encodeURIComponent(pdf)}?token=${encodeURIComponent(TOKEN)}`;
    dl.removeAttribute("download"); dl.textContent = "Download PDF"; dl.classList.remove("hidden"); return;
  }
  const blob = new Blob([data.output || ""], { type: "text/markdown" });
  dl.href = URL.createObjectURL(blob); dl.download = `${select.value}.md`;
  dl.textContent = "Download .md"; dl.classList.remove("hidden");
}

function fail(msg) {
  hide("statusBox"); show("errorBox"); $("errorBox").textContent = msg; runBtn.disabled = false;
}
