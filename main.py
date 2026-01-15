# main.py
from flask import Flask
from config_db import Config
from extensions import db
from routes.acao import acao_bp 
from routes.subacao import subacao_bp

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    db.init_app(app)
    
    app.register_blueprint(acao_bp, url_prefix='/acoes')
    app.register_blueprint(subacao_bp, url_prefix='/subacoes')

    return app

# Bloco para rodar o servidor
if __name__ == '__main__':
    app = create_app()
    app.run(debug=True, port=5071)