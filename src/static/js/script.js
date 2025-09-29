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

    uploadBtn.addEventListener("click", function () {
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
        });
    });
}

// Inicialização
document.addEventListener("DOMContentLoaded", function() {
    setupFileInput("vagasFile", "vagasFileName", "vagasError");
    setupDragAndDrop('[data-type="vagas"]', "vagasFile", "vagasFileName", "vagasError");
    setupUploadButton();
});
