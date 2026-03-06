(function () {
  "use strict";

  // Garante que o namespace global exista
  window.OneTech = window.OneTech || {};

  // Define o módulo para esta página
  window.OneTech.ReprocessarLotes = {
    SELECTOR_ROOT: '[data-page="producao-reprocessar-lotes"]',

    init(root) {
      if (!root) return;

      // Previne que o script seja inicializado múltiplas vezes no mesmo elemento
      if (root.dataset.reprocessarBound) return;
      root.dataset.reprocessarBound = "true";

      const form = root.querySelector("#form-reprocessar-lotes");
      if (!form) return;

      const statusEl = root.querySelector("#reprocessar-status");
      const logEl = root.querySelector("#reprocessar-log");
      const btnExecutar = root.querySelector("#btn-executar");
      const btnCopiar = root.querySelector("#btn-copiar-log");

      console.log("Botão Copiar Log encontrado:", btnCopiar); // DEBUG

      const setStatus = (text, kind = "secondary") => {
        if (statusEl) {
            statusEl.innerHTML = `<span class="badge text-bg-${kind}">${text}</span>`;
        }
      };

      const setLog = (text) => {
        if (logEl) logEl.textContent = text || "";
      };

      const setProcessingUI = (isProcessing) => {
        if (btnExecutar) btnExecutar.disabled = isProcessing;
        
        if (isProcessing) {
          // Apenas desabilita o botão de copiar quando um NOVO processo se inicia.
          if (btnCopiar) btnCopiar.disabled = true;
          setStatus("Processando...", "info");
          setLog("Iniciando execução...");
        }
      };

      const getCSRFToken = () => {
        // Procura o token dentro do formulário específico
        const csrfInput = form.querySelector('input[name="csrfmiddlewaretoken"]');
        return csrfInput ? csrfInput.value : "";
      };

      form.addEventListener("submit", async (e) => {
        e.preventDefault();
        const url = form.getAttribute("action");
        if (!url) {
            setStatus("Erro de configuração", "danger");
            setLog("O atributo 'action' do formulário não foi encontrado.");
            return;
        }

        setProcessingUI(true);

        try {
          const response = await fetch(url, {
            method: "POST",
            headers: {
              "X-CSRFToken": getCSRFToken(),
              "X-Requested-With": "XMLHttpRequest",
            },
            body: new FormData(form),
          });

          const data = await response.json();

          if (!response.ok) {
            throw new Error(data.message || `Erro HTTP ${response.status}`);
          }
          
          setStatus(data.dry_run ? "Simula\u00e7\u00e3o Conclu\u00edda" : "Conclu\u00eddo", "success");
          setLog(data.log || "Processo finalizado sem log de retorno.");
          if (btnCopiar) btnCopiar.disabled = false;

        } catch (error) {
          console.error("Erro ao reprocessar lote:", error);
          setStatus("Erro na Requisição", "danger");
          setLog(`Falha na comunicação com o servidor. Detalhes: ${error.message}`);
        } finally {
          setProcessingUI(false);
          if (btnExecutar) btnExecutar.disabled = false;
        }
      });

       if (btnCopiar) {
            btnCopiar.addEventListener("click", async () => {
                const text = logEl?.textContent || "";
                if (!text) return;
                try {
                    await navigator.clipboard.writeText(text);
                    setStatus("Log copiado", "success");
                } catch (err) {
                    setStatus("Falha ao copiar", "warning");
                }
            });
        }
    },
  };
})();
