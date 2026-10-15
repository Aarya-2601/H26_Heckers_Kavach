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
  initSmokeNavigation();
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

  const startTime = performance.now();

  function animate(now) {
    ctx.clearRect(0, 0, width, height);

    // Initial reveal transition from black to golden glass
    const elapsed = now ? (now - startTime) / 1000 : 0;
    const revealFactor = Math.min(1, elapsed / 2.2);

    const bgRadial = ctx.createRadialGradient(
      width / 2, height / 2, 40,
      width / 2, height / 2, Math.max(width, height) * 0.7
    );
    bgRadial.addColorStop(0, `rgba(14, 21, 36, ${revealFactor})`);
    bgRadial.addColorStop(0.5, `rgba(8, 12, 20, ${revealFactor})`);
    bgRadial.addColorStop(1, "#020305");
    ctx.fillStyle = bgRadial;
    ctx.fillRect(0, 0, width, height);

    // Crystalline golden web connectors between proximate triangles
    for (let i = 0; i < triangles.length; i++) {
      for (let j = i + 1; j < triangles.length; j++) {
        const dx = triangles[i].x - triangles[j].x;
        const dy = triangles[i].y - triangles[j].y;
        const dist = Math.sqrt(dx * dx + dy * dy);
        if (dist < 130) {
          const lineAlpha = (1 - dist / 130) * 0.22 * revealFactor;
          ctx.beginPath();
          ctx.moveTo(triangles[i].x, triangles[i].y);
          ctx.lineTo(triangles[j].x, triangles[j].y);
          ctx.strokeStyle = `rgba(251, 191, 36, ${lineAlpha})`;
          ctx.lineWidth = 0.8;
          ctx.stroke();
        }
      }
    }

    triangles.forEach((t) => {
      t.update();
      t.draw(ctx);
    });

    requestAnimationFrame(animate);
  }

  requestAnimationFrame(animate);
}

/* ==========================================================================
   2. Diffused Smoke SPA Section Navigation
   ========================================================================== */
function initSmokeNavigation() {
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
}

function navigateToSection(targetId) {
  const currentSection = document.querySelector(".section-view.active");
  const targetSection = document.getElementById(targetId);

  if (!targetSection || currentSection === targetSection) return;

  // Update navbar active status
  document.querySelectorAll(".nav-link").forEach((l) => {
    if (l.getAttribute("data-nav") === targetId) {
      l.classList.add("active");
    } else {
      l.classList.remove("active");
    }
  });

  // Update URL hash without jumping
  history.pushState(null, null, `#${targetId}`);

  // 1. Current section diffuses out into smoke
  if (currentSection) {
    currentSection.classList.add("smoke-exit");
    currentSection.classList.remove("smoke-enter");

    setTimeout(() => {
      currentSection.classList.remove("active", "smoke-exit");
      currentSection.style.display = "none";

      // 2. Target section condenses in from golden smoke
      targetSection.style.display = "block";
      targetSection.classList.add("active", "smoke-enter");
      window.scrollTo({ top: 0, behavior: "instant" });

      setTimeout(() => {
        targetSection.classList.remove("smoke-enter");
      }, 600);
    }, 400);
  } else {
    targetSection.style.display = "block";
    targetSection.classList.add("active");
  }
}

/* ==========================================================================
   3. Interactive Tree Data Structure with AST Inspector
   ========================================================================== */
function initTreeDataStructure() {
  const treeNodes = document.querySelectorAll(".tree-file-node");
  const inspectorTitle = document.getElementById("inspector-title");
  const inspectorDesc = document.getElementById("inspector-desc");
  const inspectorCode = document.getElementById("inspector-code-box");
  const inspectorActions = document.getElementById("inspector-actions");
  const btnFixInChat = document.getElementById("btn-fix-in-chat");

  let currentTargetFile = "";

  const fileData = {
    "linkwatch/checker.py": {
      title: "linkwatch/checker.py (Hero File)",
      desc: "Vulnerability: High Blast Radius (78/100). Contains unhandled requests.get without bounded socket timeout across fetch() and check_site().",
      code: `// File: linkwatch/checker.py (Lines 14-25)
// Designation: Hero File (Caller Density: 78%)
def fetch(url, session=None):
    # [AST VULNERABILITY] Unbounded connection attempt
    if session:
        return session.get(url)  # Missing timeout parameter!
    return requests.get(url)     # Fallback lacks socket bounds

def check_site(site, session=None):
    try:
        response = fetch(site.url, session=session)
        return response.status_code == 200
    except requests.exceptions.RequestException as e:
        # Fails silently without retry or metric attribution
        return False`,
      flagged: true
    },
    "linkwatch/http_patch.py": {
      title: "linkwatch/http_patch.py",
      desc: "Vulnerability: Global Scope Contamination. Monkey-patches requests.Session.request globally, breaking scope isolation in test suites.",
      code: `// File: linkwatch/http_patch.py (Lines 8-18)
// Designation: Contamination Source
def apply_global_patch():
    # [CRITICAL AST VIOLATION]
    # In-place mutation of global Python interpreter session class:
    original_request = requests.Session.request

    def patched_request(self, method, url, **kwargs):
        kwargs.setdefault('headers', {})['User-Agent'] = 'LinkWatch/1.0'
        return original_request(self, method, url, **kwargs)

    # Contaminates every module importing requests!
    requests.Session.request = patched_request`,
      flagged: true
    },
    "Dockerfile": {
      title: "Dockerfile",
      desc: "Vulnerability: Container defaults to root execution, violating Non-Root Deterministic Auditor rule.",
      code: `// File: Dockerfile (Lines 15-22)
// Designation: Container Build Spec
FROM python:3.11-slim
WORKDIR /app
COPY . /app
RUN pip install -e .

# [SECURITY AUDIT VIOLATION]
# Runs container as superuser
USER root
CMD ["linkwatch", "check"]`,
      flagged: true
    },
    "linkwatch/cache.py": {
      title: "linkwatch/cache.py",
      desc: "Status: CLEAN. Interacts with local storage via appdirs.user_cache_dir; scheduled for platformdirs migration.",
      code: `// File: linkwatch/cache.py (Lines 5-14)
import json
import appdirs

CACHE_DIR = appdirs.user_cache_dir("linkwatch")

def save_cache(data):
    with open(f"{CACHE_DIR}/cache.json", "w") as f:
        json.dump(data, f)`,
      flagged: false
    },
    "tests/test_checker.py": {
      title: "tests/test_checker.py",
      desc: "Status: TARGET OF REGRESSION CHECK. Verifies fetch() and check_site() return codes.",
      code: `// File: tests/test_checker.py (Lines 1-12)
import pytest
from linkwatch.checker import check_site
from linkwatch.config import Site

def test_check_site_up():
    site = Site(url="https://example.com")
    assert check_site(site) is True`,
      flagged: false
    }
  };

  treeNodes.forEach((node) => {
    node.addEventListener("click", () => {
      // Highlight selected node
      treeNodes.forEach((n) => (n.style.outline = "none"));
      node.style.outline = "2px solid var(--gold-primary)";

      const filePath = node.getAttribute("data-file");
      currentTargetFile = filePath;
      const data = fileData[filePath] || {
        title: filePath,
        desc: "File verified by AST Scanner. No critical scope leaks detected.",
        code: `// File: ${filePath}\n// Status: VERIFIED CLEAN BY DETERMINISTIC SCANNER`,
        flagged: false
      };

      if (inspectorTitle) inspectorTitle.textContent = data.title;
      if (inspectorDesc) inspectorDesc.textContent = data.desc;
      if (inspectorCode) inspectorCode.textContent = data.code;

      if (inspectorActions) {
        inspectorActions.style.display = data.flagged ? "block" : "none";
      }
    });
  });

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

  window.addEventListener("mousemove", (e) => {
    if (!panel.classList.contains("open")) return;

    const normX = (e.clientX / window.innerWidth - 0.5) * 2;
    const normY = (e.clientY / window.innerHeight - 0.5) * 2;

    // Layer 1: Golden Grid moves with perspective
    const moveX = normX * 18;
    const moveY = normY * 18;
    const rotX = -normY * 6;
    const rotY = normX * 6;
    grid.style.transform = `translate3d(${moveX}px, ${moveY}px, 0) rotateX(${rotX}deg) rotateY(${rotY}deg)`;

    // Layer 2: Golden Parallax Dots move in OPPOSITE direction with higher velocity
    const dotMoveX = -normX * 28;
    const dotMoveY = -normY * 28;
    dots.style.transform = `translate3d(${dotMoveX}px, ${dotMoveY}px, 0) rotateX(${-rotX * 0.8}deg) rotateY(${-rotY * 0.8}deg)`;
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
        // Append AI bubble (light blue)
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
      if (data.ast_output && data.ast_output.blast_radius_score) {
        const badge = document.getElementById("blast-radius-score");
        if (badge) {
          badge.textContent = `Blast Radius Score: ${data.ast_output.blast_radius_score} / 100`;
        }
      }
    })
    .catch(() => {});
}

function escapeHtml(str) {
  if (!str) return "";
  return str
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}
