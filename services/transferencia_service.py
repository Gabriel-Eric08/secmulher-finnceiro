from repositories.transferencia_repository import TransferenciaRepository, db
from services.ledger_service import LedgerService
from models.models import Acao, Subacao

class TransferenciaService:
    def __init__(self):
        self.transferencia_repository = TransferenciaRepository()
        self.ledger_service = LedgerService()

    def realizar_transferencia(self, dados):
        """
        dados: dict contendo ids de origem, destino, valor e usuario
        """
        try:
            valor = dados['valor']
            
            # 1. Carregar Entidades
            origem = self._get_entidade(dados['acao_origem_id'], dados.get('subacao_origem_id'))
            destino = self._get_entidade(dados['acao_destino_id'], dados.get('subacao_destino_id'))
            
            if not origem or not destino:
                raise Exception("Origem ou Destino inválidos.")

            # 2. Criar Registro da Transferência
            nova_transf = self.transferencia_repository.create(
                tipo=dados['tipo'], # 'CA' ou 'RO'
                acao_origem_id=dados['acao_origem_id'],
                subacao_origem_id=dados.get('subacao_origem_id'),
                acao_destino_id=dados['acao_destino_id'],
                subacao_destino_id=dados.get('subacao_destino_id'),
                valor=valor,
                usuario_id=dados['usuario_id']
            )

            # 3. Debitar da Origem
            self.ledger_service.registrar_movimentacao(
                entidade=origem,
                valor=-(valor),
                tipo_operacao='TRANSF_SAIDA',
                transf_id=nova_transf.id
            )

            # 4. Creditar no Destino
            self.ledger_service.registrar_movimentacao(
                entidade=destino,
                valor=valor,
                tipo_operacao='TRANSF_ENTRADA',
                transf_id=nova_transf.id
            )

            db.session.commit()
            return nova_transf

        except Exception as e:
            db.session.rollback()
            raise e

    def _get_entidade(self, acao_id, subacao_id=None):
        if subacao_id:
            return Subacao.query.get(subacao_id)
        return Acao.query.get(acao_id)
    def get_all(self):
        return self.transferencia_repository.get_all()
        # Obs: Se seu repository não tiver, use: return Transferencia.query.order_by(Transferencia.data_transferencia.desc()).all()