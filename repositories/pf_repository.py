from models.models import PF, StatusPF, db
from sqlalchemy import desc

class PFRepository:
    def create(self, acao_id, subacao_id, descricao, valor_total, usuario_id):
        try:
            # Cria com status inicial AGUARDANDO e valores zerados
            novo_pf = PF(
                acao_id=acao_id, 
                subacao_id=subacao_id, 
                descricao=descricao, 
                valor_total=valor_total,
                valor_empenhado=0.00,
                valor_liquidado=0.00,
                status=StatusPF.AGUARDANDO,
                usuario_id=usuario_id
            )
            db.session.add(novo_pf)
            db.session.flush() # Gera o ID
            return novo_pf
        except Exception as e:
            db.session.rollback()
            raise e

    def get_by_id(self, pf_id):
        return PF.query.get(pf_id)

    def save(self, pf):
        """Salva alterações feitas em um objeto PF existente."""
        try:
            db.session.add(pf)
            db.session.flush()
            return pf
        except Exception as e:
            db.session.rollback()
            raise e

    def get_all(self):
        try:
            return PF.query.order_by(desc(PF.data_cadastro)).all()
        except Exception as e:
            raise e