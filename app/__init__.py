import os
import click
from flask import Flask
from config import Config

# importa o nosso serviço de ingestão de dados
from app.services.ingest_service import process_and_consolidate_data

def create_app(config_class=Config):
    """
    Application Factory: Cria e configura a aplicação Flask.
    """
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Aqui usamos um decorator do proprio flask que ppermite registrar
    # um comando. Nsse caso, estamos usando para criar o sistema que 
    # vain ingerir as informações da pasta "data"
    @app.cli.command('ingest-data')
    def ingest_data_command():
        """
        Comando de terminal para executar a ingestão de dados dos arquivos CSV.
        """
        # O caminho para a pasta de dados é relativo à raiz do projeto.
        source_path = os.path.join('data')
        click.echo(f"Iniciando a ingestão de dados da pasta: {source_path}")
        
        try:
            consolidated_data = process_and_consolidate_data(source_path)
            
            if not consolidated_data.empty:
                click.secho("\n[SUCESSO] Dados processados e consolidados.", fg='green')
                click.echo("Amostra dos dados:")
                click.echo(consolidated_data.head().to_string())
            else:
                click.secho("\n[AVISO] O processo terminou, mas nenhum dado foi gerado.", fg='yellow')

        except Exception as e:
            click.secho(f"\n[ERRO] Ocorreu uma falha durante a ingestão: {e}", fg='red')

    # Futuramente, aqui registraremos blueprints, extensões (db, migrate), etc.
    
    return app