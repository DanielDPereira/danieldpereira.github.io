import { safeText } from '../utils/text.js';

export function renderSkills(skills) {
  const container = document.getElementById('skills-grid');
  if (!container || !Array.isArray(skills)) return;
  if (container.children.length > 0) return;

  container.innerHTML = skills
    .map(
      (item) => `
        <article class="skill-card">
          <img src="${safeText(item.icon)}" alt="${safeText(item.alt)}" loading="lazy">
          <h3>${safeText(item.name)}</h3>
          <p>${safeText(item.category || 'Tecnologia')}</p>
        </article>
      `
    )
    .join('');
}
