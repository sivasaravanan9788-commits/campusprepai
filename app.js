/**
 * CampusPrep AI - Frontend Controller & Multimodal Studio Engine
 */

document.addEventListener("DOMContentLoaded", () => {
  // --- App State ---
  let selectedCompany = "zoho";
  let activeSessionId = null;
  let currentQuestionId = null;
  let currentQuestionText = "";
  let isSessionActive = false;

  // Speech Recognition (STT) State
  let recognition = null;
  let isRecording = false;
  let recordingStartTime = null;

  // Audio Visualizer & Webcam State
  let audioContext = null;
  let analyser = null;
  let microphoneStream = null;
  let animFrameId = null;

  // --- Sample Resumes ---
  const SAMPLE_RESUME = `
SIVASANKARAN K - SENIOR SOFTWARE ENGINEER
Email: sivasankaran@example.com | GitHub: github.com/sivasankaran

SUMMARY:
Passionate Software Engineer with 3+ years of experience building scalable Web applications and Data Processing pipelines. Proficient in Data Structures and Algorithms (DSA), Python, JavaScript, React, and RESTful APIs.

TECHNICAL SKILLS:
- Languages & Core CS: Python, C++, JavaScript, Data Structures and Algorithms, Object-Oriented Programming (OOP), Operating Systems (OS memory management, virtual memory).
- Web Technologies: React, Node.js, HTML5, CSS3, REST APIs, JSON, CORS, JWT Authentication.
- Database & Systems: SQL, PostgreSQL, Database Normalization (3NF), B-Tree Indexing, System Architecture, Microservices, Redis Caching.
- Cloud & DevOps: Docker, Git, CI/CD pipelines, AWS EC2.

PROJECTS:
1. Distributed API Gateway Rate Limiter (Token Bucket Algorithm in Redis).
2. Algorithmic Trading Bot utilizing Floyd's Cycle-Finding Algorithm for graph cycle detection.
  `;

  // --- DOM Elements ---
  const companySelect = document.getElementById("companySelect");
  const companyTrackBadge = document.getElementById("companyTrackBadge");
  const hudCompanyBadge = document.getElementById("hudCompanyBadge");
  
  // ATS Elements
  const resumeText = document.getElementById("resumeText");
  const btnLoadSampleResume = document.getElementById("btnLoadSampleResume");
  const btnScanResume = document.getElementById("btnScanResume");
  const atsResults = document.getElementById("atsResults");
  const atsScoreValue = document.getElementById("atsScoreValue");
  const scoreGauge = document.getElementById("scoreGauge");
  const atsHeadlineText = document.getElementById("atsHeadlineText");
  const atsSubtext = document.getElementById("atsSubtext");
  const matrixGrid = document.getElementById("matrixGrid");
  const missingTags = document.getElementById("missingTags");
  const recommendationsList = document.getElementById("recommendationsList");

  // Interview Elements
  const webcamFeed = document.getElementById("webcamFeed");
  const hudOverlay = document.getElementById("hudOverlay");
  const telemetryWPM = document.getElementById("telemetryWPM");
  const telemetryFillers = document.getElementById("telemetryFillers");
  const telemetryScore = document.getElementById("telemetryScore");

  const sessionStepBadge = document.getElementById("sessionStepBadge");
  const promptCategoryBadge = document.getElementById("promptCategoryBadge");
  const promptDifficultyBadge = document.getElementById("promptDifficultyBadge");
  const promptQuestionText = document.getElementById("promptQuestionText");
  const btnVocalize = document.getElementById("btnVocalize");
  const btnStartSession = document.getElementById("btnStartSession");

  const btnMicRecord = document.getElementById("btnMicRecord");
  const micBtnText = document.getElementById("micBtnText");
  const btnSubmitAnswer = document.getElementById("btnSubmitAnswer");
  const answerTranscriptionText = document.getElementById("answerTranscriptionText");
  const sttStatusMsg = document.getElementById("sttStatusMsg");
  const turnFeedbackArea = document.getElementById("turnFeedbackArea");
  const turnCritiqueContent = document.getElementById("turnCritiqueContent");

  // Modal Elements
  const scorecardModal = document.getElementById("scorecardModal");
  const modalFinalScore = document.getElementById("modalFinalScore");
  const modalFinalWPM = document.getElementById("modalFinalWPM");
  const modalFinalFillers = document.getElementById("modalFinalFillers");
  const btnCloseScorecard = document.getElementById("btnCloseScorecard");

  // --- Initialization ---
  initWebcamAndHUD();
  initSpeechRecognition();
  loadCompanyTracks();
  loadCourses();

  // --- Event Listeners ---
  companySelect.addEventListener("change", (e) => {
    selectedCompany = e.target.value;
    const name = companySelect.options[companySelect.selectedIndex].text.split(" (")[0];
    companyTrackBadge.textContent = `${name} Track Active`;
    hudCompanyBadge.textContent = `${name.toUpperCase()} INTERVIEWER`;
  });

  btnLoadSampleResume.addEventListener("click", () => {
    resumeText.value = SAMPLE_RESUME.trim();
  });

  btnScanResume.addEventListener("click", scanResume);

  btnStartSession.addEventListener("click", startInterviewSession);

  btnVocalize.addEventListener("click", vocalizeQuestionPrompt);

  btnMicRecord.addEventListener("click", toggleSpeechRecognition);

  btnSubmitAnswer.addEventListener("click", submitAnswerTurn);

  btnCloseScorecard.addEventListener("click", () => {
    scorecardModal.classList.remove("active");
    resetInterviewStudio();
  });

  // --- Functions ---

  function loadCompanyTracks() {
    fetch("/api/v1/companies")
      .then(res => res.json())
      .then(data => {
        if (data.companies && data.companies.length > 0) {
          // Preloaded options are in HTML, verify server connection
          document.getElementById("apiStatusText").textContent = "API TELEMETRY ONLINE (0.0.0.0:8000)";
        }
      })
      .catch(err => {
        console.warn("API offline or loading error:", err);
        document.getElementById("apiStatusText").textContent = "API DISCONNECTED";
      });
  }

  // --- ATS Resume Scanner Functionality ---
  function scanResume() {
    const text = resumeText.value.trim();
    if (!text) {
      alert("Please enter or paste your resume text before scanning.");
      return;
    }

    btnScanResume.innerHTML = `<i class="fa-solid fa-spinner fa-spin"></i> Scanning...`;
    btnScanResume.disabled = true;

    fetch("/api/v1/resumes/scan", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        resume_text: text,
        target_company: selectedCompany
      })
    })
      .then(res => {
        if (!res.ok) throw new Error("Resume scan failed.");
        return res.json();
      })
      .then(data => {
        renderATSResults(data);
      })
      .catch(err => {
        alert("Error scanning resume: " + err.message);
      })
      .finally(() => {
        btnScanResume.innerHTML = `<i class="fa-solid fa-magnifying-glass-chart"></i> Scan & Analyze ATS Match`;
        btnScanResume.disabled = false;
      });
  }

  function renderATSResults(data) {
    atsResults.style.display = "flex";
    const score = data.ats_match_percentage;

    // Gauge Ring & Score
    atsScoreValue.textContent = `${score}%`;
    scoreGauge.style.setProperty("--score-pct", score);

    if (score >= 75) {
      atsHeadlineText.textContent = "High Recruiter Alignment!";
      atsSubtext.textContent = `Strong keyword match for ${data.target_company.toUpperCase()} core competency benchmark.`;
    } else if (score >= 50) {
      atsHeadlineText.textContent = "Moderate Recruiter Match";
      atsSubtext.textContent = "Good base technical coverage, but missing key specialized domain keywords.";
    } else {
      atsHeadlineText.textContent = "Critical Competency Gaps Detected";
      atsSubtext.textContent = "Resume requires optimization in core algorithm and system architectural terms.";
    }

    // Matrix Grid
    matrixGrid.innerHTML = "";
    Object.entries(data.domain_matrix).forEach(([domain, stats]) => {
      const card = document.createElement("div");
      card.className = "matrix-card";
      card.innerHTML = `
        <div class="matrix-header">
          <span class="matrix-name">${domain}</span>
          <span class="matrix-value">${stats.score}%</span>
        </div>
        <div class="progress-bar-bg">
          <div class="progress-bar-fill" style="width: ${stats.score}%"></div>
        </div>
      `;
      matrixGrid.appendChild(card);
    });

    // Missing Competencies Tag Cloud
    missingTags.innerHTML = "";
    if (data.missing_competencies && data.missing_competencies.length > 0) {
      data.missing_competencies.forEach(tag => {
        const pill = document.createElement("span");
        pill.className = "tag-pill";
        pill.textContent = `+ ${tag.toUpperCase()}`;
        missingTags.appendChild(pill);
      });
    } else {
      missingTags.innerHTML = `<span style="font-size: 0.85rem; color: var(--accent-emerald);">No major missing competencies!</span>`;
    }

    // Recommendations List
    recommendationsList.innerHTML = "";
    if (data.recommendations && data.recommendations.length > 0) {
      data.recommendations.forEach(rec => {
        const item = document.createElement("div");
        item.className = `rec-card ${rec.priority}`;
        item.innerHTML = `
          <div class="rec-title">
            <span>${rec.title}</span>
            <span class="hud-badge" style="font-size: 0.65rem;">${rec.priority} PRIORITY</span>
          </div>
          <p class="rec-action">${rec.action}</p>
        `;
        recommendationsList.appendChild(item);
      });
    }
  }

  // --- Multimodal AI Interview Studio Functionality ---

  function startInterviewSession() {
    btnStartSession.innerHTML = `<i class="fa-solid fa-spinner fa-spin"></i> Initiating...`;
    btnStartSession.disabled = true;

    fetch("/api/v1/interviews/sessions/initiate", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        company_slug: selectedCompany
      })
    })
      .then(res => {
        if (!res.ok) throw new Error("Failed to initiate interview session.");
        return res.json();
      })
      .then(data => {
        activeSessionId = data.session_id;
        isSessionActive = true;
        
        sessionStepBadge.textContent = `Step ${data.current_step} of ${data.total_questions}`;
        hudCompanyBadge.textContent = `${data.company_name.toUpperCase()} INTERVIEWER`;

        displayQuestion(data.question);

        // Reset Telemetry Display
        telemetryWPM.innerHTML = `0 <span style="font-size: 0.8rem;">WPM</span>`;
        telemetryFillers.textContent = `0`;
        telemetryScore.innerHTML = `0.0 <span style="font-size: 0.8rem;">/ 10</span>`;

        // Enable Microphone & Controls
        btnMicRecord.disabled = false;
        btnSubmitAnswer.disabled = false;
        answerTranscriptionText.disabled = false;
        answerTranscriptionText.value = "";
        turnFeedbackArea.style.display = "none";
        sttStatusMsg.textContent = "Voice recognition ready. Click record or type answer to begin.";

        btnStartSession.innerHTML = `<i class="fa-solid fa-arrows-rotate"></i> Reset Session`;
        btnStartSession.disabled = false;
      })
      .catch(err => {
        alert("Error starting session: " + err.message);
        btnStartSession.innerHTML = `<i class="fa-solid fa-play"></i> Initiate Interview Session`;
        btnStartSession.disabled = false;
      });
  }

  function displayQuestion(q) {
    currentQuestionId = q.id;
    currentQuestionText = q.prompt;

    promptCategoryBadge.textContent = q.category;
    promptDifficultyBadge.textContent = q.difficulty;
    promptQuestionText.textContent = q.prompt;

    btnVocalize.disabled = false;

    // Automatically vocalize prompt if Web Speech API is supported
    vocalizeQuestionPrompt();
  }

  function vocalizeQuestionPrompt() {
    if ("speechSynthesis" in window) {
      window.speechSynthesis.cancel(); // Stop any active speech
      const utterance = new SpeechSynthesisUtterance(currentQuestionText);
      utterance.rate = 1.0;
      utterance.pitch = 1.0;
      window.speechSynthesis.speak(utterance);
    }
  }

  // Speech Recognition (STT) Setup
  function initSpeechRecognition() {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRecognition) {
      sttStatusMsg.textContent = "Web Speech API not supported in this browser. You can type answers manually.";
      return;
    }

    recognition = new SpeechRecognition();
    recognition.continuous = true;
    recognition.interimResults = true;
    recognition.lang = "en-US";

    recognition.onstart = () => {
      isRecording = true;
      recordingStartTime = Date.now();
      btnMicRecord.classList.add("recording");
      micBtnText.textContent = "Stop Recording (Listening...)";
      sttStatusMsg.textContent = "Listening to your voice answer... Speak clearly into microphone.";
    };

    recognition.onresult = (event) => {
      let transcript = "";
      for (let i = 0; i < event.results.length; i++) {
        transcript += event.results[i][0].transcript + " ";
      }
      answerTranscriptionText.value = transcript.trim();
    };

    recognition.onerror = (event) => {
      console.warn("Speech recognition error:", event.error);
      sttStatusMsg.textContent = "Speech recognition notice: " + event.error;
    };

    recognition.onend = () => {
      isRecording = false;
      btnMicRecord.classList.remove("recording");
      micBtnText.textContent = "Start Speech-to-Text Answer";
      sttStatusMsg.textContent = "Speech capture complete. Review answer and click Submit.";
    };
  }

  function toggleSpeechRecognition() {
    if (!recognition) {
      alert("Speech Recognition API is not supported in your browser. Please type your answer manually.");
      return;
    }

    if (isRecording) {
      recognition.stop();
    } else {
      answerTranscriptionText.value = "";
      recognition.start();
    }
  }

  // Submit Answer Turn to FastAPI backend
  function submitAnswerTurn() {
    const answer = answerTranscriptionText.value.trim();
    if (!answer) {
      alert("Please speak or type an answer before submitting.");
      return;
    }

    if (isRecording && recognition) {
      recognition.stop();
    }

    const durationSeconds = recordingStartTime ? max(5, (Date.now() - recordingStartTime) / 1000) : 20.0;

    btnSubmitAnswer.innerHTML = `<i class="fa-solid fa-spinner fa-spin"></i> Evaluating...`;
    btnSubmitAnswer.disabled = true;

    fetch("/api/v1/interviews/sessions/turn", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        session_id: activeSessionId,
        question_id: currentQuestionId,
        answer_text: answer,
        duration_seconds: durationSeconds
      })
    })
      .then(res => {
        if (!res.ok) throw new Error("Failed to process answer turn.");
        return res.json();
      })
      .then(data => {
        renderTurnFeedback(data);
      })
      .catch(err => {
        alert("Error evaluating turn: " + err.message);
      })
      .finally(() => {
        btnSubmitAnswer.innerHTML = `<i class="fa-solid fa-paper-plane"></i> Submit Answer`;
        btnSubmitAnswer.disabled = false;
      });
  }

  function renderTurnFeedback(data) {
    const evalData = data.turn_evaluation;

    // Update Telemetry Counters
    telemetryWPM.innerHTML = `${evalData.wpm} <span style="font-size: 0.8rem;">WPM</span>`;
    telemetryFillers.textContent = `${evalData.filler_count}`;
    telemetryScore.innerHTML = `${evalData.technical_score} <span style="font-size: 0.8rem;">/ 10</span>`;

    // Render Critique Card
    turnFeedbackArea.style.display = "flex";
    turnCritiqueContent.textContent = evalData.critique;

    // Clear Textarea for Next Question
    answerTranscriptionText.value = "";

    if (data.is_completed) {
      // Session finished, show scorecard modal
      showScorecardModal(data.cumulative_stats);
    } else {
      // Load next question
      sessionStepBadge.textContent = `Step ${data.current_step} of ${data.total_questions}`;
      displayQuestion(data.next_question);
    }
  }

  function showScorecardModal(stats) {
    modalFinalScore.textContent = `${stats.average_score} / 10`;
    modalFinalWPM.textContent = `${stats.average_wpm} WPM`;
    modalFinalFillers.textContent = `${stats.total_fillers}`;

    scorecardModal.classList.add("active");
  }

  function resetInterviewStudio() {
    isSessionActive = false;
    activeSessionId = null;
    currentQuestionId = null;

    sessionStepBadge.textContent = `Step 1 of 5`;
    promptCategoryBadge.textContent = `DSA`;
    promptDifficultyBadge.textContent = `Medium`;
    promptQuestionText.textContent = `Click "Initiate Interview Session" to load your first AI technical question.`;

    btnVocalize.disabled = true;
    btnMicRecord.disabled = true;
    btnSubmitAnswer.disabled = true;
    answerTranscriptionText.disabled = true;
    answerTranscriptionText.value = "";
    turnFeedbackArea.style.display = "none";
    sttStatusMsg.textContent = "Voice recognition ready. Click record or type answer to begin.";

    btnStartSession.innerHTML = `<i class="fa-solid fa-play"></i> Initiate Interview Session`;
  }

  // --- Webcam Feed & Cyberpunk Reticle Overlay HUD ---
  function initWebcamAndHUD() {
    // Request Webcam
    if (navigator.mediaDevices && navigator.mediaDevices.getUserMedia) {
      navigator.mediaDevices.getUserMedia({ video: true, audio: true })
        .then(stream => {
          webcamFeed.srcObject = stream;
          webcamFeed.play();
          setupAudioVisualizer(stream);
        })
        .catch(err => {
          console.warn("Webcam access denied or unavailable:", err);
          setupFallbackHUD();
        });
    } else {
      setupFallbackHUD();
    }

    startHUDCanvasAnimation();
  }

  function setupAudioVisualizer(stream) {
    try {
      audioContext = new (window.AudioContext || window.webkitAudioContext)();
      analyser = audioContext.createAnalyser();
      analyser.fftSize = 64;
      microphoneStream = audioContext.createMediaStreamSource(stream);
      microphoneStream.connect(analyser);
    } catch (e) {
      console.warn("Audio Context setup failed:", e);
    }
  }

  function setupFallbackHUD() {
    // Render static cyber grid inside video container when camera is disabled
    webcamFeed.style.background = "linear-gradient(135deg, #030712, #0b132b)";
  }

  function startHUDCanvasAnimation() {
    const ctx = hudOverlay.getContext("2d");

    function drawHUD() {
      const width = (hudOverlay.width = webcamFeed.clientWidth || 400);
      const height = (hudOverlay.height = webcamFeed.clientHeight || 280);

      ctx.clearRect(0, 0, width, height);

      // 1. Draw Target Reticle Corners
      const boxWidth = 140;
      const boxHeight = 140;
      const startX = (width - boxWidth) / 2;
      const startY = (height - boxHeight) / 2;
      const cornerLen = 16;

      ctx.strokeStyle = "rgba(0, 240, 255, 0.7)";
      ctx.lineWidth = 2;

      // Top-Left
      ctx.beginPath(); ctx.moveTo(startX, startY + cornerLen); ctx.lineTo(startX, startY); ctx.lineTo(startX + cornerLen, startY); ctx.stroke();
      // Top-Right
      ctx.beginPath(); ctx.moveTo(startX + boxWidth - cornerLen, startY); ctx.lineTo(startX + boxWidth, startY); ctx.lineTo(startX + boxWidth, startY + cornerLen); ctx.stroke();
      // Bottom-Left
      ctx.beginPath(); ctx.moveTo(startX, startY + boxHeight - cornerLen); ctx.lineTo(startX, startY + boxHeight); ctx.lineTo(startX + cornerLen, startY + boxHeight); ctx.stroke();
      // Bottom-Right
      ctx.beginPath(); ctx.moveTo(startX + boxWidth - cornerLen, startY + boxHeight); ctx.lineTo(startX + boxWidth, startY + boxHeight); ctx.lineTo(startX + boxWidth, startY + boxHeight - cornerLen); ctx.stroke();

      // 2. Draw Scanning Line Effect
      const time = Date.now() * 0.002;
      const scanY = startY + (Math.sin(time) * 0.5 + 0.5) * boxHeight;
      ctx.strokeStyle = "rgba(56, 189, 248, 0.4)";
      ctx.beginPath();
      ctx.moveTo(startX, scanY);
      ctx.lineTo(startX + boxWidth, scanY);
      ctx.stroke();

      // 3. Draw Audio Waveform Spectrum at Bottom
      if (analyser) {
        const bufferLength = analyser.frequencyBinCount;
        const dataArray = new Uint8Array(bufferLength);
        analyser.getByteFrequencyData(dataArray);

        const barWidth = (width / bufferLength) * 1.5;
        let x = 10;

        for (let i = 0; i < bufferLength; i++) {
          const barHeight = (dataArray[i] / 255) * 35;
          ctx.fillStyle = `rgba(0, 240, 255, ${0.4 + (barHeight / 35) * 0.6})`;
          ctx.fillRect(x, height - barHeight - 10, barWidth - 2, barHeight);
          x += barWidth + 2;
        }
      }

      animFrameId = requestAnimationFrame(drawHUD);
    }

    drawHUD();
  }

  // --- Curated Placement Courses Loader & Category Filter ---
  function loadCourses() {
    const grid = document.getElementById("coursesGrid");
    const tabsContainer = document.getElementById("courseCategoryTabs");
    if (!grid) return;

    fetch("/api/v1/courses")
      .then(res => res.json())
      .then(data => {
        if (!data.categories) return;

        let activeCategoryFilter = "all";

        function renderCategoryTabs() {
          if (!tabsContainer) return;
          tabsContainer.innerHTML = "";

          // "All Categories" Tab
          const allBtn = document.createElement("button");
          allBtn.className = `btn-glass ${activeCategoryFilter === "all" ? "btn-primary" : ""}`;
          allBtn.style.cssText = "padding: 6px 14px; font-size: 0.82rem;";
          allBtn.innerHTML = `<i class="fa-solid fa-list-check"></i> All Mastery Tracks (${data.categories.reduce((sum, c) => sum + c.courses.length, 0)})`;
          allBtn.onclick = () => {
            activeCategoryFilter = "all";
            renderCategoryTabs();
            renderCategoryBlocks();
          };
          tabsContainer.appendChild(allBtn);

          // Individual Category Tabs
          data.categories.forEach((cat, index) => {
            const catBtn = document.createElement("button");
            const isSelected = activeCategoryFilter === cat.category;
            catBtn.className = `btn-glass ${isSelected ? "btn-primary" : ""}`;
            catBtn.style.cssText = "padding: 6px 14px; font-size: 0.82rem;";
            catBtn.innerHTML = `<i class="fa-solid ${cat.icon}"></i> ${cat.category.split(" (")[0]}`;
            catBtn.onclick = () => {
              activeCategoryFilter = cat.category;
              renderCategoryTabs();
              renderCategoryBlocks();
            };
            tabsContainer.appendChild(catBtn);
          });
        }

        function renderCategoryBlocks() {
          grid.innerHTML = "";

          const filteredCategories = activeCategoryFilter === "all" 
            ? data.categories 
            : data.categories.filter(c => c.category === activeCategoryFilter);

          filteredCategories.forEach(cat => {
            const catBlock = document.createElement("div");
            catBlock.className = "course-category-card";
            catBlock.style.cssText = "background: rgba(255, 255, 255, 0.85); border: 1px solid var(--border-subtle); border-radius: 16px; padding: 22px; display: flex; flex-direction: column; gap: 16px; box-shadow: 0 4px 16px rgba(0,0,0,0.03);";

            let coursesHTML = "";
            cat.courses.forEach(c => {
              coursesHTML += `
                <div class="course-item" style="padding: 16px; background: #ffffff; border: 1px solid var(--border-subtle); border-radius: 12px; display: flex; flex-direction: column; justify-content: space-between; gap: 10px; box-shadow: 0 2px 8px rgba(0,0,0,0.02); transition: transform 0.2s ease;">
                  <div style="display: flex; flex-direction: column; gap: 6px;">
                    <div style="display: flex; justify-content: space-between; align-items: flex-start; gap: 10px;">
                      <h4 style="font-size: 1.05rem; color: var(--text-main); font-weight: 700; line-height: 1.2;">${c.title}</h4>
                      <span class="hud-badge" style="font-size: 0.65rem; white-space: nowrap; font-weight: 700;">${c.tag}</span>
                    </div>
                    <span style="font-size: 0.78rem; color: var(--accent-cyan); font-weight: 700;"><i class="fa-solid fa-circle-user"></i> ${c.provider}</span>
                    <p style="font-size: 0.84rem; color: var(--text-muted); line-height: 1.4; margin-top: 4px;">${c.coverage}</p>
                  </div>
                  <div style="display: flex; justify-content: flex-end; margin-top: 6px;">
                    <a href="${c.url}" target="_blank" rel="noopener noreferrer" class="btn-glass btn-primary" style="padding: 6px 14px; font-size: 0.8rem; text-decoration: none; display: inline-flex; align-items: center; gap: 6px; text-transform: uppercase;">
                      <i class="fa-brands fa-youtube" style="font-size: 1rem;"></i> Open Course <i class="fa-solid fa-arrow-up-right-from-square" style="font-size: 0.7rem;"></i>
                    </a>
                  </div>
                </div>
              `;
            });

            catBlock.innerHTML = `
              <div style="display: flex; justify-content: space-between; align-items: center; padding-bottom: 12px; border-bottom: 2px solid rgba(2,132,199,0.15);">
                <div style="display: flex; align-items: center; gap: 12px;">
                  <div style="width: 36px; height: 36px; border-radius: 10px; background: rgba(2,132,199,0.12); color: var(--accent-cyan); display: flex; align-items: center; justify-content: center; font-size: 1.1rem;">
                    <i class="fa-solid ${cat.icon}"></i>
                  </div>
                  <div>
                    <h3 style="font-size: 1.2rem; color: var(--text-main); font-weight: 700;">${cat.category}</h3>
                    <span style="font-size: 0.78rem; color: var(--text-subtle);">${cat.courses.length} Targeted Course Resource(s)</span>
                  </div>
                </div>
                <span class="hud-badge"><i class="fa-solid fa-check-double"></i> Verified Track</span>
              </div>
              
              <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(320px, 1fr)); gap: 16px;">
                ${coursesHTML}
              </div>
            `;

            grid.appendChild(catBlock);
          });
        }

        renderCategoryTabs();
        renderCategoryBlocks();
      })
      .catch(err => console.warn("Failed to load courses:", err));
  }

});
