const socket = io("http://localhost:5000");

let selectedZone = null;

// ─── Connection ───────────────────────────────────────

socket.on("connect", () => {
  document.getElementById("connDot").classList.add("connected");
  document.getElementById("connText").textContent = "Connected";
  addLog("System connected to backend", "SAFE");
});

socket.on("disconnect", () => {
  document.getElementById("connDot").classList.remove("connected");
  document.getElementById("connText").textContent = "Disconnected";
  addLog("Lost connection to backend", "FIRE");
});

// ─── Zone Updates ─────────────────────────────────────

socket.on("zone_update", (data) => {
  let fireCount  = 0;
  let smokeCount = 0;
  let safeCount  = 0;

  for (const [zoneId, info] of Object.entries(data)) {
    const el = document.getElementById(zoneId);
    if (!el) continue;

    const prevStatus = el.className.includes("FIRE")  ? "FIRE"
                     : el.className.includes("SMOKE") ? "SMOKE"
                     : "SAFE";

    // Update zone card color
    el.className = `zone ${info.status}`;

    // Update status text inside card
    el.querySelector(".zone-status").textContent = info.status;

    // Count statuses
    if (info.status === "FIRE")       fireCount++;
    else if (info.status === "SMOKE") smokeCount++;
    else                              safeCount++;

    // Log if status changed
    if (prevStatus !== info.status) {
      addLog(`${zoneId} changed to ${info.status}`, info.status);
    }
  }

  // Update summary numbers
  document.getElementById("fireCount").textContent  = fireCount;
  document.getElementById("smokeCount").textContent = smokeCount;
  document.getElementById("safeCount").textContent  = safeCount;

  // If a zone is selected refresh its path
  if (selectedZone) {
    socket.emit("request_path", { zone: selectedZone });
  }
});

// ─── Path Updates ─────────────────────────────────────

socket.on("path_update", (data) => {
    const pathDisplay = document.getElementById("pathDisplay");
    pathDisplay.innerHTML = "";
  
    if (!data.path || data.path.length === 0) {
      pathDisplay.innerHTML = '<span style="color:#e94560">No safe path found!</span>';
      return;
    }
  
    if (data.path[0] === "No safe path found") {
      pathDisplay.innerHTML = '<span style="color:#e94560">⚠️ All paths blocked! Call emergency services!</span>';
      return;
    }
  
    data.path.forEach((node, index) => {
      const div = document.createElement("div");
      div.className = "path-node";
  
      if (index === 0) {
        div.classList.add("current");
      } else if (node.startsWith("EXIT")) {
        div.classList.add("exit");
      }
  
      // Show zone name not just ID
      const zoneNames = {
        "Z1":"Main Lobby","Z2":"Cafeteria","Z3":"Admin Block",
        "Z4":"Utility Room","Z5":"Lab A","Z6":"Lab B",
        "Z7":"Staff Lounge","Z8":"HOD Office","Z9":"Server Room",
        "Z10":"Conference Hall","Z11":"Director Office","Z12":"Records Room",
        "EXIT1":"Exit 1","EXIT2":"Exit 2","EXIT3":"Exit 3","EXIT4":"Exit 4"
      };
  
      div.textContent = zoneNames[node] || node;
      div.title = node;
      pathDisplay.appendChild(div);
  
      if (index < data.path.length - 1) {
        const arrow = document.createElement("span");
        arrow.className = "path-arrow";
        arrow.textContent = "→";
        pathDisplay.appendChild(arrow);
      }
    });
  
    addLog(`Path from ${data.from}: ${data.path.join(" → ")}`, "SAFE");
  });

// ─── Zone Click ───────────────────────────────────────

function selectZone(zoneId) {
  selectedZone = zoneId;

  // Highlight selected zone
  document.querySelectorAll(".zone").forEach(z => {
    z.style.outline = "none";
  });
  document.getElementById(zoneId).style.outline = "2px solid #534ab7";

  // Update dropdown
  document.getElementById("zoneSelect").value = zoneId;

  // Get safe path
  socket.emit("request_path", { zone: zoneId });

  addLog(`Selected zone ${zoneId} — calculating path...`, "SAFE");
}

// ─── Controls ─────────────────────────────────────────

function triggerFire() {
  const zone = document.getElementById("zoneSelect").value;
  if (!zone) {
    alert("Please select a zone first!");
    return;
  }
  socket.emit("trigger_fire", { zone: zone });
  addLog(`🔥 Fire triggered in ${zone}!`, "FIRE");
}

function clearFire() {
  const zone = document.getElementById("zoneSelect").value;
  if (!zone) {
    alert("Please select a zone first!");
    return;
  }
  socket.emit("clear_fire", { zone: zone });
  addLog(`✅ ${zone} cleared`, "SAFE");
}

function getPath() {
  const zone = document.getElementById("zoneSelect").value;
  if (!zone) {
    alert("Please select a zone first!");
    return;
  }
  selectedZone = zone;
  socket.emit("request_path", { zone: zone });
}

// ─── Event Log ────────────────────────────────────────

function addLog(message, status) {
  const logList = document.getElementById("logList");
  const now = new Date().toLocaleTimeString();

  const item = document.createElement("div");
  item.className = `log-item ${status}`;
  item.innerHTML = `<div class="log-time">${now}</div>${message}`;

  logList.insertBefore(item, logList.firstChild);

  // Keep only last 20 logs
  while (logList.children.length > 20) {
    logList.removeChild(logList.lastChild);
  }
}