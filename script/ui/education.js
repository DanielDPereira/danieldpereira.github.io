import { safeText } from '../utils/text.js';

export function renderEducation(education) {
  const container = document.getElementById('education-list');
  if (!container || !Array.isArray(education)) return;
  if (container.children.length > 0) return;

  container.innerHTML = education
    .map((item) => {
      const details = Array.isArray(item.details)
        ? item.details.map((detail) => `<li>${safeText(detail)}</li>`).join('')
        : '';

      return `
        <article class="education-item">
          <header>
            <h3 class="education-degree">${safeText(item.degree)}</h3>
            <p class="education-institution muted">${safeText(item.institution)}</p>
            <p class="muted">${safeText(item.period)}</p>
            <p class="muted">${safeText(item.type)}${item.issuer ? ` • ${safeText(item.issuer)}` : ''}</p>
          </header>
          <p>${safeText(item.description)}</p>
          ${details ? `<ul class="achievements">${details}</ul>` : ''}
        </article>
      `;
    })
    .join('');
}
