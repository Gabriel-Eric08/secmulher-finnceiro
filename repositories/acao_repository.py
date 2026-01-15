from models.models import Acao, db

class AcaoRepository:
    def create(self, codigo, descricao, orcamento_inicial):
        try:
            nova_acao = Acao(codigo=codigo, descricao=descricao, orcamento_inicial=orcamento_inicial, saldo_atual=orcamento_inicial)
            db.session.add(nova_acao)
            db.session.flush()
            return nova_acao
        except Exception as e:
            db.session.rollback()
            raise e