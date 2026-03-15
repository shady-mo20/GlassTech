/*
  Small client-side helpers.

  We intentionally keep JS minimal because:
  - i18n is server-rendered via Jinja + session language.
  - The Envato template already provides most UI behavior.
*/

(function () {
  // A11y/UX: ensure external image lightbox links have a sensible cursor
  document.querySelectorAll("a.image-link").forEach(function (a) {
    a.style.cursor = "zoom-in";
  });
})();

