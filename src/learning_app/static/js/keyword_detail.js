const memo = document.getElementById('memo-textarea');
const count = document.getElementById('memo-count');

function updateMemoCount() {
  if (!memo || !count) return;
  count.textContent = `${memo.value.length} / 1000文字`;
}

if (memo) {
  memo.addEventListener('input', updateMemoCount);
  updateMemoCount();
}

const understandingForm = document.getElementById('understanding-form');
const autosaveStatus = document.getElementById('autosave-status');
if (understandingForm) {
  understandingForm.querySelectorAll('input[name="status"]').forEach((input) => {
    input.addEventListener('change', async () => {
      const formData = new FormData(understandingForm);
      if (autosaveStatus) autosaveStatus.textContent = '保存中...';
      try {
        const response = await fetch(window.location.pathname, {
          method: 'POST',
          body: formData
        });
        if (!response.ok) throw new Error('save failed');
        if (autosaveStatus) {
          autosaveStatus.textContent = '保存しました';
          window.setTimeout(() => { autosaveStatus.textContent = ''; }, 1400);
        }
      } catch (error) {
        if (autosaveStatus) autosaveStatus.textContent = '保存に失敗しました';
      }
    });
  });
}

const reviewButton = document.getElementById('review-later-button');
if (reviewButton) {
  reviewButton.addEventListener('click', async () => {
    const current = reviewButton.dataset.reviewLater === '1';
    const next = !current;
    try {
      const response = await fetch(`/api/keywords/${reviewButton.dataset.keywordId}/review_later`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ review_later: next })
      });
      if (!response.ok) return;
      const data = await response.json();
      reviewButton.dataset.reviewLater = data.review_later ? '1' : '0';
      reviewButton.classList.toggle('is-active', data.review_later);
      reviewButton.querySelector('span').textContent = data.review_later ? '★' : '☆';
      reviewButton.querySelector('b').textContent = data.review_later ? 'あとで確認に追加済み' : 'あとで確認に追加';
    } catch (error) {
      console.error(error);
    }
  });
}
