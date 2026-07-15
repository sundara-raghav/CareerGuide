/**
 * quiz.js — handles multi-step quiz navigation, progress tracking, and submission.
 */

let currentIndex = 1;
const blocks = document.querySelectorAll('.question-block');
const total = blocks.length;

function showQuestion(index) {
  blocks.forEach(b => b.classList.add('hidden'));
  const current = document.querySelector(`[data-index="${index}"]`);
  if (current) {
    current.classList.remove('hidden');
    // Animate in
    gsap.fromTo(current, { x: 20, opacity: 0 }, { x: 0, opacity: 1, duration: 0.35, ease: 'power2.out' });
  }
  updateProgress(index);
  updateTabs(current?.dataset.section);
  currentIndex = index;
}

function navigate(currentIdx, direction) {
  const nextIdx = currentIdx + direction;
  if (nextIdx < 1 || nextIdx > total) return;
  showQuestion(nextIdx);
  // Scroll to top of question
  window.scrollTo({ top: 200, behavior: 'smooth' });
}

function jumpSection(section) {
  const firstInSection = Array.from(blocks).find(b => b.dataset.section === section);
  if (firstInSection) {
    showQuestion(parseInt(firstInSection.dataset.index));
  }
}

function updateProgress(index) {
  const pct = Math.round((index / total) * 100);
  const bar = document.getElementById('progress-bar');
  const text = document.getElementById('progress-text');
  const pctEl = document.getElementById('progress-pct');
  if (bar) bar.style.width = pct + '%';
  if (text) text.textContent = `Question ${index} of ${total}`;
  if (pctEl) pctEl.textContent = pct + '%';
}

function updateTabs(section) {
  document.querySelectorAll('.section-tab').forEach(tab => {
    tab.classList.remove('active', 'text-brand-400');
    if (tab.id === `tab-${section}`) {
      tab.classList.add('active', 'text-brand-400');
    }
  });
}

// Handle radio selection visual feedback
document.querySelectorAll('input[type="radio"]').forEach(radio => {
  radio.addEventListener('change', function () {
    const name = this.name;
    // Reset all options in this question
    document.querySelectorAll(`input[name="${name}"]`).forEach(r => {
      r.closest('label').classList.remove('border-brand-500', 'bg-brand-900/20');
      r.closest('label').classList.add('border-gray-700');
    });
    // Highlight selected
    this.closest('label').classList.add('border-brand-500', 'bg-brand-900/20');
    this.closest('label').classList.remove('border-gray-700');

    // Auto-advance after short delay
    setTimeout(() => {
      if (currentIndex < total) navigate(currentIndex, 1);
    }, 400);
  });
});

// Validate before submit: check all questions answered
document.getElementById('quiz-form')?.addEventListener('submit', function (e) {
  const unanswered = [];
  blocks.forEach(block => {
    const qid = block.dataset.qid;
    const answered = block.querySelector(`input[name="q_${qid}"]:checked`);
    if (!answered) unanswered.push(parseInt(block.dataset.index));
  });

  if (unanswered.length > 0) {
    e.preventDefault();
    // Jump to first unanswered
    showQuestion(unanswered[0]);
    alert(`Please answer question ${unanswered[0]} before submitting.`);
    return;
  }

  const btn = document.getElementById('submit-btn');
  if (btn) {
    btn.textContent = '⏳ Processing...';
    btn.disabled = true;
  }
});

// Keyboard navigation
document.addEventListener('keydown', e => {
  if (e.key === 'ArrowRight' || e.key === 'ArrowDown') navigate(currentIndex, 1);
  if (e.key === 'ArrowLeft' || e.key === 'ArrowUp') navigate(currentIndex, -1);
});

// Init
updateProgress(1);
updateTabs(blocks[0]?.dataset.section);
