from flask import Flask
from flask.json.provider import DefaultJSONProvider
from config_db import Config
from extensions import db
from decimal import Decimal

# Importando os Blueprints
from routes.movimentacoes import movimentacoes_bp
from routes.home import home_bp
from routes.acao import acao_bp 
from routes.subacao import subacao_bp
from routes.pf import pf_bp
from routes.transferencia import transferencia_bp
from routes.historico import historico_bp
from routes.orcamento import orcamento_bp

# --- CORREÇÃO PARA FLASK 3.0+ ---
# Nova forma de converter Decimal para JSON (para não dar erro nos gráficos/APIs)
class DecimalJSONProvider(DefaultJSONProvider):
    def default(self, obj):
        if isinstance(obj, Decimal):
            return float(obj)
        return super().default(obj)

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    
    # 1. Configura o Provider de JSON novo
    app.json = DecimalJSONProvider(app)
    
    # Inicializa o DB
    db.init_app(app)
    
    # Registra as Rotas
    app.register_blueprint(acao_bp, url_prefix='/acoes')
    app.register_blueprint(subacao_bp, url_prefix='/subacoes')
    app.register_blueprint(pf_bp, url_prefix='/pf')
    app.register_blueprint(transferencia_bp, url_prefix='/transferencias')
    app.register_blueprint(historico_bp, url_prefix='/historico')
    app.register_blueprint(home_bp, url_prefix='/')
    app.register_blueprint(movimentacoes_bp, url_prefix='/movimentacoes')
    app.register_blueprint(orcamento_bp, url_prefix='/')

    # --- FILTROS DE FORMATAÇÃO (JINJA2) ---

    # Filtro 1: Formata COM o símbolo (Ex: R$ 30.000,00)
    # Uso no HTML: {{ valor | format_currency }}
    @app.template_filter('format_currency')
    def format_currency(value):
        if value is None or value == '': 
            return "R$ 0,00"
        try:
            # Formata padrão US (30,000.00) e inverte os sinais
            return f"R$ {float(value):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        except (ValueError, TypeError):
            return "R$ 0,00"

    # Filtro 2: Formata SEM o símbolo (Ex: 30.000,00)
    # Uso no HTML: {{ valor | format_decimal }}
    @app.template_filter('format_decimal')
    def format_decimal(value):
        if value is None or value == '': 
            return "0,00"
        try:
            return f"{float(value):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        except (ValueError, TypeError):
            return "0,00"

    # 2. Cria as tabelas do banco se elas não existirem
    with app.app_context():
        # db.drop_all() # <-- CUIDADO: Descomente só se quiser limpar o banco
        db.create_all()

    return app

if __name__ == '__main__':
    app = create_app()
    # Dica: Em produção, desligue o debug
    app.run(debug=True, host='0.0.0.0', port=5071)