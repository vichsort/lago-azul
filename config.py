import os
from dotenv import load_dotenv

# Encontra o caminho absoluto do diretório raiz do projeto
basedir = os.path.abspath(os.path.dirname(__file__))

# Carrega as variáveis de ambiente do arquivo .env
load_dotenv(os.path.join(basedir, '.env'))

class Config:
    """
    Configurações base da aplicação, carregadas a partir de variáveis de ambiente.
    """
    # CONFIGURAÇÃO DO BANCO DE DADOS USANDO SQLALCHEMY E POSTGRESQL

    # Constrói a URL de conexão do banco de dados a partir das variáveis do .env
    DB_USER = os.environ.get('DB_USER')
    DB_PASSWORD = os.environ.get('DB_PASSWORD')
    DB_HOST = os.environ.get('DB_HOST')
    DB_PORT = os.environ.get('DB_PORT')
    DB_NAME = os.environ.get('DB_NAME')
    
    # Connection String que o SQLAlchemy usará para se conectar.
    # O formato é: dialect+driver://username:password@host:port/database
    SQLALCHEMY_DATABASE_URI = (
        f"postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    )

    # Desativa um recurso do Flask-SQLAlchemy que não usaremos e que consome recursos.
    SQLALCHEMY_TRACK_MODIFICATIONS = False