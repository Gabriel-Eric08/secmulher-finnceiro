from flask import Blueprint, render_template, request, redirect, url_for, flash
from services.subacao_service import SubacaoService
from services.acao_service import AcaoService

# Configuração dos Serviços
subacao_service = SubacaoService()
acao_service = AcaoService()

# ATENÇÃO: O nome do blueprint deve ser 'subacoes' para bater com url_for('subacoes.xyz')
subacao_bp = Blueprint('subacoes', __name__)

# 1. ROTA DE LISTAGEM (GET)
@subacao_bp.route('/', methods=['GET'])
def listar_subacoes():
    try:
        # Busca todas as subações para a tabela
        lista_subacoes = subacao_service.get_all()
        
        # Busca todas as ações para preencher o "Select/Dropdown" do formulário
        lista_acoes = acao_service.get_all()
        
        return render_template(
            'subacoes.html', 
            page='subacoes', 
            subacoes=lista_subacoes,
            acoes=lista_acoes 
        )
    except Exception as e:
        flash(f'Erro ao carregar dados: {str(e)}', 'danger')
        return render_template('subacoes.html', page='subacoes', subacoes=[], acoes=[])

# 2. ROTA DE CRIAÇÃO (POST)
@subacao_bp.route('/criar', methods=['POST'])
def criar_subacao():
    # Pega dados do formulário HTML
    codigo = request.form.get('codigo')
    descricao = request.form.get('descricao')
    orcamento_inicial = request.form.get('orcamento_inicial')
    acao_id = request.form.get('acao_id')

    # Validação simples de campos vazios
    if not all([codigo, descricao, orcamento_inicial, acao_id]):
        flash('Preencha todos os campos obrigatórios!', 'warning')
        return redirect(url_for('subacoes.listar_subacoes'))

    try:
        # Chama o método .create do serviço
        # Note que não precisamos converter para float aqui, o service já trata com Decimal
        sucesso = subacao_service.create(
            codigo=codigo,
            descricao=descricao,
            orcamento_inicial=orcamento_inicial,
            acao_id=int(acao_id)
        )
        
        if sucesso:
            flash('Subação criada com sucesso!', 'success')
        else:
            # Caso o service retorne False por outros motivos (ex: erro no repository)
            flash('Erro ao criar subação. Verifique os dados e tente novamente.', 'danger')
            
    except ValueError as e:
        # CAPTURA A REGRA DE NEGÓCIO: Aqui aparecerá "Orçamento excedido!..."
        flash(str(e), 'warning')
        
    except Exception as e:
        # Erros inesperados de sistema
        flash(f'Erro interno: {str(e)}', 'danger')

    return redirect(url_for('subacoes.listar_subacoes'))
# 3. ROTA DE EXCLUSÃO
@subacao_bp.route('/delete/<int:subacao_id>')
def delete_subacao(subacao_id):
    try:
        # Chama o método .delete do serviço
        if subacao_service.delete(subacao_id):
            flash('Subação removida com sucesso.', 'success')
        else:
            flash('Erro ao remover subação (Verifique se há movimentações financeiras vinculadas).', 'danger')
    except Exception as e:
        flash(f'Erro ao deletar: {str(e)}', 'danger')
        
    return redirect(url_for('subacoes.listar_subacoes'))