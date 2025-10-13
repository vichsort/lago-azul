import os
import click
from flask import Flask
from config import Config
from flask_cors import CORS
from sqlalchemy.dialects.postgresql import insert as pg_insert
from app.services import forecast_service
import matplotlib.pyplot as plt

# importa o nosso serviço de ingestão de dados
from app.services.ingest_service import process_and_consolidate_data

# extensões para conexão do bd
from .extensions import db, migrate

def create_app(config_class=Config):
    """
    Application Factory: Cria e configura a aplicação Flask.
    """
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_object(config_class)
    
    # correção para aceitar req. do vue para a api via CORS
    CORS(app, resources={r"/api/*": {"origins": "http://localhost:5173"}})
    
    db.init_app(app)
    migrate.init_app(app, db)

    os.makedirs(app.instance_path, exist_ok=True)

    from .api import api_bp
    app.register_blueprint(api_bp, url_prefix='/api/v1')

    from app import models

    # Aqui usamos um decorator do proprio flask que ppermite registrar
    # um comando. Nsse caso, estamos usando para criar o sistema que 
    # vain ingerir as informações da pasta "data"
    @app.cli.command('ingest-data')
    def ingest_data_command():
        """
        Comando de terminal para processar e salvar os dados pluviométricos no banco de dados.
        """
        source_path = os.path.join('data') # caminho para a pasta de dados, pode fazer juncao com outras pastas ex. ('data', '2023', etc)
        
        try:
            # Processar e consolidar os dados dos arquivos
            click.echo(f"Iniciando leitura de dados da pasta: {source_path}")
            consolidated_data = process_and_consolidate_data(source_path)
            
            if consolidated_data.empty:
                click.secho("\n[AVISO] Processo de leitura concluído, mas nenhum dado foi gerado. Abortando.", fg='yellow')
                return

            click.secho(f"\n[INFO] {len(consolidated_data)} registros lidos dos arquivos.", fg='cyan')
            click.echo("Iniciando inserção no banco de dados...")
            
            # Converter o DataFrame para uma lista de dicionários
            data_to_insert = consolidated_data.to_dict(orient='records')

            # Executar a inserção em massa (bulk insert) com tratamento de conflitos
            # 'with app.app_context()' é necessário para comandos de terminal acessarem o banco.
            with app.app_context():
                # Primeiro, pegamos a tabela do nosso modelo
                table = models.PluviometricData.__table__

                # Criamos a instrução de INSERT para PostgreSQL
                stmt = pg_insert(table).values(data_to_insert)

                # A parte mais importante: definimos o que fazer em caso de conflito.
                # Se um registro com a mesma 'data' e 'estacao_codigo' já existir...
                # ... não faça nada (on conflict do nothing).
                stmt = stmt.on_conflict_do_nothing(
                    index_elements=['data', 'estacao_codigo']
                )
                
                # Executamos a instrução e commitamos a transação
                db.session.execute(stmt)
                db.session.commit()
            
            click.secho(f"\n[SUCESSO] Dados salvos no banco de dados!", fg='green')
            click.echo("Registros duplicados (se houver) foram ignorados.")

        except Exception as e:
            # Se qualquer erro ocorrer, o rollback desfaz a transação.
            with app.app_context():
                db.session.rollback()
            click.secho(f"\n[ERRO] Ocorreu uma falha durante a operação com o banco de dados.", fg='red')
            click.secho(f"Detalhes: {e}", fg='red')
            click.echo("A transação foi revertida (rollback). Nenhuma alteração foi salva.")
    
    # segundo decorator para o comando de previsao
    # que recebe o nome da cidade como argumento
    @app.cli.command('generate-forecast')
    @click.argument('city_name')
    def generate_forecast_command(city_name):
        """
        Gera e exibe uma previsão de chuvas para uma cidade, usando um cache.
        Exemplo: flask generate-forecast "CURITIBANOS"
        """
        click.echo(f"Iniciando a geração de previsão para a cidade: {city_name}")

        # Constrói o nome do arquivo de cache de forma segura
        safe_city_name = city_name.lower().replace(' ', '_').replace('/', '_')
        cache_filename = f"{safe_city_name}_forecast.json"
        
        # 'app.instance_path' nos dá o caminho absoluto para a pasta 'instance'
        cache_path = os.path.join(app.instance_path, cache_filename)
        
        with app.app_context():
            # Passamos o caminho do cache para o serviço
            forecast_result = forecast_service.generate_forecast_for_city(city_name, cache_path)
        
        if forecast_result is not None:
            click.secho("\n--- Resultado da Previsão ---", fg='green')
            click.echo(forecast_result.to_string())

            with app.app_context():
                historical_data = forecast_service._load_and_prepare_data(city_name)
            
            plt.figure(figsize=(15, 7))
            plt.plot(historical_data.index, historical_data.values, label='Dados Históricos')
            plt.plot(forecast_result['date'], forecast_result['predicted_mm'], label='Previsão', color='red', marker='o')
            plt.fill_between(forecast_result['date'],
                             forecast_result['conf_int_lower'],
                             forecast_result['conf_int_upper'],
                             color='pink', alpha=0.5, label='Intervalo de Confiança')
            plt.title(f'Previsão de Precipitação Mensal para {city_name}')
            plt.xlabel('Data')
            plt.ylabel('Precipitação Total (mm)')
            plt.legend()
            plt.grid(True)
            
            filename = f'forecast_{safe_city_name}.png'
            plt.savefig(filename)
            click.secho(f"\nGráfico da previsão salvo como '{filename}'", fg='cyan')
        else:
            click.secho(f"\nNão foi possível gerar a previsão para {city_name}.", fg='red')

    return app