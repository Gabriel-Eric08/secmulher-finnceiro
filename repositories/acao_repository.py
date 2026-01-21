from models.models import Acao, db

class AcaoRepository:
    def create(self, codigo, descricao, orcamento_inicial):
        try:
            # Aqui assumimos que o saldo_atual começa igual ao orçamento inicial
            nova_acao = Acao(
                codigo=codigo, 
                descricao=descricao, 
                orcamento_inicial=orcamento_inicial, 
                saldo_atual=orcamento_inicial
            )
            db.session.add(nova_acao)
            db.session.flush() # Gera o ID mas não comita ainda (o Service comita)
            return nova_acao
        except Exception as e:
            db.session.rollback()
            raise e
        
    def delete(self, acao_id):
        try:
            acao = Acao.query.filter_by(id=acao_id).first()
            if not acao:
                return False
                
            db.session.delete(acao)
            db.session.flush()
            return True
        except Exception as e:
            # O rollback total será feito no Service se der erro
            raise e

    def get_all(self):
        try:
            return Acao.query.order_by(Acao.codigo).all() # Adicionei order_by para ficar organizado
        except Exception as e:
            raise e