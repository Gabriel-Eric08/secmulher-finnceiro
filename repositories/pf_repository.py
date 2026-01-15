from models.models import PF, db

class PFRepository:
    def create(self, acao_id, subacao_id, descricao, valor, status, data_empenho, data_liquidacao, usuario_id):
        try:
            novo_pf = PF(acao_id=acao_id, subacao_id=subacao_id, descricao=descricao, valor=valor, status=status, data_empenho=data_empenho, data_liquidacao=data_liquidacao, usuario_id=usuario_id)
            db.session.add(novo_pf)
            db.session.flush()
            return novo_pf
        except Exception as e:
            db.session.rollback()
            raise e