import json
import os
import click
from datetime import datetime
from flask import jsonify, request, current_app
from sqlalchemy import func, extract
from . import api_bp
from ..extensions import db
from ..models import PluviometricData
from ..services import forecast_service

# ========================
# --- Helper Functions ---
# ========================

def _record_to_dict(record: PluviometricData):
    """Converte um objeto PluviometricData em um dicionário."""
    if not record:
        return None
    return {
        'id': record.id,
        'data': record.data.isoformat(),
        'precipitacao_mm': record.precipitacao_mm,
        'cidade': record.cidade,
        'estado': record.estado,
        'estacao_codigo': record.estacao_codigo
    }

# =======================================
# --- Endpoints Gerais e de Utilidade ---
# =======================================

@api_bp.route('/cities', methods=['GET'])
def get_available_cities():
    """
    Retorna uma lista com os nomes de todas as cidades disponíveis no banco de dados.
    Ideal para popular menus de seleção no frontend.

    ---
    Path:
      GET /api/v1/cities
    
    Parâmetros de Entrada:
      Nenhum.

    Resposta de Sucesso (200 OK):
      Content-Type: application/json
      Corpo:
        [
          "CURITIBANOS",
          "CHAPECO",
          "FLORIANOPOLIS",
          ...
        ]
    """

    city_names = db.session.scalars(
        db.select(PluviometricData.cidade).distinct().order_by(PluviometricData.cidade)
    ).all()
    return jsonify(city_names)

# ==============================================
# --- Endpoints de Registros de Dados Brutos ---
# ==============================================

@api_bp.route('/records/by-city/<string:city_name>', methods=['GET'])
def get_records_by_city(city_name):
    """
    Retorna uma lista paginada de todos os registros históricos para uma cidade.

    ---
    Path:
      GET /api/v1/records/by-city/<city_name>
    
    Parâmetros de Path:
      - city_name (string): O nome da cidade. Ex: "CURITIBANOS"

    Parâmetros de Query (Opcional):
      - page (integer): O número da página a ser retornada. (Default: 1)
      - per_page (integer): O número de registros por página. (Default: 100)

    Resposta de Sucesso (200 OK):
      Content-Type: application/json
      Corpo:
        [
          {
            "id": 1,
            "data": "2024-10-12",
            "precipitacao_mm": 10.5,
            "cidade": "CURITIBANOS",
            "estado": "SC",
            "estacao_codigo": "A857"
          },
          ...
        ]
    
    Resposta de Erro (404 Not Found):
      - Se a cidade não for encontrada.
    """
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 100, type=int)
    
    # --- INÍCIO DA CORREÇÃO ---
    
    # 1. Primeiro, construímos a instrução da query (o 'select' statement)
    stmt = db.select(PluviometricData) \
        .where(func.lower(PluviometricData.cidade) == func.lower(city_name)) \
        .order_by(PluviometricData.data.desc())

    # 2. Em seguida, passamos a instrução para a função db.paginate()
    pagination = db.paginate(stmt, page=page, per_page=per_page, error_out=False)
    
    # 3. Os registros que queremos estão no atributo .items do objeto de paginação
    records = pagination.items
    
    # --- FIM DA CORREÇÃO ---
    
    if not records:
        return jsonify({'error': 'Cidade não encontrada ou sem registros'}), 404
        
    return jsonify([_record_to_dict(rec) for rec in records])

@api_bp.route('/records/by-city/<string:city_name>/on-date/<string:date_str>', methods=['GET'])
def get_record_for_city_on_date(city_name, date_str):
    """
    Retorna o registro único para uma cidade em uma data específica.

    ---
    Path:
      GET /api/v1/records/by-city/<city_name>/on-date/<date_str>
    
    Parâmetros de Path:
      - city_name (string): O nome da cidade.
      - date_str (string): A data no formato "YYYY-MM-DD".

    Resposta de Sucesso (200 OK):
      Content-Type: application/json
      Corpo (Objeto único, não uma lista):
        {
          "id": 1,
          "data": "2010-01-15",
          "precipitacao_mm": 5.2,
          ...
        }
    
    Respostas de Erro:
      - 400 Bad Request: Se o formato da data for inválido.
      - 404 Not Found: Se não houver registro para a cidade/data.
    """
    try:
        # Valida o formato da data
        target_date = datetime.fromisoformat(date_str).date()
    except ValueError:
        return jsonify({'error': 'Formato de data inválido. Use YYYY-MM-DD.'}), 400

    record = db.session.scalar(
        db.select(PluviometricData)
        .where(func.lower(PluviometricData.cidade) == func.lower(city_name))
        .where(PluviometricData.data == target_date)
    )
    
    if not record:
        return jsonify({'error': f'Nenhum registro encontrado para {city_name} na data {date_str}'}), 404
        
    return jsonify(_record_to_dict(record))

# ==========================================
# --- Endpoints de Análises Estatísticas ---
# ==========================================

@api_bp.route('/stats/accumulation/monthly/by-city/<string:city_name>', methods=['GET'])
def get_monthly_accumulation(city_name):
    """
    Calcula e retorna o acumulado de chuva mensal para uma cidade.

    ---
    Path:
      GET /api/v1/stats/accumulation/monthly/by-city/<city_name>
    
    Resposta de Sucesso (200 OK):
      Content-Type: application/json
      Corpo:
        [
          {"ano": 2023, "mes": 1, "acumulado_mm": 250.50},
          {"ano": 2023, "mes": 2, "acumulado_mm": 180.00},
          ...
        ]
    """
    results = db.session.execute(
        db.select(
            extract('year', PluviometricData.data).label('ano'),
            extract('month', PluviometricData.data).label('mes'),
            func.sum(PluviometricData.precipitacao_mm).label('acumulado_mm')
        )
        .where(func.lower(PluviometricData.cidade) == func.lower(city_name))
        .group_by('ano', 'mes')
        .order_by('ano', 'mes')
    ).all()

    if not results:
        return jsonify({'error': 'Cidade não encontrada ou sem registros'}), 404
        
    data = [{'ano': r.ano, 'mes': r.mes, 'acumulado_mm': round(r.acumulado_mm, 2)} for r in results]
    return jsonify(data)

@api_bp.route('/stats/accumulation/yearly/by-city/<string:city_name>', methods=['GET'])
def get_yearly_accumulation(city_name):
    """
    Calcula e retorna o acumulado de chuva anual para uma cidade.

    ---
    Path:
      GET /api/v1/stats/accumulation/yearly/by-city/<city_name>
    
    Resposta de Sucesso (200 OK):
      Content-Type: application/json
      Corpo:
        [
          {"ano": 2022, "acumulado_mm": 1850.75},
          {"ano": 2023, "acumulado_mm": 2100.20},
          ...
        ]
    """
    results = db.session.execute(
        db.select(
            extract('year', PluviometricData.data).label('ano'),
            func.sum(PluviometricData.precipitacao_mm).label('acumulado_mm')
        )
        .where(func.lower(PluviometricData.cidade) == func.lower(city_name))
        .group_by('ano')
        .order_by('ano')
    ).all()

    if not results:
        return jsonify({'error': 'Cidade não encontrada ou sem registros'}), 404
        
    # Converte o resultado (que é uma lista de tuplas) em uma lista de dicionários
    data = [{'ano': row.ano, 'acumulado_mm': round(row.acumulado_mm, 2)} for row in results]
    return jsonify(data)

@api_bp.route('/stats/extremes/by-city/<string:city_name>', methods=['GET'])
def get_city_extremes(city_name):
    """
    Retorna os registros de dias extremos (ex: mais chuvoso) para uma cidade.

    ---
    Path:
      GET /api/v1/stats/extremes/by-city/<city_name>
    
    Resposta de Sucesso (200 OK):
      Content-Type: application/json
      Corpo:
        {
          "dia_mais_chuvoso": {
            "id": 50,
            "data": "2015-07-20",
            "precipitacao_mm": 150.0,
            ...
          }
        }
    """
    # Encontra o dia mais chuvoso
    rainiest_day = db.session.scalar(
        db.select(PluviometricData)
        .where(func.lower(PluviometricData.cidade) == func.lower(city_name))
        .order_by(PluviometricData.precipitacao_mm.desc())
    )
    
    if not rainiest_day:
        return jsonify({'error': 'Cidade não encontrada ou sem registros'}), 404
        
    return jsonify({
        'dia_mais_chuvoso': _record_to_dict(rainiest_day)
    })

# ==============================
# --- Endpoints de Previsões ---
# ==============================

@api_bp.route('/forecast/by-city/<string:city_name>', methods=['GET'])
def get_forecast(city_name):
    """
    Busca e retorna a previsão em cache para uma cidade. É uma operação rápida.

    ---
    Path:
      GET /api/v1/forecast/by-city/<city_name>
    
    Resposta de Sucesso (200 OK):
      Content-Type: application/json
      Corpo (Estrutura completa do arquivo de cache JSON):
        {
          "city": "CURITIBANOS",
          "generated_at": "2025-10-12T13:30:06.123456",
          "temporal_serie_historical": ["2008-02-01T00:00:00", "2018-12-01T00:00:00"],
          "forecast": [
            {
              "date": "2019-01-01T00:00:00",
              "predicted_mm": 123.32,
              ...
            },
            ...
          ]
        }
    
    Resposta de Erro (404 Not Found):
      - Se o arquivo de cache da previsão ainda não foi gerado.
    """
    safe_city_name = city_name.lower().replace(' ', '_').replace('/', '_')
    cache_filename = f"{safe_city_name}_forecast.json"
    
    # Usamos 'current_app' para acessar o app context e encontrar a pasta 'instance'
    cache_path = os.path.join(current_app.instance_path, cache_filename)

    if not os.path.exists(cache_path):
        return jsonify({
            'error': 'Previsão não encontrada.',
            'message': f'Execute o comando "flask generate-forecast \'{city_name}\'" no servidor para gerá-la.'
        }), 404

    with open(cache_path, 'r', encoding='utf-8') as f:
        forecast_data = json.load(f)
    
    return jsonify(forecast_data)

@api_bp.route('/forecast/by-city/<string:city_name>', methods=['POST'])
def create_or_update_forecast(city_name):
    """
    Aciona a geração (ou atualização) do cache da previsão. É uma operação LENTA.

    ---
    Path:
      POST /api/v1/forecast/by-city/<city_name>
    
    Parâmetros de Entrada:
      Nenhum no corpo da requisição.

    Resposta de Sucesso (201 Created):
      Content-Type: application/json
      Corpo:
        {
          "status": "success",
          "message": "Previsão para CURITIBANOS foi gerada e salva com sucesso.",
          "cache_path": "C:\\...\\instance\\curitibanos_forecast.json"
        }
    
    Respostas de Erro:
      - 400 Bad Request: Se não houver dados suficientes para gerar a previsão.
      - 500 Internal Server Error: Se ocorrer um erro inesperado no modelo.
    """
    click.echo(f"Requisição POST recebida para gerar previsão para: {city_name}")

    safe_city_name = city_name.lower().replace(' ', '_').replace('/', '_')
    cache_filename = f"{safe_city_name}_forecast.json"
    cache_path = os.path.join(current_app.instance_path, cache_filename)

    # Forçamos a geração chamando o serviço diretamente.
    # Em uma aplicação de produção, isso seria delegado a uma fila de tarefas (Celery, RQ).
    try:
        # A chamada ao forecast_service já contém a lógica de salvar o cache
        forecast_result = forecast_service.generate_forecast_for_city(city_name, cache_path, force_regenerate=True)
        
        if forecast_result is None:
            # Isso pode acontecer se não houver dados suficientes para a cidade
             return jsonify({
                'error': 'Não foi possível gerar a previsão.',
                'message': f'Verifique se existem dados suficientes para a cidade "{city_name}".'
            }), 400

        return jsonify({
            'status': 'success',
            'message': f'Previsão para {city_name} foi gerada e salva com sucesso.',
            'cache_path': cache_path
        }), 201 # 201 Created indica que um recurso foi criado com sucesso

    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Ocorreu um erro interno: {str(e)}'
        }), 500