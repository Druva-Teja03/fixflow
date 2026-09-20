/**
 * FixFlow Multi-Step Issue Reporting Form
 * Steps:
 * 1. Describe Problem (title, description)
 * 2. Category & Priority selection (with rule-based Smart Suggestions)
 * 3. Location (block, building, room)
 * 4. Photo upload & preview
 * 5. Review & Submit (with Duplicate Detection & Community Support)
 */

let currentStep = 1;
const totalSteps = 5;
let selectedFile = null;

// Smart suggestion & duplicate state
let aiSuggestion = null;
let userEditedCategory = false;
let userEditedPriority = false;

document.addEventListener("DOMContentLoaded", async () => {
  // Ensure user is authenticated student
  if (!auth.requireAuth(["student"])) return;

  // Load dropdown options from backend
  await loadMetaOptions();

  // Setup event listeners
  setupNavigation();
  setupSmartSuggestions();
  setupPhotoUpload();
  setupFormSubmit();
});

async function loadMetaOptions() {
  try {
    const meta = await api.get("/meta/options");

    // Populate Category dropdown
    const catSelect = document.getElementById("category");
    catSelect.innerHTML = '<option value="">-- Select Category --</option>';
    meta.categories.forEach((cat) => {
      const opt = document.createElement("option");
      opt.value = cat;
      opt.textContent = cat;
      catSelect.appendChild(opt);
    });

    // Populate Priority dropdown
    const prioSelect = document.getElementById("priority");
    prioSelect.innerHTML = "";
    meta.priorities.forEach((prio) => {
      const opt = document.createElement("option");
      opt.value = prio;
      opt.textContent = prio;
      if (prio === "Medium") opt.selected = true;
      prioSelect.appendChild(opt);
    });

    // Populate Block dropdown
    const blockSelect = document.getElementById("block");
    blockSelect.innerHTML = '<option value="">-- Select Campus Block --</option>';
    meta.blocks.forEach((blk) => {
      const opt = document.createElement("option");
      opt.value = blk;
      opt.textContent = blk;
      blockSelect.appendChild(opt);
    });
  } catch (err) {
    console.error("Failed to load options:", err);
    showToast("Failed to load category/location options.", "error");
  }
}

function setupSmartSuggestions() {
  const descEl = document.getElementById("description");
  if (descEl) {
    descEl.addEventListener("blur", fetchSmartSuggestions);
    descEl.addEventListener("change", fetchSmartSuggestions);
  }

  const catSelect = document.getElementById("category");
  if (catSelect) {
    catSelect.addEventListener("change", () => {
      userEditedCategory = true;
    });
  }

  const prioSelect = document.getElementById("priority");
  if (prioSelect) {
    prioSelect.addEventListener("change", () => {
      userEditedPriority = true;
    });
  }
}

async function fetchSmartSuggestions() {
  const desc = document.getElementById("description").value.trim();
  if (desc.length < 5) return;

  try {
    const res = await api.post("/ai/suggest", {
      description: desc,
      block: document.getElementById("block")?.value || null,
      room: document.getElementById("room")?.value || null,
    });

    if (res && res.category) {
      aiSuggestion = res;

      const catSelect = document.getElementById("category");
      if (catSelect && !userEditedCategory) {
        catSelect.value = res.category;
      }

      const prioSelect = document.getElementById("priority");
      if (prioSelect && !userEditedPriority) {
        prioSelect.value = res.priority;
      }

      // Render Smart Suggestion badge
      const badgeContainer = document.getElementById("ai-suggest-badge-container");
      if (badgeContainer) {
        badgeContainer.innerHTML = `
          <span class="badge" style="background: rgba(139, 92, 246, 0.2); border: 1px solid #8b5cf6; color: #c084fc; font-size: 0.75rem; padding: 0.25rem 0.55rem;">
            ✨ Smart suggestion (${Math.round(res.confidence * 100)}% match)
          </span>
        `;
      }

      const noteBox = document.getElementById("ai-suggestion-note");
      const noteText = document.getElementById("ai-suggestion-text");
      if (noteBox && noteText) {
        noteText.textContent = `Auto-selected Category: "${res.category}" and Priority: "${res.priority}".`;
        noteBox.style.display = "block";
      }
    }
  } catch (err) {
    console.warn("Could not fetch smart suggestion:", err);
  }
}

function setupNavigation() {
  document.getElementById("btn-next").addEventListener("click", async () => {
    if (validateStep(currentStep)) {
      if (currentStep === 1) {
        // Trigger smart suggestion before showing step 2 if not fetched yet
        if (!aiSuggestion) {
          await fetchSmartSuggestions();
        }
      }
      if (currentStep < totalSteps) {
        goToStep(currentStep + 1);
      }
    }
  });

  document.getElementById("btn-prev").addEventListener("click", () => {
    if (currentStep > 1) {
      goToStep(currentStep - 1);
    }
  });
}

function validateStep(step) {
  const errorBox = document.getElementById("step-error");
  errorBox.style.display = "none";
  errorBox.textContent = "";

  if (step === 1) {
    const title = document.getElementById("title").value.trim();
    const desc = document.getElementById("description").value.trim();
    if (title.length < 3) {
      showStepError("Title must be at least 3 characters.");
      return false;
    }
    if (desc.length < 5) {
      showStepError("Please provide at least 5 characters of description.");
      return false;
    }
  } else if (step === 2) {
    const cat = document.getElementById("category").value;
    const prio = document.getElementById("priority").value;
    if (!cat) {
      showStepError("Please select an issue category.");
      return false;
    }
    if (!prio) {
      showStepError("Please select a priority level.");
      return false;
    }
  } else if (step === 3) {
    const block = document.getElementById("block").value;
    if (!block) {
      showStepError("Please select a campus block.");
      return false;
    }
  } else if (step === 4) {
    // Photo is optional, but if file is chosen check size
    if (selectedFile && selectedFile.size > 5 * 1024 * 1024) {
      showStepError("Image size must be less than 5 MB.");
      return false;
    }
  }
  return true;
}

function showStepError(msg) {
  const errorBox = document.getElementById("step-error");
  errorBox.style.display = "block";
  errorBox.textContent = msg;
}

function goToStep(step) {
  currentStep = step;

  // Update step panels visibility
  for (let i = 1; i <= totalSteps; i++) {
    const panel = document.getElementById(`step-${i}`);
    if (panel) {
      panel.style.display = i === currentStep ? "block" : "none";
    }
    const indicator = document.getElementById(`step-indicator-${i}`);
    if (indicator) {
      if (i === currentStep) {
        indicator.classList.add("active");
        indicator.classList.remove("completed");
      } else if (i < currentStep) {
        indicator.classList.add("completed");
        indicator.classList.remove("active");
      } else {
        indicator.classList.remove("active", "completed");
      }
    }
  }

  // Navigation buttons state
  const prevBtn = document.getElementById("btn-prev");
  const nextBtn = document.getElementById("btn-next");
  const submitBtn = document.getElementById("btn-submit");

  prevBtn.style.display = currentStep > 1 ? "inline-flex" : "none";

  if (currentStep === totalSteps) {
    nextBtn.style.display = "none";
    submitBtn.style.display = "inline-flex";
    populateReviewSummary();
    checkDuplicatesOnReview();
  } else {
    nextBtn.style.display = "inline-flex";
    submitBtn.style.display = "none";
  }

  // Scroll to top of form
  window.scrollTo({ top: 0, behavior: "smooth" });
}

function setupPhotoUpload() {
  const fileInput = document.getElementById("photo-input");
  const previewBox = document.getElementById("photo-preview-box");
  const previewImg = document.getElementById("photo-preview");
  const removeBtn = document.getElementById("btn-remove-photo");

  fileInput.addEventListener("change", (e) => {
    const file = e.target.files[0];
    if (!file) return;

    // Validate type
    const validTypes = ["image/jpeg", "image/png", "image/webp"];
    if (!validTypes.includes(file.type)) {
      showStepError("Invalid file type. Please upload a JPG, PNG, or WEBP image.");
      fileInput.value = "";
      return;
    }

    // Validate size (5 MB)
    if (file.size > 5 * 1024 * 1024) {
      showStepError("Image size exceeds 5 MB limit.");
      fileInput.value = "";
      return;
    }

    selectedFile = file;
    const reader = new FileReader();
    reader.onload = (event) => {
      previewImg.src = event.target.result;
      previewBox.style.display = "block";
    };
    reader.readAsDataURL(file);
  });

  removeBtn.addEventListener("click", () => {
    selectedFile = null;
    fileInput.value = "";
    previewImg.src = "";
    previewBox.style.display = "none";
  });
}

function populateReviewSummary() {
  document.getElementById("rev-title").textContent = document.getElementById("title").value.trim();
  document.getElementById("rev-desc").textContent = document.getElementById("description").value.trim();
  document.getElementById("rev-cat").textContent = document.getElementById("category").value;
  document.getElementById("rev-prio").textContent = document.getElementById("priority").value;

  const block = document.getElementById("block").value;
  const bldg = document.getElementById("building").value.trim();
  const room = document.getElementById("room").value.trim();
  const locParts = [block];
  if (bldg) locParts.push(bldg);
  if (room) locParts.push(room);
  document.getElementById("rev-loc").textContent = locParts.join(" / ");

  const revPhoto = document.getElementById("rev-photo-info");
  if (selectedFile) {
    revPhoto.textContent = `Attached: ${selectedFile.name} (${(selectedFile.size / 1024).toFixed(1)} KB)`;
  } else {
    revPhoto.textContent = "No photo attached";
  }
}

async function checkDuplicatesOnReview() {
  const dupContainer = document.getElementById("duplicate-placeholder");
  if (!dupContainer) return;

  const desc = document.getElementById("description").value.trim();
  const cat = document.getElementById("category").value;
  const blk = document.getElementById("block").value;
  const room = document.getElementById("room").value.trim();

  dupContainer.innerHTML = `
    <div style="background: rgba(15, 23, 42, 0.4); border: 1px dashed var(--border-color); border-radius: var(--radius-md); padding: 0.85rem 1rem; text-align: center; color: var(--text-muted); font-size: 0.85rem;">
      🔍 Checking campus database for similar open issues...
    </div>
  `;
  dupContainer.style.display = "block";

  try {
    const res = await api.post("/issues/check-duplicates", {
      category: cat,
      block: blk,
      room: room || null,
      description: desc,
    });

    if (res.has_duplicates && res.duplicates && res.duplicates.length > 0) {
      const dup = res.duplicates[0];
      const locStr = dup.room ? `${dup.room}` : (dup.building ? `${dup.building}` : dup.block);

      dupContainer.innerHTML = `
        <div style="background: rgba(245, 158, 11, 0.12); border: 1px solid rgba(245, 158, 11, 0.45); border-radius: var(--radius-md); padding: 1.25rem; margin-bottom: 1.5rem;">
          <div style="display: flex; align-items: flex-start; gap: 0.85rem;">
            <span style="font-size: 1.6rem; line-height: 1;">⚠️</span>
            <div style="flex: 1;">
              <h3 style="color: #fbbf24; font-size: 1.05rem; margin-bottom: 0.4rem; font-weight: 700;">
                Similar Issue Already Reported
              </h3>
              <p style="color: #fef3c7; font-size: 0.9rem; line-height: 1.5; margin-bottom: 0.85rem;">
                Similar issue already reported in <strong>${locStr}</strong>: <em>${dup.title}</em>, <strong>${dup.support_count} supporters</strong>, status <strong>${dup.status}</strong>.
              </p>
              <div style="display: flex; gap: 0.75rem; flex-wrap: wrap;">
                <button type="button" id="btn-support-dup" class="btn btn-sm" style="background: #f59e0b; color: #000; font-weight: 700; border: none;">
                  👍 Support this issue
                </button>
                <button type="button" id="btn-ignore-dup" class="btn btn-outline btn-sm" style="color: #f3f4f6; border-color: rgba(255,255,255,0.3);">
                  This is different, submit anyway
                </button>
              </div>
            </div>
          </div>
        </div>
      `;

      // Handle support button
      document.getElementById("btn-support-dup").addEventListener("click", async () => {
        const btn = document.getElementById("btn-support-dup");
        btn.disabled = true;
        btn.textContent = "Supporting...";
        try {
          const supportRes = await api.post(`/issues/${dup.issue_id}/support`);
          showToast(supportRes.message || "Supported existing issue!", "success");
          setTimeout(() => {
            window.location.href = "/student/dashboard.html";
          }, 800);
        } catch (err) {
          showToast(err.message || "Failed to support issue.", "error");
          btn.disabled = false;
          btn.textContent = "👍 Support this issue";
        }
      });

      // Handle dismiss button
      document.getElementById("btn-ignore-dup").addEventListener("click", () => {
        dupContainer.style.display = "none";
      });
    } else {
      dupContainer.innerHTML = "";
      dupContainer.style.display = "none";
    }
  } catch (err) {
    console.warn("Duplicate check failed:", err);
    dupContainer.style.display = "none";
  }
}

function setupFormSubmit() {
  document.getElementById("report-form").addEventListener("submit", async (e) => {
    e.preventDefault();

    const submitBtn = document.getElementById("btn-submit");
    submitBtn.disabled = true;
    submitBtn.innerHTML = '<span class="spinner"></span> Submitting Report...';

    const formData = new FormData();
    formData.append("title", document.getElementById("title").value.trim());
    formData.append("description", document.getElementById("description").value.trim());
    formData.append("category", document.getElementById("category").value);
    formData.append("priority", document.getElementById("priority").value);
    formData.append("block", document.getElementById("block").value);

    const bldg = document.getElementById("building").value.trim();
    if (bldg) formData.append("building", bldg);

    const room = document.getElementById("room").value.trim();
    if (room) formData.append("room", room);

    if (selectedFile) {
      formData.append("image", selectedFile);
    }

    // Attach rule-based AI suggestions if available
    if (aiSuggestion) {
      if (aiSuggestion.category) formData.append("ai_category", aiSuggestion.category);
      if (aiSuggestion.priority) formData.append("ai_priority", aiSuggestion.priority);
      if (aiSuggestion.summary) formData.append("ai_summary", aiSuggestion.summary);
    }

    try {
      const createdIssue = await api.postFormData("/issues", formData);
      showToast("Issue reported successfully!", "success");
      setTimeout(() => {
        window.location.href = "/student/my-reports.html?created=" + createdIssue.issue_id;
      }, 500);
    } catch (err) {
      submitBtn.disabled = false;
      submitBtn.textContent = "Submit Issue Report";
      showStepError(err.message || "Failed to submit issue. Please check the fields and try again.");
    }
  });
}

