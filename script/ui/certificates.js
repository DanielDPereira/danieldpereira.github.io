import { createExternalLink } from '../utils/links.js';

export function renderCertificates(certificates) {
  const container = document.getElementById('certificates-list');
  if (!container || !Array.isArray(certificates)) return;
  if (container.children.length > 0) return;

  container.innerHTML = certificates
    .map(
      (item) => `
        <li>
          ${createExternalLink(item.url, item.title, 'certificate-link')}
        </li>
      `
    )
    .join('');
}
