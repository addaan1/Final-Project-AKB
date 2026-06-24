/* ============================================================
   Galbay Score Quiz — Interaktif multi-step form
   ============================================================ */
(function() {
  'use strict';

  const TOTAL_STEPS = 6;
  let currentStep = 1;

  const steps = document.querySelectorAll('.quiz-step');
  const prevBtn = document.getElementById('quizPrev');
  const nextBtn = document.getElementById('quizNext');
  const submitBtn = document.getElementById('quizSubmit');
  const progressBar = document.getElementById('quizBar');
  const progressText = document.getElementById('quizProgress');

  if (!steps.length || !nextBtn) return;

  function updateProgress() {
    const pct = ((currentStep - 1) / TOTAL_STEPS) * 100;
    if (progressBar) progressBar.style.setProperty('--progress', pct + '%');
    if (progressText) progressText.textContent = (currentStep - 1) + ' / 6';
  }

  function showStep(n) {
    steps.forEach(s => s.classList.remove('active'));
    const step = document.querySelector(`.quiz-step[data-step="${n}"]`);
    if (step) {
      step.classList.add('active');
      step.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }
    if (prevBtn) prevBtn.disabled = (n === 1);
    if (n === TOTAL_STEPS) {
      nextBtn.style.display = 'none';
      submitBtn.style.display = 'inline-flex';
    } else {
      nextBtn.style.display = 'inline-flex';
      submitBtn.style.display = 'none';
    }
  }

  function validateCurrent() {
    const step = document.querySelector(`.quiz-step[data-step="${currentStep}"]`);
    if (!step) return true;
    const radios = step.querySelectorAll('input[type="radio"]');
    const checked = step.querySelectorAll('input[type="radio"]:checked');
    if (radios.length > 0 && checked.length === 0) {
      // visual feedback: shake
      step.style.animation = 'none';
      step.offsetHeight; /* trigger reflow */
      step.style.animation = 'shake 0.4s ease';
      return false;
    }
    return true;
  }

  // Inject shake keyframes
  if (!document.getElementById('quiz-shake-keyframes')) {
    const style = document.createElement('style');
    style.id = 'quiz-shake-keyframes';
    style.textContent = `
      @keyframes shake {
        0%, 100% { transform: translateX(0); }
        25% { transform: translateX(-8px); }
        75% { transform: translateX(8px); }
      }
    `;
    document.head.appendChild(style);
  }

  if (nextBtn) {
    nextBtn.addEventListener('click', () => {
      if (!validateCurrent()) return;
      if (currentStep < TOTAL_STEPS) {
        currentStep++;
        showStep(currentStep);
        updateProgress();
      }
    });
  }

  if (prevBtn) {
    prevBtn.addEventListener('click', () => {
      if (currentStep > 1) {
        currentStep--;
        showStep(currentStep);
        updateProgress();
      }
    });
  }

  // Auto-advance when option is selected (delight UX)
  steps.forEach(step => {
    const radios = step.querySelectorAll('input[type="radio"]');
    radios.forEach(radio => {
      radio.addEventListener('change', () => {
        // visual feedback: pulse selected
        const content = radio.nextElementSibling;
        if (content) {
          content.style.transform = 'scale(0.98)';
          setTimeout(() => { content.style.transform = ''; }, 200);
        }
        // auto-advance after 600ms (allow user to see selection first)
        setTimeout(() => {
          if (currentStep < TOTAL_STEPS) {
            currentStep++;
            showStep(currentStep);
            updateProgress();
          } else {
            // last step: trigger submit button visibility
            showStep(TOTAL_STEPS);
          }
        }, 600);
      });
    });
  });

  // Init
  showStep(1);
  updateProgress();

})();

/* ============================================================
   Source filter for charts (placeholder — toggling data series)
   ============================================================ */
(function() {
  const filters = document.querySelectorAll('.source-filter-btn');
  if (!filters.length) return;

  filters.forEach(btn => {
    btn.addEventListener('click', () => {
      const source = btn.dataset.source;
      // toggle active state
      filters.forEach(b => b.classList.toggle('active', b === btn));
      // dispatch custom event for charts to react
      window.dispatchEvent(new CustomEvent('sourceFilterChange', { detail: { source } }));
    });
  });

})();
