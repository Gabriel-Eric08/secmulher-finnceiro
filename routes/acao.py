from flask import Blueprint, request, jsonify
from services.acao_service import AcaoService

acao_service = AcaoService()

acao_bp = Blueprint('acoes', __name__)

@acao_bp.route('/create', methods=['POST'])
def create_acao():
    data = request.get_json()
    codigo = data.get('codigo')
    descricao = data.get('descricao')
    orcamento_inicial = data.get('orcamento_inicial')

    if not all([codigo, descricao, orcamento_inicial]):
        return jsonify({'sucess':False,'message': 'Dados incompletos'}), 400

    sucesso = acao_service.create(codigo, descricao, orcamento_inicial)
    if sucesso:
        return jsonify({'message': 'Ação criada com sucesso'}), 201
    else:
        return jsonify({'message': 'Erro ao criar ação'}), 500