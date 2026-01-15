from models.models import Subacao, db

class SubacaoRepository:
    def create(self, codigo, descricao, orcamento_inicial, acao_id):
        try:
            nova_subacao = Subacao(codigo=codigo, descricao=descricao, orcamento_inicial=orcamento_inicial, saldo_atual=orcamento_inicial, acao_id=acao_id)
            db.session.add(nova_subacao)
            db.session.flush()
            return nova_subacao
        except Exception as e:
            db.session.rollback()
            raise e
        
    def delete(self, subacao_id):
            try:
               subacao = Subacao.query.filter_by(id=subacao_id).first()
               db.session.delete(subacao)
               db.session.flush()
               return True
            except Exception as e:
                db.session.rollback()
                print(f"Erro ao deletar subação: {e}")
                return False