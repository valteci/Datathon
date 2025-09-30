function renderEmptyRow(message) {
  const tbody = document.getElementById("resultsBody");
  if (!tbody) return;
  tbody.innerHTML = "";

  const tr = document.createElement("tr");
  tr.className = "empty-row";

  const td = document.createElement("td");
  td.colSpan = 3;
  td.className = "text-center text-muted py-4";
  td.textContent = message;

  tr.appendChild(td);
  tbody.appendChild(tr);
}

function renderResults(candidatos) {
  const tbody = document.getElementById("resultsBody");
  if (!tbody) return;
  tbody.innerHTML = "";

  if (!Array.isArray(candidatos) || candidatos.length === 0) {
    renderEmptyRow("Nenhum candidato encontrado para essa vaga.");
    return;
  }

  for (const c of candidatos) {
    const tr = document.createElement("tr");

    const tdId = document.createElement("td");
    tdId.textContent = String(c?.id ?? "—");

    const tdNome = document.createElement("td");
    tdNome.textContent = c?.nome ?? "—";

    const tdCv = document.createElement("td");
    tdCv.className = "resume-cell"; // já tem CSS pra quebra de linha
    tdCv.textContent = c?.cv_pt ?? "—";

    tr.appendChild(tdId);
    tr.appendChild(tdNome);
    tr.appendChild(tdCv);
    tbody.appendChild(tr);
  }
}







// ===============================
// Upload de arquivo (.json)
// ===============================
function handleFile(input, output, errorEl, file) {
  const fileName = file.name.toLowerCase();

  // Validação: somente .json
  if (!fileName.endsWith(".json")) {
    errorEl.textContent = "Erro: Apenas arquivos .json são permitidos.";
    errorEl.style.display = "block";
    input.value = "";
    output.textContent = "";
    return;
  }

  // Limpa erro e exibe nome
  errorEl.textContent = "";
  errorEl.style.display = "none";
  output.textContent = `Arquivo selecionado: ${file.name}`;
}

// Clique no input
function setupFileInput(inputId, outputId, errorId) {
  const input = document.getElementById(inputId);
  const output = document.getElementById(outputId);
  const errorEl = document.getElementById(errorId);

  if (!input) return;

  input.addEventListener("change", function () {
    if (this.files && this.files.length > 0) {
      handleFile(this, output, errorEl, this.files[0]);
    }
  });
}

// Drag & Drop
function setupDragAndDrop(labelSelector, inputId, outputId, errorId) {
  const dropArea = document.querySelector(labelSelector);
  const input = document.getElementById(inputId);
  const output = document.getElementById(outputId);
  const errorEl = document.getElementById(errorId);

  if (!dropArea || !input) return;

  ["dragenter", "dragover"].forEach(eventName => {
    dropArea.addEventListener(eventName, (e) => {
      e.preventDefault();
      e.stopPropagation();
      dropArea.classList.add("dragover");
    });
  });

  ["dragleave", "drop"].forEach(eventName => {
    dropArea.addEventListener(eventName, (e) => {
      e.preventDefault();
      e.stopPropagation();
      dropArea.classList.remove("dragover");
    });
  });

  dropArea.addEventListener("drop", (e) => {
    const files = e.dataTransfer.files;
    if (files.length > 0) {
      // Valida e mostra o nome
      handleFile(input, output, errorEl, files[0]);
      // Associa o arquivo ao input hidden (para o fetch usar o input)
      const dt = new DataTransfer();
      dt.items.add(files[0]);
      input.files = dt.files;
    }
  });
}

// Envio para o servidor (apenas 1 arquivo)
function setupUploadButton() {
  const uploadBtn = document.getElementById("uploadBtn");
  const vagasFile = document.getElementById("vagasFile");
  const messageEl = document.getElementById("uploadMessage");

  if (!uploadBtn || !vagasFile) return;

  uploadBtn.addEventListener("click", function () {
    if (!messageEl) return;

    messageEl.style.display = "none";
    messageEl.textContent = "";
    messageEl.className = "upload-message";

    if (!vagasFile.files.length) {
      messageEl.textContent = "Por favor, selecione o arquivo de vagas antes de enviar.";
      messageEl.classList.add("error");
      messageEl.style.display = "block";
      return;
    }

    const formData = new FormData();
    formData.append("vagas", vagasFile.files[0]);

    uploadBtn.disabled = true;
    const originalText = uploadBtn.textContent;
    uploadBtn.textContent = "Enviando...";

    fetch("/upload", {
      method: "POST",
      body: formData
    })
    .then(response => {
      if (!response.ok) throw new Error("Erro no upload");
      return response.text();
    })
    .then(() => {
      messageEl.textContent = "Arquivo enviado com sucesso!";
      messageEl.classList.add("success");
      messageEl.style.display = "block";
    })
    .catch(() => {
      messageEl.textContent = "Erro ao enviar o arquivo.";
      messageEl.classList.add("error");
      messageEl.style.display = "block";
    })
    .finally(() => {
      uploadBtn.disabled = false;
      uploadBtn.textContent = originalText;
    });
  });
}

// ===============================
// Buscar candidatos similares (POST /predict)
// ===============================
function setupPredictButton() {
  const buscarBtn   = document.getElementById("buscarBtn");
  const jobIdInput  = document.getElementById("jobIdInput");
  const topKInput   = document.getElementById("topKInput");

  if (!buscarBtn || !jobIdInput || !topKInput) return;

  jobIdInput.addEventListener("input", () => jobIdInput.setCustomValidity(""));
  topKInput.addEventListener("input",  () => topKInput.setCustomValidity(""));

  buscarBtn.addEventListener("click", async () => {
    const jobId = jobIdInput.value.trim();
    const k     = parseInt((topKInput.value || "").trim(), 10);

    if (!jobId) {
      jobIdInput.setCustomValidity("Informe o ID da vaga.");
      jobIdInput.reportValidity();
      return;
    }
    if (Number.isNaN(k) || k < 1) {
      topKInput.setCustomValidity("K deve ser um inteiro ≥ 1.");
      topKInput.reportValidity();
      return;
    }

    // Estado de carregamento na tabela
    renderEmptyRow("Buscando resultados...");

    // UX do botão
    buscarBtn.disabled = true;
    const originalText = buscarBtn.textContent;
    buscarBtn.textContent = "Buscando...";

    try {
      const res = await fetch("/predict", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ job_id: jobId, k })
      });

      const text = await res.text();
      let data = null;
      try { data = text ? JSON.parse(text) : null; } catch (_) {}

      if (!res.ok) {
        const msg = (data && (data.message || data.error)) || "Não foi possível buscar resultados.";
        renderEmptyRow(msg);
        console.error("Erro em /predict:", data ?? text);
        return;
      }

      // Espera: { candidatos: [ { id, nome, cv_pt }, ... ] }
      const candidatos = data?.candidatos ?? [];
      renderResults(candidatos);

    } catch (err) {
      console.error("Falha na requisição /predict:", err);
      renderEmptyRow("Erro de conexão. Tente novamente.");
    } finally {
      buscarBtn.disabled = false;
      buscarBtn.textContent = originalText;
    }
  });
}


// ===============================
// Inicialização
// ===============================
document.addEventListener("DOMContentLoaded", function () {
  setupFileInput("vagasFile", "vagasFileName", "vagasError");
  setupDragAndDrop('[data-type="vagas"]', "vagasFile", "vagasFileName", "vagasError");
  setupUploadButton();
  setupPredictButton();
});
