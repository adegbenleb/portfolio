// AI Lab page: live service status, the question form and the sources list.

const HEALTH_REFRESH_MS = 15000;

const form = document.getElementById("ask-form");
const input = document.getElementById("question");
const submitButton = form.querySelector("button[type=submit]");
const result = document.getElementById("result");
const answerEl = document.getElementById("answer");
const sourcesBlock = document.getElementById("sources-block");
const sourcesList = document.getElementById("sources");
const timing = document.getElementById("timing");

function setStatus(element, state) {
  element.dataset.state = state;
  element.textContent = state === "online" ? "Online" : "Offline";
}

async function refreshHealth() {
  const elements = document.querySelectorAll(".status[data-service]");
  try {
    const response = await fetch("/api/health");
    const data = await response.json();
    elements.forEach((el) => setStatus(el, data[el.dataset.service]));
  } catch {
    elements.forEach((el) => setStatus(el, "offline"));
  }
}

function renderSources(sources) {
  sourcesList.replaceChildren();
  for (const source of sources) {
    const item = document.createElement("li");
    item.value = source.n;
    const title = document.createElement("p");
    title.className = "source-title";
    title.textContent = `${source.label} (${source.section})`;
    const snippet = document.createElement("p");
    snippet.className = "source-snippet";
    snippet.textContent = source.snippet;
    const score = document.createElement("p");
    score.className = "source-score";
    score.textContent = `Similarity ${source.score.toFixed(2)}`;
    item.append(title, snippet, score);
    sourcesList.append(item);
  }
  sourcesBlock.hidden = sources.length === 0;
}

function showMessage(text) {
  answerEl.textContent = text;
  renderSources([]);
  timing.textContent = "";
}

async function ask(question) {
  result.setAttribute("aria-busy", "true");
  submitButton.disabled = true;
  showMessage("Thinking…");
  try {
    const response = await fetch("/api/ask", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ question }),
    });
    const data = await response.json();
    if (response.ok) {
      answerEl.textContent = data.answer;
      renderSources(data.sources);
      timing.textContent = `Answered in ${data.seconds.toFixed(1)} s`;
    } else if (response.status === 422) {
      showMessage("Please enter a question of up to 500 characters.");
    } else {
      showMessage(data.detail || "Something went wrong.");
    }
  } catch {
    showMessage("The server could not be reached.");
  } finally {
    result.setAttribute("aria-busy", "false");
    submitButton.disabled = false;
  }
}

form.addEventListener("submit", (event) => {
  event.preventDefault();
  const question = input.value.trim();
  if (question) ask(question);
});

document.querySelectorAll(".example").forEach((button) => {
  button.addEventListener("click", () => {
    input.value = button.dataset.question;
    ask(button.dataset.question);
  });
});

refreshHealth();
setInterval(refreshHealth, HEALTH_REFRESH_MS);
