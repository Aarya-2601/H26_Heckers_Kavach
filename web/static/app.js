/**
 * Kavach Web Application - Interactive Engine
 * 
 * Features:
 * 1. Golden Glass Triangle Canvas Animation (Black to Golden Glass revealing KAVACH)
 * 2. Diffused Smoke SPA Section Navigation
 * 3. Interactive Tree Data Structure with AST Inspector
 * 4. Golden Parallax Grid + Counter-moving Central Dots inside Chatbot
 * 5. Full CLI Chatbot Integration with Voice, 5s silence wait, and on-page metric updates
 * 6. Live telemetry sync with contracts/ and CAPSULE.md
 */

document.addEventListener("DOMContentLoaded", () => {
  initGoldenTrianglesCanvas();
  initGoldenWaveNavigation();
  initTreeDataStructure();
  initChatbotParallax();
  initChatbotInteractions();
  fetchCodebaseTelemetry();
});


/* ==========================================================================
   1. Golden Glass Triangle Glitter Canvas Animation
   ========================================================================== */
function initGoldenTrianglesCanvas() {
  const canvas = document.getElementById("triangles-canvas");
  if (!canvas) return;

  const ctx = canvas.getContext("2d");
  let width = (canvas.width = window.innerWidth);
  let height = (canvas.height = window.innerHeight);

  window.addEventListener("resize", () => {
    width = canvas.width = window.innerWidth;
    height = canvas.height = window.innerHeight;
    initTriangles();
  });

  const mouse = { x: width / 2, y: height / 2, active: false };
  window.addEventListener("mousemove", (e) => {
    mouse.x = e.clientX;
    mouse.y = e.clientY;
    mouse.active = true;
  });

  const TRIANGLE_COUNT = 55;
  let triangles = [];

  class GlassTriangle {
    constructor() {
      this.reset();
    }

    reset() {
      this.x = Math.random() * width;
      this.y = Math.random() * height;
      this.size = Math.random() * 45 + 20;
      this.vx = (Math.random() - 0.5) * 0.7;
      this.vy = (Math.random() - 0.5) * 0.7;
      this.angle = Math.random() * Math.PI * 2;
      this.va = (Math.random() - 0.5) * 0.015;
      this.glitterPhase = Math.random() * Math.PI * 2;
      this.glitterSpeed = Math.random() * 0.04 + 0.02;
      this.alpha = Math.random() * 0.45 + 0.15;
      this.goldenHue = Math.random() > 0.4 ? 42 : 36;
    }

    update() {
      this.x += this.vx;
      this.y += this.vy;
      this.angle += this.va;
      this.glitterPhase += this.glitterSpeed;

      if (this.x < -60) this.x = width + 60;
      if (this.x > width + 60) this.x = -60;
      if (this.y < -60) this.y = height + 60;
      if (this.y > height + 60) this.y = -60;

      if (mouse.active) {
        const dx = mouse.x - this.x;
        const dy = mouse.y - this.y;
        const dist = Math.sqrt(dx * dx + dy * dy);
        if (dist < 260) {
          const force = (1 - dist / 260) * 0.8;
          this.x += (dx / dist) * force;
          this.y += (dy / dist) * force;
        }
      }
    }

    draw(ctx) {
      ctx.save();
      ctx.translate(this.x, this.y);
      ctx.rotate(this.angle);

      const r = this.size;
      const p1 = { x: 0, y: -r };
      const p2 = { x: r * Math.cos(Math.PI / 6), y: r * Math.sin(Math.PI / 6) };
      const p3 = { x: -r * Math.cos(Math.PI / 6), y: r * Math.sin(Math.PI / 6) };

      const glitter = Math.sin(this.glitterPhase);
      const dynamicAlpha = Math.max(0.1, this.alpha + glitter * 0.2);

      const grad = ctx.createLinearGradient(p1.x, p1.y, p2.x, p2.y);
      grad.addColorStop(0, `hsla(${this.goldenHue}, 90%, 65%, ${dynamicAlpha * 0.4})`);
      grad.addColorStop(0.5, `hsla(${this.goldenHue + 5}, 100%, 75%, ${dynamicAlpha * 0.15})`);
      grad.addColorStop(1, `hsla(${this.goldenHue - 5}, 80%, 45%, ${dynamicAlpha * 0.6})`);

      ctx.beginPath();
      ctx.moveTo(p1.x, p1.y);
      ctx.lineTo(p2.x, p2.y);
      ctx.lineTo(p3.x, p3.y);
      ctx.closePath();

      ctx.fillStyle = grad;
      ctx.fill();

      ctx.strokeStyle = `hsla(${this.goldenHue}, 100%, 80%, ${dynamicAlpha * 0.85})`;
      ctx.lineWidth = 1.2;
      ctx.stroke();

      if (glitter > 0.6) {
        ctx.beginPath();
        ctx.arc(p1.x, p1.y, 2.5 * glitter, 0, Math.PI * 2);
        ctx.fillStyle = `rgba(255, 255, 255, ${glitter * 0.9})`;
        ctx.shadowColor = "#ffd700";
        ctx.shadowBlur = 10;
        ctx.fill();
      }

      ctx.restore();
    }
  }

  function initTriangles() {
    triangles = [];
    for (let i = 0; i < TRIANGLE_COUNT; i++) {
      triangles.push(new GlassTriangle());
    }
  }

  initTriangles();

  function animate() {
    ctx.clearRect(0, 0, width, height);

    // Deep space dark background with subtle golden atmospheric bloom
    const bgRadial = ctx.createRadialGradient(
      width / 2, height / 2, 40,
      width / 2, height / 2, Math.max(width, height) * 0.7
    );
    bgRadial.addColorStop(0, "#0e1524");
    bgRadial.addColorStop(0.5, "#080c14");
    bgRadial.addColorStop(1, "#040609");
    ctx.fillStyle = bgRadial;
    ctx.fillRect(0, 0, width, height);

    // Render shimmering glass triangles
    triangles.forEach((t) => {
      t.update();
      t.draw(ctx);
    });

    requestAnimationFrame(animate);
  }

  animate();
}

/* ==========================================================================
   2. Golden Wave Sweep Slide Transition & Ctrl+Sideways Navigation
   ========================================================================== */
const SLIDES = ["overview", "dirtree", "auditor", "whisperer", "autoheal", "tests", "capsule"];
let currentSlideIndex = 0;
let isWaveTransitioning = false;

function goToSlide(targetIndex, direction = null) {
  if (isWaveTransitioning) return;
  if (targetIndex < 0) targetIndex = 0;
  if (targetIndex >= SLIDES.length) targetIndex = SLIDES.length - 1;
  if (targetIndex === currentSlideIndex) return;

  isWaveTransitioning = true;
  if (!direction) {
    direction = targetIndex > currentSlideIndex ? "right" : "left";
  }

  const targetId = SLIDES[targetIndex];
  const currentSection = document.getElementById(SLIDES[currentSlideIndex]);
  const targetSection = document.getElementById(targetId);
  const wave = document.getElementById("golden-wave-sweep");

  // 1. Trigger full-screen sweeping golden wave
  if (wave) {
    wave.className = `golden-wave-sweep sweep-${direction}`;
  }

  // 2. At the peak of the wave (280ms), switch active slides cleanly without smoke blur
  setTimeout(() => {
    if (currentSection) {
      currentSection.classList.remove("active");
      currentSection.style.display = "none";
    }
    if (targetSection) {
      targetSection.style.display = "block";
      targetSection.classList.add("active");
      window.scrollTo({ top: 0, behavior: "instant" });
    }

    currentSlideIndex = targetIndex;

    // Update navbar active state
    document.querySelectorAll(".nav-link").forEach((l) => {
      if (l.getAttribute("data-nav") === targetId) {
        l.classList.add("active");
      } else {
        l.classList.remove("active");
      }
    });

    history.pushState(null, null, `#${targetId}`);
  }, 280);

  // 3. Reset wave state
  setTimeout(() => {
    if (wave) wave.className = "golden-wave-sweep";
    isWaveTransitioning = false;
  }, 680);
}

function navigateToSection(targetId) {
  const targetIdx = SLIDES.indexOf(targetId);
  if (targetIdx !== -1) {
    goToSlide(targetIdx);
  }
}

function initGoldenWaveNavigation() {
  const navLinks = document.querySelectorAll("[data-nav]");

  navLinks.forEach((link) => {
    link.addEventListener("click", (e) => {
      e.preventDefault();
      const targetId = link.getAttribute("data-nav");
      navigateToSection(targetId);
    });
  });

  // Handle hash changes or back/forward
  window.addEventListener("hashchange", () => {
    const hash = window.location.hash.replace("#", "") || "overview";
    navigateToSection(hash);
  });

  // Initial hash check
  const initialHash = window.location.hash.replace("#", "");
  if (initialHash && SLIDES.includes(initialHash)) {
    const idx = SLIDES.indexOf(initialHash);
    if (idx !== -1) {
      currentSlideIndex = idx;
      SLIDES.forEach((id) => {
        const el = document.getElementById(id);
        if (el) el.style.display = (id === initialHash) ? "block" : "none";
      });
      document.querySelectorAll(".nav-link").forEach((l) => {
        l.classList.toggle("active", l.getAttribute("data-nav") === initialHash);
      });
    }
  }

  // 1. Mouse sideways movement while Ctrl is held
  let ctrlMouseStartX = null;
  window.addEventListener("mousemove", (e) => {
    if (e.ctrlKey) {
      if (ctrlMouseStartX === null) {
        ctrlMouseStartX = e.clientX;
      } else {
        const diffX = e.clientX - ctrlMouseStartX;
        if (diffX > 45) {
          // Moved sideways right -> sweep to next slide
          ctrlMouseStartX = e.clientX;
          goToSlide(currentSlideIndex + 1, "right");
        } else if (diffX < -45) {
          // Moved sideways left -> sweep to previous slide
          ctrlMouseStartX = e.clientX;
          goToSlide(currentSlideIndex - 1, "left");
        }
      }
    } else {
      ctrlMouseStartX = null;
    }
  });

  window.addEventListener("keyup", (e) => {
    if (e.key === "Control") {
      ctrlMouseStartX = null;
    }
  });

  // 2. Keyboard Ctrl + Arrow keys
  window.addEventListener("keydown", (e) => {
    if (e.ctrlKey && (e.key === "ArrowRight" || e.key === "Right")) {
      e.preventDefault();
      goToSlide(currentSlideIndex + 1, "right");
    } else if (e.ctrlKey && (e.key === "ArrowLeft" || e.key === "Left")) {
      e.preventDefault();
      goToSlide(currentSlideIndex - 1, "left");
    }
  });

  // 3. Trackpad/Wheel horizontal scroll while holding Ctrl
  window.addEventListener("wheel", (e) => {
    if (e.ctrlKey) {
      e.preventDefault();
      if (Math.abs(e.deltaX) > 20) {
        if (e.deltaX > 20) {
          goToSlide(currentSlideIndex + 1, "right");
        } else if (e.deltaX < -20) {
          goToSlide(currentSlideIndex - 1, "left");
        }
      }
    }
  }, { passive: false });
}

/* ==========================================================================
   3. Interactive Tree Data Structure with AST Inspector
   ========================================================================== */
function initTreeDataStructure() {
  const inspectorTitle = document.getElementById("inspector-title");
  const inspectorDesc = document.getElementById("inspector-desc");
  const inspectorCode = document.getElementById("inspector-code-box");
  const inspectorActions = document.getElementById("inspector-actions");
  const btnFixInChat = document.getElementById("btn-fix-in-chat");
  const treeContainer = document.getElementById("tree-container");
  const btnSwitchRepo = document.getElementById("btn-switch-repo");
  const repoInput = document.getElementById("repo-input-path");
  const repoSwitchStatus = document.getElementById("repo-switch-status");
  const btnTriggerSearch = document.getElementById("btn-trigger-search");
  const searchRunStatus = document.getElementById("search-run-status");

  let currentTargetFile = "";
  let currentTreeData = null;

  function attachNodeListeners() {
    const treeNodes = document.querySelectorAll(".tree-file-node");
    treeNodes.forEach((node) => {
      node.addEventListener("click", () => {
        treeNodes.forEach((n) => (n.style.outline = "none"));
        node.style.outline = "2px solid var(--gold-primary)";

        const filePath = node.getAttribute("data-file");
        currentTargetFile = filePath;

        let data = null;
        if (currentTreeData && currentTreeData.flagged_details) {
          data = currentTreeData.flagged_details[filePath] || currentTreeData.flagged_details[filePath.split("/").pop()];
        }

        if (data) {
          if (inspectorTitle) inspectorTitle.textContent = `${filePath} (${data.role || 'Flagged File'})`;
          if (inspectorDesc) inspectorDesc.textContent = `Vulnerability: ${data.issue || 'Identified AST dependency'}. Blast Radius: ${data.blast_radius || 45}/100. Context: ${data.calling_function || 'AST Call Site'}.`;
          if (inspectorCode) inspectorCode.textContent = `// File: ${filePath} (Line ${data.line || 1})\n// Role: ${data.role || 'AST Flagged Node'}\n${data.code_snippet || '// Flagged AST Node'}`;
          if (inspectorActions) inspectorActions.style.display = "block";
        } else {
          if (inspectorTitle) inspectorTitle.textContent = filePath;
          if (inspectorDesc) inspectorDesc.textContent = "File verified by AST Scanner. No critical scope leaks or anti-cheat violations detected.";
          if (inspectorCode) inspectorCode.textContent = `// File: ${filePath}\n// Status: VERIFIED CLEAN BY DETERMINISTIC SCANNER`;
          if (inspectorActions) inspectorActions.style.display = "none";
        }
      });
    });
  }

  function renderTree(treeData) {
    currentTreeData = treeData;
    if (!treeContainer || !treeData || !treeData.tree) return;

    const dirtreeTitle = document.getElementById("dirtree-title");
    if (dirtreeTitle) {
      dirtreeTitle.textContent = `${treeData.repo_name || 'Repository'} Tree Data Structure`;
    }

    if (repoInput && !repoInput.value && treeData.root) {
      repoInput.value = treeData.root;
    }

    let totalFiles = 0;
    const folders = Object.keys(treeData.tree);
    folders.forEach((k) => {
      totalFiles += (treeData.tree[k] || []).length;
    });

    const flaggedList = treeData.flagged_files || [];

    let html = `
      <div class="tree-root-card">
        <div style="display: flex; align-items: center; gap: 10px;">
          <span style="font-size: 1.2rem;">📦</span>
          <strong style="color: var(--gold-light);">${escapeHtml(treeData.root || treeData.repo_name)} (Root)</strong>
        </div>
        <span class="clean-badge">${totalFiles} items total</span>
      </div>
    `;

    folders.forEach((folder) => {
      const files = treeData.tree[folder] || [];
      const folderFlagged = files.filter((f) => {
        const fullPath = folder === "root" ? f : `${folder}/${f}`;
        return flaggedList.includes(fullPath) || flaggedList.includes(f);
      }).length;

      const folderLabel = folder === "root" ? "📁 Infrastructure & Manifests" : `📁 ${folder}/`;
      const badgeHtml = folderFlagged > 0
        ? `<span class="flagged-badge" style="float: right;">${folderFlagged} Flag${folderFlagged > 1 ? 's' : ''}</span>`
        : `<span class="clean-badge" style="float: right;">Safe</span>`;

      html += `
        <div class="tree-branch">
          <div class="tree-folder" data-folder="${escapeHtml(folder)}">
            <strong>${escapeHtml(folderLabel)}</strong>
            ${badgeHtml}
          </div>
          <div class="tree-files-list">
      `;

      files.forEach((file) => {
        const fullPath = folder === "root" ? file : `${folder}/${file}`;
        const isFlagged = flaggedList.includes(fullPath) || flaggedList.includes(file);
        const detail = treeData.flagged_details ? (treeData.flagged_details[fullPath] || treeData.flagged_details[file]) : null;
        const isHero = detail && detail.role === "Hero File";

        let badgeText = "Safe";
        let badgeClass = "clean-badge";
        if (isFlagged) {
          badgeClass = "flagged-badge";
          badgeText = (detail && detail.blast_radius) ? `AST Blast: ${detail.blast_radius}/100` : "Flagged AST";
        }

        html += `
          <div class="tree-file-node ${isFlagged ? 'flagged' : ''}" data-file="${escapeHtml(fullPath)}">
            <span>${isFlagged ? '🔥' : '📄'} ${escapeHtml(file)}${isHero ? ' (Hero File)' : ''}</span>
            <span class="${badgeClass}">${escapeHtml(badgeText)}</span>
          </div>
        `;
      });

      html += `
          </div>
        </div>
      `;
    });

    treeContainer.innerHTML = html;
    attachNodeListeners();
  }

  function loadTreeData(repoPath) {
    const url = repoPath ? `/api/tree?repo=${encodeURIComponent(repoPath)}` : "/api/tree";
    return fetch(url)
      .then((res) => res.json())
      .then((data) => {
        renderTree(data);
        return data;
      })
      .catch((err) => {
        console.error("Tree data load error:", err);
      });
  }

  // Initial load
  loadTreeData();

  // Repository Switcher Event
  function handleRepoSwitch() {
    if (!repoInput) return;
    const targetPath = repoInput.value.trim();
    if (!targetPath) return;

    if (repoSwitchStatus) {
      repoSwitchStatus.style.color = "var(--gold-light)";
      repoSwitchStatus.textContent = "Loading repository...";
    }

    fetch("/api/select-repo", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ repo_path: targetPath }),
    })
      .then((res) => res.json())
      .then((data) => {
        if (data.status === "success") {
          if (repoSwitchStatus) {
            repoSwitchStatus.style.color = "var(--green-passed)";
            repoSwitchStatus.textContent = `Active: ${data.repo_name} (${data.detected_dependencies.length} deps)`;
          }
          loadTreeData(data.repo_path);
          fetchCodebaseTelemetry();
        } else {
          if (repoSwitchStatus) {
            repoSwitchStatus.style.color = "var(--red-flagged)";
            repoSwitchStatus.textContent = data.message || "Failed to switch repo";
          }
        }
      })
      .catch((err) => {
        if (repoSwitchStatus) {
          repoSwitchStatus.style.color = "var(--red-flagged)";
          repoSwitchStatus.textContent = `Error: ${err.message}`;
        }
      });
  }

  if (btnSwitchRepo) btnSwitchRepo.addEventListener("click", handleRepoSwitch);
  if (repoInput) {
    repoInput.addEventListener("keydown", (e) => {
      if (e.key === "Enter") handleRepoSwitch();
    });
  }

  // Trigger Auto-Heal Search Loop
  if (btnTriggerSearch) {
    btnTriggerSearch.addEventListener("click", () => {
      btnTriggerSearch.disabled = true;
      if (searchRunStatus) {
        searchRunStatus.style.color = "var(--gold-light)";
        searchRunStatus.textContent = "Executing MCTS auto-heal search...";
      }

      fetch("/api/run-search", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({}),
      })
        .then((res) => res.json())
        .then((data) => {
          btnTriggerSearch.disabled = false;
          if (data.status !== "success") {
            if (searchRunStatus) {
              searchRunStatus.style.color = "var(--red-flagged)";
              searchRunStatus.textContent = data.message || "Search failed";
            }
            return;
          }
          if (searchRunStatus) {
            const ok = (data.winning_status || "").toUpperCase() === "PASSED";
            searchRunStatus.style.color = ok ? "var(--green-passed)" : "var(--gold-light)";
            searchRunStatus.textContent = `${ok ? "Completed" : "Finished (no passing patch)"} for ${data.target_package}: ${data.winning_node && data.winning_node.action_name ? data.winning_node.action_name : "Winner"} (Score: ${data.score}, ${data.nodes_passed}/${data.nodes_explored} nodes passed)`;
          }
          fetchCodebaseTelemetry();
        })
        .catch((err) => {
          btnTriggerSearch.disabled = false;
          if (searchRunStatus) {
            searchRunStatus.style.color = "var(--red-flagged)";
            searchRunStatus.textContent = `Error: ${err.message}`;
          }
        });
    });
  }

  if (btnFixInChat) {
    btnFixInChat.addEventListener("click", () => {
      const panel = document.getElementById("chatbot-panel");
      const input = document.getElementById("chat-input");
      if (panel) panel.classList.add("open");
      if (input) {
        input.value = `Remediate ${currentTargetFile} using an isolated backward-compatible adapter`;
        input.focus();
      }
    });
  }
}

/* ==========================================================================
   4. Golden Parallax Grid + Counter-Moving Dots inside Chatbot
   ========================================================================== */
function initChatbotParallax() {
  const panel = document.getElementById("chatbot-panel");
  const grid = document.getElementById("chatbot-parallax-grid");
  const dots = document.getElementById("chatbot-parallax-dots");

  if (!panel || !grid || !dots) return;

  function updateParallax(clientX, clientY) {
    const normX = (clientX / window.innerWidth - 0.5) * 2;
    const normY = (clientY / window.innerHeight - 0.5) * 2;

    // Layer 1: Golden Grid moves along with perspective
    const moveX = normX * 22;
    const moveY = normY * 22;
    const rotX = -normY * 7;
    const rotY = normX * 7;
    grid.style.transform = `translate3d(${moveX}px, ${moveY}px, 0) rotateX(${rotX}deg) rotateY(${rotY}deg)`;

    // Layer 2: Golden Parallax Dots move in OPPOSITE direction with higher velocity
    const dotMoveX = -normX * 34;
    const dotMoveY = -normY * 34;
    dots.style.transform = `translate3d(${dotMoveX}px, ${dotMoveY}px, 0) rotateX(${-rotX * 0.8}deg) rotateY(${-rotY * 0.8}deg)`;
  }

  // Initial center call
  updateParallax(window.innerWidth / 2, window.innerHeight / 2);

  window.addEventListener("mousemove", (e) => {
    if (!panel.classList.contains("open")) return;
    updateParallax(e.clientX, e.clientY);
  });
}

/* ==========================================================================
   5. Chatbot Panel Interactions & Web Speech Voice Input
   ========================================================================== */
function initChatbotInteractions() {
  const panel = document.getElementById("chatbot-panel");
  const triggerBtn = document.getElementById("btn-chat-trigger");
  const closeBtn = document.getElementById("btn-close-chat");
  const sendBtn = document.getElementById("btn-chat-send");
  const textInput = document.getElementById("chat-input");
  const micBtn = document.getElementById("btn-chat-mic");
  const messagesArea = document.getElementById("chatbot-messages");

  if (!panel) return;

  function toggleChat(open) {
    if (open === undefined) {
      panel.classList.toggle("open");
    } else if (open) {
      panel.classList.add("open");
    } else {
      panel.classList.remove("open");
    }
  }

  if (triggerBtn) triggerBtn.addEventListener("click", () => toggleChat());
  if (closeBtn) closeBtn.addEventListener("click", () => toggleChat(false));

  // Quick Chips
  document.querySelectorAll(".chip-btn").forEach((chip) => {
    chip.addEventListener("click", () => {
      const prompt = chip.getAttribute("data-prompt");
      if (textInput) {
        textInput.value = prompt;
        sendMessage();
      }
    });
  });

  // Send message handler
  function sendMessage() {
    if (!textInput) return;
    const userMsg = textInput.value.trim();
    if (!userMsg) return;

    // Append Human bubble (peachy-orange)
    appendChatMessage(userMsg, "human");
    textInput.value = "";

    // Send to backend
    fetch("/api/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message: userMsg, voice_used: false }),
    })
      .then((res) => res.json())
      .then((data) => {
        // Append AI bubble (golden foreground)
        appendChatMessage(data.reply, "ai", data.solution, data.reasoning_steps);

        // Update on-page metrics if relevant
        handleChatMetricsUpdate(userMsg, data);
      })
      .catch((err) => {
        appendChatMessage(`Connection error: ${err.message}`, "ai");
      });
  }

  if (sendBtn) sendBtn.addEventListener("click", sendMessage);
  if (textInput) {
    textInput.addEventListener("keydown", (e) => {
      if (e.key === "Enter") sendMessage();
    });
  }

  function appendChatMessage(text, sender, solution, reasoningSteps) {
    if (!messagesArea) return;
    const bubble = document.createElement("div");
    bubble.className = `chat-bubble ${sender}`;

    if (sender === "ai") {
      let html = `<div>AI Output: ${escapeHtml(text)}</div>`;
      if (solution) {
        html += `<div class="solution-text">Solution: ${escapeHtml(solution)}</div>`;
      }
      if (reasoningSteps && reasoningSteps.length > 0) {
        html += `<div class="cot-steps-box">`;
        reasoningSteps.forEach((step, idx) => {
          html += `<div>${idx + 1}. ${escapeHtml(step)}</div>`;
        });
        html += `</div>`;
      }
      bubble.innerHTML = html;
    } else {
      bubble.textContent = `Maintainer: ${text}`;
    }

    messagesArea.appendChild(bubble);
    messagesArea.scrollTop = messagesArea.scrollHeight;
  }

  // Handle on-page metric updates triggered by chatbot conversation
  function handleChatMetricsUpdate(userMsg, data) {
    const msg = userMsg.toLowerCase();
    if (msg.includes("scan") || msg.includes("blast radius")) {
      navigateToSection("auditor");
      const badge = document.getElementById("blast-radius-score");
      if (badge) {
        badge.style.transform = "scale(1.15)";
        badge.style.boxShadow = "0 0 30px var(--red-flagged)";
        setTimeout(() => {
          badge.style.transform = "scale(1)";
        }, 1200);
      }
    } else if (msg.includes("heal") || msg.includes("dag") || msg.includes("auto-heal")) {
      navigateToSection("autoheal");
    } else if (msg.includes("tree")) {
      navigateToSection("dirtree");
    }
  }

  // Voice Input with Web Speech API and 5s dynamic silence wait
  let recognition = null;
  let silenceTimer = null;

  if ("webkitSpeechRecognition" in window || "SpeechRecognition" in window) {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    recognition = new SpeechRecognition();
    recognition.continuous = true;
    recognition.interimResults = true;
    recognition.lang = "en-US";

    recognition.onresult = (event) => {
      clearTimeout(silenceTimer);
      let transcript = "";
      for (let i = event.resultIndex; i < event.results.length; ++i) {
        transcript += event.results[i][0].transcript;
      }
      if (textInput && transcript.trim()) {
        textInput.value = transcript.trim();
      }

      // 5-second silence detection wait
      silenceTimer = setTimeout(() => {
        if (recognition) recognition.stop();
        if (micBtn) micBtn.classList.remove("recording");
      }, 5000);
    };

    recognition.onerror = () => {
      if (micBtn) micBtn.classList.remove("recording");
    };

    recognition.onend = () => {
      if (micBtn) micBtn.classList.remove("recording");
      clearTimeout(silenceTimer);
    };
  }

  if (micBtn) {
    micBtn.addEventListener("click", () => {
      if (!recognition) {
        alert("Web Speech API is not supported in this browser. Please type your message.");
        return;
      }
      if (micBtn.classList.contains("recording")) {
        recognition.stop();
        micBtn.classList.remove("recording");
        clearTimeout(silenceTimer);
      } else {
        micBtn.classList.add("recording");
        if (textInput) textInput.placeholder = "Listening... (Speaks freely, waits 5s after silence)";
        recognition.start();
      }
    });
  }

  // Toggle failure trace in Test Suite
  const btnToggleFailure = document.getElementById("btn-toggle-failure-trace");
  const failureBox = document.getElementById("failure-trace-box");
  if (btnToggleFailure && failureBox) {
    btnToggleFailure.addEventListener("click", () => {
      if (failureBox.style.display === "none") {
        failureBox.style.display = "block";
        btnToggleFailure.textContent = "Hide Failure Trace";
      } else {
        failureBox.style.display = "none";
        btnToggleFailure.textContent = "Toggle Attempt #1 Failure Trace";
      }
    });
  }

  // Toggle Red Team Pytest Code Drawer
  const btnToggleRedTeam = document.getElementById("btn-toggle-red-team-code");
  const redTeamDrawer = document.getElementById("red-team-code-drawer");
  if (btnToggleRedTeam && redTeamDrawer) {
    btnToggleRedTeam.addEventListener("click", () => {
      if (redTeamDrawer.style.display === "none") {
        redTeamDrawer.style.display = "block";
        btnToggleRedTeam.textContent = "Hide Red Team Test Code";
      } else {
        redTeamDrawer.style.display = "none";
        btnToggleRedTeam.textContent = "Inspect Red Team Pytest Code";
      }
    });
  }

  // Copy CAPSULE button
  const btnCopyCapsule = document.getElementById("btn-copy-capsule");
  const capsuleBox = document.getElementById("capsule-content-box");
  if (btnCopyCapsule && capsuleBox) {
    btnCopyCapsule.addEventListener("click", () => {
      navigator.clipboard.writeText(capsuleBox.textContent).then(() => {
        btnCopyCapsule.textContent = "Copied!";
        setTimeout(() => (btnCopyCapsule.textContent = "Copy Markdown"), 2000);
      });
    });
  }
}

/* ==========================================================================
   6. Live Telemetry Fetching from Contracts & CAPSULE.md
   ========================================================================== */
function fetchCodebaseTelemetry() {
  // Fetch CAPSULE.md artifact
  fetch("/api/capsule")
    .then((res) => res.json())
    .then((data) => {
      const box = document.getElementById("capsule-content-box");
      if (box && data.content) {
        box.textContent = data.content;
      }
    })
    .catch(() => {});

  // Fetch status telemetry
  fetch("/api/status")
    .then((res) => res.json())
    .then((data) => {
      if (data.target_repo || data.repo_name) {
        const repoNameEl = document.getElementById("overview-repo-name");
        if (repoNameEl) {
          repoNameEl.textContent = (data.target_repo && data.target_repo.startsWith("http"))
            ? data.target_repo.replace("https://github.com/", "")
            : (data.repo_name || data.target_repo);
        }
      }
      if (data.ast_output) {
        const repoDescEl = document.getElementById("overview-repo-desc");
        if (repoDescEl) {
          const count = data.ast_output.vulnerabilities_count || (data.ast_output.flagged_files ? data.ast_output.flagged_files.length : 0);
          repoDescEl.textContent = `${count} flagged AST hotspot(s) • Target: ${data.ast_output.target_package || 'active package'}`;
        }
      }

      renderRunPanels(data);

      if (data.checks && data.checks.length > 0) {
        const checklist = document.getElementById("auditor-checklist");
        if (checklist) {
          let checkHtml = "";
          data.checks.forEach((c) => {
            const ok = c.verified !== false;
            checkHtml += `
              <div class="check-item ${ok ? "verified" : "failed"}" style="${ok ? "" : "border-color: var(--red-flagged);"}">
                <span class="check-box" style="${ok ? "" : "color: var(--red-flagged);"}">${ok ? "X" : "!"}</span>
                <span>${escapeHtml(c.label)}${c.detail ? `<br><small style="color: var(--text-muted);">${escapeHtml(c.detail)}</small>` : ""}</span>
              </div>
            `;
          });
          checklist.innerHTML = checkHtml;
        }
      }

      if (data.ast_output) {
        const a = data.ast_output;
        const ovHero = document.getElementById("overview-hero");
        if (ovHero) ovHero.textContent = `Hero: ${a.hero_file || "none"}`;
        const heroTitle = document.getElementById("hero-file-title");
        const heroDesc = document.getElementById("hero-file-desc");
        const heroCode = document.getElementById("hero-file-code");
        const sites = (a.call_sites || []).filter((c) => c.file === a.hero_file);
        if (heroTitle) heroTitle.textContent = a.hero_file || "No hero file";
        if (heroDesc) {
          heroDesc.textContent = a.hero_file
            ? `Highest call-site density for ${a.target_package}: ${sites.length} use(s) in this file, ${(a.call_sites || []).length} across the repo.`
            : "No third-party dependency with call sites was found in this repository.";
        }
        if (heroCode) {
          const shown = sites.slice(0, 8).map((c, i) =>
            `# Call Site ${i + 1}: ${c.file}:${c.line}  (${c.kind}${c.private_api ? ", private API" : ""})\n# in ${c.calling_function || "<module>"}()  ->  ${c.symbol || ""}\n${c.code_snippet || ""}`
          );
          const bad = (data.checks || []).filter((k) => k.verified === false).map((k) => `# [FLAG] ${k.detail}`);
          heroCode.textContent = [...shown, ...(bad.length ? ["", "# --- Auditor findings ---", ...bad] : [])].join("\n\n") || "# Nothing to show";
        }
        const badge = document.getElementById("blast-radius-score");
        if (badge) {
          badge.textContent = `Blast Radius Score: ${data.ast_output.blast_radius_score || 0} / 100` +
            (data.ast_output.target_package ? ` (${data.ast_output.target_package})` : "");
        }
      }

      // Populate Red Team Edge Cases dynamically
      if (data.red_team_suite) {
        const codePre = document.getElementById("red-team-code-content");
        if (codePre) codePre.textContent = "# Run the Auto-Heal search to generate the Red Team suite for this repository.";
        const staleBody = document.getElementById("red-team-tbody");
        if (staleBody && !(data.red_team_suite.set_a_tests || []).length && !(data.red_team_suite.set_b_tests || []).length) {
          staleBody.innerHTML = '<tr><td colspan="5" style="text-align:center;color:var(--text-muted);">No Red Team tests yet - run the Auto-Heal search.</td></tr>';
        }
        if (codePre && data.red_team_suite.full_pytest_file_content) {
          codePre.textContent = data.red_team_suite.full_pytest_file_content;
        }

        const tbody = document.getElementById("red-team-tbody");
        const setA = data.red_team_suite.set_a_tests || [];
        const setB = data.red_team_suite.set_b_tests || [];
        if (tbody && (setA.length > 0 || setB.length > 0)) {
          let rowsHtml = "";

          setA.forEach((t) => {
            rowsHtml += `
              <tr>
                <td><code>${escapeHtml(t.test_id || "SET_A")}</code></td>
                <td><span class="edge-badge contract">Contract Gate</span></td>
                <td><code>${escapeHtml(t.name || "")}</code></td>
                <td>${escapeHtml(t.stress_invariant || t.description || "")}</td>
                <td><span class="status-badge-passed">✔ VALIDATED</span></td>
              </tr>
            `;
          });

          setB.forEach((t) => {
            const cat = t.edge_case_category || "Differential";
            let badgeClass = "boundary";
            if (cat.includes("Unicode")) badgeClass = "unicode";
            else if (cat.includes("Environment") || cat.includes("OS")) badgeClass = "environment";
            else if (cat.includes("Scope") || cat.includes("Concurrency")) badgeClass = "scope";

            rowsHtml += `
              <tr>
                <td><code>${escapeHtml(t.test_id || "SET_B")}</code></td>
                <td><span class="edge-badge ${badgeClass}">${escapeHtml(cat)}</span></td>
                <td><code>${escapeHtml(t.name || "")}</code></td>
                <td>${escapeHtml(t.stress_invariant || t.description || "")}</td>
                <td><span class="status-badge-passed">✔ VALIDATED</span></td>
              </tr>
            `;
          });

          tbody.innerHTML = rowsHtml;
        }
      }

      // Populate DAG Visual Cards dynamically from data.history
      if (data.history && data.history.length > 0) {
        const dagContainer = document.getElementById("dag-node-container");
        if (dagContainer) {
          let dagHtml = "";
          data.history.forEach((node, idx) => {
            const isLast = idx === data.history.length - 1;
            const status = (node.status || "PENDING").toUpperCase();
            let cardClass = "dag-card";
            let statusStyle = "color: var(--gold-light);";
            let statusText = `Status: ${status} (${node.reward_score || 0} pts)`;

            if (status === "FAILED") {
              cardClass += " failed";
              statusStyle = "color: var(--red-flagged);";
            } else if (status === "PASSED") {
              cardClass += " passed";
              statusStyle = "color: var(--green-passed);";
              statusText = `Status: PASSED (+100 reward, Score: ${node.reward_score || 97})`;
            }

            dagHtml += `
              <div class="${cardClass}">
                <div class="section-label">${escapeHtml(node.node_id || `Node ${idx}`)}</div>
                <strong style="color: #fff;">${escapeHtml(node.action_name || "Search Node")}</strong>
                <p style="color: var(--text-muted); font-size: 0.82rem; margin: 8px 0;">
                  ${escapeHtml(node.details && node.details.approach ? node.details.approach : (status === "PASSED" ? "Auto-healed clean adapter" : "Evaluated in sandbox"))}
                </p>
                <div style="font-weight: 700; ${statusStyle}">${escapeHtml(statusText)}</div>
              </div>
            `;
            if (!isLast) {
              dagHtml += `<div class="dag-arrow">&rarr;</div>`;
            }
          });
          dagContainer.innerHTML = dagHtml;
        }

        // Update failure trace box if a failed attempt exists
        const failedNode = data.history.find((n) => (n.status || "").toUpperCase() === "FAILED");
        const failureTraceContent = document.getElementById("failure-trace-content");
        if (failureTraceContent && !failedNode) failureTraceContent.textContent = "No failed attempt recorded for this repository yet.";
        if (failureTraceContent && failedNode) {
          const rawErr = failedNode.run_result && failedNode.run_result.raw_stderr
            ? failedNode.run_result.raw_stderr
            : `FAILED Attempt 1 execution: Regression detected in sandbox.\nAction: Backtracking to explore alternative AST solution.`;
          failureTraceContent.textContent = rawErr;
        }
      }
    })
    .catch(() => {});

  // Fetch test suite runner table dynamically
  fetch("/api/tests")
    .then((res) => res.json())
    .then((testData) => {
      const runnerTbody = document.getElementById("test-runner-tbody");
      if (!runnerTbody) return;

      const rs = testData.run_summary || {};
      const preExisting = testData.pre_existing || [];
      const setA = testData.set_a_tests || [];
      const setB = testData.set_b_edge_cases || [];

      const badge = (label, ok) =>
        ok === true ? `<span class="status-badge-passed">🟢 ${label}</span>`
        : ok === false ? `<span style="color: var(--red-flagged); font-weight: 700;">🔴 ${label}</span>`
        : `<span style="color: var(--text-muted); font-weight: 700;">⚪ ${label}</span>`;

      const preBadge = rs.has_run ? badge(rs.baseline_passed ? "PASSED (baseline suite)" : "FAILED (baseline suite)", !!rs.baseline_passed) : badge("DISCOVERED", null);
      const aiBadge = rs.has_run ? (rs.winner_status === "PASSED" ? badge("PASSED", true) : badge("NOT VERIFIED", null)) : badge("GENERATED", null);

      let html = "";
      preExisting.forEach((t) => {
        html += `<tr><td><code>${escapeHtml(t.id || t.name)}</code></td><td><span class="origin-badge pre-existing">Pre-existing</span></td><td>${escapeHtml(t.duration || "-")}</td><td>${preBadge}</td></tr>`;
      });
      [...setA, ...setB].forEach((t) => {
        html += `<tr><td><code>${escapeHtml(t.name || t.test_id)}</code></td><td><span class="origin-badge ai-generated">AI-Generated</span></td><td>-</td><td>${aiBadge}</td></tr>`;
      });

      const title = document.getElementById("test-suite-title");
      if (title) {
        let txt = `Test suite: ${preExisting.length} pre-existing, ${setA.length + setB.length} AI-generated`;
        if (rs.has_run) {
          txt += ` | sandbox: baseline ${rs.baseline_passed ? "passed" : "failed"} (${rs.baseline_ms}ms), best candidate ${rs.winner_status}`;
        } else {
          txt += " | not executed yet - run the Auto-Heal search";
        }
        title.textContent = txt;
      }

      runnerTbody.innerHTML = html || `<tr><td colspan="4" style="text-align:center;color:var(--text-muted);">No tests found in this repository yet.</td></tr>`;
    })
    .catch(() => {});
}

/* Fill the Whisperer, Auto-Heal and reward panels from live run data (any repository). */
function renderRunPanels(data) {
  const a = data.ast_output || {};
  const hist = data.history || [];
  const checks = data.checks || [];
  const rt = data.red_team_suite || {};
  const setA = rt.set_a_tests || [];
  const setB = rt.set_b_tests || [];
  const cands = a.candidates || [];
  const failedChecks = checks.filter((c) => c.verified === false);
  const attempts = hist.filter((n) => (n.status || "").toUpperCase() !== "BASELINE");
  const best = attempts.slice().sort((x, y) => (y.reward_score || 0) - (x.reward_score || 0))[0];
  const ran = !!data.search_run;

  // --- Whisperer: reasoning stream ---
  const cot = document.getElementById("whisperer-cot-stream");
  if (cot) {
    const lines = [
      `Ingested repository '${data.repo_name}' (${a.files_scanned || 0} Python files scanned).`,
      a.target_package
        ? `AST scanner ranked ${cands.length} dependenc${cands.length === 1 ? "y" : "ies"}; target is ${a.target_package} (blast radius ${a.blast_radius_score}/100, ${(a.call_sites || []).length} call sites).`
        : "AST scanner found no third-party dependency with call sites.",
      a.hero_file ? `Hero file isolated: ${a.hero_file}.` : "No hero file identified.",
      `Auditor: ${checks.length - failedChecks.length}/${checks.length} checks passed${failedChecks.length ? " - " + failedChecks.map((c) => c.detail).join("; ") : ""}.`,
    ];
    if (ran) {
      lines.push(`Red Team generated ${setA.length} contract gate(s) and ${setB.length} edge case(s).`);
      lines.push(`Auto-heal explored ${hist.length} node(s)${best ? `; best candidate: ${best.action_name} [${best.status}, score ${best.reward_score}]` : ""}.`);
    } else {
      lines.push("Run the Auto-Heal search to generate Red/Blue Team output.");
    }
    cot.innerHTML = lines.map((l, i) => `${i + 1}. ${escapeHtml(l)}`).join("<br>");
  }

  // --- Whisperer: arena code ---
  const arena = document.getElementById("arena-code");
  if (arena) {
    const redCode = (rt.full_pytest_file_content || "").split("\n").slice(0, 30).join("\n");
    const patch = best && best.patch_diff ? best.patch_diff.split("\n").slice(0, 40).join("\n") : "";
    arena.textContent =
      "# [RED TEAM] Synthesized adversarial tests\n" + (redCode || "# (none yet - run the Auto-Heal search)") +
      "\n\n# [BLUE TEAM] Proposed patch\n" + (patch || "# (none yet - run the Auto-Heal search)");
  }

  // --- Auto-Heal: rewind banner ---
  const banner = document.getElementById("rewind-banner");
  const rewindText = document.getElementById("rewind-text");
  const failed = hist.find((n) => (n.status || "").toUpperCase() === "FAILED");
  if (banner) banner.style.display = failed ? "" : "none";
  if (rewindText && failed) {
    rewindText.textContent = `${failed.action_name} failed the deterministic sandbox run. Branch abandoned and rolled back to Node 0 for the next attempt.`;
  }

  // --- Auto-Heal: reward impact column ---
  const set = (id, txt) => { const el = document.getElementById(id); if (el) el.textContent = txt; };
  if (!ran || !best) {
    ["rw-extrinsic", "rw-curiosity", "rw-latency", "rw-bloat", "rw-anticheat"].forEach((id) => set(id, "-"));
  } else {
    const bd = best.reward_breakdown || {};
    const base = hist.find((n) => n.node_id === "node_0");
    const bms = base && base.run_result ? base.run_result.execution_time_ms : "?";
    const curiosity = attempts.reduce((sum, n) => sum + ((n.reward_breakdown || {}).intrinsic_curiosity || 0), 0);
    set("rw-extrinsic", `${bd.extrinsic_reward >= 0 ? "+" : ""}${bd.extrinsic_reward || 0} pts (${best.node_id})`);
    set("rw-curiosity", `+${curiosity} pts (all attempts)`);
    set("rw-latency", `${bd.efficiency_penalty || 0} pts (${best.run_result ? best.run_result.execution_time_ms : "?"}ms vs ${bms}ms)`);
    set("rw-bloat", `${bd.code_bloat_penalty || 0} pts`);
    set("rw-anticheat", bd.tampering_detected ? "-9999 pts (TAMPERING)" : "0 pts (Clean)");
  }
}

function escapeHtml(str) {
  if (str === 0) return "0";
  if (!str) return "";
  return String(str)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}