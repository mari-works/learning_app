(() => {
  const form = document.querySelector('[data-wizard-form]');
  if (!form) return;

  let step = 1;
  const csvState = { terms: null, questions: null };
  const required = {
    terms: ['ID', 'カテゴリ', '用語', '意味'],
    questions: ['ID', 'カテゴリ', '問題', '正答', '誤答1', '誤答2', '誤答3', '解説'],
  };

  const parseCsv = (text) => {
    const rows = [];
    let row = [], value = '', quoted = false;
    for (let i = 0; i < text.length; i += 1) {
      const char = text[i];
      if (char === '"' && quoted && text[i + 1] === '"') { value += '"'; i += 1; }
      else if (char === '"') quoted = !quoted;
      else if (char === ',' && !quoted) { row.push(value); value = ''; }
      else if ((char === '\n' || char === '\r') && !quoted) {
        if (char === '\r' && text[i + 1] === '\n') i += 1;
        row.push(value); value = '';
        if (row.some(cell => cell.trim())) rows.push(row);
        row = [];
      } else value += char;
    }
    row.push(value);
    if (row.some(cell => cell.trim())) rows.push(row);
    return rows;
  };

  const validateRows = (kind, rows) => {
    if (!rows.length) throw new Error('CSVにデータがありません。');
    const headers = rows[0].map((cell, index) => index === 0 ? cell.replace(/^\uFEFF/, '').trim() : cell.trim());
    const missing = required[kind].filter(column => !headers.includes(column));
    if (missing.length) throw new Error(`必須列がありません：${missing.join('、')}`);
    const records = rows.slice(1).map(values => Object.fromEntries(headers.map((header, index) => [header, (values[index] || '').trim()])));
    if (!records.length) throw new Error('CSVにデータ行がありません。');
    const ids = new Set();
    records.forEach((record, index) => {
      const line = index + 2;
      required[kind].forEach(column => { if (!record[column]) throw new Error(`${line}行目：「${column}」が入力されていません。`); });
      if (ids.has(record.ID)) throw new Error(`${line}行目：「ID」が重複しています。`);
      ids.add(record.ID);
      if (kind === 'questions') {
        if (!/^\d+$/.test(record.ID) || Number(record.ID) < 1) throw new Error(`${line}行目：「ID」は1以上の整数で入力してください。`);
        const answers = [record['正答'], record['誤答1'], record['誤答2'], record['誤答3']];
        if (new Set(answers).size !== 4) throw new Error(`${line}行目：4つの選択肢は異なる内容にしてください。`);
      }
    });
    return { headers, records, categories: new Set(records.map(record => record['カテゴリ'])).size };
  };

  const escapeHtml = value => String(value).replace(/[&<>'"]/g, char => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', "'": '&#39;', '"': '&quot;' }[char]));
  const renderPreview = (kind, result) => {
    const columns = kind === 'terms' ? ['ID', 'カテゴリ', '用語', '意味'] : ['ID', 'カテゴリ', '問題', '正答'];
    const head = columns.map(column => `<th class="whitespace-nowrap bg-slate-50 px-3 py-2 text-left text-xs font-bold text-slate-600">${column}</th>`).join('');
    const body = result.records.slice(0, 5).map(record => `<tr>${columns.map(column => `<td class="max-w-xs truncate border-t border-slate-200 px-3 py-2 text-xs text-slate-700">${escapeHtml(record[column])}</td>`).join('')}</tr>`).join('');
    document.querySelector(`[data-preview="${kind}"]`).innerHTML = `<table class="w-full min-w-[560px]"><thead><tr>${head}</tr></thead><tbody>${body}</tbody></table>`;
  };

  const showValidation = (kind, ok, message) => {
    const box = document.querySelector(`[data-validation="${kind}"]`);
    box.className = `mt-4 rounded-lg border px-4 py-4 text-sm font-semibold ${ok ? 'border-emerald-200 bg-emerald-50 text-emerald-800' : 'border-red-200 bg-red-50 text-red-800'}`;
    box.textContent = `${ok ? '✓' : '⚠'} ${message}`;
  };

  const handleFile = async (kind, input) => {
    const file = input.files[0];
    const name = input.closest('[data-drop-zone]').querySelector('[data-file-name]');
    const previewWrap = document.querySelector(`[data-preview-wrap="${kind}"]`);
    if (!file) return;
    name.textContent = file.name;
    try {
      if (!file.name.toLowerCase().endsWith('.csv')) throw new Error('CSVファイルを選択してください。');
      const result = validateRows(kind, parseCsv(await file.text()));
      csvState[kind] = result;
      showValidation(kind, true, `${result.records.length}件読み込み可能　カテゴリ：${result.categories}件`);
      renderPreview(kind, result);
      previewWrap.classList.remove('hidden');
    } catch (error) {
      csvState[kind] = null;
      showValidation(kind, false, error.message);
      previewWrap.classList.add('hidden');
    }
  };

  document.querySelectorAll('[data-csv-input]').forEach(input => {
    const kind = input.dataset.csvInput;
    const zone = input.closest('[data-drop-zone]');
    input.addEventListener('change', () => handleFile(kind, input));
    zone.addEventListener('click', event => { if (event.target !== input) input.click(); });
    zone.addEventListener('keydown', event => { if (event.key === 'Enter' || event.key === ' ') { event.preventDefault(); input.click(); } });
    ['dragenter', 'dragover'].forEach(type => zone.addEventListener(type, event => { event.preventDefault(); zone.classList.add('border-sky-500', 'bg-sky-50'); }));
    ['dragleave', 'drop'].forEach(type => zone.addEventListener(type, event => { event.preventDefault(); zone.classList.remove('border-sky-500', 'bg-sky-50'); }));
    zone.addEventListener('drop', event => { if (event.dataTransfer.files.length) { const transfer = new DataTransfer(); transfer.items.add(event.dataTransfer.files[0]); input.files = transfer.files; handleFile(kind, input); } });
  });

  document.querySelectorAll('[data-preview-toggle]').forEach(button => button.addEventListener('click', () => {
    const preview = document.querySelector(`[data-preview="${button.dataset.previewToggle}"]`);
    const opening = preview.classList.contains('hidden');
    preview.classList.toggle('hidden');
    button.textContent = opening ? 'プレビューを閉じる ▲' : 'プレビューを表示 ▼';
  }));

  const examToggle = form.querySelector('[data-exam-enabled]');
  const examFields = form.querySelector('[data-exam-fields]');
  const syncExam = () => { examFields.hidden = !examToggle.checked; examFields.querySelectorAll('input').forEach(input => { input.disabled = !examToggle.checked; input.required = examToggle.checked; }); };
  examToggle.addEventListener('change', syncExam); syncExam();

  const stepError = form.querySelector('[data-step-error]');
  const validateStep = () => {
    stepError.classList.add('hidden');
    if (step === 1) {
      const title = form.elements.title;
      if (!title.value.trim()) { stepError.textContent = '教材名を入力してください。'; stepError.classList.remove('hidden'); title.focus(); return false; }
      if (examToggle.checked && (!form.elements.exam_question_count.value || !form.elements.exam_time_minutes.value)) { stepError.textContent = '試験の問題数と制限時間を入力してください。'; stepError.classList.remove('hidden'); return false; }
    }
    if (step === 2 && (!csvState.terms || !csvState.questions)) {
      if (!csvState.terms) showValidation('terms', false, '正しい用語CSVを選択してください。');
      if (!csvState.questions) showValidation('questions', false, '正しい問題CSVを選択してください。');
      return false;
    }
    return true;
  };

  const fillConfirmation = () => {
    const exam = examToggle.checked;
    document.querySelector('[data-confirm-title]').textContent = form.elements.title.value.trim();
    document.querySelector('[data-confirm-description]').textContent = form.elements.description.value.trim() || '未設定';
    document.querySelector('[data-confirm-exam]').textContent = exam ? '使用する' : '使用しない';
    document.querySelector('[data-confirm-question]').textContent = exam ? `${form.elements.exam_question_count.value}問` : '—';
    document.querySelector('[data-confirm-time]').textContent = exam ? `${form.elements.exam_time_minutes.value}分` : '—';
    document.querySelector('[data-confirm-terms]').textContent = `${csvState.terms.records.length}件`;
    document.querySelector('[data-confirm-questions]').textContent = `${csvState.questions.records.length}件`;
    const categories = new Set([...csvState.terms.records, ...csvState.questions.records].map(record => record['カテゴリ']));
    document.querySelector('[data-confirm-categories]').textContent = `${categories.size}件`;
  };

  const render = () => {
    document.querySelectorAll('[data-step]').forEach(section => { section.hidden = Number(section.dataset.step) !== step; });
    document.querySelectorAll('[data-progress-item]').forEach(item => {
      const number = Number(item.dataset.progressItem), dot = item.querySelector('[data-progress-dot]'), label = item.querySelector('span:last-child');
      dot.textContent = number < step ? '✓' : number;
      dot.className = `relative z-10 flex h-8 w-8 items-center justify-center rounded-full border-2 text-xs font-bold ${number === step ? 'border-sky-600 bg-sky-600 text-white' : number < step ? 'border-emerald-600 bg-emerald-600 text-white' : 'border-slate-300 bg-white text-slate-500'}`;
      label.className = `mt-2 text-xs font-semibold sm:text-sm ${number === step ? 'text-sky-700' : number < step ? 'text-emerald-700' : 'text-slate-500'}`;
      const line = item.querySelector('[data-progress-line]'); if (line) line.className = `absolute left-1/2 top-4 h-px w-full ${number < step ? 'bg-emerald-400' : 'bg-slate-200'}`;
    });
    form.querySelector('[data-cancel]').classList.toggle('hidden', step !== 1);
    form.querySelector('[data-back]').classList.toggle('hidden', step === 1);
    form.querySelector('[data-next]').classList.toggle('hidden', step === 3);
    form.querySelector('[data-submit]').classList.toggle('hidden', step !== 3);
  };

  form.querySelector('[data-next]').addEventListener('click', () => { if (!validateStep()) return; step += 1; if (step === 3) fillConfirmation(); render(); });
  form.querySelector('[data-back]').addEventListener('click', () => { step -= 1; render(); });
  form.addEventListener('submit', event => { if (step !== 3 || !csvState.terms || !csvState.questions) event.preventDefault(); });
  render();
})();
