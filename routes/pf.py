from flask import Blueprint, request, jsonify
from  services.pf_service import PFService

pf_service = PFService()
pf_bp = Blueprint('pf_bp', __name__)

@pf_bp.route('/create', methods=['POST'])
def create():   
    data = request.get_json()
    acao_id = data.get('acao_id')
    subacao_id = data.get('subacao_id') 
    descricao = data.get('descricao')
    valor = data.get('valor')
    status = data.get('status')
    data_empenho = data.get('data_empenho')
    data_liquidacao = data.get('data_liquidacao')
    usuario_id = data.get('usuario_id')

    created_pf = pf_service.create_pf(acao_id, subacao_id, descricao, valor, status, data_empenho, data_liquidacao, usuario_id)
    if created_pf:
        return jsonify({
            'id': created_pf.id,
            'acao_id': created_pf.acao_id,
            'subacao_id': created_pf.subacao_id,
            'descricao': created_pf.descricao,
            'valor': created_pf.valor,
            'status': created_pf.status,
            'data_empenho': created_pf.data_empenho,
            'data_liquidacao': created_pf.data_liquidacao,
            'usuario_id': created_pf.usuario_id
        }), 201
    else:
        return jsonify({'error': 'Erro ao criar PF'}), 500