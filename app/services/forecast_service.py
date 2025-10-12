import pandas as pd
import pmdarima as pm
from sqlalchemy import func
from ..models import PluviometricData
from ..extensions import db
import warnings
import os
import json
from datetime import datetime, timedelta

# Ignorar avisos comuns do statsmodels para deixar a saída mais limpa
warnings.filterwarnings("ignore", category=UserWarning, module='statsmodels')

# Constante para o número mínimo de meses de dados (ex: 3 anos * 12 meses)
MINIMUM_DATA_POINTS = 3 * 12
CACHE_LIFETIME_DAYS = 7

def _load_and_prepare_data(city_name: str) -> pd.Series:
    """
    Carrega os dados de uma cidade do banco, valida e prepara a série temporal mensal.
    """
    print(f"Carregando dados históricos para '{city_name}' do banco de dados...")

    # Query para buscar os dados da cidade, ignorando maiúsculas/minúsculas
    stmt = db.select(
        PluviometricData.data,
        PluviometricData.precipitacao_mm
    ).where(
        func.lower(PluviometricData.cidade) == func.lower(city_name)
    ).order_by(
        PluviometricData.data
    )
    
    # Executamos a query diretamente com o SQLAlchemy
    result = db.session.execute(stmt)
    
    # Criamos o DataFrame a partir dos resultados da query
    # passando os nomes das colunas explicitamente.
    df = pd.DataFrame(result.all(), columns=result.keys())

    if df.empty:
        raise ValueError(f"Nenhum dado encontrado para a cidade: {city_name}")

    df['data'] = pd.to_datetime(df['data'])
    df.set_index('data', inplace=True)

    # Agrega os dados diários em totais mensais. 'MS' significa 'Month Start'.
    monthly_series = df['precipitacao_mm'].resample('MS').sum()
    
    # VALIDAÇÃO CRUCIAL: Verifica se temos dados suficientes
    if len(monthly_series) < MINIMUM_DATA_POINTS:
        raise ValueError(
            f"Dados insuficientes para '{city_name}'. "
            f"São necessários pelo menos {MINIMUM_DATA_POINTS} meses de dados, "
            f"mas apenas {len(monthly_series)} foram encontrados."
        )
    
    print(f"Dados carregados e agregados. Série temporal de {monthly_series.index.min().year} a {monthly_series.index.max().year} encontrada.")
    return monthly_series

def _find_best_model(monthly_series: pd.Series):
    """
    Usa auto_arima para encontrar o melhor modelo SARIMA para a série temporal.
    """
    print("Iniciando busca pelo melhor modelo SARIMA (auto_arima)...")
    
    # auto_arima vai testar diferentes combinações de parâmetros e encontrar a melhor
    # m=12 é o parâmetro mais importante: informa que o ciclo sazonal é de 12 meses.
    arima_model = pm.auto_arima(
        monthly_series,
        start_p=1, start_q=1,
        max_p=3, max_q=3,
        m=12, # Frequência do ciclo sazonal
        seasonal=True, # Habilita a busca por parâmetros sazonais
        d=1, D=1, # Ordens de diferenciação para tornar a série estacionária
        trace=True, # Mostra os modelos que estão sendo testados
        error_action='ignore',
        suppress_warnings=True,
        stepwise=True # Usa um algoritmo mais rápido para encontrar os parâmetros
    )
    
    print(f"Melhor modelo encontrado: {arima_model.summary().tables[0].as_text()}")
    return arima_model

def generate_forecast_for_city(city_name: str, cache_path: str, n_months: int = 12, force_regenerate: bool = False) -> pd.DataFrame:
    """
    Função principal do serviço. Orquestra o processo de geração de previsão,
    limpa os dados e enriquece o resultado com insights de tendência.
    Permite também o uso de cache para evitar recomputações desnecessárias.
    """
    # Verificação do cache
    if not force_regenerate and os.path.exists(cache_path):
        print(f"Arquivo de cache encontrado para '{city_name}'. Verificando validade...")
        with open(cache_path, 'r') as f:
            cache_data = json.load(f)
        
        generated_at = datetime.fromisoformat(cache_data['generated_at'])
        cache_age = datetime.now() - generated_at
        
        if cache_age < timedelta(days=CACHE_LIFETIME_DAYS):
            print(f"Cache VÁLIDO (criado há {cache_age.days} dias). Carregando previsão do arquivo.")
            # Converte os dados do cache de volta para um df
            forecast_df = pd.DataFrame(cache_data['forecast'])
            forecast_df['date'] = pd.to_datetime(forecast_df['date'])
            return forecast_df
        else:
            print(f"Cache EXPIRADO (criado há {cache_age.days} dias). Gerando nova previsão.")

    # Gera a previsão (se não houver cache válido)
    print("Nenhum cache válido encontrado. Iniciando processo de modelagem...")
    try:
        # Carrega e prepara os dados históricos (lá do banco de dados)
        monthly_series = _load_and_prepare_data(city_name)

        # seleciona o melhor modelo SARIMA
        model = _find_best_model(monthly_series)

        # Gera previsão bruta
        forecast, conf_int = model.predict(n_periods=n_months, return_conf_int=True)
        
        # Formata o resultado inicial em um df
        forecast_start_date = monthly_series.index[-1] + pd.DateOffset(months=1)
        forecast_dates = pd.date_range(start=forecast_start_date, periods=n_months, freq='MS')
        
        forecast_df = pd.DataFrame({
            'date': forecast_dates,
            'predicted_mm': forecast,
            'conf_int_lower': conf_int[:, 0],
            'conf_int_upper': conf_int[:, 1]
        })

        # em tese aqui teríamos acabado a previsão,
        # mas testando o valor o sistema encontrou
        # previsões negativas, o que não faz sentido
        # para nós, mas levando em conta que o sistema
        # simplesmente não sabe o que está prevendo,
        # é importante garantir que os resultados façam sentido.
        # Portanto, aplicamos algumas correções:

        # TRATAMENTO 1: Garantir que a chuva nunca seja negativa
        forecast_df['predicted_mm'] = forecast_df['predicted_mm'].clip(lower=0)
        forecast_df['conf_int_lower'] = forecast_df['conf_int_lower'].clip(lower=0)

        # TRATAMENTO 2: Adicionar coluna de tendência comparativa
        # Calcula a média histórica para cada mês do ano
        historical_monthly_avg = monthly_series.groupby(monthly_series.index.month).mean()
        
        # determina a tendência
        def get_trend(row):
            month = row['date'].month
            prediction = row['predicted_mm']
            historical_avg = historical_monthly_avg.get(month, 0)
            if historical_avg == 0: return "Sem referência histórica"
            if prediction > historical_avg * 1.15: return "Acima da média histórica"
            if prediction < historical_avg * 0.85: return "Abaixo da média histórica"
            return "Dentro da média histórica"

        forecast_df['tendencia'] = forecast_df.apply(get_trend, axis=1)

        # SALVAR O NOVO CACHE
        print(f"Salvando nova previsão no cache em: {cache_path}")
        
        output_data = {
            "city": city_name,
            "temporal_serie_historical": [
                monthly_series.index.min().isoformat(),
                monthly_series.index.max().isoformat()
            ],
            "forecast": forecast_df.to_dict('records'),
            "generated_at": datetime.now().isoformat()
        }
        
        # Converte as datas no forecast para string para serem compatíveis com JSON
        for record in output_data['forecast']:
            record['date'] = record['date'].isoformat()
            
        with open(cache_path, 'w') as f:
            json.dump(output_data, f, indent=4)

        print("Previsão gerada e salva com sucesso.")
        return forecast_df

    except ValueError as ve:
        print(f"[AVISO] {ve}")
        return None
    except Exception as e:
        print(f"[ERRO] Ocorreu um erro inesperado: {e}")
        return None