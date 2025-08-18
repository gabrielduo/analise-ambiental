// static/js/fileUpload.js
// -------------------------------------------------------------------
// Nova lógica de upload:
// - Botão "Nova Visualização" > "Selecionar Modelo" (id: select-model-btn)
// - Input oculto (id: upload-file-input)
// - Valida nome do arquivo localmente: só 'qar.xls' ou 'met.xls'
// - Envia via POST /api/upload-model
// - Exibe mensagens claras de sucesso/erro
// - NÃO altera outras funcionalidades
// -------------------------------------------------------------------

(function () {
  const pickBtn   = document.getElementById("select-model-btn");
  const fileInput = document.getElementById("upload-file-input");

  if (!pickBtn || !fileInput) return;

  // Força aceitar só .xls
  fileInput.setAttribute("accept", ".xls");

  // Clique no botão abre o seletor
  pickBtn.addEventListener("click", () => fileInput.click());

  // Helper pra mensagens (substitua por seu toast caso exista)
  function notify(msg) {
    // você pode trocar por um toast da sua UI
    alert(msg);
  }

  // Reset do input após cada tentativa
  function resetInput() {
    try { fileInput.value = ""; } catch (_) {}
  }

  fileInput.addEventListener("change", async (e) => {
    const f = e.target.files && e.target.files[0];
    if (!f) return;

    const nameLower = (f.name || "").toLowerCase().trim();
    if (nameLower !== "qar.xls" && nameLower !== "met.xls") {
      notify("O arquivo deve se chamar exatamente 'qar.xls' ou 'met.xls'. Renomeie e tente de novo.");
      return resetInput();
    }

    // Envio
    try {
      const fd = new FormData();
      fd.append("file", f);

      const rsp = await fetch("/api/upload-model", {
        method: "POST",
        body: fd,
      });

      let data = null;
      try {
        data = await rsp.json();
      } catch {
        data = { ok: false, message: "Resposta inesperada do servidor." };
      }

      // Tratamento por status
      if (!rsp.ok || !data?.ok) {
        // Mensagem vinda do backend, se houver
        const msg = (data && data.message) ? data.message : `Falha ao enviar (${rsp.status}).`;
        notify("❌ " + msg);
        return resetInput();
      }

      // Sucesso
      const { tipo, year, month, dest_dir, message } = data;
      const line1 = message || `✔ ${String(tipo || "").toUpperCase()} validado e salvo.`;
      const line2 = dest_dir ? `Destino: ${dest_dir} (${month}/${year})` : "";
      notify([line1, line2].filter(Boolean).join("\n"));
      return resetInput();
    } catch (err) {
      notify("Erro inesperado no upload: " + err);
      return resetInput();
    }
  });
})();
