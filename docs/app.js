(() => {
  const cfg = window.SITE || {};
  document.documentElement.classList.add('js');

  // Logos des technologies (devicon). Un seul endroit à corriger si une adresse change.
  // Si une icône ne se charge pas, elle disparaît : le libellé texte reste seul.
  // On sert d'abord les fichiers locaux (docs/icons/<clé>.svg) ; si l'un manque,
  // on retombe sur le CDN devicon ; si ça échoue aussi, l'icône disparaît et
  // seul le libellé texte reste. Jamais d'image cassée.
  const ICON_LOCAL = 'icons/';
  const ICON_CDN = 'https://cdn.jsdelivr.net/gh/devicons/devicon@latest/icons/';
  const ICONS = {
    java: 'java/java-original',
    spring: 'spring/spring-original',
    angular: 'angular/angular-original',
    ts: 'typescript/typescript-original',
    postgres: 'postgresql/postgresql-original',
    docker: 'docker/docker-original',
    maven: 'maven/maven-original',
    gha: 'githubactions/githubactions-original',
    junit: 'junit/junit-original',
  };
  document.querySelectorAll('[data-ic]').forEach((el) => {
    const frag = document.createDocumentFragment();
    el.dataset.ic.split(/\s+/).filter(Boolean).forEach((key) => {
      if (!ICONS[key]) return;
      const img = document.createElement('img');
      img.className = 'ic';
      img.alt = '';
      img.width = 20;
      img.height = 20;
      img.loading = 'lazy';
      let tried = 0;
      img.addEventListener('error', () => {
        if (tried === 0) { tried = 1; img.src = `${ICON_CDN}${ICONS[key]}.svg`; }
        else img.remove();
      });
      img.src = `${ICON_LOCAL}${key}.svg`;
      frag.appendChild(img);
    });
    if (frag.childNodes.length) el.prepend(frag);
  });

  // Liens de contact et de code : n'afficher que ce qui mène à une page réelle.
  document.querySelectorAll('[data-link]').forEach((a) => {
    const key = a.dataset.link;
    const value = cfg[key];
    if (!value) return;
    a.href = key === 'email' ? `mailto:${value}` : value;
    if (key !== 'email') { a.target = '_blank'; a.rel = 'noopener'; }
    const optional = a.closest('[data-optional]');
    if (optional) optional.hidden = false;
  });

  if (cfg.reposPublic) {
    document.querySelectorAll('[data-when-public]').forEach((el) => { el.hidden = false; });
    document.querySelectorAll('a[data-repo]').forEach((a) => {
      a.href = cfg.repos[a.dataset.repo];
      a.target = '_blank';
      a.rel = 'noopener';
    });
    document.querySelectorAll('a[data-code-link]').forEach((a) => {
      const [repo, path] = a.dataset.codeLink.split(':');
      a.href = `${cfg.repos[repo]}/blob/main/${path}`;
      a.target = '_blank';
      a.rel = 'noopener';
    });
    document.querySelectorAll('[data-code]').forEach((el) => {
      const [repo, path] = el.dataset.code.split(':');
      const link = document.createElement('a');
      const kind = /\.[a-z]+$/i.test(path) ? 'blob' : 'tree';
      link.href = `${cfg.repos[repo]}/${kind}/main/${path}`;
      link.target = '_blank';
      link.rel = 'noopener';
      link.textContent = el.textContent;
      el.textContent = '';
      el.appendChild(link);
    });
  }

  // Barre de progression et section courante.
  const bar = document.querySelector('.progress');
  const navLinks = [...document.querySelectorAll('.topnav a')];
  const sections = navLinks.map((a) => document.querySelector(a.getAttribute('href'))).filter(Boolean);
  let ticking = false;
  const onScroll = () => {
    const max = document.documentElement.scrollHeight - innerHeight;
    bar.style.setProperty('--p', max > 0 ? (scrollY / max).toFixed(4) : 0);
    let current = null;
    for (const s of sections) if (s.getBoundingClientRect().top < innerHeight * 0.35) current = s.id;
    navLinks.forEach((a) => a.classList.toggle('is-current', a.getAttribute('href') === `#${current}`));
    ticking = false;
  };
  addEventListener('scroll', () => { if (!ticking) { requestAnimationFrame(onScroll); ticking = true; } }, { passive: true });
  onScroll();

  // Apparitions au défilement (le contenu reste visible sans IntersectionObserver).
  const revealTargets = document.querySelectorAll('[data-reveal-group], .arch__diagram, .tests');
  const countUp = (root) => {
    root.querySelectorAll('[data-count]').forEach((el) => {
      const end = Number(el.dataset.count);
      const start = performance.now();
      const step = (now) => {
        const k = Math.min(1, (now - start) / 900);
        el.textContent = Math.round(end * (1 - Math.pow(1 - k, 3)));
        if (k < 1) requestAnimationFrame(step);
      };
      requestAnimationFrame(step);
    });
  };
  const reduced = matchMedia('(prefers-reduced-motion: reduce)').matches;
  if ('IntersectionObserver' in window && !reduced) {
    const io = new IntersectionObserver((entries) => {
      for (const e of entries) {
        if (!e.isIntersecting) continue;
        e.target.classList.add('is-visible');
        if (e.target.classList.contains('tests')) countUp(e.target);
        io.unobserve(e.target);
      }
    }, { threshold: 0.18 });
    revealTargets.forEach((el) => io.observe(el));
  } else {
    revealTargets.forEach((el) => el.classList.add('is-visible'));
  }

  // Chapitres de la vidéo.
  const video = document.getElementById('demo-video');
  const chapterButtons = [...document.querySelectorAll('#chapters button')];
  const times = chapterButtons.map((b) => Number(b.dataset.t));
  chapterButtons.forEach((b) => b.addEventListener('click', () => {
    video.currentTime = Number(b.dataset.t);
    markChapter();
    video.play().catch(() => {});
  }));
  const markChapter = () => {
    let idx = 0;
    times.forEach((t, i) => { if (video.currentTime >= t - 0.2) idx = i; });
    chapterButtons.forEach((b, i) => {
      const active = i === idx;
      b.classList.toggle('is-active', active);
      if (active) b.setAttribute('aria-current', 'step'); else b.removeAttribute('aria-current');
    });
  };
  video.addEventListener('timeupdate', markChapter);
  video.addEventListener('seeked', markChapter);
  markChapter();

  // Visite des écrans (onglets accessibles au clavier).
  const tabs = [...document.querySelectorAll('.tour__tabs [role="tab"]')];
  const img = document.getElementById('tour-img');
  const url = document.getElementById('tour-url');
  const panel = document.getElementById('panel-tour');
  const zoom = document.getElementById('tour-zoom');
  const paths = {
    'catalogue': 'products', 'import-csv': 'stock-receipts/new', 'vente': 'sales/new',
    'creances': 'debts', 'creance-detail': 'creances/…', 'mouvements': 'stock-movements', 'utilisateurs': 'admin/users',
  };
  // Précharger les images pour une transition sans saut.
  tabs.forEach((t) => { const i = new Image(); i.src = `images/${t.dataset.shot}.webp`; });
  const select = (tab, focus) => {
    tabs.forEach((t) => {
      const on = t === tab;
      t.setAttribute('aria-selected', on);
      t.tabIndex = on ? 0 : -1;
    });
    panel.setAttribute('aria-labelledby', tab.id);
    url.textContent = `localhost:4200/${paths[tab.dataset.shot]}`;
    zoom.href = `images/${tab.dataset.shot}.webp`;
    img.classList.add('is-swapping');
    setTimeout(() => {
      img.src = `images/${tab.dataset.shot}.webp`;
      img.alt = tab.dataset.alt;
      img.classList.remove('is-swapping');
    }, reduced ? 0 : 180);
    if (focus) tab.focus();
  };
  tabs.forEach((t, i) => {
    t.tabIndex = t.getAttribute('aria-selected') === 'true' ? 0 : -1;
    t.addEventListener('click', () => select(t));
    t.addEventListener('keydown', (e) => {
      const keys = { ArrowDown: 1, ArrowRight: 1, ArrowUp: -1, ArrowLeft: -1 };
      if (e.key in keys) { e.preventDefault(); select(tabs[(i + keys[e.key] + tabs.length) % tabs.length], true); }
      if (e.key === 'Home') { e.preventDefault(); select(tabs[0], true); }
      if (e.key === 'End') { e.preventDefault(); select(tabs[tabs.length - 1], true); }
    });
  });
})();
