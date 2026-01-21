from repositories.pf_repository import PFRepository
from services.ledger_service import LedgerService
from models.models import Acao, Subacao, StatusPF, db
from datetime import datetime
from decimal import Decimal

class PFService:
    def __init__(self):
        self.pf_repository = PFRepository()
        self.ledger_service = LedgerService()
    
    def criar_pf(self, acao_id, subacao_id, descricao, valor_total, usuario_id):
        """
        Cria a PF (Planejamento) e já reserva o saldo da Ação/Subação.
        """
        try:
            valor = Decimal(valor_total)
            entidade_pagadora = None

            # 1. Identificar Origem e Validar Saldo
            if subacao_id:
                entidade_pagadora = Subacao.query.get(subacao_id)
            else:
                entidade_pagadora = Acao.query.get(acao_id)

            if not entidade_pagadora:
                raise ValueError("Ação ou Subação não encontrada.")

            # REGRA: Não pode criar PF se não tiver saldo na fonte
            if entidade_pagadora.saldo_atual < valor:
                raise ValueError(f"Saldo insuficiente na origem! Disponível: {entidade_pagadora.saldo_atual}")

            # 2. Cria a PF (Status Aguardando)
            novo_pf = self.pf_repository.create(
                acao_id, subacao_id, descricao, valor, usuario_id
            )

            # 3. Debita da Ação/Subação (O dinheiro fica 'preso' na PF)
            entidade_pagadora.saldo_atual -= valor

            # 4. Ledger: Registra a Criação/Reserva
            self.ledger_service.registrar_movimentacao(
                entidade=entidade_pagadora,
                valor=-valor, 
                tipo_operacao='PF_CRIACAO', # Indica reserva de orçamento
                pf_id=novo_pf.id
            )

            db.session.commit()
            return novo_pf

        except Exception as e:
            db.session.rollback()
            raise e

    def realizar_empenho(self, pf_id, valor_a_empenhar):
        """
        Consome o 'valor_total' planejado e transforma em 'valor_empenhado'.
        """
        try:
            pf = self.pf_repository.get_by_id(pf_id)
            valor = Decimal(valor_a_empenhar)
            
            if not pf: raise ValueError("PF não encontrada")

            # REGRA: Não pode empenhar mais do que foi planejado (Saldo Disponível na PF)
            saldo_para_empenhar = pf.valor_total - pf.valor_empenhado
            if valor > saldo_para_empenhar:
                raise ValueError(f"Valor excede o saldo disponível para empenho. Restante: {saldo_para_empenhar}")

            # Atualiza valores
            pf.valor_empenhado += valor
            pf.data_ultimo_empenho = datetime.now()

            # Atualiza Status
            if pf.valor_empenhado >= pf.valor_total:
                pf.status = StatusPF.EMPENHADO_TOTAL
            else:
                pf.status = StatusPF.EMPENHADO_PARCIAL

            # Salva
            self.pf_repository.save(pf)

            # Ledger (Apenas informativo, pois o dinheiro já saiu da Subação na criação)
            # Mas é crucial registrar para o histórico de "Status por data"
            origem = Subacao.query.get(pf.subacao_id) if pf.subacao_id else Acao.query.get(pf.acao_id)
            self.ledger_service.registrar_movimentacao(
                entidade=origem,
                valor=valor, # Valor simbólico ou zero, dependendo se você quer mexer no caixa de novo. Normalmente aqui é só registro.
                tipo_operacao='EMPENHO',
                pf_id=pf.id
            )
            
            db.session.commit()
            return pf

        except Exception as e:
            db.session.rollback()
            raise e

    def realizar_liquidacao(self, pf_id, valor_a_liquidar):
        """
        Registra pagamento. Deduz do 'valor_empenhado' pendente.
        """
        try:
            pf = self.pf_repository.get_by_id(pf_id)
            valor = Decimal(valor_a_liquidar)
            
            if not pf: raise ValueError("PF não encontrada")

            # REGRA: Só liquida o que já foi empenhado
            saldo_a_liquidar = pf.valor_empenhado - pf.valor_liquidado
            if valor > saldo_a_liquidar:
                raise ValueError(f"Valor maior que o empenhado pendente. Disponível: {saldo_a_liquidar}")

            # Atualiza valores
            pf.valor_liquidado += valor
            pf.data_ultima_liquidacao = datetime.now()

            # Atualiza Status
            if pf.valor_liquidado >= pf.valor_total:
                pf.status = StatusPF.LIQUIDADO_TOTAL
            elif pf.valor_liquidado > 0:
                pf.status = StatusPF.LIQUIDADO_PARCIAL

            self.pf_repository.save(pf)

            # Ledger (Registro do pagamento/nota fiscal)
            origem = Subacao.query.get(pf.subacao_id) if pf.subacao_id else Acao.query.get(pf.acao_id)
            self.ledger_service.registrar_movimentacao(
                entidade=origem,
                valor=valor,
                tipo_operacao='LIQUIDACAO',
                pf_id=pf.id
            )

            db.session.commit()
            return pf

        except Exception as e:
            db.session.rollback()
            raise e

    def get_all(self):
        return self.pf_repository.get_all()