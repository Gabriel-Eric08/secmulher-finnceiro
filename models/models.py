from extensions import db
from datetime import datetime
from sqlalchemy.dialects.mysql import JSON
from enum import Enum
from decimal import Decimal  # <--- IMPORTANTE: Adicione este import
import enum
# ---------------------------------------
# 1. Usuários e Autenticação
# ---------------------------------------
class Usuario(db.Model):
    __tablename__ = 'usuarios'

    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    senha_hash = db.Column(db.String(255), nullable=False)
    perfil = db.Column(db.Enum('ADMIN', 'OPERADOR'), default='OPERADOR')
    ativo = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.now)

    def __repr__(self):
        return f'<Usuario {self.nome}>'


# ---------------------------------------
# 2. Estrutura Orçamentária (Ações e Subações)
# ---------------------------------------
class Acao(db.Model):
    __tablename__ = 'acoes'

    id = db.Column(db.Integer, primary_key=True)
    codigo = db.Column(db.String(50), unique=True, nullable=False)
    descricao = db.Column(db.String(255))
    
    # CORREÇÃO: Usar Decimal('0.00') no default
    orcamento_inicial = db.Column(db.Numeric(15, 2), default=Decimal('0.00'))
    saldo_atual = db.Column(db.Numeric(15, 2), default=Decimal('0.00'))
    
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)

    subacoes = db.relationship('Subacao', backref='acao', cascade='all, delete-orphan', lazy=True)
    pfs = db.relationship('PF', backref='acao', cascade='all, delete-orphan', lazy=True)


    @property
    def orcamento_atual(self):
        return self.saldo_atual

    def __repr__(self):
        return f'<Acao {self.codigo} - Saldo: {self.saldo_atual}>'


class Subacao(db.Model):
    __tablename__ = 'subacoes'

    id = db.Column(db.Integer, primary_key=True)
    acao_id = db.Column(db.Integer, db.ForeignKey('acoes.id'), nullable=False)
    
    codigo = db.Column(db.String(50), nullable=False)
    descricao = db.Column(db.String(255))
    
    # CORREÇÃO: Usar Decimal('0.00') no default
    orcamento_inicial = db.Column(db.Numeric(15, 2), default=Decimal('0.00'))
    saldo_atual = db.Column(db.Numeric(15, 2), default=Decimal('0.00'))
    
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)

    __table_args__ = (db.UniqueConstraint('acao_id', 'codigo', name='uix_acao_codigo'),)

    def __repr__(self):
        return f'<Subacao {self.codigo} - Saldo: {self.saldo_atual}>'


# ---------------------------------------
# 3. Movimentações Financeiras (PFs e Transferências)
# ---------------------------------------
class StatusPF(str, enum.Enum):
    AGUARDANDO = "AGUARDANDO"
    EMPENHADO_PARCIAL = "EMPENHADO_PARCIAL"
    EMPENHADO_TOTAL = "EMPENHADO_TOTAL"
    LIQUIDADO_PARCIAL = "LIQUIDADO_PARCIAL"
    LIQUIDADO_TOTAL = "LIQUIDADO_TOTAL"
    # Novos Status
    PAGO_PARCIAL = "PAGO_PARCIAL"
    PAGO_TOTAL = "PAGO_TOTAL"

# 2. Na classe PF, adicione os campos de pagamento
class PF(db.Model):
    __tablename__ = 'pfs'
    # --- O ERRO ESTAVA AQUI (Faltava o ID) ---
    id = db.Column(db.Integer, primary_key=True) 
    # -----------------------------------------
    
    descricao = db.Column(db.String(500), nullable=False)
    
    # Valores
    valor_total = db.Column(db.Numeric(10, 2), nullable=False)
    valor_empenhado = db.Column(db.Numeric(10, 2), default=0.00)
    valor_liquidado = db.Column(db.Numeric(10, 2), default=0.00)
    valor_pago = db.Column(db.Numeric(10, 2), default=0.00)

    # Datas e Status
    data_cadastro = db.Column(db.DateTime, default=datetime.now)
    data_ultimo_empenho = db.Column(db.DateTime, nullable=True)
    data_ultima_liquidacao = db.Column(db.DateTime, nullable=True)
    data_ultimo_pagamento = db.Column(db.DateTime, nullable=True)
    
    status = db.Column(db.Enum(StatusPF), default=StatusPF.AGUARDANDO)

    # Relacionamentos
    acao_id = db.Column(db.Integer, db.ForeignKey('acoes.id'), nullable=False)
    subacao_id = db.Column(db.Integer, db.ForeignKey('subacoes.id'), nullable=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)

    subacao = db.relationship('Subacao', backref='pfs', lazy=True)


class Transferencia(db.Model):
    __tablename__ = 'transferencias'

    id = db.Column(db.Integer, primary_key=True)
    tipo = db.Column(db.Enum('CA', 'RO'), nullable=False)
    
    acao_origem_id = db.Column(db.Integer, db.ForeignKey('acoes.id'), nullable=False)
    subacao_origem_id = db.Column(db.Integer, db.ForeignKey('subacoes.id'), nullable=True)
    
    acao_destino_id = db.Column(db.Integer, db.ForeignKey('acoes.id'), nullable=False)
    subacao_destino_id = db.Column(db.Integer, db.ForeignKey('subacoes.id'), nullable=True)
    
    valor = db.Column(db.Numeric(15, 2), nullable=False)
    data_transferencia = db.Column(db.DateTime, default=datetime.now)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)

    acao_origem = db.relationship('Acao', foreign_keys=[acao_origem_id])
    acao_destino = db.relationship('Acao', foreign_keys=[acao_destino_id])


# ---------------------------------------
# 4. O Coração: Ledger (Livro Razão)
# ---------------------------------------
class MovimentacaoLedger(db.Model):
    __tablename__ = 'movimentacoes_ledger'

    id = db.Column(db.BigInteger, primary_key=True)
    
    acao_id = db.Column(db.Integer, db.ForeignKey('acoes.id'), nullable=False)
    subacao_id = db.Column(db.Integer, db.ForeignKey('subacoes.id'), nullable=True)
    
    tipo_operacao = db.Column(db.Enum(
        'SALDO_INICIAL', 
        'PF_CRIACAO', 
        'PF_ESTORNO', 
        'TRANSF_ENTRADA', 
        'TRANSF_SAIDA',
        'EMPENHO',      # Adicionei para garantir que o enum bata com o service
        'LIQUIDACAO',
        'PAGAMENTO'   # Adicionei para garantir que o enum bata com o service
    ), nullable=False)
    
    pf_id = db.Column(db.Integer, db.ForeignKey('pfs.id'), nullable=True)
    transferencia_id = db.Column(db.Integer, db.ForeignKey('transferencias.id'), nullable=True)
    
    valor_movimento = db.Column(db.Numeric(15, 2), nullable=False)
    saldo_anterior = db.Column(db.Numeric(15, 2), nullable=False)
    saldo_novo = db.Column(db.Numeric(15, 2), nullable=False)
    
    data_movimento = db.Column(db.DateTime, default=datetime.now, index=True)


# ---------------------------------------
# 5. Auditoria Administrativa
# ---------------------------------------
class LogAuditoria(db.Model):
    __tablename__ = 'logs_auditoria'

    id = db.Column(db.Integer, primary_key=True)
    tabela_afetada = db.Column(db.String(50), nullable=False)
    registro_id = db.Column(db.Integer, nullable=False)
    acao_realizada = db.Column(db.String(50), nullable=False)
    
    dados_anteriores = db.Column(JSON, nullable=True)
    dados_novos = db.Column(JSON, nullable=True)
    
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)
    data_log = db.Column(db.DateTime, default=datetime.now)