function initGerenciarEventos() {
  const ROOT_SEL = "#gerenciar-eventos";
  const TBL_SEL  = "#tabela-mortalidade tbody";
  const API_URL  = "/producao/api/eventos/mortalidade/";

  const root = document.querySelector(ROOT_SEL);
  if (!root) {
    return; // Se a tela não está na página, não faz nada
  }
  if (root.dataset.bound === "1") {
    return; // Já inicializado
  }
  root.dataset.bound = "1";

  console.log("✅ initGerenciarEventos() executado.");

  // ---- helpers ----
  const q  = (sel, ctx=root) => ctx.querySelector(sel);
  const qa = (sel, ctx=root) => Array.from(ctx.querySelectorAll(sel));

  function sanitize(v) {
    if (!v) return "";
    const s = String(v).trim().toLowerCase();
    return (s === "todas" || s === "todos") ? "" : v;
  }

  function setLoading() {
    const tbody = q(TBL_SEL);
    if (tbody) tbody.innerHTML =
      `<tr><td colspan="99" class="text-center"><span class="badge bg-primary">Carregando dados...</span></td></tr>`;
  }
  function setError(msg) {
    const tbody = q(TBL_SEL);
    if (tbody) tbody.innerHTML =
      `<tr><td colspan="99" class="text-center"><span class="badge bg-danger">${msg || "Erro ao carregar"}</span></td></tr>`;
  }
  function render(items) {
    const tbody = q(TBL_SEL);
    if (!tbody) return;
    if (!items || !items.length) {
      tbody.innerHTML = `<tr><td colspan="99" class="text-center">Nenhum lote ativo na data.</td></tr>`;
      return;
    }
    const rows = items.map(it => `
      <tr data-lote="${it.lote_id}">
        <td>${it.tanque}</td>
        <td>${it.lote}</td>
        <td>${it.data_inicio}</td>
        <td class="text-end">${it.qtd_atual}</td>
        <td class="text-end">${it.peso_medio_g}</td>
        <td class="text-end">${it.biomassa_kg}</td>
        <td class="text-end"><input type="number" min="0" class="form-control form-control-sm input-mort" value="${it.qtd_mortalidade || 0}"></td>
        <td class="text-end">${(it.peso_medio_dia_g ?? "-")}</td>
        <td class="text-end">0.00</td>
      </tr>
    `).join("");
    tbody.innerHTML = rows;
  }

  async function carregarMortalidade() {
    try {
      const unidade = sanitize(q("#filtro-unidade")?.value);
      const linha   = sanitize(q("#filtro-linha")?.value);
      const fase    = sanitize(q("#filtro-fase")?.value);
      const data    = q("#filtro-data")?.value;

      const params = new URLSearchParams();
      if (unidade) params.set("unidade", unidade);
      if (linha)   params.set("linha_producao", linha);
      if (fase)    params.set("fase", fase);
      if (data)    params.set("data", data);

      setLoading();
      const url = `${API_URL}?${params.toString()}`;
      const doFetch = (window.fetchWithCreds || window.fetch).bind(window);
      const resp = await doFetch(url, { headers: { "X-Requested-With": "XMLHttpRequest" }, credentials: "include" });

      if (!resp.ok) {
        console.error("Falha API mortalidade:", resp.status, resp.statusText);
        setError("Falha na API");
        return;
      }

      const ct = (resp.headers.get("content-type") || "").toLowerCase();
      if (!ct.includes("application/json")) {
        const text = await resp.text();
        if (typeof window.isLikelyLoginHTML === "function" && window.isLikelyLoginHTML(text)) {
          window.location.href = `/accounts/login/?next=${encodeURIComponent(window.location.pathname)}`;
          return;
        }
        console.error("Conteúdo inesperado:", ct, text.slice(0, 200));
        setError("Resposta inesperada do servidor");
        return;
      }

      const dataJson = await resp.json();
      const items = Array.isArray(dataJson) ? dataJson : (dataJson.results || []);
      render(items);
    } catch (err) {
      console.error("Erro JS ao carregar mortalidade:", err);
      setError("Erro inesperado no JavaScript");
    }
  }

  // Liga os eventos
  ["#filtro-unidade", "#filtro-linha", "#filtro-fase", "#filtro-data"].forEach(sel => {
    const el = q(sel);
    if (el) el.addEventListener("change", carregarMortalidade);
  });

  qa('[data-bs-toggle="tab"]').forEach(el => {
    el.addEventListener("shown.bs.tab", (e) => {
      const target = e.target?.getAttribute("data-bs-target");
      if (target === "#pane-mortalidade") carregarMortalidade();
    });
  });

  // Carga inicial
  carregarMortalidade();
}
