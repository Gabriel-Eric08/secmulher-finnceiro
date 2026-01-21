from flask import Blueprint, request, jsonify
from services.transferencia_service import TransferenciaService

transferencia_bp = Blueprint('transferencia_bp', __name__)
service = TransferenciaService()

@transferencia_bp.route('/create', methods=['POST'])
def create():
    data = request.get_json()
    # Espera json: { acao_origem_id, subacao_origem_id, acao_destino_id, subacao_destino_id, valor, tipo, usuario_id }
    try:
        transf = service.realizar_transferencia(data)
        return jsonify({'message': 'Transferência realizada com sucesso', 'id': transf.id}), 201
    except ValueError as ve:
        return jsonify({'error': str(ve)}), 400 # Saldo insuficiente
    except Exception as e:
        return jsonify({'error': str(e)}), 500
