# aqui teremos a importaão toda do ambiente
import os

class Config:
    """
    Configurações base da aplicação.
    Outras configurações (desenvolvimento, produção) podem herdar desta.
    """

    # Configuração do banco de dados (será usada no futuro)
    # SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL')
    # SQLALCHEMY_TRACK_MODIFICATIONS = False