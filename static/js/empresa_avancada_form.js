// static/js/empresa_avancada_form.js
window.OneTech = window.OneTech || {};
OneTech.EmpresaForm = (function () {
  const SELECTOR_ROOT = '#form-empresa-avancada';
  const SELECTOR_TIPO = '[name="tipo_empresa"]';
  const SELECTOR_PF   = '#campos-pf';
  const SELECTOR_PJ   = '#campos-pj';

  function toggleSection(root, tipo) {
    const pf = root.querySelector(SELECTOR_PF);
    const pj = root.querySelector(SELECTOR_PJ);
    if (!pf || !pj) return;

    const showPF = tipo === 'PF';
    pf.classList.toggle('d-none', !showPF);
    pj.classList.toggle('d-none', showPF);

    // Habilita/Desabilita inputs para evitar submissão de dados ocultos
    pf.querySelectorAll('input,select,textarea').forEach(el => el.disabled = !showPF);
    pj.querySelectorAll('input,select,textarea').forEach(el => el.disabled = showPF);
  }

  function readTipo(selectEl) {
    if (!selectEl) return null;
    return (selectEl.value || '').trim().toUpperCase();
  }

  function init(rootEl) {
    if (!rootEl || rootEl.dataset.initialized === '1') return;
    rootEl.dataset.initialized = '1';

    const selectTipo = rootEl.querySelector(SELECTOR_TIPO);

    // Estado inicial (importante para a edição)
    toggleSection(rootEl, readTipo(selectTipo));

    // Listener para futuras mudanças
    if (selectTipo) {
      selectTipo.addEventListener('change', () => {
        toggleSection(rootEl, readTipo(selectTipo));
      });
    }

    // Lógica para abas Bootstrap, se aplicável
    rootEl.closest('.tab-content')?.addEventListener('shown.bs.tab', (ev) => {
      const target = ev.target?.getAttribute('data-bs-target') || '';
      if (target && target.includes('identificacao')) {
        toggleSection(rootEl, readTipo(selectTipo));
      }
    }, true);
  }

  function destroy(rootEl) {
    if (!rootEl) return;
    delete rootEl.dataset.initialized;
    // Lógica para remover listeners se necessário no futuro
  }

  return { init, destroy, SELECTOR_ROOT };
})();