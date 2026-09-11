document.querySelectorAll('.review-star').forEach((button) => {
  button.addEventListener('click', async () => {
    const current = button.dataset.reviewLater === '1';
    const next = !current;
    const id = button.dataset.keywordId;
    try {
      const response = await fetch(`/api/keywords/${id}/review_later`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ review_later: next })
      });
      if (!response.ok) return;
      const data = await response.json();
      button.dataset.reviewLater = data.review_later ? '1' : '0';
      button.classList.toggle('is-active', data.review_later);
      button.textContent = data.review_later ? '★' : '☆';
    } catch (error) {
      console.error(error);
    }
  });
});
