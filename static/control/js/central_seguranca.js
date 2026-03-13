(function () {
  'use strict';

  window.OneTech = window.OneTech || {};

  var SecurityCenter = {
    SELECTOR_ROOT: '[data-page="central_seguranca"]',

    getCsrfToken: function () {
      var c = document.cookie.split(';').find(function (x) { return x.trim().startsWith('csrftoken='); });
      return c ? c.split('=')[1] : '';
    },

    notify: function (type, message) {
      if (window.mostrarMensagem) {
        window.mostrarMensagem(type, message);
        return;
      }
      console.log(type + ': ' + message);
    },

    postJson: async function (url, payload) {
      var response = await fetch(url, {
        method: 'POST',
        credentials: 'same-origin',
        headers: {
          'Content-Type': 'application/json',
          'X-Requested-With': 'XMLHttpRequest',
          'X-CSRFToken': SecurityCenter.getCsrfToken()
        },
        body: JSON.stringify(payload || {})
      });

      var data = {};
      try {
        data = await response.json();
      } catch (_) {
        data = { success: false, message: 'Resposta invalida do servidor.' };
      }

      if (!response.ok) {
        var msg = data.message || ('Falha HTTP ' + response.status);
        throw new Error(msg);
      }

      return data;
    },

    bindAuditButtons: function (root) {
      var output = root.querySelector('[data-role="audit-output"]');
      root.querySelectorAll('[data-action="run-audit"]').forEach(function (btn) {
        btn.addEventListener('click', async function () {
          var mode = btn.dataset.mode || 'normal';
          var auditUrl = root.dataset.auditUrl;
          if (!auditUrl) return;

          btn.disabled = true;
          if (output) {
            output.textContent = 'Executando auditoria ' + mode + '...';
          }
          try {
            var data = await SecurityCenter.postJson(auditUrl, { mode: mode });
            SecurityCenter.notify('success', data.message || ('Auditoria ' + mode + ' concluida.'));
            if (output) {
              output.textContent = data.output || 'Sem saida.';
            }
          } catch (error) {
            SecurityCenter.notify('error', error.message || 'Falha ao executar auditoria.');
          } finally {
            btn.disabled = false;
          }
        });
      });
    },

    bindForceLogoutButtons: function (root) {
      var url = root.dataset.forceLogoutUrl;
      if (!url) return;

      root.querySelectorAll('[data-action="force-logout"]').forEach(function (btn) {
        btn.addEventListener('click', async function () {
          var userId = btn.dataset.userId;
          var username = btn.dataset.username || 'usuario';
          if (!userId) return;

          var confirmed = true;
          if (window.Swal) {
            var result = await window.Swal.fire({
              title: 'Encerrar sessoes?',
              text: 'Deseja encerrar as sessoes ativas de ' + username + '?',
              icon: 'warning',
              showCancelButton: true,
              confirmButtonText: 'Sim, encerrar',
              cancelButtonText: 'Cancelar'
            });
            confirmed = !!result.isConfirmed;
          }

          if (!confirmed) return;

          btn.disabled = true;
          try {
            var data = await SecurityCenter.postJson(url, { user_id: userId });
            SecurityCenter.notify('success', data.message || 'Sessoes encerradas com sucesso.');
            if (typeof loadAjaxContent === 'function') {
              loadAjaxContent(window.location.pathname);
            } else {
              window.location.reload();
            }
          } catch (error) {
            SecurityCenter.notify('error', error.message || 'Falha ao encerrar sessoes.');
            btn.disabled = false;
          }
        });
      });
    },

    init: function (root) {
      if (!root || root.dataset.securityInit === '1') return;
      root.dataset.securityInit = '1';
      SecurityCenter.bindAuditButtons(root);
      SecurityCenter.bindForceLogoutButtons(root);
    }
  };

  function bootstrap() {
    var root = document.querySelector(SecurityCenter.SELECTOR_ROOT);
    if (root) {
      SecurityCenter.init(root);
    }
  }

  window.OneTech.SecurityCenter = SecurityCenter;
  bootstrap();
  document.addEventListener('DOMContentLoaded', bootstrap);
  document.addEventListener('ajaxContentLoaded', bootstrap);
})();

