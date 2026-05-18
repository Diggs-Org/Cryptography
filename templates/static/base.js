(function () {
  const ATTEMPTS_BEFORE_HINT = 3;
  let attempts = 0;
  let hintsUnlocked = 0;

  const form      = document.getElementById('answer-form');
  const input     = document.getElementById('answer-input');
  const feedback  = document.getElementById('feedback');
  const hintList  = document.getElementById('hint-list');
  const hintItems = Array.from(hintList.querySelectorAll('li'));
  const hintToggle = document.getElementById('hint-toggle');
  const puzzleId   = document.body.dataset.puzzleId;

  document.getElementById('share-link').href = window.location.href;

  hintToggle.addEventListener('click', () => {
    hintList.classList.toggle('visible');
  });

  form.addEventListener('submit', async (e) => {
    e.preventDefault();
    const guess = input.value.trim();
    if (!guess) return;

    const res = await fetch(`/puzzle/${puzzleId}/check`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ answer: guess, token: form.token.value }),
    });
    const data = await res.json();

    attempts++;
    if (data.correct) {
      feedback.textContent = '✓ Correct!';
      feedback.className = 'feedback correct';
      form.querySelector('button').disabled = true;
    } else {
      feedback.textContent = '✗ Not quite. Try again.';
      feedback.className = 'feedback incorrect';
      if (attempts % ATTEMPTS_BEFORE_HINT === 0 && hintsUnlocked < hintItems.length) {
        hintItems[hintsUnlocked].classList.remove('locked');
        hintsUnlocked++;
        hintList.classList.add('visible');
      }
    }
  });
}());
