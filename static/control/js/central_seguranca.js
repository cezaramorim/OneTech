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


        friendlyRequestErrorMessage: function (status, serverMessage) {
      var msg = (serverMessage || '').trim();
      if (msg) return msg;
      if (status === 401) return 'Sessao expirada. Faca login novamente.';
      if (status === 403) return 'Acesso negado. Voce nao tem permissao para esta acao.';
      if (status === 404) return 'Recurso nao encontrado.';
      if (status === 408) return 'A requisicao expirou. Tente novamente.';
      if (status === 429) return 'Muitas tentativas em pouco tempo. Aguarde e tente novamente.';
      if (status === 500) return 'Erro interno do servidor. Tente novamente em instantes.';
      if (status === 502 || status === 503 || status === 504) return 'Servico temporariamente indisponivel. Tente novamente em instantes.';
      return 'Nao foi possivel concluir a requisicao no momento.';
    },
    postJson: async function (url, payload) {
      var response;
      try {
        response = await fetch(url, {
          method: 'POST',
          credentials: 'same-origin',
          headers: {
            'Content-Type': 'application/json',
            'X-Requested-With': 'XMLHttpRequest',
            'X-CSRFToken': SecurityCenter.getCsrfToken()
          },
          body: JSON.stringify(payload || {})
        });
      } catch (err) {
        if (err && err.name === 'AbortError') {
          throw new Error('A requisicao demorou demais e expirou. Tente novamente.');
        }
        if (typeof navigator !== 'undefined' && navigator && navigator.onLine === false) {
          throw new Error('Sem conexao com a internet. Verifique sua rede e tente novamente.');
        }
        throw new Error('Nao foi possivel conectar ao servidor. Verifique se o sistema esta online e tente novamente.');
      }

      var data = {};
      try {
        data = await response.json();
      } catch (_) {
        data = { success: false, message: 'Resposta invalida do servidor.' };
      }

      if (!response.ok) {
        var serverMsg = data.message || data.error || data.detail || '';
        throw new Error(SecurityCenter.friendlyRequestErrorMessage(response.status, serverMsg));
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

          var confirmUsername = '';
          if (window.Swal) {
            var result = await window.Swal.fire({
              title: 'Confirmacao reforcada',
              text: 'Digite o login do usuario para confirmar o encerramento de todas as sessoes.',
              input: 'text',
              inputPlaceholder: username,
              icon: 'warning',
              showCancelButton: true,
              confirmButtonText: 'Encerrar sessoes',
              cancelButtonText: 'Cancelar',
              preConfirm: function (value) {
                var typed = (value || '').trim();
                if (!typed || typed.toLowerCase() !== username.toLowerCase()) {
                  window.Swal.showValidationMessage('Confirmacao invalida. Digite: ' + username);
                  return false;
                }
                return typed;
              }
            });
            if (!result.isConfirmed) return;
            confirmUsername = (result.value || '').trim();
          } else {
            var typedFallback = (window.prompt('Digite o login para confirmar: ' + username) || '').trim();
            if (!typedFallback || typedFallback.toLowerCase() !== username.toLowerCase()) {
              SecurityCenter.notify('error', 'Confirmacao invalida.');
              return;
            }
            confirmUsername = typedFallback;
          }

          btn.disabled = true;
          try {
            var data = await SecurityCenter.postJson(url, { user_id: userId, confirm_username: confirmUsername });
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



    bindToggleLockButtons: function (root) {
      var url = root.dataset.userLockUrl;
      if (!url) return;

      root.querySelectorAll('[data-action="toggle-lock"]').forEach(function (btn) {
        btn.addEventListener('click', async function () {
          var userId = btn.dataset.userId;
          var username = btn.dataset.username || 'usuario';
          var mode = (btn.dataset.mode || 'lock').toLowerCase();
          var minutes = parseInt(btn.dataset.minutes || '15', 10);
          if (!userId) return;

          var confirmUsername = '';
          if (window.Swal) {
            var title = mode === 'unlock' ? 'Confirmar desbloqueio' : 'Confirmar bloqueio temporario';
            var result = await window.Swal.fire({
              title: title,
              text: 'Digite o login do usuario para confirmar a acao.',
              input: 'text',
              inputPlaceholder: username,
              icon: 'warning',
              showCancelButton: true,
              confirmButtonText: mode === 'unlock' ? 'Desbloquear' : 'Bloquear',
              cancelButtonText: 'Cancelar',
              preConfirm: function (value) {
                var typed = (value || '').trim();
                if (!typed || typed.toLowerCase() !== username.toLowerCase()) {
                  window.Swal.showValidationMessage('Confirmacao invalida. Digite: ' + username);
                  return false;
                }
                return typed;
              }
            });
            if (!result.isConfirmed) return;
            confirmUsername = (result.value || '').trim();
          } else {
            var typedFallback = (window.prompt('Digite o login para confirmar: ' + username) || '').trim();
            if (!typedFallback || typedFallback.toLowerCase() !== username.toLowerCase()) {
              SecurityCenter.notify('error', 'Confirmacao invalida.');
              return;
            }
            confirmUsername = typedFallback;
          }

          btn.disabled = true;
          try {
            var data = await SecurityCenter.postJson(url, {
              user_id: userId,
              mode: mode,
              minutes: minutes,
              confirm_username: confirmUsername
            });
            SecurityCenter.notify('success', data.message || 'Operacao concluida com sucesso.');
            if (typeof loadAjaxContent === 'function') {
              loadAjaxContent(window.location.pathname);
            } else {
              window.location.reload();
            }
          } catch (error) {
            SecurityCenter.notify('error', error.message || 'Falha ao alterar bloqueio do usuario.');
            btn.disabled = false;
          }
        });
      });
    },


    bindToggleTenantQuarantineButtons: function (root) {
      var url = root.dataset.tenantQuarantineUrl;
      if (!url) return;

      root.querySelectorAll('[data-action="toggle-tenant-quarantine"]').forEach(function (btn) {
        btn.addEventListener('click', async function () {
          var tenantSlug = btn.dataset.tenantSlug || '';
          var mode = (btn.dataset.mode || 'enable').toLowerCase();
          if (!tenantSlug) return;

          var confirmSlug = '';
          var reason = '';
          if (window.Swal) {
            var result = await window.Swal.fire({
              title: mode === 'disable' ? 'Remover quarentena do tenant' : 'Ativar quarentena do tenant',
              text: 'Digite o slug do tenant para confirmar.',
              input: 'text',
              inputPlaceholder: tenantSlug,
              icon: 'warning',
              showCancelButton: true,
              confirmButtonText: mode === 'disable' ? 'Remover' : 'Ativar',
              cancelButtonText: 'Cancelar',
              preConfirm: function (value) {
                var typed = (value || '').trim();
                if (!typed || typed.toLowerCase() !== tenantSlug.toLowerCase()) {
                  window.Swal.showValidationMessage('Confirmacao invalida. Digite: ' + tenantSlug);
                  return false;
                }
                return typed;
              }
            });
            if (!result.isConfirmed) return;
            confirmSlug = (result.value || '').trim();
          } else {
            var typedFallback = (window.prompt('Digite o slug para confirmar: ' + tenantSlug) || '').trim();
            if (!typedFallback || typedFallback.toLowerCase() !== tenantSlug.toLowerCase()) {
              SecurityCenter.notify('error', 'Confirmacao invalida.');
              return;
            }
            confirmSlug = typedFallback;
          }

          btn.disabled = true;
          try {
            var data = await SecurityCenter.postJson(url, {
              tenant_slug: tenantSlug,
              mode: mode,
              reason: reason,
              confirm_slug: confirmSlug
            });
            SecurityCenter.notify('success', data.message || 'Operacao de quarentena concluida.');
            if (typeof loadAjaxContent === 'function') {
              loadAjaxContent(window.location.pathname);
            } else {
              window.location.reload();
            }
          } catch (error) {
            SecurityCenter.notify('error', error.message || 'Falha ao alterar quarentena do tenant.');
            btn.disabled = false;
          }
        });
      });
    },


    bindDependencyAuditButton: function (root) {
      var url = root.dataset.dependencyAuditUrl;
      if (!url) return;

      var output = root.querySelector('[data-role="dependency-audit-output"]');
      var btn = root.querySelector('[data-action="run-dependency-audit"]');
      if (!btn) return;

      btn.addEventListener('click', async function () {
        btn.disabled = true;
        if (output) {
          output.textContent = 'Executando auditoria de dependencias...';
        }

        try {
          var data = await SecurityCenter.postJson(url, {});
          SecurityCenter.notify(data.success ? 'success' : 'error', data.message || 'Auditoria de dependencias concluida.');
          if (output) {
            output.textContent = data.output || 'Sem saida.';
          }
          if (typeof loadAjaxContent === 'function') {
            loadAjaxContent(window.location.pathname);
          }
        } catch (error) {
          SecurityCenter.notify('error', error.message || 'Falha ao executar auditoria de dependencias.');
          if (output) {
            output.textContent = 'Falha ao executar auditoria de dependencias.';
          }
        } finally {
          btn.disabled = false;
        }
      });
    },
    bindMatrixAuditButton: function (root) {
      var url = root.dataset.matrixAuditUrl;
      if (!url) return;

      var output = root.querySelector('[data-role="matrix-audit-output"]');
      var btn = root.querySelector('[data-action="run-matrix-audit"]');
      if (!btn) return;

      btn.addEventListener('click', async function () {
        btn.disabled = true;
        if (output) {
          output.textContent = 'Executando auditoria matriz x menu...';
        }

        try {
          var data = await SecurityCenter.postJson(url, {});
          SecurityCenter.notify(data.success ? 'success' : 'warning', data.message || 'Auditoria matriz concluida.');
          if (output) {
            output.textContent = data.output || 'Sem saida.';
          }

          var statusEl = root.querySelector('[data-role="matrix-audit-status"]');
          var ranAtEl = root.querySelector('[data-role="matrix-audit-ran-at"]');
          if (statusEl && data.snapshot) {
            statusEl.classList.remove('bg-success', 'bg-danger', 'bg-secondary');
            statusEl.classList.add(data.snapshot.success ? 'bg-success' : 'bg-danger');
            statusEl.textContent = data.snapshot.success ? 'Consistente' : 'Divergente';
          }
          if (ranAtEl && data.snapshot && data.snapshot.ran_at) {
            ranAtEl.textContent = data.snapshot.ran_at_display || data.snapshot.ran_at || '-';
          }
        } catch (error) {
          SecurityCenter.notify('error', error.message || 'Falha ao executar auditoria matriz x menu.');
          if (output) {
            output.textContent = 'Falha ao executar auditoria matriz x menu.';
          }
        } finally {
          btn.disabled = false;
        }
      });
    },    init: function (root) {
      if (!root || root.dataset.securityInit === '1') return;
      root.dataset.securityInit = '1';
      SecurityCenter.bindAuditButtons(root);
      SecurityCenter.bindForceLogoutButtons(root);
      SecurityCenter.bindToggleLockButtons(root);
      SecurityCenter.bindToggleTenantQuarantineButtons(root);
      SecurityCenter.bindDependencyAuditButton(root);
      SecurityCenter.bindMatrixAuditButton(root);
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






