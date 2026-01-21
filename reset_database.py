from main import create_app  # Importa a factory do seu arquivo main.py
from extensions import db
# É importante importar os models para o SQLAlchemy saber quais tabelas criar
from models.models import Usuario, Acao, Subacao, PF, Transferencia, MovimentacaoLedger, LogAuditoria

# 1. Cria a instância da aplicação
app = create_app()

# 2. Abre o contexto da aplicação (isso carrega as configs do banco)
with app.app_context():
    print("--- INICIANDO RESET DO BANCO DE DADOS ---")
    
    print("1. Apagando tabelas antigas (com Floats)...")
    db.drop_all()
    
    print("2. Criando novas tabelas (com Decimals)...")
    db.create_all()
    
    print("--- SUCESSO: BANCO LIMPO E RECRIADO ---")