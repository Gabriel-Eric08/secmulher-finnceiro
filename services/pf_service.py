from repositories.pf_repository import PFRepository, db

class PFService:
    def __init__(self):
        self.pf_repository = PFRepository()
    
    def create_pf(self, acao_id, subacao_id, descricao, valor, status, data_empenho, data_liquidacao, usuario_id):
        try:
            novo_pf = self.pf_repository.create(acao_id, subacao_id, descricao, valor, status, data_empenho, data_liquidacao, usuario_id)
            db.session.commit()
            return novo_pf
        except Exception as e:
            db.session.rollback()
            raise e