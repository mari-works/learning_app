(function () {
  const choices = Array.from(document.querySelectorAll('.answer-choice'));
  choices.forEach((choice) => {
    choice.addEventListener('change', function () {
      choices.forEach((item) => item.classList.toggle('is-selected', item.querySelector('input').checked));
    });
  });

  const timerEl = document.getElementById('exam-timer');
  if (!timerEl) return;

  const startMs = Number(document.getElementById('hidden-start-ms').value) || Date.now();
  const timeLimitSec = Number(document.getElementById('hidden-time-limit-seconds').value) || 0;
  const pauseElapsed = document.getElementById('pause-elapsed');
  const pauseAnswered = document.getElementById('pause-answered');

  function pad(value) {
    return String(value).padStart(2, '0');
  }

  function formatHMS(sec) {
    const safe = Math.max(0, Math.floor(Math.abs(sec)));
    const h = Math.floor(safe / 3600);
    const m = Math.floor((safe % 3600) / 60);
    const s = safe % 60;
    return pad(h) + ':' + pad(m) + ':' + pad(s);
  }

  function updateTimer() {
    const elapsed = Math.floor((Date.now() - startMs) / 1000);
    const remaining = timeLimitSec - elapsed;
    const label = remaining >= 0 ? '残り時間' : '超過時間';
    const color = remaining >= 0 ? 'text-emerald-700' : 'text-orange-700';
    timerEl.innerHTML = '<p class="text-xs font-semibold text-slate-500">' + label + '</p><p class="font-mono text-2xl font-bold ' + color + '">' + (remaining < 0 ? '+' : '') + formatHMS(remaining) + '</p>';
    if (pauseElapsed) pauseElapsed.textContent = formatHMS(elapsed);
  }

  function updatePauseAnswered() {
    if (!pauseAnswered) return;
    const baseAnswered = Number(pauseAnswered.dataset.baseAnswered) || 0;
    const currentAnswered = Number(pauseAnswered.dataset.currentAnswered) || 0;
    const currentSelected = Boolean(document.querySelector('input[name="choice"]:checked'));
    const adjusted = baseAnswered + (currentSelected && !currentAnswered ? 1 : 0);
    pauseAnswered.textContent = adjusted + '問';
  }

  updateTimer();
  updatePauseAnswered();
  setInterval(updateTimer, 1000);

  const modal = document.getElementById('pause-modal');
  const open = document.getElementById('pause-open');
  const closeButtons = [document.getElementById('pause-close'), document.getElementById('pause-cancel')].filter(Boolean);
  if (open && modal) {
    open.addEventListener('click', function () {
      modal.classList.remove('hidden');
      modal.classList.add('flex');
      updateTimer();
      updatePauseAnswered();
    });
  }
  closeButtons.forEach((button) => {
    button.addEventListener('click', function () {
      modal.classList.add('hidden');
      modal.classList.remove('flex');
    });
  });
})();
