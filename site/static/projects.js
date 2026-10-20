// Projects page: filter cards by category. Without JavaScript all cards stay visible.

const buttons = document.querySelectorAll(".filter");
const cards = document.querySelectorAll(".project-card");

buttons.forEach((button) => {
  button.addEventListener("click", () => {
    const filter = button.dataset.filter;
    buttons.forEach((b) => b.setAttribute("aria-pressed", String(b === button)));
    cards.forEach((card) => {
      card.hidden = filter !== "all" && card.dataset.category !== filter;
    });
  });
});
