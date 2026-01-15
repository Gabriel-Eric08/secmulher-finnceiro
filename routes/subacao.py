from flask import Blueprint, request, jsonify
from services.subacao_service import SubacaoService

subacao_service= SubacaoService()

subacao_bp = Blueprint('subacao_bp', __name__)

@subacao_bp.route('/create', methods=['POST'])
def create():
    data = request.get_json()
    codigo = data.get('codigo')
    descricao = data.get('descricao')
    orcamento_inicial = data.get('orcamento_inicial')
    acao_id = data.get('acao_id')
    try:
        nova_subacao = subacao_service.create_subacao(codigo, descricao, orcamento_inicial, acao_id)
        return jsonify({
            'id': nova_subacao.id,
            'codigo': nova_subacao.codigo,
            'descricao': nova_subacao.descricao,
            'orcamento_inicial': nova_subacao.orcamento_inicial,
            'saldo_atual': nova_subacao.saldo_atual,
            'acao_id': nova_subacao.acao_id
        }), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500
@subacao_bp.route('/delete/<int:subacao_id>', methods=['DELETE'])
def delete(subacao_id):
    try:
        sucesso = subacao_service.delete_subacao(subacao_id)
        if sucesso:
            return jsonify({'message': 'Subação deletada com sucesso.'}), 200
        else:
            return jsonify({'error': 'Falha ao deletar subação.'}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500