const result = JSON.parse(sessionStorage.getItem('flashcardResult') || '{}');
  const cards = Array.isArray(result.cards) ? result.cards : [];
  const total = Number(result.total || cards.length || 0);
  const mastered = Number(result.mastered || 0);
  const ambiguous = Number(result.ambiguous || 0);
  const weak = Number(result.weak || 0);
  const rate = total ? Math.round((mastered / total) * 100) : 0;

  function pct(value) {
    return total ? Math.round((Number(value || 0) / total) * 100) : 0;
  }

  function setText(selector, value) {
    const element = document.querySelector(selector);
    if (element) element.textContent = value;
  }

  const masteredPct = pct(mastered);
  const ambiguousPct = pct(ambiguous);
  const weakPct = Math.max(0, 100 - masteredPct - ambiguousPct);
  const greenDeg = total ? (mastered / total) * 360 : 0;
  const amberDeg = total ? ((mastered + ambiguous) / total) * 360 : 0;
  const donut = document.querySelector('#result-donut');
  if (donut) {
    donut.style.background = `conic-gradient(#10b981 0deg ${greenDeg}deg, #fbbf24 ${greenDeg}deg ${amberDeg}deg, #fb7185 ${amberDeg}deg 360deg)`;
  }

  setText('#result-rate', `${rate}%`);
  setText('#result-mastered-total', `${mastered} / ${total}語`);
  setText('#legend-mastered', `${mastered}語（${masteredPct}%）`);
  setText('#legend-ambiguous', `${ambiguous}語（${ambiguousPct}%）`);
  setText('#legend-weak', `${weak}語（${weakPct}%）`);
  setText('#legend-total', `${total}語`);
  setText('#info-total', `${total}語`);
  setText('#info-rate', `${rate}%`);

  const studiedAt = result.studiedAt ? new Date(result.studiedAt) : new Date();
  const dateLabel = `${studiedAt.getFullYear()}/${String(studiedAt.getMonth() + 1).padStart(2, '0')}/${String(studiedAt.getDate()).padStart(2, '0')} ${String(studiedAt.getHours()).padStart(2, '0')}:${String(studiedAt.getMinutes()).padStart(2, '0')}`;
  setText('#info-date', dateLabel);

  const retryLink = document.querySelector('#retry-link');
  if (retryLink && result.retryUrl) {
    retryLink.href = result.retryUrl;
  }

  const statusMap = {
    '理解済み': { label: 'わかった', cls: 'green' },
    'あいまい': { label: 'あいまい', cls: 'amber' },
    '未理解': { label: 'わからなかった', cls: 'rose' }
  };
  const historyBody = document.querySelector('#history-body');
  if (historyBody && cards.length) {
    historyBody.innerHTML = cards.map((card, index) => {
      const status = statusMap[card.status] || statusMap['未理解'];
      const detailUrl = `/keywords/${encodeURIComponent(card.id)}`;
      return `
        <tr class="history-row" data-url="${detailUrl}">
          <td>${index + 1}</td>
          <td>${card.keyword || '-'}</td>
          <td>${card.category || '-'}</td>
          <td><span class="status-badge ${status.cls}">${status.label}</span></td>
          <td><span class="row-arrow">›</span></td>
        </tr>
      `;
    }).join('');
    historyBody.querySelectorAll('.history-row').forEach(row => {
      row.addEventListener('click', () => {
        window.location.href = row.dataset.url;
      });
    });
  }
