// State management
let authToken = localStorage.getItem("scholarai_token") || null;
let currentUser = null;
let userBookmarks = new Set();
let currentProfile = null;
let allMatches = [];
let filteredMatches = [];
let selectedScholarship = null;
let chatMessages = [];

// Initialize on DOM load
document.addEventListener("DOMContentLoaded", () => {
  checkApiKeyStatus();
  checkUserAuth();
  loadCuratedInitialList();
  setupEventListeners();
  loadPreset("stem");
});

function setupEventListeners() {
  const profileForm = document.getElementById("profile-form");
  if (profileForm) profileForm.addEventListener("submit", handleRunAgent);

  const chatForm = document.getElementById("chat-form");
  if (chatForm) chatForm.addEventListener("submit", handleSendChatMessage);

  const apiKeyForm = document.getElementById("api-key-form");
  if (apiKeyForm) apiKeyForm.addEventListener("submit", handleSaveApiKey);

  const regForm = document.getElementById("register-form");
  if (regForm) regForm.addEventListener("submit", handleRegister);

  const loginForm = document.getElementById("login-form");
  if (loginForm) loginForm.addEventListener("submit", handleLogin);
}

// Preset loader
function loadPreset(type) {
  if (type === "stem") {
    document.getElementById("full_name").value = "Alex Chen";
    document.getElementById("nationality").value = "India";
    document.getElementById("bachelor_field").value = "B.Tech Computer Science & Engineering";
    document.getElementById("gpa").value = "3.75";
    document.getElementById("gpa_scale").value = "4.0";
    document.getElementById("target_degree_field").value = "Artificial Intelligence & Data Science";
    document.getElementById("target_countries").value = "Germany, Sweden, UK, Europe";
    document.getElementById("work_experience_years").value = "1.5";
    document.getElementById("english_test").value = "IELTS 7.5";
    document.getElementById("funding_type_needed").value = "Fully Funded";
    document.getElementById("research_experience").value = "Published 1 IEEE conference paper on computer vision; 6 months AI research internship.";
  } else if (type === "policy") {
    document.getElementById("full_name").value = "Amina Bello";
    document.getElementById("nationality").value = "Nigeria";
    document.getElementById("bachelor_field").value = "B.Sc. Economics";
    document.getElementById("gpa").value = "4.35";
    document.getElementById("gpa_scale").value = "5.0";
    document.getElementById("target_degree_field").value = "Public Policy & Development Economics";
    document.getElementById("target_countries").value = "UK, Germany, USA";
    document.getElementById("work_experience_years").value = "2.5";
    document.getElementById("english_test").value = "English Medium / IELTS 8.0";
    document.getElementById("funding_type_needed").value = "Fully Funded";
    document.getElementById("research_experience").value = "Undergraduate honors thesis on African economic diversification; 2 years policy analyst at regional NGO.";
  }
}

// ==========================================
// USER AUTHENTICATION & ACCOUNT LOGIC
// ==========================================

async function checkUserAuth() {
  if (!authToken) {
    updateAuthUI(false);
    return;
  }

  try {
    const res = await fetch("/api/auth/me", {
      headers: { "Authorization": `Bearer ${authToken}` }
    });
    if (res.ok) {
      const data = await res.json();
      currentUser = data.user;
      updateAuthUI(true);
      await loadUserProfile();
      await loadUserBookmarks();
    } else {
      // Invalid/expired token
      authToken = null;
      localStorage.removeItem("scholarai_token");
      updateAuthUI(false);
    }
  } catch (err) {
    console.error("Auth check failed:", err);
    updateAuthUI(false);
  }
}

function updateAuthUI(isLoggedIn) {
  const triggerBtn = document.getElementById("btn-auth-trigger");
  const userBadge = document.getElementById("user-badge");
  const nameDisplay = document.getElementById("user-name-display");
  const avatar = document.getElementById("user-avatar");

  if (isLoggedIn && currentUser) {
    if (triggerBtn) triggerBtn.classList.add("hidden");
    if (userBadge) {
      userBadge.classList.remove("hidden");
      userBadge.classList.add("flex");
    }
    if (nameDisplay) nameDisplay.textContent = currentUser.full_name || currentUser.email;
    if (avatar) avatar.textContent = (currentUser.full_name || currentUser.email).charAt(0).toUpperCase();
  } else {
    if (triggerBtn) triggerBtn.classList.remove("hidden");
    if (userBadge) {
      userBadge.classList.add("hidden");
      userBadge.classList.remove("flex");
    }
  }
}

function openAuthModal(mode = "register") {
  const modal = document.getElementById("modal-auth");
  modal.classList.remove("hidden");
  switchAuthMode(mode);
  const fb = document.getElementById("auth-feedback");
  if (fb) fb.classList.add("hidden");
}

function closeAuthModal() {
  const modal = document.getElementById("modal-auth");
  modal.classList.add("hidden");
}

function switchAuthMode(mode) {
  const regTab = document.getElementById("auth-tab-register");
  const loginTab = document.getElementById("auth-tab-login");
  const regForm = document.getElementById("register-form");
  const loginForm = document.getElementById("login-form");
  const prompt = document.getElementById("auth-switch-prompt");
  const fb = document.getElementById("auth-feedback");
  if (fb) fb.classList.add("hidden");

  if (mode === "register") {
    regTab.className = "text-xs font-bold pb-2 border-b-2 border-indigo-500 text-white transition";
    loginTab.className = "text-xs font-semibold pb-2 text-slate-400 hover:text-slate-200 border-b-2 border-transparent transition";
    regForm.classList.remove("hidden");
    loginForm.classList.add("hidden");
    prompt.innerHTML = `Already have an account? <a href="javascript:void(0)" onclick="switchAuthMode('login')" class="text-indigo-400 hover:underline">Sign In here</a>.`;
  } else {
    loginTab.className = "text-xs font-bold pb-2 border-b-2 border-indigo-500 text-white transition";
    regTab.className = "text-xs font-semibold pb-2 text-slate-400 hover:text-slate-200 border-b-2 border-transparent transition";
    loginForm.classList.remove("hidden");
    regForm.classList.add("hidden");
    prompt.innerHTML = `Don't have an account yet? <a href="javascript:void(0)" onclick="switchAuthMode('register')" class="text-indigo-400 hover:underline">Create an account</a>.`;
  }
}

async function handleRegister(e) {
  e.preventDefault();
  const name = document.getElementById("reg-name").value.trim();
  const email = document.getElementById("reg-email").value.trim();
  const nationality = document.getElementById("reg-nationality").value.trim();
  const password = document.getElementById("reg-password").value;
  const fb = document.getElementById("auth-feedback");
  const btn = document.getElementById("btn-submit-register");

  btn.disabled = true;
  btn.textContent = "Creating Account...";
  fb.classList.add("hidden");

  try {
    const res = await fetch("/api/auth/register", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        email,
        password,
        full_name: name,
        nationality
      })
    });
    const data = await res.json();

    if (res.ok) {
      authToken = data.token;
      currentUser = data.user;
      localStorage.setItem("scholarai_token", authToken);
      updateAuthUI(true);

      // Pre-fill profile name and nationality
      document.getElementById("full_name").value = name;
      document.getElementById("nationality").value = nationality;

      fb.className = "text-xs p-3 rounded-xl mb-4 bg-emerald-950/80 text-emerald-300 border border-emerald-500/30 block";
      fb.textContent = "✓ Account created successfully! Syncing your profile...";

      setTimeout(() => {
        closeAuthModal();
      }, 1000);
    } else {
      fb.className = "text-xs p-3 rounded-xl mb-4 bg-rose-950/80 text-rose-300 border border-rose-500/30 block";
      fb.textContent = data.detail || "Registration failed.";
    }
  } catch (err) {
    fb.className = "text-xs p-3 rounded-xl mb-4 bg-rose-950/80 text-rose-300 border border-rose-500/30 block";
    fb.textContent = `Connection error: ${err.message}`;
  } finally {
    btn.disabled = false;
    btn.textContent = "Create Free Scholar Account";
  }
}

async function handleLogin(e) {
  e.preventDefault();
  const email = document.getElementById("login-email").value.trim();
  const password = document.getElementById("login-password").value;
  const fb = document.getElementById("auth-feedback");
  const btn = document.getElementById("btn-submit-login");

  btn.disabled = true;
  btn.textContent = "Signing In...";
  fb.classList.add("hidden");

  try {
    const res = await fetch("/api/auth/login", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email, password })
    });
    const data = await res.json();

    if (res.ok) {
      authToken = data.token;
      currentUser = data.user;
      localStorage.setItem("scholarai_token", authToken);
      updateAuthUI(true);

      fb.className = "text-xs p-3 rounded-xl mb-4 bg-emerald-950/80 text-emerald-300 border border-emerald-500/30 block";
      fb.textContent = `✓ Welcome back, ${currentUser.full_name || currentUser.email}! Loading profile...`;

      await loadUserProfile();
      await loadUserBookmarks();

      setTimeout(() => {
        closeAuthModal();
      }, 900);
    } else {
      fb.className = "text-xs p-3 rounded-xl mb-4 bg-rose-950/80 text-rose-300 border border-rose-500/30 block";
      fb.textContent = data.detail || "Invalid login credentials.";
    }
  } catch (err) {
    fb.className = "text-xs p-3 rounded-xl mb-4 bg-rose-950/80 text-rose-300 border border-rose-500/30 block";
    fb.textContent = `Connection error: ${err.message}`;
  } finally {
    btn.disabled = false;
    btn.textContent = "Sign In to My Account";
  }
}

async function handleLogout() {
  if (authToken) {
    try {
      await fetch("/api/auth/logout", {
        method: "POST",
        headers: { "Authorization": `Bearer ${authToken}` }
      });
    } catch (e) {}
  }
  authToken = null;
  currentUser = null;
  userBookmarks = new Set();
  localStorage.removeItem("scholarai_token");
  updateAuthUI(false);
  updateSavedCount();
  renderScholarshipCards(filteredMatches);
}

async function loadUserProfile() {
  if (!authToken) return;
  try {
    const res = await fetch("/api/user/profile", {
      headers: { "Authorization": `Bearer ${authToken}` }
    });
    if (res.ok) {
      const data = await res.json();
      const p = data.profile;
      if (p) {
        if (p.full_name) document.getElementById("full_name").value = p.full_name;
        if (p.nationality) document.getElementById("nationality").value = p.nationality;
        if (p.bachelor_field) document.getElementById("bachelor_field").value = p.bachelor_field;
        if (p.gpa) document.getElementById("gpa").value = p.gpa;
        if (p.gpa_scale) document.getElementById("gpa_scale").value = p.gpa_scale;
        if (p.target_degree_field) document.getElementById("target_degree_field").value = p.target_degree_field;
        if (p.target_countries && p.target_countries.length) {
          document.getElementById("target_countries").value = p.target_countries.join(", ");
        }
        if (p.work_experience_years !== undefined) document.getElementById("work_experience_years").value = p.work_experience_years;
        if (p.english_test) document.getElementById("english_test").value = p.english_test;
        if (p.funding_type_needed) document.getElementById("funding_type_needed").value = p.funding_type_needed;
        if (p.research_experience) document.getElementById("research_experience").value = p.research_experience;
      }
    }
  } catch (err) {
    console.error("Failed to load profile from database:", err);
  }
}

async function handleSaveProfileToAccount() {
  if (!authToken) {
    openAuthModal("register");
    const fb = document.getElementById("auth-feedback");
    if (fb) {
      fb.className = "text-xs p-3 rounded-xl mb-4 bg-indigo-950/80 text-indigo-300 border border-indigo-500/30 block";
      fb.textContent = "Please create an account or sign in to save your profile to the cloud.";
    }
    return;
  }

  const countriesStr = document.getElementById("target_countries").value;
  const countriesList = countriesStr ? countriesStr.split(",").map(c => c.trim()).filter(Boolean) : [];

  const profilePayload = {
    full_name: document.getElementById("full_name").value.trim(),
    nationality: document.getElementById("nationality").value.trim(),
    bachelor_field: document.getElementById("bachelor_field").value.trim(),
    gpa: parseFloat(document.getElementById("gpa").value) || 3.0,
    gpa_scale: parseFloat(document.getElementById("gpa_scale").value) || 4.0,
    target_degree_field: document.getElementById("target_degree_field").value.trim(),
    target_countries: countriesList,
    work_experience_years: parseFloat(document.getElementById("work_experience_years").value) || 0.0,
    english_test: document.getElementById("english_test").value.trim() || null,
    funding_type_needed: document.getElementById("funding_type_needed").value,
    research_experience: document.getElementById("research_experience").value.trim() || null
  };

  const btn = document.getElementById("btn-save-account");
  const origText = btn.innerHTML;
  btn.disabled = true;
  btn.innerHTML = `<span class="animate-spin mr-1">⚙️</span> Saving...`;

  try {
    const res = await fetch("/api/user/profile", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "Authorization": `Bearer ${authToken}`
      },
      body: JSON.stringify(profilePayload)
    });
    if (res.ok) {
      btn.innerHTML = `<i data-lucide="check" class="w-4 h-4 text-emerald-400"></i> Saved to Cloud!`;
      setTimeout(() => {
        btn.innerHTML = origText;
        if (window.lucide) lucide.createIcons();
      }, 2000);
    } else {
      alert("Failed to save profile. Please try again.");
      btn.innerHTML = origText;
    }
  } catch (err) {
    alert(`Error: ${err.message}`);
    btn.innerHTML = origText;
  } finally {
    btn.disabled = false;
    if (window.lucide) lucide.createIcons();
  }
}

async function loadUserBookmarks() {
  if (!authToken) return;
  try {
    const res = await fetch("/api/user/bookmarks", {
      headers: { "Authorization": `Bearer ${authToken}` }
    });
    if (res.ok) {
      const data = await res.json();
      userBookmarks = new Set(data.bookmarks || []);
      updateSavedCount();
      renderScholarshipCards(filteredMatches);
    }
  } catch (err) {
    console.error("Failed to load bookmarks:", err);
  }
}

async function handleToggleBookmark(scholarshipId, event) {
  if (event) event.stopPropagation();

  if (!authToken) {
    openAuthModal("register");
    const fb = document.getElementById("auth-feedback");
    if (fb) {
      fb.className = "text-xs p-3 rounded-xl mb-4 bg-indigo-950/80 text-indigo-300 border border-indigo-500/30 block";
      fb.textContent = "Please sign in or create an account to save scholarships to your profile.";
    }
    return;
  }

  try {
    const res = await fetch("/api/user/bookmarks/toggle", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "Authorization": `Bearer ${authToken}`
      },
      body: JSON.stringify({ scholarship_id: scholarshipId })
    });
    if (res.ok) {
      const data = await res.json();
      if (data.bookmarked) {
        userBookmarks.add(scholarshipId);
      } else {
        userBookmarks.delete(scholarshipId);
      }
      updateSavedCount();
      renderScholarshipCards(filteredMatches);
    }
  } catch (err) {
    console.error("Bookmark toggle error:", err);
  }
}

function updateSavedCount() {
  const el = document.getElementById("saved-count");
  if (el) el.textContent = userBookmarks.size;
}

// ==========================================
// GEMINI API KEY LOGIC
// ==========================================

async function checkApiKeyStatus() {
  try {
    const res = await fetch("/api/api-key/status");
    const data = await res.json();
    const dot = document.getElementById("api-status-dot");
    const text = document.getElementById("api-status-text");
    const btn = document.getElementById("api-status-btn");

    if (data.has_key) {
      dot.className = "w-2 h-2 rounded-full bg-emerald-400";
      text.textContent = "Gemini Grounding: Active";
      btn.classList.add("border-emerald-500/40", "bg-emerald-950/20");
    } else {
      dot.className = "w-2 h-2 rounded-full bg-amber-400 animate-pulse";
      text.textContent = "Gemini Key: Configure Key";
    }
  } catch (err) {
    console.error("Error checking API key status:", err);
  }
}

async function handleSaveApiKey(e) {
  e.preventDefault();
  const input = document.getElementById("input-api-key");
  const feedback = document.getElementById("api-key-feedback");
  const saveBtn = document.getElementById("btn-save-key");
  const key = input.value.trim();

  if (!key) return;

  saveBtn.disabled = true;
  saveBtn.textContent = "Verifying with Google AI...";
  feedback.classList.remove("hidden", "bg-emerald-900/40", "text-emerald-300", "bg-rose-900/40", "text-rose-300");

  try {
    const res = await fetch("/api/api-key/set", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ api_key: key })
    });
    const data = await res.json();

    if (res.ok) {
      feedback.className = "text-xs p-2.5 rounded-lg bg-emerald-950/80 text-emerald-300 border border-emerald-500/30";
      feedback.textContent = "✓ Key verified and active! Live search grounding enabled.";
      checkApiKeyStatus();
      setTimeout(() => {
        closeApiKeyModal();
        feedback.classList.add("hidden");
      }, 1500);
    } else {
      feedback.className = "text-xs p-2.5 rounded-lg bg-rose-950/80 text-rose-300 border border-rose-500/30";
      feedback.textContent = `Error: ${data.detail || "Invalid Key"}`;
    }
  } catch (err) {
    feedback.className = "text-xs p-2.5 rounded-lg bg-rose-950/80 text-rose-300 border border-rose-500/30";
    feedback.textContent = `Connection error: ${err.message}`;
  } finally {
    saveBtn.disabled = false;
    saveBtn.textContent = "Save & Test Key";
  }
}

function openApiKeyModal() {
  document.getElementById("modal-api-key").classList.remove("hidden");
}
function closeApiKeyModal() {
  document.getElementById("modal-api-key").classList.add("hidden");
}

// Switch Tab
function switchTab(tabId) {
  const tabs = ["profile", "discovery", "roadmap", "chat"];
  tabs.forEach(t => {
    const section = document.getElementById(`tab-${t}`);
    const navBtn = document.getElementById(`nav-${t}-btn`);
    const mBtn = document.getElementById(`m-${t}`);

    if (t === tabId) {
      if (section) section.classList.remove("hidden");
      if (navBtn) navBtn.classList.add("active");
      if (mBtn) mBtn.classList.add("active");
    } else {
      if (section) section.classList.add("hidden");
      if (navBtn) navBtn.classList.remove("active");
      if (mBtn) mBtn.classList.remove("active");
    }
  });

  if (window.lucide) {
    lucide.createIcons();
  }
}

// Fetch Initial Curated List
async function loadCuratedInitialList() {
  try {
    const res = await fetch("/api/scholarships");
    const data = await res.json();
    allMatches = data.map(item => ({
      ...item,
      computed_suitability: 80
    }));
    filteredMatches = [...allMatches];
    renderScholarshipCards(filteredMatches);
  } catch (err) {
    console.error("Failed to load initial scholarships:", err);
  }
}

// Run Multi-Agent Discovery
async function handleRunAgent(e) {
  e.preventDefault();

  const countriesStr = document.getElementById("target_countries").value;
  const countriesList = countriesStr ? countriesStr.split(",").map(c => c.trim()).filter(Boolean) : [];

  currentProfile = {
    full_name: document.getElementById("full_name").value.trim() || "Applicant",
    nationality: document.getElementById("nationality").value.trim(),
    bachelor_field: document.getElementById("bachelor_field").value.trim(),
    gpa: parseFloat(document.getElementById("gpa").value) || 3.0,
    gpa_scale: parseFloat(document.getElementById("gpa_scale").value) || 4.0,
    target_degree_field: document.getElementById("target_degree_field").value.trim(),
    target_countries: countriesList,
    work_experience_years: parseFloat(document.getElementById("work_experience_years").value) || 0.0,
    english_test: document.getElementById("english_test").value.trim() || null,
    funding_type_needed: document.getElementById("funding_type_needed").value,
    research_experience: document.getElementById("research_experience").value.trim() || null
  };

  // If logged in, automatically save profile in background
  if (authToken) {
    fetch("/api/user/profile", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "Authorization": `Bearer ${authToken}`
      },
      body: JSON.stringify(currentProfile)
    }).catch(() => {});
  }

  const btn = document.getElementById("btn-run-agent");
  const origBtnContent = btn.innerHTML;
  btn.disabled = true;
  btn.innerHTML = `
    <span class="inline-block animate-spin mr-2">⚙️</span>
    <span>Orchestrating AI Agents (Evaluating profile & searching live intakes)...</span>
  `;

  try {
    const res = await fetch("/api/agent/discover", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(currentProfile)
    });
    const data = await res.json();

    if (!res.ok) {
      throw new Error(data.detail || "Agent discovery failed");
    }

    allMatches = data.matched_scholarships || [];
    filteredMatches = [...allMatches];

    // Update Grounding badge
    const gBadge = document.getElementById("grounding-badge");
    if (data.search_grounded) {
      gBadge.classList.remove("hidden");
      gBadge.classList.add("flex");
    } else {
      gBadge.classList.add("hidden");
    }

    // Update profile recap
    const recap = document.getElementById("profile-recap");
    const summary = data.profile_summary;
    recap.textContent = `Evaluated: ${currentProfile.nationality} citizen • Normalized GPA: ${summary.normalized_gpa}/4.0 (${summary.academic_tier}) • Target: ${currentProfile.target_degree_field} • Exp: ${summary.work_years} yrs`;

    // Update AI Insights box
    const insightsBox = document.getElementById("ai-insights-content");
    insightsBox.innerHTML = renderMarkdown(data.ai_insights);

    // Render cards
    renderScholarshipCards(filteredMatches);

    // Switch to discovery tab
    switchTab("discovery");
    window.scrollTo({ top: 0, behavior: "smooth" });

  } catch (err) {
    alert(`Discovery Agent error: ${err.message}`);
  } finally {
    btn.disabled = false;
    btn.innerHTML = origBtnContent;
    if (window.lucide) lucide.createIcons();
  }
}

// Filter Scholarships
function filterScholarships(filter) {
  document.querySelectorAll(".filter-btn").forEach(btn => {
    btn.classList.remove("active", "bg-indigo-600", "text-white");
    btn.classList.add("bg-slate-800", "text-slate-300");
  });
  if (event && event.currentTarget) {
    event.currentTarget.classList.add("active", "bg-indigo-600", "text-white");
    event.currentTarget.classList.remove("bg-slate-800", "text-slate-300");
  }

  if (filter === "all") {
    filteredMatches = [...allMatches];
  } else if (filter === "saved") {
    filteredMatches = allMatches.filter(s => userBookmarks.has(s.id));
  } else if (filter === "high-match") {
    filteredMatches = allMatches.filter(s => (s.computed_suitability || 80) >= 80);
  } else if (filter === "fully-funded") {
    filteredMatches = allMatches.filter(s => s.funding_type.toLowerCase().includes("fully"));
  } else if (filter === "europe") {
    filteredMatches = allMatches.filter(s => s.host_countries.some(c => c.toLowerCase().includes("europe") || c.toLowerCase().includes("germany") || c.toLowerCase().includes("uk") || c.toLowerCase().includes("france") || c.toLowerCase().includes("sweden") || c.toLowerCase().includes("belgium") || c.toLowerCase().includes("switzerland") || c.toLowerCase().includes("hungary")));
  } else if (filter === "asia") {
    filteredMatches = allMatches.filter(s => s.host_countries.some(c => c.toLowerCase().includes("japan") || c.toLowerCase().includes("korea") || c.toLowerCase().includes("turkey") || c.toLowerCase().includes("china")));
  }

  renderScholarshipCards(filteredMatches);
}

// Render Scholarship Cards
function renderScholarshipCards(list) {
  const grid = document.getElementById("scholarships-grid");
  const countBadge = document.getElementById("match-count-badge");
  countBadge.textContent = `${list.length} Matches`;

  if (!list.length) {
    grid.innerHTML = `
      <div class="col-span-full py-12 text-center text-slate-400">
        <i data-lucide="search-x" class="w-12 h-12 mx-auto mb-3 text-slate-600"></i>
        <p class="text-sm">No scholarships match the selected filter. Try clicking 'All'.</p>
      </div>
    `;
    if (window.lucide) lucide.createIcons();
    return;
  }

  grid.innerHTML = list.map(item => {
    const score = item.computed_suitability || 80;
    const hosts = item.host_countries.join(", ");
    const tagsHtml = (item.tags || []).slice(0, 3).map(t => `<span class="px-2 py-0.5 rounded text-[10px] bg-slate-800 text-slate-300 font-medium">${t}</span>`).join(" ");
    const isBookmarked = userBookmarks.has(item.id);

    return `
      <div class="scholarship-card bg-slate-900/90 border border-slate-800/90 rounded-2xl p-5 flex flex-col justify-between shadow-lg relative group">
        <div>
          <!-- Header with Match Score Badge and Bookmark Button -->
          <div class="flex items-start justify-between gap-3 mb-3">
            <div class="flex-1 pr-1">
              <span class="text-[11px] font-semibold text-indigo-400 tracking-wider uppercase">${escapeHtml(item.sponsor)}</span>
              <h3 class="text-base font-bold text-white leading-snug mt-0.5 group-hover:text-indigo-300 transition-colors">${escapeHtml(item.name)}</h3>
            </div>
            
            <div class="flex items-center gap-2 shrink-0">
              <!-- Bookmark Heart Button -->
              <button onclick="handleToggleBookmark('${item.id}', event)" title="${isBookmarked ? 'Remove Bookmark' : 'Save to My Account'}" class="w-8 h-8 rounded-xl flex items-center justify-center transition border ${isBookmarked ? 'bg-indigo-600/30 text-indigo-400 border-indigo-500/50' : 'bg-slate-800/80 text-slate-400 border-slate-700/60 hover:text-white hover:bg-slate-700'}">
                <i data-lucide="bookmark" class="w-4 h-4 ${isBookmarked ? 'fill-indigo-400 text-indigo-400' : ''}"></i>
              </button>

              <!-- Match score circle -->
              <div class="score-circle shrink-0" style="--percent: ${score}%;">
                <span class="score-value">${score}%</span>
              </div>
            </div>
          </div>

          <!-- Quick Tags -->
          <div class="flex flex-wrap gap-1.5 mb-3.5">
            <span class="px-2 py-0.5 rounded text-[10px] font-semibold bg-emerald-500/10 text-emerald-300 border border-emerald-500/20">${escapeHtml(item.funding_type)}</span>
            ${tagsHtml}
          </div>

          <!-- Details & Benefits -->
          <p class="text-xs text-slate-300 line-clamp-2 mb-3">${escapeHtml(item.coverage_details)}</p>

          <!-- Criteria Highlights -->
          <div class="space-y-1.5 text-[11px] text-slate-400 bg-slate-950/60 p-3 rounded-xl border border-slate-800/60 mb-4">
            <div class="flex items-center gap-1.5">
              <i data-lucide="map-pin" class="w-3.5 h-3.5 text-indigo-400 shrink-0"></i>
              <span class="truncate"><strong>Host:</strong> ${escapeHtml(hosts)}</span>
            </div>
            <div class="flex items-center gap-1.5">
              <i data-lucide="calendar" class="w-3.5 h-3.5 text-violet-400 shrink-0"></i>
              <span class="truncate"><strong>Deadline:</strong> ${escapeHtml(item.typical_deadline)}</span>
            </div>
            <div class="flex items-center gap-1.5">
              <i data-lucide="briefcase" class="w-3.5 h-3.5 text-cyan-400 shrink-0"></i>
              <span class="truncate"><strong>Work Exp:</strong> ${escapeHtml(item.work_exp_requirement)}</span>
            </div>
          </div>
        </div>

        <!-- Action Buttons -->
        <div class="pt-2 border-t border-slate-800/80 flex items-center gap-2">
          <button onclick="triggerDeepAudit('${item.id}')" class="flex-1 py-2 px-3 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-semibold flex items-center justify-center gap-1.5 border border-slate-700 transition">
            <i data-lucide="shield-check" class="w-3.5 h-3.5 text-emerald-400"></i>
            <span>Audit Eligibility</span>
          </button>
          
          <button onclick="triggerRoadmap('${item.id}')" class="flex-1 py-2 px-3 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold flex items-center justify-center gap-1.5 shadow-md shadow-indigo-600/20 transition">
            <i data-lucide="compass" class="w-3.5 h-3.5"></i>
            <span>Roadmap</span>
          </button>

          <a href="${item.official_url}" target="_blank" rel="noopener noreferrer" title="Official Website" class="p-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-400 hover:text-white border border-slate-700 transition">
            <i data-lucide="external-link" class="w-3.5 h-3.5"></i>
          </a>
        </div>
      </div>
    `;
  }).join("");

  if (window.lucide) lucide.createIcons();
}

// Trigger Deep Audit Modal
async function triggerDeepAudit(scholarshipId) {
  const scholarship = allMatches.find(s => s.id === scholarshipId);
  if (!scholarship) return;

  const modal = document.getElementById("modal-audit");
  const content = document.getElementById("audit-modal-content");
  modal.classList.remove("hidden");

  content.innerHTML = `
    <div class="text-center py-8">
      <div class="inline-block animate-spin text-2xl mb-2">⚙️</div>
      <p class="text-xs text-slate-400">Auditing candidate eligibility criteria against selection committee metrics...</p>
    </div>
  `;

  try {
    const payloadProfile = currentProfile || {
      full_name: "Applicant",
      nationality: "International",
      bachelor_field: "General",
      gpa: 3.5,
      gpa_scale: 4.0,
      target_degree_field: "Master's Degree",
      target_countries: [],
      work_experience_years: 1.0,
      funding_type_needed: "Fully Funded"
    };

    const res = await fetch("/api/agent/evaluate", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        profile: payloadProfile,
        scholarship_id: scholarshipId
      })
    });
    const evalData = await res.json();

    const checklistItems = Object.entries(evalData.checklist).map(([k, v]) => {
      const label = k.replace(/_/g, " ").replace(/\b\w/g, l => l.toUpperCase());
      return `
        <div class="flex items-center justify-between py-1.5 px-3 rounded-lg bg-slate-950/60 border border-slate-800 text-xs">
          <span class="text-slate-300">${label}</span>
          <span class="font-bold ${v ? 'text-emerald-400' : 'text-rose-400'}">${v ? '✓ Pass' : '⚠ Caution / Risk'}</span>
        </div>
      `;
    }).join("");

    const strengthsList = evalData.strengths.map(s => `<li class="text-emerald-300">✓ ${escapeHtml(s)}</li>`).join("");
    const obstaclesList = evalData.potential_obstacles.length ? evalData.potential_obstacles.map(o => `<li class="text-amber-300">⚠ ${escapeHtml(o)}</li>`).join("") : `<li class="text-slate-400">None detected. Full criteria satisfied.</li>`;

    content.innerHTML = `
      <div class="space-y-5">
        <div class="border-b border-slate-800 pb-3">
          <span class="px-2.5 py-0.5 rounded-full text-[11px] font-bold bg-indigo-500/20 text-indigo-300 border border-indigo-500/30">Eligibility & Risk Audit</span>
          <h2 class="text-lg font-bold text-white mt-1">${escapeHtml(evalData.scholarship_name)}</h2>
          <div class="flex items-center gap-3 mt-1 text-xs">
            <span class="text-slate-400">Match Score: <strong class="text-indigo-400">${evalData.match_score}/100</strong></span>
            <span class="px-2 py-0.5 rounded font-semibold text-xs bg-slate-800 text-slate-200">${escapeHtml(evalData.verdict)}</span>
          </div>
        </div>

        <!-- 5-Point Checklist -->
        <div>
          <h4 class="text-xs font-bold text-slate-300 uppercase tracking-wider mb-2">Eligibility Verification Checks</h4>
          <div class="grid grid-cols-1 sm:grid-cols-2 gap-2">
            ${checklistItems}
          </div>
        </div>

        <!-- Strengths & Obstacles -->
        <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div class="bg-emerald-950/20 border border-emerald-900/40 p-3.5 rounded-xl">
            <h4 class="text-xs font-bold text-emerald-400 uppercase tracking-wider mb-2">Key Profile Strengths</h4>
            <ul class="text-xs space-y-1.5">
              ${strengthsList}
            </ul>
          </div>

          <div class="bg-amber-950/20 border border-amber-900/40 p-3.5 rounded-xl">
            <h4 class="text-xs font-bold text-amber-400 uppercase tracking-wider mb-2">Disqualification Risks</h4>
            <ul class="text-xs space-y-1.5">
              ${obstaclesList}
            </ul>
          </div>
        </div>

        <!-- Tactical Advice -->
        <div class="p-4 rounded-xl bg-indigo-950/40 border border-indigo-800/40">
          <h4 class="text-xs font-bold text-indigo-300 uppercase tracking-wider mb-1 flex items-center gap-1.5">
            <i data-lucide="lightbulb" class="w-3.5 h-3.5"></i>
            Admissions Committee Tactical Advice
          </h4>
          <p class="text-xs text-slate-200 leading-relaxed">${escapeHtml(evalData.key_advice)}</p>
        </div>

        <div class="flex justify-end gap-2 pt-2">
          <button onclick="closeAuditModal()" class="px-4 py-2 rounded-xl text-xs font-semibold bg-slate-800 hover:bg-slate-700 text-slate-300">Close</button>
          <button onclick="closeAuditModal(); triggerRoadmap('${scholarshipId}')" class="px-4 py-2 rounded-xl text-xs font-semibold bg-indigo-600 hover:bg-indigo-500 text-white">Generate Roadmap</button>
        </div>
      </div>
    `;

    if (window.lucide) lucide.createIcons();

  } catch (err) {
    content.innerHTML = `<p class="text-xs text-rose-400">Failed to evaluate: ${err.message}</p>`;
  }
}

function closeAuditModal() {
  document.getElementById("modal-audit").classList.add("hidden");
}

// Generate Roadmap
async function triggerRoadmap(scholarshipId) {
  selectedScholarship = allMatches.find(s => s.id === scholarshipId);
  const container = document.getElementById("roadmap-container");
  const title = document.getElementById("roadmap-scholarship-title");
  const deadlineBadge = document.getElementById("roadmap-deadline-badge");

  if (selectedScholarship) {
    title.textContent = `${selectedScholarship.name} — Application Roadmap`;
    deadlineBadge.textContent = selectedScholarship.typical_deadline;
  }

  container.innerHTML = `
    <div class="text-center py-12">
      <div class="inline-block animate-spin text-3xl mb-3">🧭</div>
      <p class="text-xs text-slate-400">Roadmap Agent is engineering your tailored Statement of Purpose structure and milestone plan...</p>
    </div>
  `;

  switchTab("roadmap");

  try {
    const payloadProfile = currentProfile || {
      full_name: "Applicant",
      nationality: "International",
      bachelor_field: "General",
      gpa: 3.5,
      gpa_scale: 4.0,
      target_degree_field: "Master's Degree",
      target_countries: [],
      work_experience_years: 1.0,
      funding_type_needed: "Fully Funded"
    };

    const res = await fetch("/api/agent/roadmap", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        profile: payloadProfile,
        scholarship_id: scholarshipId
      })
    });
    const rm = await res.json();

    // Render Timeline Steps
    const stepsHtml = rm.timeline_steps.map((st, i) => `
      <div class="flex items-start gap-4 relative">
        <div class="w-8 h-8 rounded-full bg-indigo-600/20 text-indigo-400 border border-indigo-500/40 flex items-center justify-center font-bold text-xs shrink-0 mt-0.5">
          ${i + 1}
        </div>
        <div class="flex-1 bg-slate-950/60 border border-slate-800 p-4 rounded-xl">
          <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-1 mb-2">
            <h4 class="text-xs font-bold text-white">${escapeHtml(st.phase)}</h4>
            <span class="text-[11px] font-semibold text-violet-400 bg-violet-950/50 px-2 py-0.5 rounded border border-violet-800/40">${escapeHtml(st.timing)}</span>
          </div>
          <ul class="space-y-1.5 text-xs text-slate-300">
            ${st.tasks.map(t => `<li class="flex items-start gap-2"><span class="text-indigo-400">•</span><span>${escapeHtml(t)}</span></li>`).join("")}
          </ul>
        </div>
      </div>
    `).join("");

    // Render SOP Framework
    const sop = rm.sop_framework;
    const sopAiExtra = sop.ai_custom_angle ? `
      <div class="mt-3 p-3 rounded-lg bg-indigo-900/30 border border-indigo-700/40 text-indigo-200 text-xs">
        <strong class="text-indigo-300 block mb-1">AI Tailored Angle:</strong>
        ${escapeHtml(sop.ai_custom_angle)}
      </div>
    ` : "";

    // Documents
    const docsHtml = rm.required_documents.map(d => `
      <div class="p-3 rounded-xl bg-slate-950/60 border border-slate-800 text-xs flex flex-col justify-between">
        <div>
          <div class="flex items-center justify-between gap-2 mb-1">
            <span class="font-bold text-white">${escapeHtml(d.document)}</span>
            <span class="px-1.5 py-0.5 rounded text-[10px] font-semibold ${d.status === 'Critical' ? 'bg-rose-500/20 text-rose-300 border border-rose-500/30' : 'bg-slate-800 text-slate-300'}">${escapeHtml(d.status)}</span>
          </div>
          <p class="text-slate-400 text-[11px] mt-1">${escapeHtml(d.tip)}</p>
        </div>
      </div>
    `).join("");

    container.innerHTML = `
      <div class="space-y-8">
        <!-- Section 1: Timeline -->
        <div>
          <h3 class="text-sm font-bold text-white uppercase tracking-wider flex items-center gap-2 mb-4">
            <i data-lucide="clock" class="w-4 h-4 text-indigo-400"></i>
            Preparation & Submission Timeline
          </h3>
          <div class="space-y-4">
            ${stepsHtml}
          </div>
        </div>

        <!-- Section 2: Statement of Purpose Blueprint -->
        <div class="bg-gradient-to-br from-indigo-950/30 via-slate-950 to-slate-950 p-5 rounded-2xl border border-indigo-900/40">
          <h3 class="text-sm font-bold text-white uppercase tracking-wider flex items-center gap-2 mb-3">
            <i data-lucide="file-text" class="w-4 h-4 text-violet-400"></i>
            Statement of Purpose (SOP) Blueprint
          </h3>
          <div class="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs">
            <div class="p-3.5 rounded-xl bg-slate-900/80 border border-slate-800">
              <span class="text-indigo-400 font-bold block mb-1">1. The Urgent Hook (0-15%)</span>
              <p class="text-slate-300 leading-relaxed">${escapeHtml(sop.hook_section)}</p>
            </div>
            <div class="p-3.5 rounded-xl bg-slate-900/80 border border-slate-800">
              <span class="text-indigo-400 font-bold block mb-1">2. Academic & Technical Foundation (15-45%)</span>
              <p class="text-slate-300 leading-relaxed">${escapeHtml(sop.academic_bridge)}</p>
            </div>
            <div class="p-3.5 rounded-xl bg-slate-900/80 border border-slate-800">
              <span class="text-indigo-400 font-bold block mb-1">3. Why This Program & Lab? (45-75%)</span>
              <p class="text-slate-300 leading-relaxed">${escapeHtml(sop.program_alignment)}</p>
            </div>
            <div class="p-3.5 rounded-xl bg-slate-900/80 border border-slate-800">
              <span class="text-indigo-400 font-bold block mb-1">4. Long-term Impact & ROI (75-100%)</span>
              <p class="text-slate-300 leading-relaxed">${escapeHtml(sop.impact_and_future_vision)}</p>
            </div>
          </div>
          ${sopAiExtra}
        </div>

        <!-- Section 3: Document Checklist -->
        <div>
          <h3 class="text-sm font-bold text-white uppercase tracking-wider flex items-center gap-2 mb-4">
            <i data-lucide="folder-check" class="w-4 h-4 text-cyan-400"></i>
            Document Preparation Matrix
          </h3>
          <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
            ${docsHtml}
          </div>
        </div>

        <!-- Section 4: Referee & Interview Advice -->
        <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div class="p-4 rounded-xl bg-slate-950/60 border border-slate-800">
            <h4 class="text-xs font-bold text-emerald-400 uppercase tracking-wider mb-2 flex items-center gap-1.5">
              <i data-lucide="users" class="w-3.5 h-3.5"></i>
              Letters of Recommendation (LOR) Strategy
            </h4>
            <ul class="text-xs text-slate-300 space-y-2">
              ${rm.recommendation_tips.map(t => `<li class="flex items-start gap-2"><span class="text-emerald-400">✓</span><span>${escapeHtml(t)}</span></li>`).join("")}
            </ul>
          </div>

          <div class="p-4 rounded-xl bg-slate-950/60 border border-slate-800">
            <h4 class="text-xs font-bold text-violet-400 uppercase tracking-wider mb-2 flex items-center gap-1.5">
              <i data-lucide="mic" class="w-3.5 h-3.5"></i>
              Interview Defense Protocol
            </h4>
            <ul class="text-xs text-slate-300 space-y-2">
              ${rm.interview_prep.map(t => `<li class="flex items-start gap-2"><span class="text-violet-400">★</span><span>${escapeHtml(t)}</span></li>`).join("")}
            </ul>
          </div>
        </div>
      </div>
    `;

    if (window.lucide) lucide.createIcons();

  } catch (err) {
    container.innerHTML = `<p class="text-xs text-rose-400">Failed to generate roadmap: ${err.message}</p>`;
  }
}

// Interactive Chat
async function handleSendChatMessage(e) {
  e.preventDefault();
  const input = document.getElementById("chat-input");
  const msg = input.value.trim();
  if (!msg) return;

  input.value = "";
  appendChatMessage("user", msg);

  const sendBtn = document.getElementById("chat-send-btn");
  sendBtn.disabled = true;

  try {
    chatMessages.push({ role: "user", content: msg });

    const payload = {
      profile: currentProfile,
      messages: chatMessages,
      selected_scholarship_id: selectedScholarship ? selectedScholarship.id : null
    };

    const res = await fetch("/api/agent/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });
    const data = await res.json();

    if (res.ok && data.reply) {
      chatMessages.push({ role: "assistant", content: data.reply });
      appendChatMessage("assistant", data.reply);
    } else {
      appendChatMessage("assistant", "Apologies, I encountered an issue generating a response.");
    }
  } catch (err) {
    appendChatMessage("assistant", `Network error: ${err.message}`);
  } finally {
    sendBtn.disabled = false;
  }
}

function appendChatMessage(role, content) {
  const container = document.getElementById("chat-messages");
  const isUser = role === "user";

  const msgDiv = document.createElement("div");
  msgDiv.className = `flex items-start gap-3 ${isUser ? 'flex-row-reverse' : ''}`;

  const iconDiv = document.createElement("div");
  iconDiv.className = isUser 
    ? "w-8 h-8 rounded-lg bg-slate-700 text-slate-200 flex items-center justify-center shrink-0 mt-0.5 font-bold text-xs"
    : "w-8 h-8 rounded-lg bg-indigo-600/30 text-indigo-400 border border-indigo-500/30 flex items-center justify-center shrink-0 mt-0.5";
  iconDiv.innerHTML = isUser ? "YOU" : `<i data-lucide="bot" class="w-4 h-4"></i>`;

  const bubble = document.createElement("div");
  bubble.className = isUser
    ? "bg-indigo-600 text-white rounded-2xl rounded-tr-sm p-3.5 max-w-xl text-xs sm:text-sm leading-relaxed shadow-md"
    : "bg-slate-800/90 text-slate-200 rounded-2xl rounded-tl-sm p-4 border border-slate-700/60 max-w-2xl text-xs sm:text-sm leading-relaxed";

  bubble.innerHTML = renderMarkdown(content);

  msgDiv.appendChild(iconDiv);
  msgDiv.appendChild(bubble);
  container.appendChild(msgDiv);

  container.scrollTop = container.scrollHeight;
  if (window.lucide) lucide.createIcons();
}

function sendQuickPrompt(promptText) {
  document.getElementById("chat-input").value = promptText;
  handleSendChatMessage(new Event("submit"));
}

function clearChat() {
  chatMessages = [];
  const container = document.getElementById("chat-messages");
  container.innerHTML = `
    <div class="flex items-start gap-3">
      <div class="w-8 h-8 rounded-lg bg-indigo-600/30 text-indigo-400 border border-indigo-500/30 flex items-center justify-center shrink-0 mt-0.5">
        <i data-lucide="bot" class="w-4 h-4"></i>
      </div>
      <div class="bg-slate-800/90 rounded-2xl rounded-tl-sm p-4 border border-slate-700/60 max-w-2xl text-xs sm:text-sm text-slate-200 leading-relaxed">
        <p class="font-semibold text-white mb-1">Chat history cleared.</p>
        <p>Ask any new question about master's scholarships, eligibility rules, or application essays!</p>
      </div>
    </div>
  `;
  if (window.lucide) lucide.createIcons();
}

// Helpers
function escapeHtml(str) {
  if (!str) return "";
  return String(str)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}

function renderMarkdown(text) {
  if (!text) return "";
  let html = escapeHtml(text);

  // Headers
  html = html.replace(/^### (.*$)/gim, '<h4 class="text-xs font-bold text-indigo-300 mt-2 mb-1">$1</h4>');
  html = html.replace(/^## (.*$)/gim, '<h3 class="text-sm font-bold text-white mt-3 mb-1.5">$1</h3>');
  html = html.replace(/^# (.*$)/gim, '<h2 class="text-base font-bold text-white mt-3 mb-2">$1</h2>');

  // Bold
  html = html.replace(/\*\*(.*?)\*\*/g, '<strong class="text-white font-semibold">$1</strong>');
  // Italic
  html = html.replace(/\*(.*?)\*/g, '<em class="text-slate-300">$1</em>');

  // Lists
  html = html.replace(/^\- (.*$)/gim, '<li class="ml-4 list-disc text-slate-300 my-0.5">$1</li>');
  html = html.replace(/^([0-9]+)\. (.*$)/gim, '<li class="ml-4 list-decimal text-slate-300 my-0.5">$2</li>');

  // Line breaks
  html = html.replace(/\n\n/g, '<p class="my-1.5"></p>');
  html = html.replace(/\n/g, '<br/>');

  return html;
}
