# main.py
from flask import Flask
from config_db import Config
from extensions import db
from routes.acoes import acoes_bp 

def create_app():
    app = Flask(__name__)
    
    # 1. Carregar Configurações
    app.config.from_object(Config)
    
    # 2. Inicializar o Banco de Dados com este App
    db.init_app(app)
    
    # 3. Registrar Blueprints
    app.register_blueprint(acoes_bp)
    # app.register_blueprint(pfs_bp)
    
    # 4. Criar tabelas automaticamente (útil em dev)
    with app.app_context():
        # Importar models aqui dentro para o SQLAlchemy reconhecê-los antes do create_all
        # from models import Acao, Subacao, PF (Exemplo)
        
        # db.create_all() # Descomente isso se quiser que o Flask crie as tabelas
        pass

    return app

# Bloco para rodar o servidor
if __name__ == '__main__':
    app = create_app()
    app.run(debug=True, port=5000)