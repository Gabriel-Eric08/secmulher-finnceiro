from repositories.acao_repository import AcaoRepository, db

class AcaoService:
    def __init__(self):
        self.acao_repository = AcaoRepository()
    def create(self, codigo, descricao, orcamento_inicial):
        try:
            nova_acao = self.acao_repository.create(codigo, descricao, orcamento_inicial)
            if nova_acao:
                db.session.commit()
                return True
            else:
                return False
        except Exception as e:
            db.session.rollback()
            print(f"Erro ao criar ação: {e}")
            return False
    def delete(self, acao_id):
        try:
            sucesso = self.acao_repository.delete(acao_id)
            if sucesso:
                db.session.commit()
                return True
            else:
                return False
        except Exception as e:
            db.session.rollback()
            print(f"Erro ao deletar ação: {e}")
            return False