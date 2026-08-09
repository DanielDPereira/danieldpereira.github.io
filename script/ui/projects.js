import { openProjectModal } from './modal.js';
import { safeText } from '../utils/text.js';

function buildProjectCard(project, index) {
  const technologies = Array.isArray(project.technologies)
    ? project.technologies.slice(0, 3).map((tech) => `<span class="chip">${safeText(tech)}</span>`).join('')
    : '';

  return `
    <article class="project-card" data-project-index="${index}">
      <img src="${safeText(project.thumbnail)}" alt="Thumbnail do projeto ${safeText(project.title)}" loading="lazy">
      <div class="project-body">
        <p class="project-meta">${safeText(project.category)} • ${safeText(project.year)}</p>
        <h3>${safeText(project.title)}</h3>
        <p>${safeText(project.description)}</p>
        <div class="chip-list">${technologies}</div>
      </div>
      <button class="btn btn-ghost project-open" data-project-index="${index}">Ver detalhes</button>
    </article>
  `;
}

export function renderProjects(projects) {
  const container = document.getElementById('projects-grid');
  if (!container || !Array.isArray(projects)) return;

  // Se o contêiner estiver vazio, renderiza o HTML dos projetos
  if (container.children.length === 0) {
    container.innerHTML = projects.map((project, index) => buildProjectCard(project, index)).join('');
  }

  // Hidrata a escuta de cliques do modal sem duplicar listeners
  if (!container.dataset.hydrated) {
    container.addEventListener('click', (event) => {
      const target = event.target;
      if (!(target instanceof HTMLElement)) return;

      const trigger = target.closest('[data-project-index]');
      if (!(trigger instanceof HTMLElement)) return;

      const index = Number(trigger.dataset.projectIndex);
      const selectedProject = projects[index];
      if (selectedProject) {
        openProjectModal(selectedProject);
      }
    });
    container.dataset.hydrated = 'true';
  }
}
