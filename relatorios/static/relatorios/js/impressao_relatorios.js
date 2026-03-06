window.OneTech = window.OneTech || {};

OneTech.ImpressaoRelatorios = (function () {
  const SELECTOR_ROOT = '[data-page="impressao-relatorios"]';

  function init(rootEl) {
    const root = rootEl || document.querySelector(SELECTOR_ROOT);
    if (!root || root.dataset.bound === '1') return;
    root.dataset.bound = '1';

    const menu = root.querySelector('#lista-relatorios-impressao');
    const buttons = Array.from(root.querySelectorAll('[data-report]'));
    const panels = {
      tanques: root.querySelector('#relatorio-form-tanques'),
      empresas: root.querySelector('#relatorio-form-empresas'),
    };

    if (!menu || buttons.length === 0) return;

    const showPanel = (reportKey) => {
      Object.entries(panels).forEach(([key, panel]) => {
        if (!panel) return;
        panel.classList.toggle('d-none', key !== reportKey);
      });
      buttons.forEach((btn) => {
        btn.classList.toggle('active', btn.dataset.report === reportKey);
      });
    };

    menu.addEventListener('click', (event) => {
      const btn = event.target.closest('[data-report]');
      if (!btn) return;
      showPanel(btn.dataset.report);
    });

    showPanel('tanques');
  }

  function destroy(rootEl) {
    const root = rootEl || document.querySelector(SELECTOR_ROOT);
    if (!root) return;
    delete root.dataset.bound;
  }

  return { init, destroy, SELECTOR_ROOT };
})();


(function(){
  const boot = () => {
    if (window.OneTech && window.OneTech.ImpressaoRelatorios) {
      const root = document.querySelector(window.OneTech.ImpressaoRelatorios.SELECTOR_ROOT);
      if (root) window.OneTech.ImpressaoRelatorios.init(root);
    }
  };
  document.addEventListener('DOMContentLoaded', boot);
  document.addEventListener('ajaxContentLoaded', boot);
})();
