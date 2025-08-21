// static/js/fileUpload.js
// -------------------------------------------------------------------
// Fluxo de upload com senha:
// 1) Clique no botão -> pede senha -> POST /api/upload-auth
// 2) Recebe token curto -> abre seletor de arquivo
// 3) Envia /api/upload-model com Authorization: Bearer <token>
// Observação: mantém a validação original (somente 'qar.xls' ou 'met.xls').
// -------------------------------------------------------------------

(function () {
  const pickBtn   = document.getElementById("select-model-btn"); // troque para "file-upload-trigger" se for o teu id real
  const fileInput = document.getElementById("upload-file-input");

  if (!pickBtn || !fileInput) return;

  // Força aceitar só .xls (mantido como estava)
  fileInput.setAttribute("accept", ".xls");

  // Token temporário para upload (expira conforme back)
  let uploadToken = null;

  // Helper de mensagens (troque por toast/snackbar se tiver)
  function notify(msg) {
    alert(msg);
  }

  // Reset do input após cada tentativa
  function resetInput() {
    try { fileInput.value = ""; } catch (_) {}
  }

  // Pede senha e obtém token do backend
  async function askPasswordAndGetToken() {
    const pwd = window.prompt("Digite a senha de upload:");
    if (pwd === null) return null; // cancelado
    try {
      const resp = await fetch("/api/upload-auth", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ password: pwd }),
      });
      const data = await resp.json();
      if (!resp.ok || !data?.ok) {
        notify(data?.message || "Senha inválida.");
        return null;
      }
      return data.token;
    } catch (e) {
      notify("Falha ao autenticar: " + e);
      return null;
    }
  }

  // Clique no botão: primeiro autentica, depois abre seletor
  pickBtn.addEventListener("click", async (ev) => {
    ev.preventDefault();
    // Se não houver token, ou se quiser sempre renovar, peça novamente:
    if (!uploadToken) {
      uploadToken = await askPasswordAndGetToken();
    }
    if (!uploadToken) return; // cancelado ou falha

    // Autenticado -> abrir seletor
    fileInput.click();
  });

  // Validação do nome do arquivo (mantida)
  function validateLocalFileName(file) {
    const nameLower = (file.name || "").toLowerCase().trim();
    return nameLower === "qar.xls" || nameLower === "met.xls";
  }

  // Envio do arquivo com Authorization: Bearer <token>
  fileInput.addEventListener("change", async (e) => {
    const f = e.target.files && e.target.files[0];
    if (!f) return;

    if (!uploadToken) {
      notify("Sessão de upload expirada. Clique em 'Selecionar Modelo' novamente e informe a senha.");
      return resetInput();
    }

    if (!validateLocalFileName(f)) {
      notify("O arquivo deve se chamar exatamente 'qar.xls' ou 'met.xls'. Renomeie e tente de novo.");
      return resetInput();
    }

    try {
      const fd = new FormData();
      fd.append("file", f);

      let rsp = await fetch("/api/upload-model", {
        method: "POST",
        headers: { "Authorization": `Bearer ${uploadToken}` },
        body: fd,
      });

      // Se o token expirou, tenta 1x reautenticar e reenviar
      if (rsp.status === 401) {
        uploadToken = await askPasswordAndGetToken();
        if (!uploadToken) {
          resetInput();
          return;
        }
        rsp = await fetch("/api/upload-model", {
          method: "POST",
          headers: { "Authorization": `Bearer ${uploadToken}` },
          body: fd,
        });
      }

      let data = null;
      try {
        data = await rsp.json();
      } catch {
        data = { ok: false, message: "Resposta inesperada do servidor." };
      }

      if (!rsp.ok || data?.ok === false) {
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
