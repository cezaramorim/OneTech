// static/js/permissions.js
window.OneTech = window.OneTech || {};

OneTech.Permissions = (function () {
  const SELECTOR_ROOT = '[data-page="gerenciar_permissoes"]';

  function setToggleState(toggle, items) {
    const total = items.length;
    const marcados = Array.from(items).filter(item => item.checked).length;

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

  function updateEntityState(entityEl) {
    const entityToggle = entityEl.querySelector('.permission-entity-toggle');
    const items = entityEl.querySelectorAll('.permission-item');
    if (entityToggle) setToggleState(entityToggle, items);
  }

  function updateGroupState(groupEl) {
    const groupToggle = groupEl.querySelector('.permission-group-toggle');
    const items = groupEl.querySelectorAll('.permission-item');
    if (groupToggle) setToggleState(groupToggle, items);
  }

  function toggleApp(groupEl, forceOpen) {
    const body = groupEl.querySelector('[data-permission-group-body]');
    const trigger = groupEl.querySelector('[data-permission-group-trigger]');
    if (!body || !trigger) return;

    const willOpen = typeof forceOpen === 'boolean' ? forceOpen : body.classList.contains('d-none');
    body.classList.toggle('d-none', !willOpen);
    trigger.setAttribute('aria-expanded', willOpen ? 'true' : 'false');
  }

  function toggleEntity(entityEl, forceOpen) {
    const body = entityEl.querySelector('[data-permission-entity-body]');
    const trigger = entityEl.querySelector('[data-permission-entity-trigger]');
    if (!body || !trigger) return;

    const willOpen = typeof forceOpen === 'boolean' ? forceOpen : body.classList.contains('d-none');
    body.classList.toggle('d-none', !willOpen);
    trigger.setAttribute('aria-expanded', willOpen ? 'true' : 'false');
  }

  function closeOtherApps(rootEl, currentGroupEl) {
    rootEl.querySelectorAll('[data-permission-group]').forEach(groupEl => {
      if (groupEl !== currentGroupEl) {
        toggleApp(groupEl, false);
      }
    });
  }

  function init(rootEl) {
    if (!rootEl || rootEl.dataset.initialized === 'true') return;
    rootEl.dataset.initialized = 'true';

    const permissionGroups = rootEl.querySelectorAll('[data-permission-group]');
    const permissionEntities = rootEl.querySelectorAll('[data-permission-entity]');
    const permissionItems = rootEl.querySelectorAll('.permission-item');

    rootEl.querySelectorAll('.permission-group-toggle').forEach(toggle => {
      toggle.addEventListener('change', function () {
        const groupEl = this.closest('[data-permission-group]');
        if (!groupEl) return;

        groupEl.querySelectorAll('.permission-item').forEach(item => {
          item.checked = this.checked;
        });
        groupEl.querySelectorAll('[data-permission-entity]').forEach(updateEntityState);
        updateGroupState(groupEl);
      });
    });

    rootEl.querySelectorAll('.permission-entity-toggle').forEach(toggle => {
      toggle.addEventListener('change', function () {
        const entityEl = this.closest('[data-permission-entity]');
        if (!entityEl) return;

        entityEl.querySelectorAll('.permission-item').forEach(item => {
          item.checked = this.checked;
        });
        updateEntityState(entityEl);

        const groupEl = entityEl.closest('[data-permission-group]');
        if (groupEl) updateGroupState(groupEl);
      });
    });

    rootEl.querySelectorAll('[data-permission-group-trigger]').forEach(trigger => {
      trigger.addEventListener('click', function () {
        const groupEl = this.closest('[data-permission-group]');
        if (!groupEl) return;

        const body = groupEl.querySelector('[data-permission-group-body]');
        const isClosed = body.classList.contains('d-none');
        closeOtherApps(rootEl, groupEl);
        toggleApp(groupEl, isClosed);
      });
    });

    rootEl.querySelectorAll('[data-permission-entity-trigger]').forEach(trigger => {
      trigger.addEventListener('click', function () {
        const entityEl = this.closest('[data-permission-entity]');
        if (entityEl) toggleEntity(entityEl);
      });
    });

    permissionItems.forEach(item => {
      item.addEventListener('change', function () {
        const entityEl = this.closest('[data-permission-entity]');
        if (entityEl) updateEntityState(entityEl);

        const groupEl = this.closest('[data-permission-group]');
        if (groupEl) updateGroupState(groupEl);
      });
    });

    permissionEntities.forEach(entityEl => updateEntityState(entityEl));
    permissionGroups.forEach(groupEl => updateGroupState(groupEl));
  }

  return { init, SELECTOR_ROOT };
})();
