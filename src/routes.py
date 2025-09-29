from flask import Blueprint, render_template, request, jsonify
from src.services.load_data import Load
#from src.services.gemini_api import Teste

# cria um blueprint chamado "main"
bp = Blueprint("main", __name__)

@bp.route("/")
def index():
    return render_template("index.html")

@bp.route("/upload", methods=["POST"])
def upload_files():
    # Verifica se os arquivos estão presentes na requisição
    if "vagas" not in request.files:
        return jsonify({"error": "O arquivo de vaga e obrigatorio."}), 400

    vagas_file = request.files["vagas"]
    # Verifica se os arquivos têm extensão .json
    if not vagas_file.filename.endswith(".json"):
        return jsonify({"error": "O arquivo deve ser no formato .json."}), 400
    
    try:
        loader = Load()

        # Carrega vagas e candidados no Redis
        loader.load_vagas(vagas_file)

        return jsonify({
            "message": "Arquivo recebido e vagas salvas no Redis com sucesso!",
            "vagas_filename": vagas_file.filename,
        }), 200
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

