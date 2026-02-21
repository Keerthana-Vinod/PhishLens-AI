/**
 * script.js  —  SpamShield AI Frontend
 *
 * HOW IT WORKS (simple terms):
 * 1. User types a message and clicks "Analyze Message"
 * 2. We send the message to the Flask backend via fetch() (an HTTP POST request)
 * 3. The backend returns a JSON object with prediction, confidence, suspicious
 *    words, and explanation
 * 4. We update the UI dynamically: show verdict, fill the progress bar,
 *    highlight suspicious words in the message preview, and list reasons.
 */

// ─────────────────────────────────────────────
// Example Messages
// ─────────────────────────────────────────────
const EXAMPLES = {
    spam: "Congratulations! You've been selected as a WINNER in our exclusive lottery! Claim your FREE prize of £10,000 now! Call 09001234567 urgently. Offer expires TODAY!!!",
    ham: "Hey, are you free this Saturday? We're planning a small get-together at Sarah's place. Let me know if you can make it!",
    phish: "URGENT: Your bank account has been compromised. Verify your identity immediately at http://secure-banklogin.xyz/verify?token=abc123 to avoid suspension."
};

// ─────────────────────────────────────────────
// Character Counter
// ─────────────────────────────────────────────
const textarea = document.getElementById("message-input");
const charCounter = document.getElementById("char-counter");
const MAX_CHARS = 500;

textarea.addEventListener("input", () => {
    const len = textarea.value.length;
    charCounter.textContent = `${len} / ${MAX_CHARS}`;

    // Warn when approaching limit
    charCounter.style.color = len > MAX_CHARS * 0.9
        ? "#f59e0b"   // amber warning
        : "var(--text-subtle)";

    // Cap input at max chars
    if (len > MAX_CHARS) {
        textarea.value = textarea.value.slice(0, MAX_CHARS);
        charCounter.textContent = `${MAX_CHARS} / ${MAX_CHARS}`;
    }
});

// ─────────────────────────────────────────────
// Load Example Messages
// ─────────────────────────────────────────────
function loadExample(type) {
    textarea.value = EXAMPLES[type] || "";
    textarea.dispatchEvent(new Event("input")); // trigger char counter update
    textarea.focus();

    // Animate the textarea briefly to draw attention
    textarea.classList.add("focus-pulse");
    setTimeout(() => textarea.classList.remove("focus-pulse"), 600);
}

// ─────────────────────────────────────────────
// Clear All
// ─────────────────────────────────────────────
function clearAll() {
    textarea.value = "";
    textarea.dispatchEvent(new Event("input"));

    // Hide results card and remove threat level classes
    const resultCard = document.getElementById("result-card");
    resultCard.classList.add("hidden");
    resultCard.classList.remove("threat-dangerous", "threat-safe");
    textarea.focus();
}

// ─────────────────────────────────────────────
// Highlight Suspicious Words in Message Text
// ─────────────────────────────────────────────
/**
 * Takes the original message string and a list of suspicious words,
 * and returns an HTML string where each suspicious word is wrapped
 * in a <span class="spam-word"> for red highlighting.
 *
 * We escape HTML characters first to prevent XSS.
 */
function buildHighlightedHTML(message, suspiciousWords) {
    // 1. Escape HTML special chars to prevent injection
    let safe = message
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;");

    if (!suspiciousWords || suspiciousWords.length === 0) {
        return safe;
    }

    // 2. Build a regex that matches any suspicious word (case-insensitive, whole words)
    //    We sort by length descending so longer phrases match before substrings
    const sortedWords = [...suspiciousWords].sort((a, b) => b.length - a.length);

    const escapedWords = sortedWords.map(w =>
        w.replace(/[.*+?^${}()|[\]\\]/g, "\\$&")   // escape regex special chars
    );

    const pattern = new RegExp(`\\b(${escapedWords.join("|")})\\b`, "gi");

    // 3. Replace each match with a highlighted span
    safe = safe.replace(pattern, match =>
        `<span class="spam-word" title="Suspicious word detected">⚠ ${match}</span>`
    );

    return safe;
}

// ─────────────────────────────────────────────
// Main Analyze Function
// ─────────────────────────────────────────────
async function analyzeMessage() {
    const message = textarea.value.trim();

    // ── Validation ──
    if (!message) {
        shakElement(textarea);
        textarea.focus();
        return;
    }

    // ── Show loading state ──
    const checkBtn = document.getElementById("check-btn");
    const btnText = checkBtn.querySelector(".btn-text");
    const btnLoader = document.getElementById("btn-loader");

    checkBtn.disabled = true;
    btnText.textContent = "Analyzing…";
    btnLoader.classList.remove("hidden");

    // Hide previous results while loading
    document.getElementById("result-card").classList.add("hidden");

    try {
        // ── Call Flask API ──
        const response = await fetch("/predict", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ message })
        });

        if (!response.ok) {
            throw new Error(`Server error: ${response.status}`);
        }

        const data = await response.json();

        // ── Render Results ──
        renderResults(message, data);

    } catch (err) {
        console.error("Prediction error:", err);
        alert("⚠️ Could not connect to the server.\nMake sure Flask is running: python app.py");
    } finally {
        // ── Restore button ──
        checkBtn.disabled = false;
        btnText.textContent = "Analyze Message";
        btnLoader.classList.add("hidden");
    }
}

// ─────────────────────────────────────────────
// Render Results to the DOM
// ─────────────────────────────────────────────
/**
 * data = {
 *   prediction:       "spam" | "ham"
 *   confidence:       number (0-100)
 *   suspicious_words: string[]
 *   explanation:      string[]
 * }
 */
function renderResults(originalMessage, data) {
    const { prediction, confidence, suspicious_words, explanation, scammer_intent } = data;

    const isSpam = prediction === "spam";

    // ── 1. Show result card with threat level border ──
    const resultCard = document.getElementById("result-card");
    resultCard.classList.remove("hidden");
    
    // Apply threat level border color
    resultCard.classList.remove("threat-dangerous", "threat-safe");
    resultCard.classList.add(isSpam ? "threat-dangerous" : "threat-safe");

    // Scroll smoothly to results
    setTimeout(() => resultCard.scrollIntoView({ behavior: "smooth", block: "start" }), 100);

    // ── 2. Verdict Banner ──
    const banner = document.getElementById("verdict-banner");
    const verdictIcon = document.getElementById("verdict-icon");
    const verdictLabel = document.getElementById("verdict-label");
    const verdictSub = document.getElementById("verdict-sub");

    banner.className = `verdict-banner ${isSpam ? "is-spam" : "is-ham"}`;
    verdictIcon.textContent = isSpam ? "🚨" : "✅";
    verdictLabel.textContent = isSpam ? "SPAM / PHISHING" : "SAFE MESSAGE";
    verdictSub.textContent = isSpam
        ? "This message shows signs of spam or phishing."
        : "No significant spam patterns detected.";

    // ── 3. Confidence Bar ──
    const confValue = document.getElementById("confidence-value");
    const progFill = document.getElementById("progress-fill");

    confValue.textContent = `${confidence}%`;
    progFill.className = `progress-fill ${isSpam ? "fill-spam" : "fill-ham"}`;

    // Animate bar: reset to 0 first, then set to actual value
    progFill.style.width = "0%";
    setTimeout(() => { progFill.style.width = `${confidence}%`; }, 50);

    // ── 4. Scammer Intent Detection ──
    const intentSection = document.getElementById("intent-section");
    const intentList = document.getElementById("intent-list");

    intentList.innerHTML = "";

    if (isSpam && scammer_intent && scammer_intent.length > 0) {
        intentSection.classList.remove("hidden");
        scammer_intent.forEach(intent => {
            const intentItem = document.createElement("div");
            intentItem.className = "intent-item";
            intentItem.innerHTML = `
                <div class="intent-icon">${intent.icon}</div>
                <div class="intent-content">
                    <div class="intent-goal">${intent.goal}</div>
                    <div class="intent-description">${intent.description}</div>
                </div>
            `;
            intentList.appendChild(intentItem);
        });
    } else {
        intentSection.classList.add("hidden");
    }

    // ── 5. Highlighted Message ──
    const highlightedDiv = document.getElementById("highlighted-text");
    highlightedDiv.innerHTML = buildHighlightedHTML(originalMessage, suspicious_words);

    // ── 6. Explanation List ──
    const explSection = document.getElementById("explanation-section");
    const explList = document.getElementById("explanation-list");

    explList.innerHTML = "";

    if (explanation && explanation.length > 0) {
        explSection.classList.remove("hidden");
        explanation.forEach(reason => {
            const li = document.createElement("li");
            li.innerHTML = reason;   // reasons may contain <b> tags from backend
            explList.appendChild(li);
        });
    } else {
        explSection.classList.add("hidden");
    }

    // ── 7. Suspicious Word Chips ──
    const chipsSection = document.getElementById("chips-section");
    const chipsContainer = document.getElementById("chips-container");

    chipsContainer.innerHTML = "";

    const displayWords = (suspicious_words || []).filter(
        w => w !== "http" && w !== "www"    // don't show internal URL markers as chips
    );

    if (displayWords.length > 0) {
        chipsSection.classList.remove("hidden");
        displayWords.forEach(word => {
            const chip = document.createElement("span");
            chip.className = "chip";
            chip.textContent = word;
            chipsContainer.appendChild(chip);
        });
    } else {
        chipsSection.classList.add("hidden");
    }
}

// ─────────────────────────────────────────────
// Shake animation for empty input
// ─────────────────────────────────────────────
function shakElement(el) {
    el.style.animation = "none";
    el.offsetHeight;   // reflow to restart animation
    el.style.animation = "shake 0.4s ease";
    setTimeout(() => { el.style.animation = ""; }, 400);
}

// Inject shake keyframes dynamically
const shakeStyle = document.createElement("style");
shakeStyle.textContent = `
  @keyframes shake {
    0%,100% { transform: translateX(0); }
    20%      { transform: translateX(-8px); }
    40%      { transform: translateX(8px); }
    60%      { transform: translateX(-5px); }
    80%      { transform: translateX(5px); }
  }
  @keyframes focus-pulse {
    0%,100% { border-color: var(--border-glass); }
    50%     { border-color: var(--accent-purple); box-shadow: 0 0 0 3px rgba(124,58,237,0.25); }
  }
  .focus-pulse { animation: focus-pulse 0.6s ease; }
`;
document.head.appendChild(shakeStyle);

// ─────────────────────────────────────────────
// Allow pressing Ctrl+Enter to submit
// ─────────────────────────────────────────────
textarea.addEventListener("keydown", (e) => {
    if (e.key === "Enter" && (e.ctrlKey || e.metaKey)) {
        analyzeMessage();
    }
});
