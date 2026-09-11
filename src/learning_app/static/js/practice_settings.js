(function () {
  const modeInputs = Array.from(document.querySelectorAll('input[name="mode"]'));
  const categoryRow = document.getElementById('practice-category-row');
  const categorySelect = document.getElementById('normal-category');

  function syncCategoryField() {
    const selected = modeInputs.find((input) => input.checked);
    const needsCategory = selected && selected.value === 'category';
    if (categorySelect) {
      categorySelect.required = Boolean(needsCategory);
      categorySelect.disabled = !needsCategory;
      if (!needsCategory) {
        categorySelect.value = '';
      }
    }
    if (categoryRow) {
      categoryRow.classList.toggle('is-hidden', !needsCategory);
    }
  }

  modeInputs.forEach((input) => input.addEventListener('change', syncCategoryField));
  syncCategoryField();
})();

(function () {
  const cards = Array.from(document.querySelectorAll('[data-exam-card]'));
  const timeField = document.getElementById('exam-time');

  function syncCards() {
    cards.forEach((card) => {
      const input = card.querySelector('input[type="radio"]');
      card.classList.toggle('is-selected', input.checked);
      if (input.checked && timeField) {
        timeField.value = input.dataset.minutes;
      }
    });
  }

  cards.forEach((card) => card.addEventListener('change', syncCards));
  syncCards();
})();
