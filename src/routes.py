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


@bp.route("/predict", methods=["POST"])
def predict():
    # Garantir que o body é JSON
    if not request.is_json:
        return jsonify({"error": "O corpo da requisicao deve ser um JSON."}), 400

    data = request.get_json(silent=True)

    if data is None:
        return jsonify({"error": "JSON invalido."}), 400

    # Extrair campos
    job_id = data.get("job_id")
    k = data.get("k")

    # Validações
    if not job_id or not isinstance(job_id, str):
        return jsonify({"error": "Campo 'job_id' e obrigatorio e deve ser uma string."}), 400

    if k is None:
        return jsonify({"error": "Campo 'k' é obrigatorio."}), 400

    try:
        k = int(k)
        if k <= 0:
            return jsonify({"error": "Campo 'k' deve ser um inteiro positivo."}), 400
    except (ValueError, TypeError):
        return jsonify({"error": "Campo 'k' deve ser um numero inteiro."}), 400

    # (Por enquanto apenas retorna os valores validados)
    return jsonify({
        "message": "Parametros recebidos com sucesso.",
        "job_id": job_id,
        "k": k
    }), 200


