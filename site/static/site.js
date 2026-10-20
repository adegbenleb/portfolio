// Shared behaviour on every page: the mobile menu and the Ctrl+K / Cmd+K command palette.
// Works the same on the live site and the static build.

// Mobile menu: the nav folds into a dropdown under the header on small screens.
const menuButton = document.querySelector("[data-menu-toggle]");

function setMenu(open) {
  document.body.classList.toggle("menu-open", open);
  menuButton.setAttribute("aria-expanded", String(open));
}

menuButton.addEventListener("click", () => setMenu(!document.body.classList.contains("menu-open")));
document.addEventListener("keydown", (event) => {
  if (event.key === "Escape" && document.body.classList.contains("menu-open")) {
    setMenu(false);
    menuButton.focus();
  }
});

// Command palette.
const palette = document.getElementById("command-palette");
const paletteInput = document.getElementById("palette-input");
const paletteResults = document.getElementById("palette-results");
const index = JSON.parse(document.getElementById("search-index").textContent);
const MAX_RESULTS = 8;
let matches = [];
let selected = 0;

function search(query) {
  const words = query.toLowerCase().split(/\s+/).filter(Boolean);
  if (!words.length) return index.filter((entry) => entry.kind === "Page");
  return index
    .map((entry) => {
      const title = entry.title.toLowerCase();
      const haystack = `${title} ${entry.kind} ${entry.hint}`.toLowerCase();
      if (!words.every((word) => haystack.includes(word))) return null;
      const score = words.reduce((sum, word) => sum + (title.includes(word) ? 2 : 1), 0);
      return { entry, score };
    })
    .filter(Boolean)
    .sort((a, b) => b.score - a.score)
    .map((match) => match.entry);
}

function renderResults() {
  matches = search(paletteInput.value).slice(0, MAX_RESULTS);
  selected = Math.min(selected, Math.max(matches.length - 1, 0));
  paletteResults.replaceChildren();
  if (!matches.length) {
    const empty = document.createElement("li");
    empty.className = "palette-empty";
    empty.textContent = "No matches";
    paletteResults.append(empty);
    paletteInput.removeAttribute("aria-activedescendant");
    return;
  }
  matches.forEach((entry, i) => {
    const item = document.createElement("li");
    item.id = `palette-option-${i}`;
    item.className = "palette-option";
    item.setAttribute("role", "option");
    item.setAttribute("aria-selected", String(i === selected));
    const kind = document.createElement("span");
    kind.className = "palette-kind";
    kind.textContent = entry.kind;
    const title = document.createElement("span");
    title.className = "palette-title";
    title.textContent = entry.title;
    item.append(kind, title);
    item.addEventListener("mousemove", () => {
      if (selected !== i) {
        selected = i;
        renderResults();
      }
    });
    item.addEventListener("click", () => go(entry));
    paletteResults.append(item);
  });
  paletteInput.setAttribute("aria-activedescendant", `palette-option-${selected}`);
}

function go(entry) {
  palette.close();
  window.location.href = entry.url;
}

function openPalette() {
  paletteInput.value = "";
  selected = 0;
  renderResults();
  palette.showModal();
  paletteInput.focus();
}

document.querySelectorAll("[data-open-palette]").forEach((button) => {
  button.addEventListener("click", openPalette);
});

document.addEventListener("keydown", (event) => {
  if ((event.metaKey || event.ctrlKey) && event.key.toLowerCase() === "k") {
    event.preventDefault();
    palette.open ? palette.close() : openPalette();
  }
});

paletteInput.addEventListener("input", () => {
  selected = 0;
  renderResults();
});

paletteInput.addEventListener("keydown", (event) => {
  if (event.key === "ArrowDown" || event.key === "ArrowUp") {
    event.preventDefault();
    if (!matches.length) return;
    const step = event.key === "ArrowDown" ? 1 : -1;
    selected = (selected + step + matches.length) % matches.length;
    renderResults();
    document.getElementById(`palette-option-${selected}`)?.scrollIntoView({ block: "nearest" });
  } else if (event.key === "Enter") {
    event.preventDefault();
    if (matches[selected]) go(matches[selected]);
  }
});

// Close when clicking the dimmed area around the palette.
palette.addEventListener("click", (event) => {
  if (event.target === palette) palette.close();
});

// Links like /experience#role-miele open that role's card.
function openFromHash() {
  if (!location.hash) return;
  const target = document.getElementById(location.hash.slice(1));
  // The target can be the <details> itself, sit inside one, or wrap one (timeline items).
  const details = target?.closest("details") || target?.querySelector("details");
  if (details) details.open = true;
}

window.addEventListener("hashchange", openFromHash);
openFromHash();
