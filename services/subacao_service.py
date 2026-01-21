from repositories.subacao_repository import SubacaoRepository
from services.ledger_service import LedgerService
from models.models import Acao, Subacao
from extensions import db
from sqlalchemy import func
from decimal import Decimal

class SubacaoService:
    def __init__(self):
        self.subacao_repository = SubacaoRepository()
        self.ledger_service = LedgerService()

    def create(self, codigo, descricao, orcamento_inicial, acao_id):
        try:
            # 1. Conversão segura para Decimal
            valor_novo = Decimal(str(orcamento_inicial)) if orcamento_inicial else Decimal('0.00')
            
            # 2. Busca a Ação Pai
            acao_pai = Acao.query.get(acao_id)
            if not acao_pai:
                raise ValueError("Ação Pai não encontrada.")

            # --- CORREÇÃO DA REGRA DE TETO ---
            # Usamos orcamento_inicial que é o campo real no seu model Acao
            teto_pai = Decimal(str(acao_pai.orcamento_inicial))

            # Soma o orçamento inicial de todas as subações já existentes
            total_alocado = db.session.query(func.sum(Subacao.orcamento_inicial))\
                .filter(Subacao.acao_id == acao_id).scalar() or Decimal('0.00')

            if (total_alocado + valor_novo) > teto_pai:
                saldo_disponivel = teto_pai - total_alocado
                raise ValueError(
                    f"Orçamento excedido! A Ação {acao_pai.codigo} tem apenas "
                    f"R$ {saldo_disponivel:.2f} disponível para novas subações."
                )

            # 3. Cria a Subação via Repository
            nova_subacao = self.subacao_repository.create(
                codigo, descricao, valor_novo, acao_id
            )
            
            if nova_subacao:
                # 4. Registro no Ledger (usando o objeto recém criado)
                if valor_novo > 0:
                    self.ledger_service.registrar_movimentacao(
                        entidade=nova_subacao,
                        valor=float(valor_novo),
                        tipo_operacao='SALDO_INICIAL'
                    )

                db.session.commit()
                return True 
            
            return False

        except ValueError as e:
            db.session.rollback()
            raise e # Repassa para a rota capturar e mostrar no flash
        except Exception as e:
            db.session.rollback()
            print(f"Erro inesperado no Service Subacao: {e}")
            return False

    def delete(self, subacao_id):
        try:
            # Import local para evitar erro circular com Ledger se necessário
            from models.models import MovimentacaoLedger
            
            # Limpa o histórico da subação no ledger antes de deletar
            MovimentacaoLedger.query.filter_by(subacao_id=subacao_id).delete()
            
            sucesso = self.subacao_repository.delete(subacao_id)
            if sucesso:
                db.session.commit()
                return True
            return False
        except Exception as e:
            db.session.rollback()
            print(f"Erro ao deletar subação: {e}")
            return False
    def get_all(self):
        try:
            subacoes = self.subacao_repository.get_all()
            return subacoes
        except Exception as e:
            print(f"Erro ao buscar subações: {e}")
            return []