# Portfólio Pessoal — Daniel Dias Pereira

Portfólio pessoal híbrido de **Daniel Dias Pereira**, desenvolvido com foco em Ciência de Dados, Engenharia de Dados, Inteligência Artificial e Backend.

O projeto utiliza uma arquitetura baseada em dados (`portfolio-data.json`), gerenciamento local com CMS desktop (`gerenciador_portfolio.py`), validação automatizada (`validator.py`), pré-renderização estática de HTML e metadados SEO (`build.py`), e hidratação com JavaScript puro no frontend.

---

## 🏛️ Arquitetura do Projeto

```text
gerenciador_portfolio.py (Edição de Conteúdo & Backups)
        │
        ▼
portfolio-data.json (Fonte Única de Verdade)
        │
        ▼
     build.py ───▶ validator.py (Validação dos dados)
        │
        ├── pré-renderiza conteúdo HTML (Hero, Sobre, Formação, Exp, Skills, Projetos, Certificados)
        ├── gera metadados SEO (Title, Description, Canonical, OG, Twitter Card)
        ├── gera dados estruturados JSON-LD (Schema.org Person)
        ├── gera sitemap.xml e robots.txt
        └── atualiza index.html deterministicamente
        │
        ▼
   index.html (Documento Estático Completo)
        │
        ▼
  GitHub Pages ───▶ Navegador (HTML pré-renderizado imediato sem FOUC/flicker)
        ▲
        │
    JavaScript (Hidratação, Modal de Projetos, Scroll Reveal, Navegação Mobile)
```

---

## 📂 Estrutura de Arquivos

### Scripts Python & CMS

- `gerenciador_portfolio.py`: Interface desktop (Tkinter) para edição do `portfolio-data.json` com backup automático e integração com o build estático.
- `validator.py`: Validador de esquema e presença de dados obrigatórios no JSON.
- `build.py`: Script determinístico de pré-renderização estática de HTML, SEO e geração de `sitemap.xml` / `robots.txt`.
- `portfolio-data.json`: Fonte única de verdade contendo todos os dados do portfólio.

### Frontend JavaScript (`script/`)

- `main.js`: Ponto de entrada e hidratação imediata da aplicação.
- `config/`: Constantes globais (`constants.js`).
- `services/`: Serviço de carregamento dos dados (`portfolio-data-service.js`).
- `utils/`: Funções utilitárias de texto e sanitização de links (`text.js`, `links.js`).
- `ui/`: Módulos de interface (`profile.js`, `about.js`, `education.js`, `experiences.js`, `skills.js`, `projects.js`, `certificates.js`, `modal.js`, `events.js`, `reveal.js`).

### Estilos CSS (`style/`)

- `style.css`: Agregador de estilos usando `@import`.
- `base/`: Reset e variáveis globais (`variables.css`, `reset.css`).
- `layout/`: Estrutura do documento (`header.css`, `footer.css`, `layout.css`).
- `components/`: Componentes visuais e modais (`buttons.css`, `chips.css`, `cards.css`, `modal.css`).
- `sections/`: Estilização individual das seções (`hero.css`, `about.css`, `timeline.css`, `skills.css`, `projects.css`, `certificates.css`).
- `utilities/`: Efeitos de animação e scroll reveal (`reveal.css`, `animations.css`).
- `responsive/`: Media queries para responsividade (`responsive.css`).

---

## ⚡ Fluxo de Desenvolvedor / Atualização do Portfólio

Para atualizar o conteúdo do portfólio:

1. **Editar dados via CMS:**
   ```bash
   python gerenciador_portfolio.py
   ```
   *Ou edite `portfolio-data.json` diretamente em um editor de código.*

2. **Executar o Build Estático (validação + pré-renderização + SEO):**
   ```bash
   python build.py
   ```

3. **Verificar o resultado localmente:**
   ```bash
   python -m http.server 8000
   ```
   Abra no navegador: `http://localhost:8000`

4. **Fazer commit e enviar para o GitHub:**
   ```bash
   git add portfolio-data.json index.html sitemap.xml robots.txt
   git commit -m "feat: atualiza dados do portfólio"
   git push origin main
   ```

---

## 🎯 SEO & Acessibilidade

- HTML5 100% semântico com hierarquia de títulos (`H1` único para a pessoa, `H2` para seções, `H3` para cards).
- Metadados completos no `<head>`: Title, Description, Canonical Tag, Open Graph, Twitter Cards.
- Dados Estruturados Schema.org (`@type: Person`) via JSON-LD.
- Resiliência total: O site exibe 100% do conteúdo textual e visual mesmo se o JavaScript estiver desabilitado.