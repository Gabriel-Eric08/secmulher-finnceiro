from flask import Blueprint, render_template, request, redirect, url_for, flash
from services.movimentacao_service import MovimentacaoService
from services.acao_service import AcaoService
from services.subacao_service import SubacaoService
from models.models import PF
from decimal import Decimal

movimentacoes_bp = Blueprint('movimentacoes', __name__)

# Instanciando os serviços
mov_service = MovimentacaoService() # Instância correta
acao_service = AcaoService()
subacao_service = SubacaoService()

# 1. LISTAR (GET) -> Renomeado para 'index' para corrigir o erro de BuildError
@movimentacoes_bp.route('/', methods=['GET'])
def index():
    try:
        # Usando os métodos do MovimentacaoService unificado
        pfs = mov_service.get_all_pfs()
        transferencias = mov_service.get_all_transferencias()
        
        # Para preencher os Selects dos Modais
        acoes = acao_service.get_all()
        subacoes = subacao_service.get_all()
        
        return render_template(
            'movimentacoes.html', 
            page='movimentacoes',
            pfs=pfs,
            transferencias=transferencias,
            acoes=acoes,
            subacoes=subacoes
        )
    except Exception as e:
        flash(f'Erro ao carregar dados: {str(e)}', 'danger')
        return render_template('movimentacoes.html', page='movimentacoes', pfs=[], transferencias=[], acoes=[], subacoes=[])

# 2. CRIAR PF (POST)
@movimentacoes_bp.route('/pf/criar', methods=['POST'])
def criar_pf():
    try:
        acao_id = request.form.get('acao_id')
        subacao_id = request.form.get('subacao_id')
        descricao = request.form.get('descricao')
        valor = request.form.get('valor')
        
        # Tratamento do subacao_id
        if not subacao_id or subacao_id == '':
            subacao_id = None
        else:
            subacao_id = int(subacao_id)

        mov_service.criar_pf(
            acao_id=int(acao_id),
            subacao_id=subacao_id,
            descricao=descricao,
            valor=valor, # Deixe o service converter para Decimal
            usuario_id=1 # Ou current_user.id
        )
        flash('PF emitido com sucesso!', 'success')

    except ValueError as e:
        # Aqui capturamos a mensagem "Saldo insuficiente..." vinda do service
        flash(f'{str(e)}', 'warning')
    except Exception as e:
        # Erros inesperados ou de banco de dados
        flash(f'Erro ao criar PF: {str(e)}', 'danger')

    return redirect(url_for('movimentacoes.index'))

# 3. CRIAR TRANSFERÊNCIA (POST)
@movimentacoes_bp.route('/transferencia/criar', methods=['POST'])
def criar_transferencia():
    try:
        acao_origem = request.form.get('acao_origem_id')
        sub_origem = request.form.get('subacao_origem_id')
        
        acao_destino = request.form.get('acao_destino_id')
        sub_destino = request.form.get('subacao_destino_id')
        
        valor = request.form.get('valor')
        tipo = request.form.get('tipo', 'RO') 

        dados = {
            'acao_origem_id': int(acao_origem),
            'subacao_origem_id': int(sub_origem) if sub_origem else None,
            'acao_destino_id': int(acao_destino),
            'subacao_destino_id': int(sub_destino) if sub_destino else None,
            'valor': valor,
            'tipo': tipo,
            'usuario_id': 1 
        }

        mov_service.criar_transferencia(dados)
        flash('Transferência realizada com sucesso!', 'success')
        
    except ValueError:
        flash('Erro de formato nos valores.', 'warning')
    except Exception as e:
        flash(f'Erro na transferência: {str(e)}', 'danger')

    return redirect(url_for('movimentacoes.index'))

# 4. DETALHE DO PF
@movimentacoes_bp.route('/pf/<int:pf_id>', methods=['GET'])
def detalhe_pf(pf_id):
    pf = PF.query.get_or_404(pf_id)
    
    saldo_a_empenhar = pf.valor_total - pf.valor_empenhado
    saldo_a_liquidar = pf.valor_empenhado - pf.valor_liquidado
    
    return render_template(
        'detalhe_pf.html', 
        pf=pf, 
        saldo_a_empenhar=saldo_a_empenhar,
        saldo_a_liquidar=saldo_a_liquidar
    )

# --- ROTA POST PARA EMPENHAR ---
@movimentacoes_bp.route('/pf/<int:pf_id>/empenhar', methods=['POST'])
def post_empenhar(pf_id):
    # ANTES ERA: valor = float(request.form.get('valor', 0))
    # MUDE PARA:
    valor = Decimal(request.form.get('valor', '0'))
    
    usuario_id = 1 
    
    sucesso, msg = mov_service.realizar_empenho(pf_id, valor, usuario_id)
    
    if sucesso:
        flash(msg, 'success')
    else:
        flash(f"Erro: {msg}", 'danger')
        
    return redirect(url_for('movimentacoes.detalhe_pf', pf_id=pf_id))

# --- ROTA POST PARA LIQUIDAR ---
@movimentacoes_bp.route('/pf/<int:pf_id>/liquidar', methods=['POST'])
def post_liquidar(pf_id):
    # ANTES ERA: valor = float(request.form.get('valor', 0))
    # MUDE PARA:
    valor = Decimal(request.form.get('valor', '0'))
    
    usuario_id = 1 
    
    sucesso, msg = mov_service.realizar_liquidacao(pf_id, valor, usuario_id)
    
    if sucesso:
        flash(msg, 'success')
    else:
        flash(f"Erro: {msg}", 'danger')
        
    return redirect(url_for('movimentacoes.detalhe_pf', pf_id=pf_id))

@movimentacoes_bp.route('/pf/<int:pf_id>/pagar', methods=['POST'])
def post_pagar(pf_id):
    # Recebe o valor do formulário como Decimal para evitar erros de precisão
    valor = Decimal(request.form.get('valor', '0'))
    
    usuario_id = 1 
    
    # Chama o serviço (certifique-se de que o método realizar_pagamento existe no seu MovimentacaoService)
    sucesso, msg = mov_service.realizar_pagamento(pf_id, valor, usuario_id)
    
    if sucesso:
        flash(msg, 'success')
    else:
        flash(f"Erro: {msg}", 'danger')
        
    return redirect(url_for('movimentacoes.detalhe_pf', pf_id=pf_id))