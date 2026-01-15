from flask import Blueprint, jsonify

acoes_bp = Blueprint('acoes', __name__, url_prefix='/acoes')

@acoes_bp.route('/', methods=['GET'])
def listar_acoes():
    return jsonify({"msg": "Rota de ações funcionando"})