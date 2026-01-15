# config.py
import os

class Config:
    # Substitua usuario, senha, host (geralmente localhost) e o nome do banco
    # Formato: mysql+pymysql://USUARIO:SENHA@HOST:PORTA/NOME_BANCO
    SQLALCHEMY_DATABASE_URI = 'mysql+pymysql://root:1234@localhost:3306/sistema_financeiro_acoes'
    
    # Desativa aviso de rastreamento de modificações (economiza memória)
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Chave secreta para sessões e segurança
    SECRET_KEY = 'chave_super_secreta_financeira'