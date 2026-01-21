from flask import Blueprint, render_template, request, redirect, url_for, flash
from services.acao_service import AcaoService

# Configuração do Blueprint
# O nome 'acoes' é o que usamos no HTML: url_for('acoes.criar_acao')
acao_bp = Blueprint('acoes', __name__)
acao_service = AcaoService()

# 1. ROTA DE LISTAGEM (GET)
@acao_bp.route('/', methods=['GET'])
def listar_acoes():
    try:
        lista_acoes = acao_service.get_all()
        return render_template('acoes.html', page='acoes', acoes=lista_acoes)
    except Exception as e:
        flash(f'Erro ao carregar ações: {str(e)}', 'danger')
        return render_template('acoes.html', page='acoes', acoes=[])

# 2. ROTA DE CRIAÇÃO (POST)
@acao_bp.route('/criar', methods=['POST'])
def criar_acao():
    codigo = request.form.get('codigo')
    descricao = request.form.get('descricao')
    orcamento_inicial = request.form.get('orcamento_inicial')

    # Validação simples
    if not all([codigo, descricao, orcamento_inicial]):
        flash('Todos os campos são obrigatórios!', 'warning')
        return redirect(url_for('acoes.listar_acoes'))

    try:
        sucesso = acao_service.create(
            codigo=codigo, 
            descricao=descricao, 
            orcamento_inicial=float(orcamento_inicial)
        )
        
        if sucesso:
            flash('Ação criada com sucesso!', 'success')
        else:
            flash('Erro ao criar: Verifique se o código já existe.', 'danger')
            
    except ValueError:
        flash('O orçamento inicial deve ser um número válido.', 'warning')
    except Exception as e:
        flash(f'Erro interno: {str(e)}', 'danger')
        
    return redirect(url_for('acoes.listar_acoes'))

# 3. ROTA DE EXCLUSÃO
# Atenção: No HTML, o link deve ser url_for('acoes.deletar_acao', acao_id=x)
@acao_bp.route('/deletar/<int:acao_id>')
def deletar_acao(acao_id):
    try:
        if acao_service.delete(acao_id):
            flash('Ação removida com sucesso.', 'success')
        else:
            flash('Não foi possível remover. Verifique se a ação possui Subações ou Movimentações vinculadas.', 'danger')
    except Exception as e:
        flash(f'Erro ao deletar: {str(e)}', 'danger')
        
    return redirect(url_for('acoes.listar_acoes'))