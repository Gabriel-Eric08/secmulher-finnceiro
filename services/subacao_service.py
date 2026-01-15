from repositories.subacao_repository import SubacaoRepository, db

class SubacaoService:
    def __init__(self):
        self.subacao_repository = SubacaoRepository()
    def create_subacao(self, codigo, descricao, orcamento_inicial, acao_id):
        try:
            nova_subacao = self.subacao_repository.create(codigo, descricao, orcamento_inicial, acao_id)
            db.session.commit()
            return nova_subacao
        except Exception as e:
            db.session.rollback()
            raise e
    def delete_subacao(self, subacao_id):
        try:
            sucesso = self.subacao_repository.delete(subacao_id)
            if sucesso:
                db.session.commit()
            else:
                db.session.rollback()
            return sucesso
        except Exception as e:
            db.session.rollback()
            raise e