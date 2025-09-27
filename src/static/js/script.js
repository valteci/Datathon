function handleFile(input, output, errorEl, file) {
    const fileName = file.name.toLowerCase();

    if (!fileName.endsWith(".json")) {
        errorEl.textContent = "Erro: Apenas arquivos .json são permitidos.";
        errorEl.style.display = "block";
        input.value = "";
        output.textContent = "";
        return;
    }

    errorEl.textContent = "";
    errorEl.style.display = "none";
    output.textContent = `Arquivo selecionado: ${file.name}`;
}

// Input normal
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
            handleFile(input, output, errorEl, files[0]);
            input.files = files; // associa ao input hidden
        }
    });
}

// Upload para o servidor
function setupUploadButton() {
    const uploadBtn = document.getElementById("uploadBtn");
    const vagasFile = document.getElementById("vagasFile");
    const candidatosFile = document.getElementById("candidatosFile");
    const messageEl = document.getElementById("uploadMessage");

    uploadBtn.addEventListener("click", function () {
        if (!vagasFile.files.length || !candidatosFile.files.length) {
            messageEl.textContent = "Por favor, selecione os dois arquivos antes de enviar.";
            messageEl.className = "upload-message error";
            messageEl.style.display = "block";
            return;
        }

        const formData = new FormData();
        formData.append("vagas", vagasFile.files[0]);
        formData.append("candidatos", candidatosFile.files[0]);

        fetch("/upload", {
            method: "POST",
            body: formData
        })
        .then(response => {
            if (!response.ok) {
                throw new Error("Erro no upload");
            }
            return response.text();
        })
        .then(data => {
            messageEl.textContent = "Arquivos enviados com sucesso!";
            messageEl.className = "upload-message success";
            messageEl.style.display = "block";
        })
        .catch(err => {
            messageEl.textContent = "Erro ao enviar os arquivos.";
            messageEl.className = "upload-message error";
            messageEl.style.display = "block";
        });
    });
}

// Inicialização
document.addEventListener("DOMContentLoaded", function() {
    setupFileInput("vagasFile", "vagasFileName", "vagasError");
    setupFileInput("candidatosFile", "candidatosFileName", "candidatosError");

    setupDragAndDrop('[data-type="vagas"]', "vagasFile", "vagasFileName", "vagasError");
    setupDragAndDrop('[data-type="candidatos"]', "candidatosFile", "candidatosFileName", "candidatosError");

    setupUploadButton();
});
