// static/js/criar_usuario.js
window.OneTech = window.OneTech || {};

OneTech.CriarUsuario = (function () {
  const SELECTOR_ROOT = '[data-page="criar_usuario"]';

  function clearFormErrors(form) {
    form.querySelectorAll('.is-invalid').forEach(el => el.classList.remove('is-invalid'));
    form.querySelectorAll('.invalid-feedback, .text-danger.small').forEach(el => el.textContent = '');
  }

  function displayFormErrors(form, errors) {
    if (!errors) return;

    for (const [field, errorList] of Object.entries(errors)) {
      const fieldName = field === 'password2' ? 'password2' : field;
      const input = form.querySelector(`[name="${fieldName}"]`);
      
      if (input) {
        input.classList.add('is-invalid');
        let errorContainer = input.closest('.mb-3')?.querySelector('.invalid-feedback, .text-danger.small');
        if (!errorContainer) {
            errorContainer = document.createElement('div');
            errorContainer.className = 'invalid-feedback d-block';
            input.parentNode.appendChild(errorContainer);
        }
        errorContainer.textContent = errorList.join(' ');
      } else if (field === '__all__') {
        if(typeof mostrarMensagem === 'function') {
            mostrarMensagem('danger', 'Erro no Formulário', errorList.join(' '));
        }
      }
    }
  }

  async function handleFormSubmit(event) {
    console.log('[DEBUG] handleFormSubmit INICIADO.');
    event.preventDefault();
    event.stopPropagation();

    const form = event.currentTarget;
    const submitButton = form.querySelector('button[type="submit"], input[type="submit"]');
    console.log('[DEBUG] Formulário e botão encontrados.', form, submitButton);

    clearFormErrors(form);

    if (submitButton) {
      submitButton.disabled = true;
      submitButton.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Salvando...';
    } else {
      console.warn('[DEBUG] Nenhum botão submit encontrado dentro do formulário criar_usuario.');
    }

    try {
      const result = await submitAjaxForm(form);
      console.log('[DEBUG] Resposta AJAX recebida:', result);

      if (result.success === false) {
        console.log('[DEBUG] Resposta de falha (validação).');
        if (result.errors) {
          displayFormErrors(form, result.errors);
        }
        if (result.message) {
          mostrarMensagem('danger', 'Erro de Validação', result.message);
        }
      } else if (result.redirect_url) {
        console.log('[DEBUG] Resposta de sucesso com redirecionamento.');
        if (result.message) {
          sessionStorage.setItem('flashMessage', JSON.stringify({
            type: 'success',
            message: result.message,
          }));
        }
        window.location.href = result.redirect_url;
      } else {
        console.log('[DEBUG] Resposta de sucesso sem redirecionamento.');
        if (result.message) {
          mostrarMensagem('success', 'Sucesso', result.message);
        }
      }
    } catch (error) {
      console.error('❌ [DEBUG] Erro CAPTURADO dentro do handleFormSubmit:', error);
      mostrarMensagem('danger', 'Erro Inesperado', 'Ocorreu uma falha de comunicação. Tente novamente.');
    } finally {
      console.log('[DEBUG] Bloco finally executado, reabilitando botão.');
      if (submitButton) {
        submitButton.disabled = false;
        submitButton.innerHTML = '<i class="bi bi-check-circle"></i> Salvar';
      }
    }
  }

  function init(rootEl) {
    console.log('[DEBUG] OneTech.CriarUsuario.init executado.', rootEl);
    const form = rootEl.querySelector('#form-criar-usuario');
    console.log('[DEBUG] Formulário encontrado:', form);
    if (!form || form.dataset.criarUsuarioBound) {
      console.log('[DEBUG] Formulário já inicializado ou não encontrado. Abortando.');
      return;
    }
    form.dataset.criarUsuarioBound = 'true';
    form.dataset.skipGlobal = '1';   // ignora o handler global
    console.log('[DEBUG] Adicionando listener de submit ao formulário.');
    form.addEventListener('submit', handleFormSubmit);
  }

  function destroy(rootEl) {
    const form = rootEl.querySelector('#form-criar-usuario');
    if (form && form.dataset.criarUsuarioBound) {
      form.removeEventListener('submit', handleFormSubmit);
      delete form.dataset.criarUsuarioBound;
      delete form.dataset.skipGlobal;
    }
  }

  return {
    init,
    destroy,
    SELECTOR_ROOT,
  };
})();