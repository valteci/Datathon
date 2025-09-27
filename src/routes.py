from flask import Blueprint, render_template, request, jsonify
from src.services.load_data import Load

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
    print('tipo:', type(vagas_file))
    # Verifica se os arquivos têm extensão .json
    if not vagas_file.filename.endswith(".json") or not candidatos_file.filename.endswith(".json"):
        return jsonify({"error": "Os arquivos devem ser no formato .json."}), 400
    
    try:
        loader = Load()

        # Carrega vagas no Redis
        loader.load_vagas(vagas_file)

        return jsonify({
            "message": "Arquivos recebidos e vagas salvas no Redis com sucesso!",
            "vagas_filename": vagas_file.filename,
            "candidatos_filename": candidatos_file.filename
        }), 200
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

