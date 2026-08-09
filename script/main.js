import { renderAbout } from './ui/about.js';
import { renderCertificates } from './ui/certificates.js';
import { renderEducation } from './ui/education.js';
import { attachGlobalEvents } from './ui/events.js';
import { renderExperiences } from './ui/experiences.js';
import { renderProfile } from './ui/profile.js';
import { renderProjects } from './ui/projects.js';
import { applyRevealAttributes, initScrollReveal } from './ui/reveal.js';
import { renderSkills } from './ui/skills.js';
import { loadPortfolioData } from './services/portfolio-data-service.js';

async function bootstrapPortfolio() {
  // Inicializa imediatamente interatividade e animações no HTML pré-renderizado
  applyRevealAttributes();
  initScrollReveal();
  attachGlobalEvents();

  try {
    const data = await loadPortfolioData();

    renderProfile(data.profile);
    renderAbout(data.about);
    renderEducation(data.education);
    renderExperiences(data.experiences);
    renderSkills(data.skills);
    renderProjects(data.projects);
    renderCertificates(data.certificates);

    // Re-aplica seletores de animação caso novos elementos tenham sido renderizados
    applyRevealAttributes();
    initScrollReveal();
  } catch (error) {
    console.warn('Usando conteúdo pré-renderizado estático (JSON offline ou não carregado):', error);
  }
}

document.addEventListener('DOMContentLoaded', bootstrapPortfolio);
