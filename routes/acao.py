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
    
@acao_bp.route('/delete/<int:acao_id>', methods=['DELETE'])
def delete(acao_id):
    sucesso = acao_service.delete(acao_id)
    if sucesso:
        return jsonify({'message': 'Ação deletada com sucesso'}), 200
    else:
        return jsonify({'message': 'Erro ao deletar ação'}), 500
    
@acao_bp.route('/all', methods=['GET'])
def get_all_acoes():
    try:
        acoes = acao_service.get_all()
        acoes_list = [{
            'id': acao.id,
            'codigo': acao.codigo,
            'descricao': acao.descricao,
            'orcamento_inicial': acao.orcamento_inicial,
            'saldo_atual': acao.saldo_atual
        } for acao in acoes]
        return jsonify(acoes_list), 200
    except Exception as e:
        return jsonify({'message': 'Erro ao obter ações', 'error': str(e)}), 500