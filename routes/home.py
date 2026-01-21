from flask import Blueprint, render_template
from services.acao_service import AcaoService
from services.subacao_service import SubacaoService

home_bp = Blueprint('home', __name__)

@home_bp.route('/')
def dashboard():
    # Buscando dados reais para os cards do dashboard
    acao_service = AcaoService()
    sub_service = SubacaoService()
    
    acoes = acao_service.get_all()
    
    total_acoes = len(acoes)
    orcamento_total = sum(a.orcamento_inicial for a in acoes)
    saldo_atual = sum(a.orcamento_atual for a in acoes)
    
    return render_template('index.html', 
                           page='dashboard',
                           total_acoes=total_acoes,
                           orcamento_total=orcamento_total,
                           saldo_atual=saldo_atual)