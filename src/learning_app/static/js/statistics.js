document.querySelectorAll('[data-stats-tab]').forEach((button) => {
    button.addEventListener('click', () => {
      const target = button.dataset.statsTab;
      document.querySelectorAll('[data-stats-tab]').forEach((tab) => {
        tab.classList.toggle('is-active', tab.dataset.statsTab === target);
      });
      document.querySelectorAll('[data-stats-panel]').forEach((panel) => {
        panel.classList.toggle('is-active', panel.dataset.statsPanel === target);
      });
    });
  });

  document.querySelectorAll('[data-trend-tab]').forEach((button) => {
    button.addEventListener('click', () => {
      const target = button.dataset.trendTab;
      document.querySelectorAll('[data-trend-tab]').forEach((tab) => {
        tab.classList.toggle('is-active', tab.dataset.trendTab === target);
      });
      document.querySelectorAll('[data-trend-panel]').forEach((panel) => {
        panel.classList.toggle('is-active', panel.dataset.trendPanel === target);
      });
      document.querySelectorAll('[data-trend-stats]').forEach((stats) => {
        stats.classList.toggle('is-active', stats.dataset.trendStats === target);
      });
    });
  });

  document.querySelectorAll('[data-analysis-tab]').forEach((button) => {
    button.addEventListener('click', () => {
      const target = button.dataset.analysisTab;
      document.querySelectorAll('[data-analysis-tab]').forEach((tab) => {
        tab.classList.toggle('is-active', tab.dataset.analysisTab === target);
      });
      document.querySelectorAll('[data-analysis-panel]').forEach((panel) => {
        panel.classList.toggle('is-active', panel.dataset.analysisPanel === target);
      });
    });
  });

  const categorySort = document.querySelector('[data-category-sort]');
  const categoryTable = document.querySelector('.category-term-table');
  if (categorySort && categoryTable) {
    categorySort.addEventListener('change', () => {
      const rows = Array.from(categoryTable.querySelectorAll('[data-category-row]'));
      const sorted = rows.sort((a, b) => {
        const rateA = Number(a.dataset.rate || 0);
        const rateB = Number(b.dataset.rate || 0);
        const unknownA = Number(a.dataset.unknown || 0);
        const unknownB = Number(b.dataset.unknown || 0);
        const untrainedA = Number(a.dataset.untrained || 0);
        const untrainedB = Number(b.dataset.untrained || 0);
        const nameA = a.dataset.name || '';
        const nameB = b.dataset.name || '';
        if (categorySort.value === 'high') return rateB - rateA || nameA.localeCompare(nameB, 'ja');
        if (categorySort.value === 'unknown') return unknownB - unknownA || rateA - rateB || nameA.localeCompare(nameB, 'ja');
        if (categorySort.value === 'untrained') return untrainedB - untrainedA || rateA - rateB || nameA.localeCompare(nameB, 'ja');
        if (categorySort.value === 'name') return nameA.localeCompare(nameB, 'ja');
        return rateA - rateB || nameA.localeCompare(nameB, 'ja');
      });
      sorted.forEach((row) => categoryTable.appendChild(row));
    });
  }

  const showReviewMore = document.querySelector('[data-show-review-more]');
  if (showReviewMore) {
    showReviewMore.addEventListener('click', () => {
      document.querySelectorAll('[data-extra-review]').forEach((row) => {
        row.hidden = false;
      });
      showReviewMore.hidden = true;
    });
  }

  const showWeakMore = document.querySelector('[data-show-weak-more]');
  if (showWeakMore) {
    showWeakMore.addEventListener('click', () => {
      document.querySelectorAll('[data-extra-weak]').forEach((row) => {
        row.hidden = false;
      });
      showWeakMore.hidden = true;
      const panel = showWeakMore.closest('[data-analysis-panel]');
      const select = panel ? panel.querySelector('[data-detail-category-filter]') : null;
      if (select) applyDetailCategoryFilter(select);
    });
  }

  function applyDetailCategoryFilter(select) {
    const panel = select.closest('[data-analysis-panel], [data-practice-analysis-panel]');
    if (!panel) return;
    const selected = select.value || 'all';
    const rows = Array.from(panel.querySelectorAll('[data-detail-category]'));
    const showMore = panel.querySelector('[data-show-review-more]');
    const reviewExpanded = showMore ? showMore.hidden : true;
    const weakShowMore = panel.querySelector('[data-show-weak-more]');
    const weakExpanded = weakShowMore ? weakShowMore.hidden : true;
    let visibleCount = 0;
    rows.forEach((row) => {
      const matches = selected === 'all' || row.dataset.detailCategory === selected;
      if (row.matches('[data-extra-review]')) {
        row.hidden = selected === 'all' && !reviewExpanded;
      }
      if (row.matches('[data-extra-weak]')) {
        row.hidden = selected === 'all' && !weakExpanded;
      }
      row.dataset.categoryFiltered = matches ? '0' : '1';
      row.style.display = matches ? '' : 'none';
      if (matches && !row.hidden) visibleCount += 1;
    });
    const empty = panel.querySelector('[data-category-empty]');
    if (empty) {
      empty.hidden = visibleCount > 0;
    }
  }

  document.querySelectorAll('[data-detail-category-filter]').forEach((select) => {
    select.addEventListener('change', () => applyDetailCategoryFilter(select));
    applyDetailCategoryFilter(select);
  });

  document.querySelectorAll('[data-practice-category-sort]').forEach((select) => {
    select.addEventListener('change', () => {
      const mode = select.dataset.practiceCategorySort;
      const table = document.querySelector(`[data-practice-category-table="${mode}"]`);
      if (!table) return;
      const rows = Array.from(table.querySelectorAll('[data-practice-category-row]'));
      rows.sort((a, b) => {
        const accuracyA = Number(a.dataset.accuracy || 0);
        const accuracyB = Number(b.dataset.accuracy || 0);
        const totalA = Number(a.dataset.total || 0);
        const totalB = Number(b.dataset.total || 0);
        const nameA = a.dataset.name || '';
        const nameB = b.dataset.name || '';
        if (select.value === 'high') return accuracyB - accuracyA || nameA.localeCompare(nameB, 'ja');
        if (select.value === 'total') return totalB - totalA || accuracyA - accuracyB || nameA.localeCompare(nameB, 'ja');
        if (select.value === 'name') return nameA.localeCompare(nameB, 'ja');
        return accuracyA - accuracyB || nameA.localeCompare(nameB, 'ja');
      });
      rows.forEach((row) => table.appendChild(row));
    });
  });

  document.querySelectorAll('[data-practice-trend-tab]').forEach((button) => {
    button.addEventListener('click', () => {
      const target = button.dataset.practiceTrendTab;
      const panelRoot = button.closest('[data-practice-mode-panel]') || document;
      panelRoot.querySelectorAll('[data-practice-trend-tab]').forEach((tab) => {
        tab.classList.toggle('is-active', tab.dataset.practiceTrendTab === target);
      });
      panelRoot.querySelectorAll('[data-practice-trend-panel]').forEach((panel) => {
        panel.classList.toggle('is-active', panel.dataset.practiceTrendPanel === target);
      });
      panelRoot.querySelectorAll('[data-practice-trend-stats]').forEach((stats) => {
        stats.classList.toggle('is-active', stats.dataset.practiceTrendStats === target);
      });
    });
  });

  document.querySelectorAll('[data-practice-analysis-tab]').forEach((button) => {
    button.addEventListener('click', () => {
      const target = button.dataset.practiceAnalysisTab;
      const panelRoot = button.closest('[data-practice-mode-panel]') || document;
      panelRoot.querySelectorAll('[data-practice-analysis-tab]').forEach((tab) => {
        tab.classList.toggle('is-active', tab.dataset.practiceAnalysisTab === target);
      });
      panelRoot.querySelectorAll('[data-practice-analysis-panel]').forEach((panel) => {
        panel.classList.toggle('is-active', panel.dataset.practiceAnalysisPanel === target);
      });
    });
  });

  document.querySelectorAll('[data-practice-mode-tab]').forEach((button) => {
    button.addEventListener('click', () => {
      const target = button.dataset.practiceModeTab;
      document.querySelectorAll('[data-practice-mode-tab]').forEach((tab) => {
        tab.classList.toggle('is-active', tab.dataset.practiceModeTab === target);
      });
      document.querySelectorAll('[data-practice-mode-panel]').forEach((panel) => {
        panel.classList.toggle('is-active', panel.dataset.practiceModePanel === target);
      });
    });
  });

  document.querySelectorAll('[data-overall-analysis-tab]').forEach((button) => {
    button.addEventListener('click', () => {
      const target = button.dataset.overallAnalysisTab;
      document.querySelectorAll('[data-overall-analysis-tab]').forEach((tab) => {
        tab.classList.toggle('is-active', tab.dataset.overallAnalysisTab === target);
      });
      document.querySelectorAll('[data-overall-analysis-panel]').forEach((panel) => {
        panel.classList.toggle('is-active', panel.dataset.overallAnalysisPanel === target);
      });
    });
  });

  document.querySelectorAll('[data-map-category]').forEach((button) => {
    button.addEventListener('click', () => {
      const category = button.dataset.mapCategory;
      document.querySelectorAll('[data-map-category]').forEach((bubble) => {
        bubble.classList.toggle('is-active', bubble.dataset.mapCategory === category);
      });
      const matchingCard = document.querySelector(`[data-recommend-category="${CSS.escape(category)}"]`);
      document.querySelectorAll('[data-recommend-category]').forEach((card) => {
        card.classList.toggle('is-active', card.dataset.recommendCategory === category);
      });
      document.querySelectorAll('[data-map-detail]').forEach((card) => {
        card.classList.toggle('is-active', card.dataset.mapDetail === category);
      });
      document.querySelectorAll('.map-selected-panel, .ov3-selected-panel').forEach((panel) => {
        panel.classList.toggle('is-open', !matchingCard);
      });
      if (matchingCard) {
        matchingCard.scrollIntoView({ block: 'nearest', behavior: 'smooth' });
      }
    });
  });

  document.querySelectorAll('.ov3-map').forEach((map) => {
    const points = Array.from(map.querySelectorAll('.ov3-map-point'));
    const occupiedPoints = [];
    const pointOffsets = [
      [0, 0], [24, 0], [-24, 0], [0, -24], [0, 24],
      [24, -24], [-24, -24], [24, 24], [-24, 24],
      [42, 0], [-42, 0], [0, -42], [0, 42],
    ];
    points.forEach((point) => {
      const bubble = point.querySelector('.ov3-bubble');
      if (!bubble) return;
      for (const [x, y] of pointOffsets) {
        point.style.transform = `translate(calc(-50% + ${x}px), calc(-50% + ${y}px))`;
        const rect = bubble.getBoundingClientRect();
        const overlaps = occupiedPoints.some((prev) => !(
          rect.right + 6 < prev.left ||
          rect.left - 6 > prev.right ||
          rect.bottom + 6 < prev.top ||
          rect.top - 6 > prev.bottom
        ));
        if (!overlaps) {
          occupiedPoints.push(rect);
          break;
        }
      }
    });

    const labels = Array.from(map.querySelectorAll('.ov3-map-point span'));
    const placed = [];
    labels.forEach((label, index) => {
      label.style.marginTop = '';
      let guard = 0;
      let rect = label.getBoundingClientRect();
      while (placed.some((prev) => !(rect.right < prev.left || rect.left > prev.right || rect.bottom < prev.top || rect.top > prev.bottom)) && guard < 8) {
        const direction = index % 2 === 0 ? 1 : -1;
        label.style.marginTop = `${direction * (guard + 1) * 8}px`;
        rect = label.getBoundingClientRect();
        guard += 1;
      }
      placed.push(rect);
    });
  });

  document.querySelectorAll('[data-show-more]').forEach((button) => {
    const panel = button.closest('[data-overall-analysis-panel]');
    if (!panel || !panel.querySelector('[data-extra-analysis]')) {
      button.hidden = true;
      return;
    }
    button.addEventListener('click', () => {
      if (!panel) return;
      const expanded = panel.classList.toggle('is-expanded');
      button.textContent = expanded ? '折りたたむ' : 'もっと見る';
    });
  });
