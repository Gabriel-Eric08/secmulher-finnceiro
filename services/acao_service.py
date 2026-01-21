from repositories.acao_repository import AcaoRepository
from services.ledger_service import LedgerService
from extensions import db

class AcaoService:
    def __init__(self):
        self.acao_repository = AcaoRepository()
        self.ledger_service = LedgerService()

    def create(self, codigo, descricao, orcamento_inicial):
        try:
            nova_acao = self.acao_repository.create(codigo, descricao, orcamento_inicial)
            
            if nova_acao:
                valor_inicial = float(orcamento_inicial) if orcamento_inicial else 0.0
                if valor_inicial > 0:
                    self.ledger_service.registrar_movimentacao(
                        entidade=nova_acao,
                        valor=valor_inicial,
                        tipo_operacao='SALDO_INICIAL'
                    )
                db.session.commit()
                return True
            return False
        except Exception as e:
            db.session.rollback()
            print(f"Erro no Service (Create Ação): {e}")
            return False

    def delete(self, acao_id):
        """
        Deleta uma ação, limpando TODAS as referências em outras tabelas primeiro.
        """
        try:
            # Importação local para evitar erros de importação circular
            from models.models import MovimentacaoLedger, Subacao, PF, Transferencia, Acao

            # 1. Verificar se a ação existe
            acao = Acao.query.get(acao_id)
            if not acao:
                return False

            # 2. Limpar Movimentações do Ledger vinculadas às subações desta ação
            subacoes_ids = [s.id for s in acao.subacoes]
            if subacoes_ids:
                MovimentacaoLedger.query.filter(MovimentacaoLedger.subacao_id.in_(subacoes_ids)).delete(synchronize_session=False)

            # 3. Limpar Movimentações do Ledger vinculadas diretamente à ação
            MovimentacaoLedger.query.filter_by(acao_id=acao_id).delete(synchronize_session=False)

            # 4. Limpar PFs (Projetos Financeiros) vinculados
            PF.query.filter_by(acao_id=acao_id).delete(synchronize_session=False)

            # 5. Limpar Transferências (onde a ação é origem OU destino)
            Transferencia.query.filter(
                (Transferencia.acao_origem_id == acao_id) | 
                (Transferencia.acao_destino_id == acao_id)
            ).delete(synchronize_session=False)

            # 6. Limpar Subações
            Subacao.query.filter_by(acao_id=acao_id).delete(synchronize_session=False)

            # 7. Finalmente, deletar a ação através do repositório
            sucesso = self.acao_repository.delete(acao_id)
            
            if sucesso:
                db.session.commit()
                return True
            
            db.session.rollback()
            return False

        except Exception as e:
            db.session.rollback()
            print(f"ERRO CRÍTICO AO DELETAR AÇÃO: {str(e)}")
            return False
        
    def get_all(self):
        try:
            return self.acao_repository.get_all()
        except Exception as e:
            print(f"Erro ao obter ações: {e}")
            return []