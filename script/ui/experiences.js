import { createExternalLink } from '../utils/links.js';
import { safeText } from '../utils/text.js';

export function renderExperiences(experiences) {
  const container = document.getElementById('experience-list');
  if (!container || !Array.isArray(experiences)) return;
  if (container.children.length > 0) return;

  container.innerHTML = experiences
    .map((item) => {
      const achievements = Array.isArray(item.achievements)
        ? item.achievements.map((achievement) => `<li>${safeText(achievement)}</li>`).join('')
        : '';

      const technologies = Array.isArray(item.technologies)
        ? item.technologies.map((tech) => `<span class="chip">${safeText(tech)}</span>`).join('')
        : '';

      return `
        <article class="timeline-item">
          <header>
            <h3>${safeText(item.title)}</h3>
            <p class="muted">${safeText(item.period)} • ${safeText(item.type)} • ${safeText(item.location)}</p>
            ${createExternalLink(item.companyUrl, item.company, 'company-link')}
          </header>
          <p>${safeText(item.description)}</p>
          <ul class="achievements">${achievements}</ul>
          <div class="chip-list">${technologies}</div>
        </article>
      `;
    })
    .join('');
}
