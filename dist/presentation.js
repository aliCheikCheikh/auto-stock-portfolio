// Keep content visible when motion is reduced or observation is unsupported.
if (!window.matchMedia('(prefers-reduced-motion: reduce)').matches && 'IntersectionObserver' in window) {
  const observer = new IntersectionObserver((entries) => {
    for (const entry of entries) {
      if (!entry.isIntersecting) continue;
      entry.target.classList.remove('reveal-pending');
      entry.target.classList.add('reveal-ready');
      observer.unobserve(entry.target);
    }
  }, { threshold: 0.08 });
  for (const section of document.querySelectorAll('.feature-list article, .decisions article')) {
    section.classList.add('reveal-pending');
    observer.observe(section);
  }
}
