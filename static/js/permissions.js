// static/js/permissions.js
window.OneTech = window.OneTech || {};

OneTech.Permissions = (function () {

  const SELECTOR_ROOT = '[data-page="gerenciar_permissoes"]';

  function init(rootEl) {
    if (!rootEl || rootEl.dataset.initialized === 'true') return;
    rootEl.dataset.initialized = 'true';

    const permissionGroupToggles = rootEl.querySelectorAll('.permission-group-toggle');
    const permissionItems = rootEl.querySelectorAll('.permission-item');

    // Lógica Pai -> Filho
    permissionGroupToggles.forEach(toggle => {
        toggle.addEventListener('change', function() {
            const parentDiv = this.closest('[data-permission-group]');
            if (parentDiv) {
                const items = parentDiv.querySelectorAll('.permission-item');
                items.forEach(item => {
                    item.checked = this.checked;
                });
            }
        });
    });

    // Lógica Filho -> Pai
    permissionItems.forEach(item => {
        item.addEventListener('change', function () {
            const parentDiv = this.closest('[data-permission-group]');
            if (parentDiv) {
                const groupToggle = parentDiv.querySelector('.permission-group-toggle');
                const allItemsInGroup = parentDiv.querySelectorAll('.permission-item');
                const allCheckedInGroup = parentDiv.querySelectorAll('.permission-item:checked');

                if (groupToggle) {
                    const total = allItemsInGroup.length;
                    const marcados = allCheckedInGroup.length;

                    if (marcados === total && total > 0) {
                        groupToggle.checked = true;
                        groupToggle.indeterminate = false;
                    } else if (marcados === 0) {
                        groupToggle.checked = false;
                        groupToggle.indeterminate = false;
                    } else {
                        groupToggle.checked = false;
                        groupToggle.indeterminate = true;
                    }
                }
            }
        });
    });

    // Inicializa o estado dos toggles de grupo ao carregar a página
    permissionGroupToggles.forEach(toggle => {
        const parentDiv = toggle.closest('[data-permission-group]');
        if (parentDiv) {
            const allItemsInGroup = parentDiv.querySelectorAll('.permission-item');
            const allCheckedInGroup = parentDiv.querySelectorAll('.permission-item:checked');
            const total = allItemsInGroup.length;
            const marcados = allCheckedInGroup.length;

            if (marcados === total && total > 0) {
                toggle.checked = true;
                toggle.indeterminate = false;
            } else if (marcados === 0) {
                toggle.checked = false;
                toggle.indeterminate = false;
            } else {
                toggle.checked = false;
                toggle.indeterminate = true;
            }
        }
    });
  }

  return { init, SELECTOR_ROOT };
})();