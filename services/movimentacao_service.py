from models.models import PF, Transferencia, Subacao, Acao, StatusPF
from services.ledger_service import LedgerService
from extensions import db
from datetime import datetime
from decimal import Decimal, InvalidOperation
import traceback

# --- FUNÇÃO AUXILIAR GLOBAL ---
def to_decimal(valor):
    """
    Converte qualquer valor (float, str, None) para Decimal de forma segura.
    Evita erros de conversão direta e problemas com ponto flutuante.
    """
    if valor is None or valor == '':
        return Decimal('0.00')
    if isinstance(valor, Decimal):
        return valor
    try:
        return Decimal(str(valor))
    except InvalidOperation:
        return Decimal('0.00')

class MovimentacaoService:
    def __init__(self):
        self.ledger_service = LedgerService()

    def get_all_pfs(self):
        return PF.query.order_by(PF.data_cadastro.desc()).all()

    def get_all_transferencias(self):
        return Transferencia.query.order_by(Transferencia.data_transferencia.desc()).all()

    def criar_pf(self, acao_id, subacao_id, descricao, valor, usuario_id):
        try:
            valor_decimal = to_decimal(valor)

            # --- REGRA DE OURO: VALIDAÇÃO DE SALDO ---
            if subacao_id:
                entidade = Subacao.query.get(subacao_id)
                nome_entidade = f"Subação {entidade.codigo}"
            else:
                entidade = Acao.query.get(acao_id)
                nome_entidade = f"Ação {entidade.codigo}"

            # Verifica se o valor do PF é maior que o saldo atual da entidade
            if valor_decimal > entidade.saldo_atual:
                raise ValueError(f"Saldo insuficiente na {nome_entidade}! Disponível: R$ {entidade.saldo_atual}")
            # -----------------------------------------

            novo_pf = PF(
                acao_id=acao_id,
                subacao_id=subacao_id if subacao_id else None,
                descricao=descricao,
                valor_total=valor_decimal,
                valor_empenhado=Decimal('0.00'),
                valor_liquidado=Decimal('0.00'),
                valor_pago=Decimal('0.00'),
                status=StatusPF.AGUARDANDO, 
                data_cadastro=datetime.now(),
                usuario_id=usuario_id
            )
            
            db.session.add(novo_pf)
            db.session.flush()

            self.ledger_service.registrar_movimentacao(
                entidade=entidade,
                valor=-abs(valor_decimal),
                tipo_operacao='PF_CRIACAO',
                pf_id=novo_pf.id
            )

            db.session.commit()
            return True

        except ValueError as e:
            db.session.rollback()
            raise e  # Repassa o erro de saldo para a rota
        except Exception as e:
            db.session.rollback()
            print(f"Erro ao criar PF: {e}")
            raise Exception("Erro interno ao processar o PF.")

    def criar_transferencia(self, dados):
        try:
            valor_decimal = to_decimal(dados['valor'])

            # --- REGRA DE OURO: VALIDAÇÃO DE SALDO NA ORIGEM ---
            if dados.get('subacao_origem_id'):
                origem = Subacao.query.get(dados['subacao_origem_id'])
            else:
                origem = Acao.query.get(dados['acao_origem_id'])

            if valor_decimal > origem.saldo_atual:
                raise ValueError(f"Saldo insuficiente para transferência! Disponível na origem: R$ {origem.saldo_atual}")
            # --------------------------------------------------

            nova_transf = Transferencia(
                tipo=dados['tipo'],
                valor=valor_decimal,
                acao_origem_id=dados['acao_origem_id'],
                subacao_origem_id=dados.get('subacao_origem_id') or None,
                acao_destino_id=dados['acao_destino_id'],
                subacao_destino_id=dados.get('subacao_destino_id') or None,
                usuario_id=dados['usuario_id'],
                data_transferencia=datetime.now()
            )
            db.session.add(nova_transf)
            db.session.flush()

            # Registro de Saída
            self.ledger_service.registrar_movimentacao(
                entidade=origem,
                valor=-abs(valor_decimal),
                tipo_operacao='TRANSF_SAIDA',
                transferencia_id=nova_transf.id
            )

            # Registro de Entrada
            if nova_transf.subacao_destino_id:
                destino = Subacao.query.get(nova_transf.subacao_destino_id)
            else:
                destino = Acao.query.get(nova_transf.acao_destino_id)

            self.ledger_service.registrar_movimentacao(
                entidade=destino,
                valor=abs(valor_decimal),
                tipo_operacao='TRANSF_ENTRADA',
                transferencia_id=nova_transf.id
            )

            db.session.commit()
            return True

        except ValueError as e:
            db.session.rollback()
            raise e
        except Exception as e:
            db.session.rollback()
            raise Exception("Erro ao processar transferência.")

    def realizar_empenho(self, pf_id, valor, usuario_id):
        """
        Atualiza o valor empenhado do PF.
        """
        pf = PF.query.get(pf_id)
        if not pf: return False, "PF não encontrado."

        try:
            # --- BLINDAGEM DE TIPOS ---
            valor_input = to_decimal(valor)
            total_pf = to_decimal(pf.valor_total)
            empenhado_atual = to_decimal(pf.valor_empenhado)

            # Validação
            saldo_disponivel = total_pf - empenhado_atual
            
            if valor_input > saldo_disponivel:
                return False, f"Saldo insuficiente. Disponível para empenho: R$ {saldo_disponivel}"

            # 3. Atualiza valor
            pf.valor_empenhado = empenhado_atual + valor_input
            pf.data_ultimo_empenho = datetime.now()

            # 4. Atualiza Status
            if pf.valor_empenhado >= total_pf:
                pf.status = StatusPF.EMPENHADO_TOTAL
            else:
                pf.status = StatusPF.EMPENHADO_PARCIAL
            
            # 5. Registra no Ledger
            self.ledger_service.registrar_movimentacao(
                entidade=pf, 
                valor=valor_input, 
                tipo_operacao='EMPENHO',
                pf_id=pf.id
            )

            db.session.commit()
            return True, "Empenho realizado com sucesso!"

        except Exception as e:
            db.session.rollback()
            return False, str(e)

    def realizar_liquidacao(self, pf_id, valor, usuario_id):
        """
        Atualiza o valor liquidado do PF.
        """
        pf = PF.query.get(pf_id)
        if not pf: return False, "PF não encontrado."

        try:
            valor_input = to_decimal(valor)
            total_pf = to_decimal(pf.valor_total)
            empenhado_atual = to_decimal(pf.valor_empenhado)
            liquidado_atual = to_decimal(pf.valor_liquidado)

            # Validação: Não pode liquidar mais do que foi empenhado
            saldo_a_liquidar = empenhado_atual - liquidado_atual

            if valor_input > saldo_a_liquidar:
                return False, f"Valor excede o saldo empenhado. Disponível para liquidação: R$ {saldo_a_liquidar}"

            # 3. Atualiza valores
            pf.valor_liquidado = liquidado_atual + valor_input
            pf.data_ultima_liquidacao = datetime.now()

            # 4. Atualiza Status
            if pf.valor_liquidado >= total_pf:
                pf.status = StatusPF.LIQUIDADO_TOTAL
            else:
                pf.status = StatusPF.LIQUIDADO_PARCIAL

            # 5. Registra no Ledger
            self.ledger_service.registrar_movimentacao(
                entidade=pf,
                valor=valor_input, 
                tipo_operacao='LIQUIDACAO',
                pf_id=pf.id
            )

            db.session.commit()
            return True, "Liquidação realizada com sucesso!"
            
        except Exception as e:
            db.session.rollback()
            return False, str(e)

    def realizar_pagamento(self, pf_id, valor, usuario_id):
        """
        Registra o pagamento de um valor já liquidado.
        """
        pf = PF.query.get(pf_id)
        if not pf: return False, "PF não encontrado."

        try:
            valor_pagar = to_decimal(valor)
            liquidado = to_decimal(pf.valor_liquidado)
            pago = to_decimal(pf.valor_pago)
            
            # Regra: Só pode pagar o que foi liquidado
            # Saldo a Pagar = Total Liquidado - Já Pago
            saldo_a_pagar = liquidado - pago

            if valor_pagar > saldo_a_pagar:
                return False, f"Valor excede o saldo liquidado a pagar. Disponível: {saldo_a_pagar}"

            # Atualiza valores
            pf.valor_pago = pago + valor_pagar
            pf.data_ultimo_pagamento = datetime.now()

            # Atualiza Status
            total_pf = to_decimal(pf.valor_total)
            
            # Lógica de status hierárquica
            if pf.valor_pago >= total_pf:
                pf.status = StatusPF.PAGO_TOTAL
            else:
                pf.status = StatusPF.PAGO_PARCIAL
            
            db.session.add(pf)
            db.session.flush()

            # Registra no Ledger
            self.ledger_service.registrar_movimentacao(
                entidade=pf, 
                valor=valor_pagar, 
                tipo_operacao='PAGAMENTO',
                pf_id=pf.id
            )

            db.session.commit()
            return True, "Pagamento realizado com sucesso!"

        except Exception as e:
            db.session.rollback()
            print(traceback.format_exc())
            return False, str(e)