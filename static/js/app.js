/**
 * app.js — Staywise frontend utilities
 */

'use strict';

// ── Score bar animation ───────────────────────────────────────────────────────
// Animate score bars from 0 → target width on page load for a satisfying reveal.
document.addEventListener('DOMContentLoaded', () => {
  const fills = document.querySelectorAll(
    '.score-fill, .score-fill-large'
  );

  fills.forEach((el) => {
    const target = el.style.width;
    el.style.width = '0';
    // Two rAF calls ensure the initial width:0 is painted before transitioning
    requestAnimationFrame(() => {
      requestAnimationFrame(() => {
        el.style.width = target;
      });
    });
  });
});

// ── Copy link to clipboard ────────────────────────────────────────────────────
/**
 * Copy a URL to the clipboard and give the button visual feedback.
 *
 * @param {string} url
 */
function copyLink(url) {
  if (!navigator.clipboard) {
    // Fallback for older browsers
    const textarea = document.createElement('textarea');
    textarea.value = url;
    textarea.style.position = 'fixed';
    textarea.style.opacity = '0';
    document.body.appendChild(textarea);
    textarea.select();
    document.execCommand('copy');
    document.body.removeChild(textarea);
    _flashCopyButton('✓ Copied!', '#c6f6d5', '#276749');
    return;
  }

  navigator.clipboard.writeText(url).then(() => {
    _flashCopyButton('✓ Copied!', '#c6f6d5', '#276749');
  }).catch(() => {
    _flashCopyButton('Failed', '#fed7d7', '#9b2c2c');
  });
}

function _flashCopyButton(label, bg, color) {
  const btn = document.getElementById('copy-btn');
  if (!btn) return;

  const originalLabel = btn.textContent;
  const originalBg    = btn.style.background;
  const originalColor = btn.style.color;

  btn.textContent    = label;
  btn.style.background = bg;
  btn.style.color      = color;

  setTimeout(() => {
    btn.textContent      = originalLabel;
    btn.style.background = originalBg;
    btn.style.color      = originalColor;
  }, 2200);
}
