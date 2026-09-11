(function () {
  const buttons = Array.from(document.querySelectorAll('[data-result-view-button]'));
  const panels = Array.from(document.querySelectorAll('[data-result-view-panel]'));

  function activate(view) {
    buttons.forEach((button) => {
      button.classList.toggle('is-active', button.dataset.resultViewButton === view);
    });
    panels.forEach((panel) => {
      panel.classList.toggle('hidden', panel.dataset.resultViewPanel !== view);
    });
    const url = new URL(window.location.href);
    url.searchParams.set('view', view);
    window.history.replaceState({}, '', url);
  }

  buttons.forEach((button) => {
    button.addEventListener('click', function () {
      activate(button.dataset.resultViewButton);
    });
  });
})();
