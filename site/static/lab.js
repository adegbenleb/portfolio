// AI Lab page: live service status and the question form.

const HEALTH_REFRESH_MS = 15000;

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

async function ask(event) {
  event.preventDefault();
  const question = document.getElementById("question").value.trim();
  const answer = document.getElementById("answer");
  if (!question) return;

  answer.textContent = "Thinking…";
  try {
    const response = await fetch("/api/ask", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ question }),
    });
    const data = await response.json();
    answer.textContent = response.ok ? data.answer : data.detail || "Something went wrong.";
  } catch {
    answer.textContent = "The server could not be reached.";
  }
}

document.getElementById("ask-form").addEventListener("submit", ask);
refreshHealth();
setInterval(refreshHealth, HEALTH_REFRESH_MS);
