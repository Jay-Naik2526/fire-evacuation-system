const socket = io("http://localhost:5000");

let selectedZone = null;

const zoneNames = {
  "Z1":"Main Lobby","Z2":"Cafeteria","Z3":"Admin Block",
  "Z4":"Utility Room","Z5":"Lab A","Z6":"Lab B",
  "Z7":"Staff Lounge","Z8":"HOD Office","Z9":"Server Room",
  "Z10":"Conference Hall","Z11":"Director Office","Z12":"Records Room",
  "EXIT1":"Exit 1","EXIT2":"Exit 2","EXIT3":"Exit 3","EXIT4":"Exit 4"
};

function $(id) { return document.getElementById(id); }
function setText(id, val) { const el = $(id); if (el) el.textContent = val; }
function setClass(id, cls) { const el = $(id); if (el) el.className = cls; }

// ── Connection ────────────────────────────────────────────────────────────────

socket.on("connect", () => {
  const dot = $("connDot");
  const txt = $("connText");
  const pill = $("connPill");
  if (dot) { dot.classList.add("connected"); }
  if (txt) txt.textContent = "Connected";
  if (pill) pill.style.borderColor = "rgba(16,185,129,0.3)";
  addLog("System connected to backend", "SAFE");
});

socket.on("disconnect", () => {
  const dot = $("connDot");
  const txt = $("connText");
  const pill = $("connPill");
  if (dot) dot.classList.remove("connected");
  if (txt) txt.textContent = "Disconnected";
  if (pill) pill.style.borderColor = "rgba(255,59,59,0.3)";
  addLog("Lost connection to backend", "FIRE");
});

// ── Zone Updates ──────────────────────────────────────────────────────────────

socket.on("zone_update", (data) => {
  let fireCount = 0, smokeCount = 0, safeCount = 0;
  let hasNewFire = false;

  for (const [zoneId, info] of Object.entries(data)) {
    const el = $(zoneId);
    if (!el) continue;

    const prevStatus = el.classList.contains("FIRE")  ? "FIRE"
                     : el.classList.contains("SMOKE") ? "SMOKE"
                     : "SAFE";

    el.className = "zone " + info.status;
    if (zoneId === selectedZone) el.classList.add("selected");

    const badge = el.querySelector(".zone-badge");
    if (badge) badge.textContent = info.status;

    const smokeEl = $(`${zoneId}-smoke`);
    const crowdEl = $(`${zoneId}-crowd`);
    if (smokeEl && info.smoke !== undefined) smokeEl.textContent = Math.round(info.smoke) + " ppm";
    if (crowdEl && info.crowd !== undefined) crowdEl.textContent = info.crowd + " ppl";

    if (info.status === "FIRE")       { fireCount++; if (prevStatus !== "FIRE") hasNewFire = true; }
    else if (info.status === "SMOKE") smokeCount++;
    else                              safeCount++;

    if (prevStatus !== info.status) {
      addLog(`${zoneId} (${zoneNames[zoneId] || zoneId}) → ${info.status}`, info.status);
    }
  }

  setText("fireCount",  fireCount);
  setText("smokeCount", smokeCount);
  setText("safeCount",  safeCount);

  if (hasNewFire) {
    const fireZones = Object.entries(data)
      .filter(([,v]) => v.status === "FIRE")
      .map(([k]) => zoneNames[k] || k).join(", ");
    const banner = $("alertBanner");
    const alertTxt = $("alertText");
    if (banner && alertTxt) {
      alertTxt.textContent = "Fire detected in " + fireZones + " — evacuate immediately!";
      banner.style.display = "flex";
    }
  }

  if (selectedZone) socket.emit("request_path", { zone: selectedZone });
});

// ── MQTT Data ─────────────────────────────────────────────────────────────────

socket.on("mqtt_data", (data) => {
  const smokeEl = $(`${data.zone}-smoke`);
  const crowdEl = $(`${data.zone}-crowd`);
  if (smokeEl) smokeEl.textContent = Math.round(data.smoke) + " ppm";
  if (crowdEl) crowdEl.textContent = data.crowd + " ppl";
});

// ── Path Updates ──────────────────────────────────────────────────────────────

socket.on("path_update", (data) => {
  const pathDisplay = $("pathDisplay");
  const pathHint    = $("pathHint");
  if (!pathDisplay) return;

  pathDisplay.innerHTML = "";
  document.querySelectorAll(".exit-box").forEach(e => e.classList.remove("highlighted"));

  if (!data.path || data.path.length === 0 || data.path[0] === "No safe path found") {
    pathDisplay.innerHTML = `
      <div style="text-align:center;padding:16px;width:100%">
        <div style="color:#ff6b6b;font-size:13px;margin-bottom:6px">All paths blocked!</div>
        <div style="color:#4a5568;font-size:11px">Call emergency services</div>
      </div>`;
    if (pathHint) pathHint.textContent = "no route";
    return;
  }

  if (pathHint) pathHint.textContent = (data.path.length - 1) + " steps";

  data.path.forEach((node, index) => {
    const div = document.createElement("div");
    div.className = "path-node";
    if (index === 0) div.classList.add("current");
    else if (node.startsWith("EXIT")) {
      div.classList.add("exit");
      const num = node.replace("EXIT", "");
      const exitEl = $("exit" + num);
      if (exitEl) exitEl.classList.add("highlighted");
    }
    div.textContent = zoneNames[node] || node;
    pathDisplay.appendChild(div);

    if (index < data.path.length - 1) {
      const arrow = document.createElement("span");
      arrow.className = "path-arrow";
      arrow.textContent = " → ";
      pathDisplay.appendChild(arrow);
    }
  });

  const pathStr = data.path.map(n => zoneNames[n] || n).join(" → ");
  addLog("Path from " + (zoneNames[data.from] || data.from) + ": " + pathStr, "SAFE");
});

// ── Zone Click ────────────────────────────────────────────────────────────────

function selectZone(zoneId) {
  selectedZone = zoneId;
  document.querySelectorAll(".zone").forEach(z => z.classList.remove("selected"));
  const el = $(zoneId);
  if (el) el.classList.add("selected");
  const sel = $("zoneSelect");
  if (sel) sel.value = zoneId;
  socket.emit("request_path", { zone: zoneId });
  addLog("Selected " + (zoneNames[zoneId] || zoneId) + " — calculating path...", "SAFE");
}

// ── Controls ──────────────────────────────────────────────────────────────────

function triggerFire() {
  const zone = $("zoneSelect").value;
  if (!zone) { alert("Please select a zone first!"); return; }
  socket.emit("trigger_fire", { zone });
  addLog("Fire triggered in " + (zoneNames[zone] || zone), "FIRE");
}

function clearFire() {
  const zone = $("zoneSelect").value;
  if (!zone) { alert("Please select a zone first!"); return; }
  socket.emit("clear_fire", { zone });
  addLog((zoneNames[zone] || zone) + " cleared", "SAFE");
}

function getPath() {
  const zone = $("zoneSelect").value;
  if (!zone) { alert("Please select a zone first!"); return; }
  selectedZone = zone;
  document.querySelectorAll(".zone").forEach(z => z.classList.remove("selected"));
  const el = $(zone);
  if (el) el.classList.add("selected");
  socket.emit("request_path", { zone });
}

// ── Event Log ─────────────────────────────────────────────────────────────────

function addLog(message, status) {
  const logList = $("logList");
  if (!logList) return;
  const now = new Date().toLocaleTimeString("en-IN", {
    hour: "2-digit", minute: "2-digit", second: "2-digit"
  });
  const item = document.createElement("div");
  item.className = "log-item " + (status || "SAFE");
  item.innerHTML = `
    <span class="log-dot"></span>
    <div class="log-body">
      <div class="log-time">${now}</div>
      <div class="log-msg">${message}</div>
    </div>`;
  logList.insertBefore(item, logList.firstChild);
  while (logList.children.length > 30) logList.removeChild(logList.lastChild);
}