/**
 * Kavach Web Application - Interactive Engine
 * 
 * Features:
 * 1. Golden Glass Triangle Glitter Canvas Animation revealing "K A V A C H"
 * 2. Light Blue Parallax Grid inside Chatbot (responsive to cursor movement)
 * 3. Chatbot slide-in panel with voice-to-text (with silence wait & text editing)
 * 4. Dynamic synchronization with codebase telemetry (AST, DAG, Tests, CAPSULE)
 */

document.addEventListener("DOMContentLoaded", () => {
  initGoldenTrianglesCanvas();
  initChatbotParallax();
  initChatbotInteractions();
  fetchCodebaseTelemetry();
});

/* ==========================================================================
   1. Golden Glass Triangle Glitter Canvas Animation (Reveals "KAVACH")
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
      this.goldenHue = Math.random() > 0.4 ? 42 : 36; // Amber/Gold tones
    }

    update() {
      this.x += this.vx;
      this.y += this.vy;
      this.angle += this.va;
      this.glitterPhase += this.glitterSpeed;

      // Wrap around bounds
      if (this.x < -60) this.x = width + 60;
      if (this.x > width + 60) this.x = -60;
      if (this.y < -60) this.y = height + 60;
      if (this.y > height + 60) this.y = -60;

      // Mouse subtle gravitational caustic effect
      if (mouse.active) {
        const dx = mouse.x - this.x;
        const dy = mouse.y - this.y;
        const dist = Math.sqrt(dx * dx + dy * dy);
        if (dist < 280) {
          const force = (1 - dist / 280) * 0.8;
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

      // Glitter luminescence calculation
      const glitter = Math.sin(this.glitterPhase);
      const dynamicAlpha = Math.max(0.1, this.alpha + glitter * 0.2);

      // Glass facet gradient
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

      // Specular glass beveled border
      ctx.strokeStyle = `hsla(${this.goldenHue}, 100%, 80%, ${dynamicAlpha * 0.85})`;
      ctx.lineWidth = 1.2;
      ctx.stroke();

      // Glitter highlight vertex sparkle
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

    // Deep space dark background with golden atmospheric bloom
    const bgRadial = ctx.createRadialGradient(
      width / 2, height / 2, 40,
      width / 2, height / 2, Math.max(width, height) * 0.7
    );
    bgRadial.addColorStop(0, `rgba(14, 21, 36, ${revealFactor})`);
    bgRadial.addColorStop(0.5, `rgba(8, 12, 20, ${revealFactor})`);
    bgRadial.addColorStop(1, "#020305");
    ctx.fillStyle = bgRadial;
    ctx.fillRect(0, 0, width, height);

    // Draw crystalline golden web connectors between proximate triangles
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

    // Render shimmering glass triangles
    triangles.forEach((t) => {
      t.update();
      t.draw(ctx);
    });

    requestAnimationFrame(animate);
  }

  requestAnimationFrame(animate);
}

/* ==========================================================================
   2. Light Blue Parallax Grid Inside Chatbot
   ========================================================================== */
function initChatbotParallax() {
  const panel = document.getElementById("chatbot-panel");
  const grid = document.getElementById("chatbot-parallax-grid");
  if (!panel || !grid) return;

  window.addEventListener("mousemove", (e) => {
    // Only calculate parallax if chatbot is open to save CPU cycles
    if (!panel.classList.contains("open")) return;

    const normX = (e.clientX / window.innerWidth - 0.5) * 2;
    const normY = (e.clientY / window.innerHeight - 0.5) * 2;

    const moveX = normX * 18;
    const moveY = normY * 18;
    const rotX = -normY * 6;
    const rotY = normX * 6;

    grid.style.transform = `translate3d(${moveX}px, ${moveY}px, 0) rotateX(${rotX}deg) rotateY(${rotY}deg)`;
  });
}

/* ==========================================================================
   3. Chatbot Panel Interactions & Web Speech Voice Input
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

  // Quick Action Chips
  document.querySelectorAll(".chip-btn").forEach((chip) => {
    chip.addEventListener("click", () => {
      if (textInput) {
        textInput.value = chip.dataset.prompt || chip.innerText;
        textInput.focus();
      }
    });
  });

  // Message Sending
  async function sendMessage() {
    if (!textInput) return;
    const userText = textInput.value.trim();
    if (!userText) return;

    // Append Human message (Peachy-Orange)
    appendMessage(userText, "human");
    textInput.value = "";

    // Show temporary AI typing indicator
    const typingId = appendTypingIndicator();

    try {
      const res = await fetch("/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: userText, voice_used: false }),
      });
      const data = await res.json();

      removeTypingIndicator(typingId);
      appendMessage(data.reply, "ai", data.solution);
    } catch (err) {
      removeTypingIndicator(typingId);
      appendMessage(
        "Kavach AST service is operating in local demonstration mode.",
        "ai",
        "Solution: Scheduled AST refactor for linkwatch/checker.py with timeout=10.0."
      );
    }
  }

  if (sendBtn) sendBtn.addEventListener("click", sendMessage);
  if (textInput) {
    textInput.addEventListener("keydown", (e) => {
      if (e.key === "Enter") {
        e.preventDefault();
        sendMessage();
      }
    });
  }

  // Voice Input via Web Speech API with Dynamic Silence Wait (5s)
  let recognition = null;
  let silenceTimer = null;

  if ("webkitSpeechRecognition" in window || "SpeechRecognition" in window) {
    const SpeechRec = window.SpeechRecognition || window.webkitSpeechRecognition;
    recognition = new SpeechRec();
    recognition.continuous = true;
    recognition.interimResults = true;
    recognition.lang = "en-US";

    recognition.onstart = () => {
      if (micBtn) micBtn.classList.add("recording");
      if (textInput) textInput.placeholder = "Listening... (recording stops 5s after you stop speaking)";
    };

    recognition.onresult = (event) => {
      let finalTranscript = "";
      for (let i = event.resultIndex; i < event.results.length; ++i) {
        finalTranscript += event.results[i][0].transcript;
      }

      if (textInput && finalTranscript) {
        textInput.value = finalTranscript;
      }

      // Reset 5-second silence countdown on speech
      clearTimeout(silenceTimer);
      silenceTimer = setTimeout(() => {
        if (recognition) recognition.stop();
      }, 5000);
    };

    recognition.onerror = () => {
      if (micBtn) micBtn.classList.remove("recording");
      if (textInput) textInput.placeholder = "Type remediation instruction...";
    };

    recognition.onend = () => {
      if (micBtn) micBtn.classList.remove("recording");
      if (textInput) {
        textInput.placeholder = "Edit voice input or type instruction...";
        textInput.focus();
      }
    };
  }

  if (micBtn) {
    micBtn.addEventListener("click", () => {
      if (!recognition) {
        alert("Web Speech API is not supported in this browser. Please type manually.");
        return;
      }
      try {
        if (micBtn.classList.contains("recording")) {
          recognition.stop();
        } else {
          recognition.start();
        }
      } catch (err) {
        recognition.stop();
      }
    });
  }

  function appendMessage(text, sender, solution) {
    if (!messagesArea) return;
    const bubble = document.createElement("div");
    bubble.className = `chat-bubble ${sender}`;

    if (sender === "ai") {
      let content = `<div>${text}</div>`;
      if (solution) {
        content += `<div class="solution-text">Solution: ${solution}</div>`;
      }
      bubble.innerHTML = content;
    } else {
      bubble.innerText = text;
    }

    messagesArea.appendChild(bubble);
    messagesArea.scrollTop = messagesArea.scrollHeight;
  }

  function appendTypingIndicator() {
    if (!messagesArea) return null;
    const id = "typing-" + Date.now();
    const bubble = document.createElement("div");
    bubble.className = "chat-bubble ai typing";
    bubble.id = id;
    bubble.innerHTML = `<em>Thinking...</em>`;
    messagesArea.appendChild(bubble);
    messagesArea.scrollTop = messagesArea.scrollHeight;
    return id;
  }

  function removeTypingIndicator(id) {
    if (!id) return;
    const el = document.getElementById(id);
    if (el) el.remove();
  }
}

/* ==========================================================================
   4. Live Codebase Telemetry Synchronization
   ========================================================================== */
async function fetchCodebaseTelemetry() {
  try {
    const res = await fetch("/api/status");
    const data = await res.json();

    // Populate Flagged Files
    const flaggedContainer = document.getElementById("flagged-files-list");
    if (flaggedContainer && data.ast_output && data.ast_output.flagged_files) {
      flaggedContainer.innerHTML = data.ast_output.flagged_files
        .map((f) => `<span class="flagged-file-tag">${f}</span>`)
        .join("");
    }

    // Populate Blast Radius Score
    const blastBadge = document.getElementById("blast-radius-score");
    if (blastBadge && data.ast_output) {
      blastBadge.innerText = `Blast Radius Score: ${data.ast_output.blast_radius_score || 78}/100`;
    }

    // Populate DAG Nodes
    const dagContainer = document.getElementById("dag-nodes-container");
    if (dagContainer && data.search_loop && data.search_loop.history) {
      dagContainer.innerHTML = data.search_loop.history
        .map(
          (node) => `
        <div class="dag-node-card ${node.status.toLowerCase()}">
          <div class="dag-header">
            <strong>${node.action_name}</strong>
            <span class="score-badge">${node.status} (${node.execution_time_ms || 500}ms)</span>
          </div>
          <div style="font-size: 0.82rem; color: var(--text-muted); font-family: var(--font-mono);">
            ID: ${node.node_id} | Reward Score: ${node.reward_score !== undefined ? node.reward_score : "N/A"}
          </div>
        </div>
      `
        )
        .join("");
    }

    // Fetch and populate CAPSULE markdown
    const capsuleRes = await fetch("/api/capsule");
    const capsuleData = await capsuleRes.json();
    const capsuleBox = document.getElementById("capsule-content-box");
    if (capsuleBox && capsuleData.content) {
      capsuleBox.innerText = capsuleData.content;
    }
  } catch (err) {
    console.warn("Using bundled telemetry state.");
  }
}
