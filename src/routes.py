from flask import Blueprint, render_template, request, jsonify

# cria um blueprint chamado "main"
bp = Blueprint("main", __name__)

@bp.route("/")
def index():
    return render_template("index.html")

@bp.route("/upload", methods=["POST"])
def upload_files():
    # Verifica se os arquivos estão presentes na requisição
    if "vagas" not in request.files or "candidatos" not in request.files:
        return jsonify({"error": "Os dois arquivos (vagas e candidatos) sao obrigatorios."}), 400

    vagas_file = request.files["vagas"]
    candidatos_file = request.files["candidatos"]

    # Verifica se os arquivos têm extensão .json
    if not vagas_file.filename.endswith(".json") or not candidatos_file.filename.endswith(".json"):
        return jsonify({"error": "Os arquivos devem ser no formato .json."}), 400

    # Aqui você poderia processar os arquivos (ler JSON, salvar, etc.)
    # Mas por enquanto vamos só retornar um JSON genérico
    return jsonify({
        "message": "Arquivos recebidos com sucesso!",
        "vagas_filename": vagas_file.filename,
        "candidatos_filename": candidatos_file.filename
    }), 200
