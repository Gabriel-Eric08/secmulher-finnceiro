from repositories.ledger_repository import LedgerRepository
from decimal import Decimal
from models.models import PF

class LedgerService:
    def __init__(self):
        self.ledger_repository = LedgerRepository()

    def registrar_movimentacao(self, entidade, valor, tipo_operacao, pf_id=None, transferencia_id=None):
        """
        Registra uma entrada no histórico financeiro (Ledger).
        Aceita tanto objeto Acao, Subacao quanto PF.
        """
        try:
            # --- PROTEÇÃO 1: Conversão imediata do valor de entrada ---
            val_decimal = Decimal(str(valor))

            acao_id = None
            subacao_id = None
            
            # Lógica para identificar IDs baseada no tipo da entidade
            # 1. Se for um PF (tem acao_id e subacao_id, mas é um objeto PF)
            if isinstance(entidade, PF) or hasattr(entidade, 'valor_total'):
                acao_id = entidade.acao_id
                subacao_id = entidade.subacao_id # Pode ser None
                
            # 2. Se for uma SUBAÇÃO (tem acao_id e NÃO é PF)
            elif hasattr(entidade, 'acao_id') and hasattr(entidade, 'codigo'):
                acao_id = entidade.acao_id
                subacao_id = entidade.id
                
            # 3. Se for uma AÇÃO MÃE (tem orcamento_inicial e não tem acao_id)
            elif hasattr(entidade, 'orcamento_inicial'):
                acao_id = entidade.id
            
            if not acao_id:
                print("Erro Ledger: Não foi possível identificar Ação ID.")
                return False

            # Busca saldo anterior no repositório
            saldo_anterior_raw = self.ledger_repository.get_saldo_em_data(acao_id, '9999-12-31', subacao_id)
            
            # --- PROTEÇÃO 2: Conversão do retorno do banco para Decimal ---
            # O banco pode retornar None ou float, aqui garantimos Decimal
            if saldo_anterior_raw is None:
                saldo_ant_decimal = Decimal('0.00')
            else:
                saldo_ant_decimal = Decimal(str(saldo_anterior_raw))

            # Cálculo Seguro
            if tipo_operacao == 'SALDO_INICIAL':
                saldo_novo = val_decimal
            else:
                saldo_novo = saldo_ant_decimal + val_decimal

            # Chama o repositório para salvar
            self.ledger_repository.create(
                acao_id=acao_id,
                subacao_id=subacao_id,
                tipo_operacao=tipo_operacao,
                valor=val_decimal,           # Passa Decimal
                saldo_anterior=saldo_ant_decimal, # Passa Decimal
                saldo_novo=saldo_novo,       # Passa Decimal
                pf_id=pf_id,
                transferencia_id=transferencia_id
            )
            return True

        except Exception as e:
            print(f"Erro no LedgerService: {e}")
            raise e 
            
    def get_saldo_em_data(self, acao_id, data_limite, subacao_id=None):
        valor = self.ledger_repository.get_saldo_em_data(acao_id, data_limite, subacao_id)
        return Decimal(str(valor)) if valor is not None else Decimal('0.00')