const categorySelect = document.querySelector('#category-select');
  const selectedBigCategory = document.querySelector('#selected-big-category');
  const selectedCategory = document.querySelector('#selected-category');
  const scopeRadios = document.querySelectorAll('[name="scope"]');

  function syncCategoryScope() {
    const selectedScope = document.querySelector('[name="scope"]:checked');
    if (!selectedBigCategory || !selectedCategory || !selectedScope) return;
    if (selectedScope.value !== 'category' || !categorySelect || !categorySelect.value) {
      selectedBigCategory.value = '';
      selectedCategory.value = '';
      return;
    }
    const parts = categorySelect.value.split('||');
    selectedBigCategory.value = parts[0] || '';
    selectedCategory.value = parts[1] || '';
  }

  scopeRadios.forEach((input) => {
    input.addEventListener('change', syncCategoryScope);
  });

  if (categorySelect) {
    categorySelect.addEventListener('change', () => {
      const categoryScope = document.querySelector('[name="scope"][value="category"]');
      if (categoryScope && categorySelect.value) categoryScope.checked = true;
      syncCategoryScope();
    });
  }

  const resumeCard = document.querySelector('#resume-card');
  if (resumeCard) {
    const resumeUrl = resumeCard.dataset.resumeUrl;
    if (resumeUrl) {
      const resumeQuickGrid = resumeCard.closest('.resume-quick-grid');
      if (resumeQuickGrid) resumeQuickGrid.classList.add('has-resume');
      resumeCard.addEventListener('click', () => {
        window.location.href = resumeUrl;
      });
    }
  }
