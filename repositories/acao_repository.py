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
        
    def delete(self, acao_id):
            try:
               acao = Acao.query.filter_by(id=acao_id).first()
               db.session.delete(acao)
               db.session.flush()
               return True
            except Exception as e:
                db.session.rollback()
                print(f"Erro ao deletar ação: {e}")
                return False