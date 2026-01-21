from flask import Blueprint, request, jsonify
from services.pf_service import PFService

pf_service = PFService()
pf_bp = Blueprint('pf_bp', __name__)

# 1. CRIAR PF (Planejamento)
@pf_bp.route('/criar', methods=['POST'])
def create():   
    data = request.get_json()
    try:
        created_pf = pf_service.criar_pf(
            acao_id=data.get('acao_id'),
            subacao_id=data.get('subacao_id'),
            descricao=data.get('descricao'),
            valor_total=data.get('valor'), # Valor Total
            usuario_id=data.get('usuario_id')
        )
        return jsonify({'message': 'PF criada com sucesso', 'id': created_pf.id}), 201
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({'error': 'Erro interno ao criar PF'}), 500

# 2. EMPENHAR (Parcial ou Total)
@pf_bp.route('/empenhar', methods=['POST'])
def empenhar():
    data = request.get_json()
    try:
        pf = pf_service.realizar_empenho(
            pf_id=data.get('pf_id'),
            valor_a_empenhar=data.get('valor')
        )
        return jsonify({
            'message': 'Empenho realizado', 
            'status_atual': pf.status.value,
            'empenhado': str(pf.valor_empenhado)
        }), 200
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# 3. LIQUIDAR (Pagar)
@pf_bp.route('/liquidar', methods=['POST'])
def liquidar():
    data = request.get_json()
    try:
        pf = pf_service.realizar_liquidacao(
            pf_id=data.get('pf_id'),
            valor_a_liquidar=data.get('valor')
        )
        return jsonify({
            'message': 'Liquidação realizada', 
            'status_atual': pf.status.value,
            'liquidado': str(pf.valor_liquidado)
        }), 200
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500