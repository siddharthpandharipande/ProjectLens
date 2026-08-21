// Student database for simulation
const STUDENTS = {
  "Alex Chen": {
    name: "Alex Chen",
    project: "Smart Attendance System",
    overallScore: 84,
    execution: 88,
    originality: 81,
    documentation: 91,
    process: 86,
    techStack: ["Python 3.10", "Flask", "Pytest", "PostgreSQL", "Bash", "Docker"],
    loc: "15,204",
    complexity: "4.3",
    coverage: "82%",
    aiGen: "12%",
    strengths: [
      "Clean separation of concerns between frontend assets and backend service layer.",
      "Well-documented setup instructions and setup scripts in the root README.",
      "Robust unit testing of core face recognition algorithms using OpenCV mock parameters."
    ],
    improvements: [
      "Lack of database connection pooling in Flask backend causing queries to overflow connection limits.",
      "Mobile responsive layout breaking on dashboard screens under 480px width limits."
    ],
    signals: {
      likelihood: "Medium",
      conf: "84%",
      id: "PRJ-24-991A",
      time: "Oct 24, 14:38 UTC",
      node: "/src/backend/core"
    },
    innovation: {
      novelty: 87,
      contributions: [
        { title: "Optimized Loss Function", desc: "Custom contrastive loss model reduces convergence calculation steps by 15% under validation test metrics." },
        { title: "Hybrid Asynchronous Data Pipeline", desc: "Real-time video loading tasks offloaded via secondary thread queues in Python backend structure." }
      ],
      matches: [
        { name: "Sensor-based Defect Detection", pct: "85% Match" },
        { name: "Automated QA System", pct: "68% Match" }
      ]
    },
    viva: {
      projectName: "Attendance Prediction via ML",
      sessionId: "VX-892-ATT",
      qNum: "Question 03/10",
      qCat: "Methodology",
      qText: "Why did you choose Random Forest instead of Logistic Regression for the attendance model, given the dataset's size?",
      qTags: ["Model Selection", "Ensemble Methods", "Dataset Constraints"],
      upcoming: [
        "Q04: handling class imbalance",
        "Q05: ethics of predicting attendance",
        "Q06: deployment complexity targets"
      ],
      transcript: "We decided to implement a Random Forest architecture rather than Logistic Regression because the relationships between the student schedule parameters, course levels, and history are highly non-linear. Logistic regression models struggled to converge efficiently without heavy one-hot encoding feature scaling, which bloated model size. The ensemble trees gave us implicit feature importance scales out-of-the-box, ensuring robust validation handling.",
      accuracy: 85,
      clarity: 92,
      depth: 68
    },
    report: {
      grade: "A+",
      summary: "The candidate demonstrates an exceptional grasp of advanced AI execution, implementing a robust and scalable architectural design. The code demonstrates robust unit testing, structured database migrations, and highly original loss optimization modifications. The candidate successfully defended technical design choices during the Viva Voce session, showing depth in ensemble modeling selection parameters. Minor opportunities for connection pooling optimization and dependency reduction are recommended."
    }
  },
  "Elena Rostova": {
    name: "Elena Rostova",
    project: "Image Segmentation Pipeline",
    overallScore: 91,
    execution: 94,
    originality: 88,
    documentation: 89,
    process: 92,
    techStack: ["PyTorch", "FastAPI", "NVIDIA CUDA", "Redis", "MinIO"],
    loc: "32,450",
    complexity: "5.8",
    coverage: "89%",
    aiGen: "8%",
    strengths: [
      "Excellent performance scaling utilizing PyTorch tensor optimization hooks.",
      "Asynchronous file streaming framework via FastAPI reducing response latency.",
      "Robust logging architecture recording epoch weights and segmentation masks."
    ],
    improvements: [
      "Insufficient inline documentation inside CUDA custom kernel loaders.",
      "Unused legacy image preprocessing scripts left inside /notebooks folder."
    ],
    signals: {
      likelihood: "Low",
      conf: "95%",
      id: "PRJ-24-112B",
      time: "Oct 25, 09:12 UTC",
      node: "/src/cuda/kernels"
    },
    innovation: {
      novelty: 93,
      contributions: [
        { title: "Dynamic Spatial Weighting", desc: "Custom attention maps weight regions of interest dynamically during semantic segment extraction." },
        { title: "Zero-copy CUDA Memory Shared Nodes", desc: "Direct GPU data transfer from capture cards straight to model memory spaces." }
      ],
      matches: [
        { name: "Real-time Medical Scanner Image Maps", pct: "42% Match" },
        { name: "Automated QA Defects Scanner", pct: "30% Match" }
      ]
    },
    viva: {
      projectName: "Spatial Vision Segmentation Pipeline",
      sessionId: "VX-893-IMG",
      qNum: "Question 02/10",
      qCat: "GPU Optimization",
      qText: "Explain how you eliminated memory bottlenecks between the host CPU and the GPU during live frame analysis.",
      qTags: ["CUDA Memory", "FastAPI Stream", "Buffer Management"],
      upcoming: [
        "Q03: U-Net vs Transformer encoding",
        "Q04: dataset labeling validation",
        "Q05: Docker image size minimization"
      ],
      transcript: "To eliminate the memory transfers overhead, we wrote a custom C++ CUDA binding that registers physical memory buffers on the host CPU. By utilizing pinned memory layouts rather than standard virtual page space allocations, the GPU can direct-memory-access (DMA) the incoming network camera streams. This bypassed the host CPU memory copy stages, shaving 40% off our total inference cycle overhead.",
      accuracy: 94,
      clarity: 88,
      depth: 92
    },
    report: {
      grade: "A+",
      summary: "Elena Rostova has submitted an exceptional project demonstrating industrial-level understanding of hardware accelerated pipelines. The core CUDA kernels and FastAPI framework show exemplary engineering layout. The candidate defended CUDA memory allocation logic with outstanding clarity. High score documentation aligns seamlessly with code structures. An excellent submission overall."
    }
  },
  "Marcus Vance": {
    name: "Marcus Vance",
    project: "Distributed Database Consensus",
    overallScore: 76,
    execution: 78,
    originality: 73,
    documentation: 79,
    process: 75,
    techStack: ["Go 1.19", "gRPC", "Protobuf", "Raft Consensus", "Kubernetes"],
    loc: "18,910",
    complexity: "6.2",
    coverage: "71%",
    aiGen: "18%",
    strengths: [
      "Effective implementation of Raft consensus protocol in pure Go.",
      "Protobuf models well structured with clean version numbering guidelines.",
      "Clear orchestration manifests for cluster deployment."
    ],
    improvements: [
      "Edge cases in leader election under heavy network partitioning fail tests.",
      "Documentation lacks architectural maps describing state transitions."
    ],
    signals: {
      likelihood: "Medium",
      conf: "72%",
      id: "PRJ-24-388F",
      time: "Oct 25, 11:45 UTC",
      node: "/src/consensus/raft"
    },
    innovation: {
      novelty: 74,
      contributions: [
        { title: "Optimized Heartbeat Triggers", desc: "Adjustable heartbeat frequency depending on network packet drop rates reduces consensus lag." },
        { title: "Compact Log Compaction Logs", desc: "Custom snapshots format saving only terminal states of atomic variables." }
      ],
      matches: [
        { name: "Distributed Ledger Blockchain Node", pct: "79% Match" },
        { name: "Etcd Core Key-Value Backend", pct: "65% Match" }
      ]
    },
    viva: {
      projectName: "Go Raft Ledger Consensus",
      sessionId: "VX-894-RFT",
      qNum: "Question 01/10",
      qCat: "Network Partitioning",
      qText: "How does your cluster handle split-brain situations when the network partitions into two disconnected halves?",
      qTags: ["Leader Election", "Network Partition", "Raft Consensus"],
      upcoming: [
        "Q02: log compaction schedules",
        "Q03: gRPC connection pooling",
        "Q04: cluster nodes health checks"
      ],
      transcript: "Our consensus protocol resolves split-brain partitions by enforcing strict majority quorums. If the cluster splits into two segments, only the segment containing a mathematical majority (e.g., 3 out of 5 nodes) can elect a leader and accept writes. The minority partition will refuse write attempts and drop transactions. Once network connectivity heals, the nodes synchronize with the correct leader.",
      accuracy: 80,
      clarity: 75,
      depth: 72
    },
    report: {
      grade: "B+",
      summary: "Marcus Vance has executed a solid consensus protocol implementation. The node communication layer in Go is structured correctly. Election logic fails under strict partition tests, but the student was able to explain consensus mechanics adequately during Q&A review. Recommending a B+ grade with a focus on fixing node serialization bugs."
    }
  }
};

// Global variables for active student and simulation states
let activeStudent = "Alex Chen";
let activeView = "overview";

// Initialize on page load
window.addEventListener("DOMContentLoaded", () => {
  setupNavigation();
  setupUploadModal();
  setupInnovationDnaCanvas();
  setupVivaSimulator();
  setupFacultyDashboard();
  setupReanalyzeAction();
  setupSearchAndFilters();
  
  // Check if directed from landing page with upload query
  const urlParams = new URLSearchParams(window.location.search);
  if (urlParams.get("action") === "upload") {
    openUploadModal();
  }

  // Load default student data
  loadStudent(activeStudent);
});

/* ==========================================================================
   TAB NAVIGATION SYSTEM
   ========================================================================== */
function setupNavigation() {
  const menuItems = document.querySelectorAll(".db-sidebar .db-menu-item");
  const viewTitle = document.getElementById("currentViewTitle");

  menuItems.forEach(item => {
    const btn = item.querySelector("button") || item.querySelector("a");
    if (!btn) return;

    btn.addEventListener("click", (e) => {
      // Don't intercept sign out link
      if (btn.getAttribute("href") === "index.html") return;

      e.preventDefault();
      
      const targetView = item.getAttribute("data-view");
      if (!targetView) return;

      // Update active sidebar item
      menuItems.forEach(mi => mi.classList.remove("active"));
      item.classList.add("active");

      // Switch main view panels
      const allViews = document.querySelectorAll(".db-tab-view");
      allViews.forEach(v => v.classList.remove("active"));

      const activePanel = document.getElementById(`view-${targetView}`);
      if (activePanel) {
        activePanel.classList.add("active");
        activeView = targetView;
        
        // Update Title
        const namesMap = {
          "overview": "Project Overview",
          "signals": "AI Assistance Signals",
          "innovation": "Innovation DNA Analysis",
          "viva": "Viva Voce Examination Console",
          "report": "Evaluation Summary & Report",
          "faculty": "Academic Roster Management",
          "styleguide": "ProjectLens Suite Design Tokens"
        };
        viewTitle.innerText = namesMap[targetView] || "Dashboard";
      }
    });
  });
}

/* ==========================================================================
   DATA LOADING SYSTEM (Student Context Switching)
   ========================================================================== */
function loadStudent(studentName) {
  const student = STUDENTS[studentName];
  if (!student) return;

  activeStudent = studentName;

  // Header & Avatar Update
  document.getElementById("userProfileName").innerText = studentName;
  const initials = studentName.split(" ").map(n => n[0]).join("");
  document.getElementById("userAvatar").innerText = initials;

  // 1. Overview Tab
  document.getElementById("projNameText").innerText = student.project;
  document.getElementById("projAuthorText").innerText = studentName;
  document.getElementById("overallScoreVal").innerText = student.overallScore;

  // Subscores
  document.getElementById("subscoreExecution").innerText = student.execution;
  document.getElementById("subscoreOriginality").innerText = student.originality;
  document.getElementById("subscoreDocumentation").innerText = student.documentation;
  document.getElementById("subscoreProcess").innerText = student.process;

  // Animate Gauges
  animateGauges(student);

  // Tech Stack Badges
  const techStackContainer = document.getElementById("overviewTechStack");
  techStackContainer.innerHTML = "";
  student.techStack.forEach(tech => {
    const badge = document.createElement("span");
    badge.className = "tech-badge";
    badge.innerText = tech;
    techStackContainer.appendChild(badge);
  });

  // Analytics Metrics
  document.getElementById("metricLOC").innerText = student.loc;
  document.getElementById("metricComplexity").innerText = student.complexity;
  document.getElementById("metricCoverage").innerText = student.coverage;
  document.getElementById("metricAI").innerText = student.aiGen;

  // Strengths List
  const strengthsContainer = document.getElementById("listStrengths");
  strengthsContainer.innerHTML = "";
  student.strengths.forEach(str => {
    const li = document.createElement("li");
    li.innerHTML = `
      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="color: var(--status-green);"><polyline points="20 6 9 17 4 12"/></svg>
      ${str}
    `;
    strengthsContainer.appendChild(li);
  });

  // Improvements List
  const improvementsContainer = document.getElementById("listImprovements");
  improvementsContainer.innerHTML = "";
  student.improvements.forEach(imp => {
    const li = document.createElement("li");
    li.innerHTML = `
      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="color: var(--color-secondary);"><line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/></svg>
      ${imp}
    `;
    improvementsContainer.appendChild(li);
  });

  // 2. AI Signals Tab
  document.getElementById("signalLikelihoodVal").innerText = student.signals.likelihood;
  document.getElementById("signalConfPercent").innerText = student.signals.conf;
  document.getElementById("signalInspectionId").innerText = student.signals.id;
  document.getElementById("signalRunTime").innerText = student.signals.time;
  document.getElementById("signalTargetNode").innerText = student.signals.node;

  // Update classes for signals card based on status
  const likelihoodBadge = document.getElementById("signalLikelihoodVal");
  likelihoodBadge.className = "signal-value-badge";
  if (student.signals.likelihood === "Low") {
    likelihoodBadge.style.color = "var(--status-green)";
    likelihoodBadge.style.background = "rgba(16, 185, 129, 0.1)";
  } else if (student.signals.likelihood === "Medium") {
    likelihoodBadge.style.color = "var(--status-yellow)";
    likelihoodBadge.style.background = "rgba(245, 158, 11, 0.1)";
  } else {
    likelihoodBadge.style.color = "var(--status-red)";
    likelihoodBadge.style.background = "rgba(239, 68, 68, 0.1)";
  }

  // 3. Innovation DNA Tab
  document.getElementById("noveltyScoreVal").innerText = student.innovation.novelty;
  
  // Custom contributions list
  const contributionsContainer = document.querySelector(".innovation-contributions");
  // Keep the header h4, clear the rest
  const headerContribution = contributionsContainer.querySelector("h4");
  contributionsContainer.innerHTML = "";
  contributionsContainer.appendChild(headerContribution);
  
  student.innovation.contributions.forEach(cont => {
    const div = document.createElement("div");
    div.className = "innovation-contribution-item";
    div.innerHTML = `
      <h5>${cont.title}</h5>
      <p>${cont.desc}</p>
    `;
    contributionsContainer.appendChild(div);
  });

  // Matches list
  const matchesList = document.querySelector(".matches-list");
  matchesList.innerHTML = "";
  student.innovation.matches.forEach(match => {
    const div = document.createElement("div");
    div.className = "match-item";
    div.innerHTML = `
      <span class="match-title">${match.name}</span>
      <span class="match-percentage">${match.pct}</span>
    `;
    matchesList.appendChild(div);
  });

  // 4. Viva Console
  document.getElementById("vivaProjectName").innerText = student.viva.projectName;
  document.getElementById("vivaSessionId").innerText = student.viva.sessionId;
  document.getElementById("vivaQuestionNum").innerText = student.viva.qNum;
  document.getElementById("vivaQuestionCat").innerText = student.viva.qCat;
  document.getElementById("vivaQuestionText").innerText = student.viva.qText;

  // Question Tags
  const tagsBox = document.getElementById("vivaQuestionTags");
  tagsBox.innerHTML = "";
  student.viva.qTags.forEach(tag => {
    const span = document.createElement("span");
    span.className = "viva-tag";
    span.innerText = tag;
    tagsBox.appendChild(span);
  });

  // Clear transcript and reset evaluation bars
  document.getElementById("vivaTranscriptBox").innerHTML = `
    <span class="transcript-placeholder" style="color: var(--text-muted); font-style: italic;">Press the microphone button to start answering...</span>
  `;
  document.getElementById("vivaScoreAccuracy").style.width = "0%";
  document.getElementById("vivaValAccuracy").innerText = "0%";
  document.getElementById("vivaScoreClarity").style.width = "0%";
  document.getElementById("vivaValClarity").innerText = "0%";
  document.getElementById("vivaScoreDepth").style.width = "0%";
  document.getElementById("vivaValDepth").innerText = "0%";

  // Queue
  const queueBox = document.querySelector(".viva-queue-list");
  queueBox.innerHTML = "";
  student.viva.upcoming.forEach((upc, idx) => {
    const div = document.createElement("div");
    div.className = `viva-queue-item ${idx === 0 ? 'upcoming' : ''}`;
    div.innerHTML = `
      <span>${upc}</span>
      <span style="font-family: var(--font-mono); color: ${idx === 0 ? 'var(--color-primary)' : 'var(--text-muted)'};">${idx === 0 ? 'Upcoming' : 'Queued'}</span>
    `;
    queueBox.appendChild(div);
  });

  // 5. Final Report
  document.getElementById("reportSubmissionId").innerText = `#${student.signals.id}-EVAL`;
  document.getElementById("reportEvalDate").innerText = new Date().toLocaleDateString('en-US', { year: 'numeric', month: 'short', day: 'numeric' });
  document.getElementById("reportFinalGrade").innerText = student.report.grade;
  document.getElementById("reportExecSummary").innerText = student.report.summary;

  // Load report strengths/refinements bullet lists
  const reportStrengthsContainer = document.getElementById("reportCoreStrengths");
  reportStrengthsContainer.innerHTML = `
    <li>
      <strong>Algorithmic Execution</strong>
      <span>${student.strengths[0]}</span>
    </li>
    <li>
      <strong>Documentation Rigor</strong>
      <span>${student.strengths[1]}</span>
    </li>
  `;
  const reportRefinementsContainer = document.getElementById("reportRefinements");
  reportRefinementsContainer.innerHTML = `
    <li>
      <strong>Execution Refinements</strong>
      <span>${student.improvements[0]}</span>
    </li>
    <li>
      <strong>Secondary Optimization</strong>
      <span>${student.improvements[1]}</span>
    </li>
  `;
}

function animateGauges(student) {
  // Simple animation using dashoffset triggers
  const getOffset = (score) => (100 - score);
  document.getElementById("gaugeExecution").setAttribute("stroke-dasharray", `${student.execution}, 100`);
  document.getElementById("gaugeOriginality").setAttribute("stroke-dasharray", `${student.originality}, 100`);
  document.getElementById("gaugeDocumentation").setAttribute("stroke-dasharray", `${student.documentation}, 100`);
  document.getElementById("gaugeProcess").setAttribute("stroke-dasharray", `${student.process}, 100`);
}

// Global scope binding for student switching from faculty list
window.loadStudentData = function(studentName) {
  loadStudent(studentName);
  
  // Flash toast showing loading
  showToast(`Switched view to ${studentName}'s assessment evaluation report.`);

  // Auto transition to project overview
  const overviewMenu = document.querySelector('.db-menu-item[data-view="overview"]');
  if (overviewMenu) {
    overviewMenu.querySelector("button").click();
  }
};

/* ==========================================================================
   VIVA VOICE SIMULATOR (Microphone interaction)
   ========================================================================== */
function setupVivaSimulator() {
  const micBtn = document.getElementById("vivaMicBtn");
  const micStatus = document.getElementById("vivaMicStatus");
  const transcriptBox = document.getElementById("vivaTranscriptBox");

  micBtn.addEventListener("click", () => {
    // If already recording or playing, ignore
    if (micBtn.classList.contains("recording")) return;

    const student = STUDENTS[activeStudent];
    if (!student) return;

    // Trigger recording active state
    micBtn.classList.add("recording");
    micStatus.innerText = "MIC STATUS: RECORDING AUDIO...";
    transcriptBox.innerHTML = '<span class="recording-dots" style="color: var(--status-red); font-weight: 500;">Listening for audio speech input...</span>';

    // After 2 seconds, begin mock transcribing typing effect
    setTimeout(() => {
      micStatus.innerText = "MIC STATUS: TRANSCRIBING AUDIO FEED...";
      transcriptBox.innerHTML = "";
      
      const words = student.viva.transcript.split(" ");
      let i = 0;

      function typeWord() {
        if (i < words.length) {
          transcriptBox.innerHTML += words[i] + " ";
          transcriptBox.scrollTop = transcriptBox.scrollHeight;
          i++;
          setTimeout(typeWord, 100); // 100ms per word
        } else {
          // Finished transcribing
          micBtn.classList.remove("recording");
          micStatus.innerText = "MIC STATUS: OFFLINE (TRANSCRIPT SAVED)";
          
          // Animate the evaluation metrics score progress bars
          setTimeout(() => {
            animateVivaScores(student);
            showToast("Viva Q&A Question graded successfully!");
          }, 800);
        }
      }
      typeWord();

    }, 2000);
  });
}

function animateVivaScores(student) {
  const accBar = document.getElementById("vivaScoreAccuracy");
  const clrBar = document.getElementById("vivaScoreClarity");
  const depBar = document.getElementById("vivaScoreDepth");

  const accVal = document.getElementById("vivaValAccuracy");
  const clrVal = document.getElementById("vivaValClarity");
  const depVal = document.getElementById("vivaValDepth");

  // Animate bars widths
  accBar.style.width = `${student.viva.accuracy}%`;
  clrBar.style.width = `${student.viva.clarity}%`;
  depBar.style.width = `${student.viva.depth}%`;

  // Count up value texts
  countUpText(accVal, student.viva.accuracy);
  countUpText(clrVal, student.viva.clarity);
  countUpText(depVal, student.viva.depth);
}

function countUpText(element, limit) {
  let count = 0;
  const interval = setInterval(() => {
    if (count <= limit) {
      element.innerText = `${count}%`;
      count++;
    } else {
      clearInterval(interval);
    }
  }, 15);
}

/* ==========================================================================
   INNOVATION DNA GRAPH INTEGRATION
   ========================================================================= */
function setupInnovationDnaCanvas() {
  const canvas = document.getElementById("dnaCanvas");
  const svg = document.getElementById("dnaConnectionsSvg");
  const nodes = canvas.querySelectorAll(".dna-node");
  
  // Render connectors line logic on canvas
  function drawLines() {
    svg.innerHTML = "";
    const activeNode = canvas.querySelector(".dna-node.selected");
    if (!activeNode) return;

    const startX = activeNode.offsetLeft + 20;
    const startY = activeNode.offsetTop + 20;

    nodes.forEach(node => {
      if (node === activeNode) return;

      const endX = node.offsetLeft + 20;
      const endY = node.offsetTop + 20;

      // Draw SVG lines
      const line = document.createElementNS("http://www.w3.org/2000/svg", "line");
      line.setAttribute("x1", startX);
      line.setAttribute("y1", startY);
      line.setAttribute("x2", endX);
      line.setAttribute("y2", endY);
      line.setAttribute("stroke", "rgba(49, 87, 213, 0.25)");
      line.setAttribute("stroke-width", "2");
      if (node.classList.contains("accent")) {
        line.setAttribute("stroke", "rgba(233, 120, 91, 0.25)");
      }
      svg.appendChild(line);
    });
  }

  // Bind click handlers to nodes
  nodes.forEach(node => {
    node.addEventListener("click", () => {
      nodes.forEach(n => n.classList.remove("selected"));
      node.classList.add("selected");

      // Update Node details card
      document.getElementById("nodeName").innerText = node.getAttribute("data-name");
      document.getElementById("nodeDesc").innerText = node.getAttribute("data-desc");
      document.getElementById("nodeWeight").innerText = `Weight: ${node.getAttribute("data-weight")}`;
      
      drawLines();
    });
  });

  // Initial draw lines
  setTimeout(drawLines, 200);

  // Redraw on window resize
  window.addEventListener("resize", drawLines);
}

/* ==========================================================================
   UPLOAD DIRECTORY SCAN MOCK SYSTEM
   ========================================================================== */
function setupUploadModal() {
  const modal = document.getElementById("uploadModal");
  const openBtn = document.getElementById("newAnalysisBtn");
  const closeBtn = document.getElementById("closeUploadModalBtn");
  const dropzone = document.getElementById("dropzone");
  const fileInput = document.getElementById("fileInput");

  // Open / Close actions
  openBtn.addEventListener("click", openUploadModal);
  closeBtn.addEventListener("click", closeUploadModal);

  window.openUploadModal = openUploadModal; // Global access
  window.closeUploadModal = closeUploadModal;

  function openUploadModal() {
    modal.classList.add("active");
  }

  function closeUploadModal() {
    modal.classList.remove("active");
  }

  // Dropzone drag events
  dropzone.addEventListener("click", () => fileInput.click());
  
  dropzone.addEventListener("dragover", (e) => {
    e.preventDefault();
    dropzone.classList.add("dragover");
  });

  dropzone.addEventListener("dragleave", () => {
    dropzone.classList.remove("dragover");
  });

  dropzone.addEventListener("drop", (e) => {
    e.preventDefault();
    dropzone.classList.remove("dragover");
    if (e.dataTransfer.files.length > 0) {
      handleFileUpload(e.dataTransfer.files[0]);
    }
  });

  fileInput.addEventListener("change", (e) => {
    if (fileInput.files.length > 0) {
      handleFileUpload(fileInput.files[0]);
    }
  });
}

function handleFileUpload(file) {
  // Close upload modal
  closeUploadModal();

  // Hide main view grid, show Scan loading view
  const dbWrapper = document.getElementById("dashboardWrapper");
  const mainView = document.getElementById("dbMainView");
  const sidebar = document.querySelector(".db-sidebar");
  const scanView = document.getElementById("scanLoadingView");
  const progressText = document.getElementById("scanProgressText");

  mainView.style.display = "none";
  sidebar.style.display = "none";
  dbWrapper.style.gridTemplateColumns = "1fr";
  scanView.classList.add("active");

  // Run mock scan progression logging messages
  const logs = [
    "Loading source file payload nodes...",
    "Running Abstract Syntax Tree (AST) token mappings...",
    "Scanning code segments with probabilistic models...",
    "Cross-referencing codebase against project documentation...",
    "Compiling Innovation DNA vector nodes...",
    "Compiling final reports and Viva session parameters..."
  ];

  let step = 0;
  function runLogs() {
    if (step < logs.length) {
      progressText.innerText = logs[step];
      step++;
      setTimeout(runLogs, 700);
    } else {
      // Completed, return view, reset grid, load Elena Rostova data as a mock output
      scanView.classList.remove("active");
      dbWrapper.style.gridTemplateColumns = "var(--sidebar-width) 1fr";
      mainView.style.display = "flex";
      
      // Handle responsive layout reset
      if (window.innerWidth <= 1024) {
        dbWrapper.style.gridTemplateColumns = "1fr";
        sidebar.style.display = "none";
      } else {
        sidebar.style.display = "flex";
      }

      loadStudent("Elena Rostova");
      showToast("Evaluation file successfully parsed & analyzed!");
      
      // Switch sidebar tab selection highlight to overview
      const menuItems = document.querySelectorAll(".db-sidebar .db-menu-item");
      menuItems.forEach(mi => mi.classList.remove("active"));
      const overviewMenu = document.querySelector('.db-menu-item[data-view="overview"]');
      if (overviewMenu) overviewMenu.classList.add("active");
      document.getElementById("currentViewTitle").innerText = "Project Overview";
      
      // Switch view panel visibility
      const allViews = document.querySelectorAll(".db-tab-view");
      allViews.forEach(v => v.classList.remove("active"));
      document.getElementById("view-overview").classList.add("active");
    }
  }
  runLogs();
}

/* ==========================================================================
   RE-ANALYZE BUTTON MOCK TRIGGER
   ========================================================================== */
function setupReanalyzeAction() {
  const reanalyzeBtn = document.getElementById("overviewScanTrigger");
  reanalyzeBtn.addEventListener("click", () => {
    const studentName = activeStudent;
    showToast(`Re-triggering scanner pipeline on ${studentName}'s files...`);
    
    // Simulate simple reloading scanner trigger
    reanalyzeBtn.setAttribute("disabled", "true");
    reanalyzeBtn.innerHTML = `
      <svg class="scan-spinner-mini" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="animation: spin 0.8s linear infinite;"><path d="M21.5 2v6h-6M21.34 15.57a10 10 0 1 1-.57-8.38l5.67-5.67"/></svg>
      Scanning...
    `;

    setTimeout(() => {
      reanalyzeBtn.removeAttribute("disabled");
      reanalyzeBtn.innerHTML = `
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21.5 2v6h-6M21.34 15.57a10 10 0 1 1-.57-8.38l5.67-5.67"/></svg>
        Re-Analyze
      `;
      loadStudent(studentName);
      showToast("Static analysis metrics re-compiled!");
    }, 1500);
  });
}

/* ==========================================================================
   FACULTY ROSTER FILTERS & STUDENT QUEUE SEARCH
   ========================================================================== */
function setupFacultyDashboard() {
  const tabs = document.querySelectorAll(".faculty-filter-tab");
  const rows = document.querySelectorAll("#facultyRosterBody tr");

  tabs.forEach(tab => {
    tab.addEventListener("click", () => {
      tabs.forEach(t => t.classList.remove("active"));
      tab.classList.add("active");

      const filter = tab.getAttribute("data-filter");
      
      rows.forEach(row => {
        const rowStatus = row.getAttribute("data-status");
        if (filter === "all" || rowStatus === filter) {
          row.style.display = "";
        } else {
          row.style.display = "none";
        }
      });
    });
  });

  // Mock import roster button action
  const importBtn = document.getElementById("facultyImportBtn");
  importBtn.addEventListener("click", () => {
    showToast("Synchronizing roster with university database...");
    importBtn.setAttribute("disabled", "true");
    
    setTimeout(() => {
      importBtn.removeAttribute("disabled");
      showToast("Academic roster synced successfully!");
    }, 1200);
  });
}

function setupSearchAndFilters() {
  const searchInput = document.getElementById("dbSearchField");
  
  searchInput.addEventListener("input", (e) => {
    const query = e.target.value.toLowerCase().trim();
    
    // If active view is Faculty Dashboard, filter table rows
    if (activeView === "faculty") {
      const rows = document.querySelectorAll("#facultyRosterBody tr");
      rows.forEach(row => {
        const name = row.querySelector("h4").innerText.toLowerCase();
        const project = row.cells[1].innerText.toLowerCase();
        
        if (name.includes(query) || project.includes(query)) {
          row.style.display = "";
        } else {
          row.style.display = "none";
        }
      });
    }
  });

  // Export PDF Report action
  const exportBtn = document.getElementById("btnExportPdf");
  exportBtn.addEventListener("click", () => {
    exportBtn.setAttribute("disabled", "true");
    exportBtn.innerText = "Generating PDF...";
    
    setTimeout(() => {
      exportBtn.removeAttribute("disabled");
      exportBtn.innerHTML = `
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></svg>
        Export PDF Report
      `;
      showToast("Evaluation report exported as PDF.");
    }, 1500);
  });

  // Innovation Proceed to Viva action
  document.getElementById("proceedToVivaBtn").addEventListener("click", () => {
    const vivaMenu = document.querySelector('.db-menu-item[data-view="viva"]');
    if (vivaMenu) {
      vivaMenu.querySelector("button").click();
    }
  });
}

/* ==========================================================================
   TOAST NOTIFICATION COMPONENT
   ========================================================================== */
function showToast(message, isError = false) {
  const toast = document.getElementById("toastNotification");
  toast.innerText = message;
  toast.className = "toast-msg";
  if (isError) toast.classList.add("error");
  
  toast.style.display = "block";
  
  // Hide after 3.5 seconds
  setTimeout(() => {
    toast.style.display = "none";
  }, 3500);
}
