from extensions import db
from datetime import datetime
from sqlalchemy.dialects.mysql import JSON

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
    codigo = db.Column(db.String(20), unique=True, nullable=False)  # Ex: 202512
    descricao = db.Column(db.String(255))
    
    # DECIMAL(15,2) é crucial para dinheiro. Float gera erros de arredondamento.
    orcamento_inicial = db.Column(db.Numeric(15, 2), default=0.00)
    saldo_atual = db.Column(db.Numeric(15, 2), default=0.00)
    
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)

    # Relacionamentos
    # cascade='all, delete-orphan' remove as subações se a ação for deletada
    subacoes = db.relationship('Subacao', backref='acao', cascade='all, delete-orphan', lazy=True)
    pfs = db.relationship('PF', backref='acao_pai', lazy=True)

    def __repr__(self):
        return f'<Acao {self.codigo} - Saldo: {self.saldo_atual}>'


class Subacao(db.Model):
    __tablename__ = 'subacoes'

    id = db.Column(db.Integer, primary_key=True)
    acao_id = db.Column(db.Integer, db.ForeignKey('acoes.id'), nullable=False)
    
    codigo = db.Column(db.String(20), nullable=False)
    descricao = db.Column(db.String(255))
    
    orcamento_inicial = db.Column(db.Numeric(15, 2), default=0.00)
    saldo_atual = db.Column(db.Numeric(15, 2), default=0.00)
    
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)

    # Garante que não exista código duplicado DENTRO da mesma ação
    __table_args__ = (db.UniqueConstraint('acao_id', 'codigo', name='uix_acao_codigo'),)

    def __repr__(self):
        return f'<Subacao {self.codigo} - Saldo: {self.saldo_atual}>'


# ---------------------------------------
# 3. Movimentações Financeiras (PFs e Transferências)
# ---------------------------------------
class PF(db.Model):
    __tablename__ = 'pfs'

    id = db.Column(db.Integer, primary_key=True)
    acao_id = db.Column(db.Integer, db.ForeignKey('acoes.id'), nullable=False)
    subacao_id = db.Column(db.Integer, db.ForeignKey('subacoes.id'), nullable=True)
    
    descricao = db.Column(db.String(255), nullable=False)
    valor = db.Column(db.Numeric(15, 2), nullable=False)
    
    # Status da PF
    status = db.Column(db.Enum('EMPENHADO', 'LIQUIDADO'), default='EMPENHADO')
    
    data_empenho = db.Column(db.DateTime, default=datetime.now)
    data_liquidacao = db.Column(db.DateTime, nullable=True)
    
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)

    # Relacionamentos
    subacao = db.relationship('Subacao', backref='pfs')
    usuario = db.relationship('Usuario')


class Transferencia(db.Model):
    __tablename__ = 'transferencias'

    id = db.Column(db.Integer, primary_key=True)
    tipo = db.Column(db.Enum('CA', 'RO'), nullable=False) # CA = Crédito Adicional, RO = Remanejamento
    
    # Origem
    acao_origem_id = db.Column(db.Integer, db.ForeignKey('acoes.id'), nullable=False)
    subacao_origem_id = db.Column(db.Integer, db.ForeignKey('subacoes.id'), nullable=True)
    
    # Destino
    acao_destino_id = db.Column(db.Integer, db.ForeignKey('acoes.id'), nullable=False)
    subacao_destino_id = db.Column(db.Integer, db.ForeignKey('subacoes.id'), nullable=True)
    
    valor = db.Column(db.Numeric(15, 2), nullable=False)
    data_transferencia = db.Column(db.DateTime, default=datetime.now)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)

    # Relacionamentos auxiliares (opcionais, facilitam queries complexas)
    acao_origem = db.relationship('Acao', foreign_keys=[acao_origem_id])
    acao_destino = db.relationship('Acao', foreign_keys=[acao_destino_id])


# ---------------------------------------
# 4. O Coração: Ledger (Livro Razão)
# ---------------------------------------
class MovimentacaoLedger(db.Model):
    """
    Tabela imutável que registra toda alteração de saldo.
    Usada para reconstruir o saldo em qualquer data passada.
    """
    __tablename__ = 'movimentacoes_ledger'

    id = db.Column(db.BigInteger, primary_key=True)
    
    acao_id = db.Column(db.Integer, db.ForeignKey('acoes.id'), nullable=False)
    subacao_id = db.Column(db.Integer, db.ForeignKey('subacoes.id'), nullable=True)
    
    tipo_operacao = db.Column(db.Enum(
        'SALDO_INICIAL', 
        'PF_CRIACAO', 
        'PF_ESTORNO', 
        'TRANSF_ENTRADA', 
        'TRANSF_SAIDA'
    ), nullable=False)
    
    # Chaves estrangeiras opcionais (para saber o que gerou o movimento)
    pf_id = db.Column(db.Integer, db.ForeignKey('pfs.id'), nullable=True)
    transferencia_id = db.Column(db.Integer, db.ForeignKey('transferencias.id'), nullable=True)
    
    # Valores matemáticos
    valor_movimento = db.Column(db.Numeric(15, 2), nullable=False) # Negativo se saiu, Positivo se entrou
    saldo_anterior = db.Column(db.Numeric(15, 2), nullable=False)
    saldo_novo = db.Column(db.Numeric(15, 2), nullable=False)
    
    data_movimento = db.Column(db.DateTime, default=datetime.now, index=True)


# ---------------------------------------
# 5. Auditoria Administrativa
# ---------------------------------------
class LogAuditoria(db.Model):
    __tablename__ = 'logs_auditoria'

    id = db.Column(db.Integer, primary_key=True)
    tabela_afetada = db.Column(db.String(50), nullable=False) # 'acoes', 'subacoes'
    registro_id = db.Column(db.Integer, nullable=False)
    acao_realizada = db.Column(db.String(50), nullable=False) # 'UPDATE', 'DELETE'
    
    # JSON para guardar o "antes" e "depois" de forma flexível
    dados_anteriores = db.Column(JSON, nullable=True)
    dados_novos = db.Column(JSON, nullable=True)
    
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)
    data_log = db.Column(db.DateTime, default=datetime.now)