from flask import Blueprint, request, jsonify
from repositories.ledger_repository import LedgerRepository
from datetime import datetime

historico_bp = Blueprint('historico_bp', __name__)
ledger_repo = LedgerRepository()

@historico_bp.route('/saldo', methods=['GET'])
def get_saldo_data():
    # Ex: /historico/saldo?acao_id=1&data=2023-10-25&subacao_id=5
    acao_id = request.args.get('acao_id')
    subacao_id = request.args.get('subacao_id')
    data_str = request.args.get('data')

    if not acao_id or not data_str:
        return jsonify({'error': 'acao_id e data são obrigatórios'}), 400

    try:
        # Converter string para datetime, assumindo fim do dia para pegar tudo do dia
        data_limite = datetime.strptime(data_str, '%Y-%m-%d').replace(hour=23, minute=59, second=59)
        
        saldo = ledger_repo.get_saldo_em_data(acao_id, data_limite, subacao_id)
        
        return jsonify({
            'acao_id': acao_id,
            'subacao_id': subacao_id,
            'data_referencia': data_str,
            'saldo_historico': float(saldo)
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500