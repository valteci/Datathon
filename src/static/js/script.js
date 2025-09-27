// Validação: garante que apenas arquivos .json possam ser selecionados
function handleFileInput(inputId, outputId) {
    const input = document.getElementById(inputId);
    const output = document.getElementById(outputId);

    input.addEventListener("change", function () {
        if (this.files && this.files.length > 0) {
            const file = this.files[0];
            const fileName = file.name.toLowerCase();

            if (!fileName.endsWith(".json")) {
                alert("Erro: Apenas arquivos .json são permitidos.");
                this.value = ""; // limpa o input
                output.textContent = ""; // limpa a mensagem
                return;
            }

            output.textContent = `Arquivo selecionado: ${file.name}`;
        } else {
            output.textContent = "";
        }
    });
}

// Inicialização
document.addEventListener("DOMContentLoaded", function() {
    handleFileInput("vagasFile", "vagasFileName");
    handleFileInput("candidatosFile", "candidatosFileName");
});
