import { safeText } from '../utils/text.js';

export function renderAbout(about) {
  const container = document.getElementById('about-content');
  if (!container || !about) return;
  if (container.children.length > 0) return;

  const paragraphs = Array.isArray(about.paragraphs)
    ? about.paragraphs.map((text) => `<p>${safeText(text)}</p>`).join('')
    : '';

  const highlights = Array.isArray(about.highlights)
    ? `
      <div class="chip-list">
        ${about.highlights.map((item) => `<span class="chip">${safeText(item)}</span>`).join('')}
      </div>
    `
    : '';

  container.innerHTML = `
    <p class="lead">${safeText(about.greeting)}</p>
    ${paragraphs}
    ${highlights}
  `;
}
