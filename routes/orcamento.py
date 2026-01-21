from flask import Blueprint, render_template, request
from datetime import datetime, date
from sqlalchemy import func
from decimal import Decimal

# Importações dos Modelos e DB
from models.models import Acao, Subacao, MovimentacaoLedger, PF
from extensions import db

orcamento_bp = Blueprint('orcamento', __name__)

# --- FUNÇÃO AUXILIAR (Mantida para compatibilidade futura) ---
def get_total_por_tipo(acao_id, tipo_operacao, data_limite, subacao_id=None):
    try:
        query = db.session.query(func.sum(MovimentacaoLedger.valor_movimento))\
            .join(PF, MovimentacaoLedger.pf_id == PF.id)\
            .filter(PF.acao_id == acao_id)
        
        if subacao_id:
            query = query.filter(PF.subacao_id == subacao_id)
            
        query = query.filter(MovimentacaoLedger.tipo_operacao == tipo_operacao)
        query = query.filter(func.date(MovimentacaoLedger.data_movimentacao) <= data_limite)
        
        resultado = query.scalar()
        return Decimal(resultado) if resultado else Decimal('0.00')
    except Exception as e:
        print(f"Erro calculando {tipo_operacao}: {e}")
        return Decimal('0.00')

# --- ROTAS ---

@orcamento_bp.route('/acoes/<int:id>/consulta', methods=['GET'])
def consultar_acao(id):
    acao = Acao.query.get_or_404(id)
    
    # 1. Filtro de Data
    data_param = request.args.get('data_corte')
    if data_param:
        try:
            data_consulta = datetime.strptime(data_param, '%Y-%m-%d').date()
        except ValueError:
            data_consulta = date.today()
    else:
        data_consulta = date.today()

    # 2. Busca FILTRADA de PFs
    # Filtra PFs criados até a data selecionada
    pfs = PF.query.filter(
        PF.acao_id == id,
        func.date(PF.data_cadastro) <= data_consulta
    ).all()

    subacoes = Subacao.query.filter_by(acao_id=id).all()

    # 3. CÁLCULO DOS VALORES (Lógica de Fluxo/Abatimento)
    
    # A) Primeiro, somamos os valores TOTAIS reais de cada etapa
    total_empenhado_bruto = sum(pf.valor_empenhado for pf in pfs)
    total_liquidado_bruto = sum(pf.valor_liquidado for pf in pfs)
    total_pago_bruto      = sum(pf.valor_pago for pf in pfs)

    # B) Agora aplicamos a lógica de abatimento para visualização (Saldos Pendentes)
    
    # Card Empenhado: Mostra apenas o que falta liquidar
    # Ex: Empenhei 150, Liquidei 100 -> Mostra 50
    visual_empenhado = total_empenhado_bruto - total_liquidado_bruto
    
    # Card Liquidado: Mostra apenas o que falta pagar
    # Ex: Liquidei 100, Paguei 0 -> Mostra 100
    visual_liquidado = total_liquidado_bruto - total_pago_bruto
    
    # Card Pago: Mostra o total pago efetivamente
    visual_pago = total_pago_bruto

    orcamento_inicial = Decimal(str(acao.orcamento_inicial))
    
    # Disponível: Calculado sobre o total bruto empenhado (pois o orçamento já foi comprometido)
    disponivel = orcamento_inicial - total_empenhado_bruto

    return render_template(
        'detalhes_acao.html', 
        acao=acao,
        subacoes=subacoes,
        pfs=pfs,
        resumo={
            'orcamento': orcamento_inicial,
            'empenhado': visual_empenhado, # Valor abatido (Saldo a Liquidar)
            'liquidado': visual_liquidado, # Valor abatido (Saldo a Pagar)
            'pago': visual_pago,           # Valor Total Pago
            'disponivel': disponivel
        },
        data_atual=data_consulta.strftime('%Y-%m-%d')
    )

@orcamento_bp.route('/subacoes/<int:id>/consulta', methods=['GET'])
def consultar_subacao(id):
    return "Em desenvolvimento"