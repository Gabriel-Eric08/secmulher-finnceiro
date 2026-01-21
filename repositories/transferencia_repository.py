from models.models import Transferencia, db

class TransferenciaRepository:
    def create(self, tipo, acao_origem_id, acao_destino_id, valor, usuario_id, subacao_origem_id=None, subacao_destino_id=None):
        try:
            transf = Transferencia(
                tipo=tipo,
                acao_origem_id=acao_origem_id,
                subacao_origem_id=subacao_origem_id,
                acao_destino_id=acao_destino_id,
                subacao_destino_id=subacao_destino_id,
                valor=valor,
                usuario_id=usuario_id
            )
            db.session.add(transf)
            db.session.flush()
            return transf
        except Exception as e:
            db.session.rollback()
            raise e
    def get_all(self):
        try:
            transferencias = Transferencia.query.order_by(Transferencia.data_transferencia.desc()).all()
            return transferencias
        except Exception as e:
            raise e