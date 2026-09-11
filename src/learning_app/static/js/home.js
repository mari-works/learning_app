const goalModal = document.querySelector('[data-goal-modal]');
  document.querySelectorAll('[data-open-goal-modal]').forEach((button) => {
    button.addEventListener('click', () => {
      goalModal?.classList.add('is-open');
      goalModal?.setAttribute('aria-hidden', 'false');
    });
  });
  document.querySelectorAll('[data-close-goal-modal]').forEach((button) => {
    button.addEventListener('click', () => {
      goalModal?.classList.remove('is-open');
      goalModal?.setAttribute('aria-hidden', 'true');
    });
  });
