from models.models import MovimentacaoLedger, db
from sqlalchemy import desc, func

class LedgerRepository:
    # 1. Ajustei o nome do argumento final para 'transferencia_id'
    def create(self, acao_id, subacao_id, tipo_operacao, valor, saldo_anterior, saldo_novo, pf_id=None, transferencia_id=None):
        try:
            movimento = MovimentacaoLedger(
                acao_id=acao_id,
                subacao_id=subacao_id,
                tipo_operacao=tipo_operacao,
                valor_movimento=valor,
                saldo_anterior=saldo_anterior,
                saldo_novo=saldo_novo,
                pf_id=pf_id,
                # 2. Agora o nome da variável bate com o nome da coluna no banco
                transferencia_id=transferencia_id
            )
            db.session.add(movimento)
            db.session.flush()
            return movimento
        except Exception as e:
            db.session.rollback()
            raise e

    def get_saldo_em_data(self, acao_id, data_limite, subacao_id=None):
        """Busca o último saldo registrado até uma data específica."""
        query = MovimentacaoLedger.query.filter(
            MovimentacaoLedger.data_movimento <= data_limite,
            MovimentacaoLedger.acao_id == acao_id
        )

        if subacao_id:
            query = query.filter(MovimentacaoLedger.subacao_id == subacao_id)
        else:
            query = query.filter(MovimentacaoLedger.subacao_id.is_(None))

        # Pega o último registro ordenado por data e ID
        ultimo_movimento = query.order_by(
            desc(MovimentacaoLedger.data_movimento), 
            desc(MovimentacaoLedger.id)
        ).first()

        return ultimo_movimento.saldo_novo if ultimo_movimento else 0.00
    def get_posicao_pf_em_data(self, pf_id, data_limite):
        """
        Reconstitui o status de uma PF em uma data específica no passado.
        """
        # 1. Soma todos os empenhos feitos até a data
        total_empenhado = db.session.query(func.sum(MovimentacaoLedger.valor_movimento)).filter(
            MovimentacaoLedger.pf_id == pf_id,
            MovimentacaoLedger.tipo_operacao == 'EMPENHO',
            MovimentacaoLedger.data_movimento <= data_limite
        ).scalar() or 0.0

        # 2. Soma todas as liquidações feitas até a data
        total_liquidado = db.session.query(func.sum(MovimentacaoLedger.valor_movimento)).filter(
            MovimentacaoLedger.pf_id == pf_id,
            MovimentacaoLedger.tipo_operacao == 'LIQUIDACAO',
            MovimentacaoLedger.data_movimento <= data_limite
        ).scalar() or 0.0

        return {
            "pf_id": pf_id,
            "data_referencia": data_limite,
            "empenhado_na_data": total_empenhado,
            "liquidado_na_data": total_liquidado,
            "saldo_a_liquidar_na_data": total_empenhado - total_liquidado
        }