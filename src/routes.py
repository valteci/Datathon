from flask import Blueprint, render_template, request, jsonify, Response
from src.services.Data import Data
from src.services.gemini_api import Model
from src.services.log import Log
import requests

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
        loader = Data()

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
    vaga_id = data.get("job_id")
    k = data.get("k")

    # Validações
    if not vaga_id or not isinstance(vaga_id, str):
        return jsonify({"error": "Campo 'job_id' e obrigatorio e deve ser uma string."}), 400

    if k is None:
        return jsonify({"error": "Campo 'k' é obrigatorio."}), 400

    try:
        k = int(k)
        if k <= 0:
            return jsonify({"error": "Campo 'k' deve ser um inteiro positivo."}), 400
    except (ValueError, TypeError):
        return jsonify({"error": "Campo 'k' deve ser um numero inteiro."}), 400


    dados = Data()
    model = Model()
    log = Log()
    t0 = log.timed()

    descricao_vaga = dados.get_vaga_descricao(vaga_id)
    output_model = model.predict(descricao_vaga, k)
    similaridades = output_model['similarities'][0]
    candidatos_id = output_model['ids'][0]

    candidatos_json = dados.get_candidatos(candidatos_id)

    log.log(duration_ms=log.timed()-t0, similarities=similaridades, k=k)
    return Response(candidatos_json, status=200, mimetype="application/json")


@bp.route("/metrics", methods=["GET"])
def metrics():
    try:
        include_history = (request.args.get("history", "true").lower() != "false")
        cap = int(request.args.get("cap", 1000))
    except Exception:
        include_history, cap = True, 1000

    try:
        data = Log.fetch_all(include_history=include_history, cap_history=cap)
        return jsonify(data), 200
    except requests.RequestException as e:
        # MLflow fora do ar, timeout, etc.
        return jsonify({"error": "mlflow_unreachable", "detail": str(e)}), 503
    except Exception as e:
        return jsonify({"error": "unexpected", "detail": str(e)}), 500

