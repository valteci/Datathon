function handleFile(input, output, errorEl, file) {
    const fileName = file.name.toLowerCase();

    // Validação de extensão
    if (!fileName.endsWith(".json")) {
        errorEl.textContent = "Erro: Apenas arquivos .json são permitidos.";
        errorEl.style.display = "block";
        input.value = "";
        output.textContent = "";
        return;
    }

    // Reset de erro e exibição do nome do arquivo
    errorEl.textContent = "";
    errorEl.style.display = "none";
    output.textContent = `Arquivo selecionado: ${file.name}`;
}

// Configuração do input normal (clique)
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

// Configuração do drag & drop
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
        }
    });
}

// Inicialização
document.addEventListener("DOMContentLoaded", function() {
    setupFileInput("vagasFile", "vagasFileName", "vagasError");
    setupFileInput("candidatosFile", "candidatosFileName", "candidatosError");

    setupDragAndDrop('[data-type="vagas"]', "vagasFile", "vagasFileName", "vagasError");
    setupDragAndDrop('[data-type="candidatos"]', "candidatosFile", "candidatosFileName", "candidatosError");
});
