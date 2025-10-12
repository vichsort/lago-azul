import pandas as pd
import numpy as np
import os
import glob

def _process_single_file(file_path: str) -> pd.DataFrame:
    """
    Processa um único arquivo de dados.
    """
    filename = os.path.basename(file_path)
    print(f"  > Processando arquivo: {filename}...")

    # Pega metadados
    metadata = {}
    try:
        with open(file_path, 'r', encoding='latin-1') as f:
            for i, line in enumerate(f):
                if 'ESTAÇÃO:' in line:
                    metadata['cidade'] = line.split(';')[1].strip()
                elif 'UF:' in line:
                    metadata['estado'] = line.split(';')[1].strip()
                elif 'CODIGO (WMO):' in line:
                    metadata['estacao_codigo'] = line.split(';')[1].strip()
                if i > 8: break
    except Exception as e:
        print(f"    [AVISO] Não foi possível ler o cabeçalho de {filename}: {e}")
        return pd.DataFrame()

    # Leitura
    try:
        df = pd.read_csv(file_path, skiprows=8, delimiter=';', encoding='latin-1', decimal=',')
        
        # Eu vi que muitos arquivos terminam com uma linha vazia.
        # ao invés de tirar manualmente, isso limpa a linha final que não agrega nada ao sistema
        if df.iloc[:, -1].isnull().all():
            df = df.iloc[:, :-1]

    except Exception as e:
        print(f"    [ERRO] Falha ao ler o CSV {filename}: {e}")
        return pd.DataFrame()

    # Limpa / transforma
    try:
        col_precipitacao = next(col for col in df.columns if 'PRECIPITA' in col.upper())
        col_data = next(col for col in df.columns if 'DATA' in col.upper())
    except StopIteration:
        print(f"    [ERRO] Colunas essenciais (Data, Precipitação) não encontradas em {filename}.")
        return pd.DataFrame()

    df_clean = df[[col_data, col_precipitacao]].copy()
    df_clean.columns = ['data', 'precipitacao_mm']

    # por algum motivo, dados que não são registrados, não aconteceram
    # ou foram invalidados são registrados como "-9999" -> só vamos
    # automatizar a limpeza aqui.
    df_clean.replace(-9999, np.nan, inplace=True)
    df_clean['precipitacao_mm'] = df_clean['precipitacao_mm'].fillna(0)
    df_clean['data'] = pd.to_datetime(df_clean['data'])
    df_clean['precipitacao_mm'] = pd.to_numeric(df_clean['precipitacao_mm'])

    # agregação diária
    df_daily = df_clean.groupby('data').agg(precipitacao_mm=('precipitacao_mm', 'sum')).reset_index()

    # Adiciona metadados
    for key, value in metadata.items():
        df_daily[key] = value

    print(f"    -> Concluído: {len(df_daily)} registros diários gerados.")
    return df_daily


def process_and_consolidate_data(source_directory: str) -> pd.DataFrame:
    """
    Função principal do serviço. Itera sobre todos os arquivos CSV em um diretório,
    processa cada um e retorna um único DataFrame consolidado.
    """
    print(f"Iniciando serviço de ingestão de dados do diretório: '{source_directory}'")
    
    # Encontra todos os arquivos .csv no diretório especificado
    csv_files = glob.glob(os.path.join(source_directory, '*.csv'))

    if not csv_files:
        print("Nenhum arquivo .csv encontrado no diretório.")
        return pd.DataFrame()

    print(f"Encontrados {len(csv_files)} arquivos para processar.")
    
    all_dataframes = []
    # realiza a limpeza item a item usando a função privada.
    # isso é à prova de CSVs vazios. 
    for file in csv_files:
        processed_df = _process_single_file(file)
        if not processed_df.empty:
            all_dataframes.append(processed_df)
    
    if not all_dataframes:
        print("Nenhum arquivo pôde ser processado com sucesso.")
        return pd.DataFrame()

    # Consolida todos os dataframes em um só
    consolidated_df = pd.concat(all_dataframes, ignore_index=True)

    # e depois reordena as colunas para um padrão limpo
    final_columns = ['data', 'precipitacao_mm', 'cidade', 'estado', 'estacao_codigo']
    consolidated_df = consolidated_df.reindex(columns=final_columns)

    print("\n--- Consolidação finalizada! ---")
    print(f"Total de registros processados: {len(consolidated_df)}")
    
    return consolidated_df


# Este bloco só será executado quando você rodar o script diretamente
if __name__ == '__main__':
    # O caminho é relativo à localização do projeto, ! não do script !
    # Supondo que você execute o comando da pasta raiz do projeto
    DATA_FOLDER = 'data'
    
    final_data = process_and_consolidate_data(DATA_FOLDER)

    if not final_data.empty:
        print("\n--- Amostra dos Dados Consolidados ---")
        print("Primeiros 5 registros:")
        print(final_data.head())
        print("\nÚltimos 5 registros:")
        print(final_data.tail())
        print(f"\nCidades encontradas: {final_data['cidade'].unique().tolist()}")