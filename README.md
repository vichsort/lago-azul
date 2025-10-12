# 🌦️ Painel de Análise e Previsão de Dados Pluviométricos

Este projeto é uma API backend completa para a ingestão, armazenamento, análise e previsão de dados históricos de chuva. A aplicação foi desenvolvida em Python com o framework Flask e utiliza um banco de dados PostgreSQL para persistência dos dados. O sistema inclui um modelo estatístico SARIMA para gerar previsões de tendências futuras de precipitação.

## 📜 Índice

  - [Funcionalidades Principais](#-funcionalidades-principais)
  - [Tecnologias Utilizadas](#️-tecnologias-utilizadas)
  - [Estrutura do Projeto](#estrutura-do-projeto)
  - [Configuração e Execução Local](#-configuração-e-execução-local)
  - [Utilização da Aplicação](#️-utilização-da-aplicação)
  - [Documentação da API](#-documentação-da-api)
  - [Modelo de Previsão](#-modelo-de-previsão)
  - [Possíveis Melhorias Futuras](#-possíveis-melhorias-futuras)

## ✨ Funcionalidades Principais

  * **Ingestão de Dados em Lote:** Processa múltiplos arquivos CSV de dados meteorológicos do INMET de uma só vez.
  * **Armazenamento Robusto:** Persiste os dados tratados em um banco de dados PostgreSQL, com um esquema versionado através de migrações.
  * **API RESTful Completa:** Expõe endpoints claros e organizados para consultar dados brutos, estatísticas agregadas e previsões.
  * **Modelo de Previsão Estatística:** Gera previsões de precipitação para os próximos 12 meses para qualquer localidade com dados suficientes.
  * **Sistema de Cache Inteligente:** Armazena as previsões geradas para evitar reprocessamento computacionalmente caro, com tempo de vida configurável.

## 🛠️ Tecnologias Utilizadas

  * **Backend:** Python 3.11+, Flask
  * **Banco de Dados:** PostgreSQL
  * **ORM e Migrações:** Flask-SQLAlchemy, Flask-Migrate (Alembic)
  * **Manipulação de Dados:** Pandas, NumPy
  * **Modelo Estatístico:** Statsmodels, Pmdarima (auto\_arima)
  * **Ambiente e Dependências:** Python venv, Pip

## 📁 Estrutura do Projeto

```
/
|-- app/                    # Módulo principal da aplicação Flask
|   |-- api/                # Blueprint da API (rotas)
|   |-- services/           # Lógica de negócio (ingestão, previsão)
|   |-- extensions.py       # Inicialização das extensões (ex: db)
|   |-- models.py           # Modelos de dados do SQLAlchemy
|   |-- __init__.py         # Application Factory (create_app)
|
|-- data/                   # Pasta para colocar os arquivos CSV brutos
|
|-- instance/               # Pasta de cache para previsões (gerada automaticamente)
|
|-- migrations/             # Scripts de migração do banco de dados (Alembic)
|
|-- .env                    # Arquivo de configuração local (credenciais)
|-- .env.example            # Template do arquivo de configuração
|-- config.py               # Configurações da aplicação
|-- requirements.txt        # Lista de dependências Python
|-- run.py                  # Ponto de entrada para iniciar o servidor
|-- README.md               # Este arquivo
```

## 🚀 Configuração e Execução Local

Siga os passos abaixo para configurar e executar o projeto em seu ambiente de desenvolvimento.

### 1\. Pré-requisitos

  * [Python 3.10+](https://www.python.org/)
  * [PostgreSQL](https://www.postgresql.org/download/) instalado e rodando.
  * [Git](https://git-scm.com/)

### 2\. Clonar o Repositório

```bash
git clone https://github.com/vichsort/lago-azul.git
cd lago-azul
```

### 3\. Configurar o Banco de Dados

Você precisa criar um banco de dados e um usuário para a aplicação. No pgAdmin ou `psql`, execute:

```sql
CREATE DATABASE pluviometric_data;
```

*(Você pode usar o usuário padrão `postgres` ou criar um novo).*

### 4\. Configurar o Ambiente

a. **Crie o arquivo de variáveis de ambiente** copiando o template:

```bash
# No Windows
copy .env.example .env

# No Linux/macOS
cp .env.example .env
```

b. **Edite o arquivo `.env`** com as suas credenciais do PostgreSQL:

```ini
# .env
DB_HOST="localhost"
DB_PORT="5432"
DB_USER="postgres"
DB_PASSWORD="sua_senha_do_postgres"
DB_NAME="pluviometric_data"
```

c. **Crie e ative o ambiente virtual:**

```bash
# Criar o ambiente
python -m venv .venv

# Ativar no Windows
.\.venv\Scripts\activate

# Ativar no Linux/macOS
source .venv/bin/activate
```

d. **Instale as dependências Python:**

```bash
pip install -r requirements.txt
```

### 5\. Aplicar as Migrações do Banco

Este comando criará todas as tabelas necessárias no seu banco de dados.

```bash
flask db upgrade
```

## ▶️ Utilização da Aplicação

### 1\. Ingestão dos Dados

Execute o comando de ingestão no terminal. Ele irá processar todos os arquivos e salvá-los no banco de dados.

```bash
flask ingest-data
```

### 2\. Iniciar o Servidor da API

Com os dados no banco, inicie o servidor de desenvolvimento do Flask.

```bash
flask run
```

A API estará disponível em `http://127.0.0.1:5000`. Todas as rotas são prefixadas com `/api/v1`.

### 3\. Gerar uma Previsão

Para gerar o cache de uma previsão, utilize o endpoint `POST` com uma ferramenta como `curl` ou Postman, ou execute o comando de terminal:

```bash
# Via terminal
flask generate-forecast "NOME_DA_CIDADE"

# Via API (exemplo com curl)
curl -X POST http://127.0.0.1:5000/api/v1/forecast/by-city/NOME_DA_CIDADE
```

## 📋 Documentação da API

Todos os endpoints estão disponíveis sob o prefixo `/api/v1`.

| Método | Endpoint                                                     | Descrição                                                              |
| :----- | :----------------------------------------------------------- | :--------------------------------------------------------------------- |
| `GET`  | `/cities`                                                    | Retorna uma lista com todas as cidades disponíveis.                    |
| `GET`  | `/records/by-city/<cidade>`                                  | Retorna registros diários paginados para uma cidade.                   |
| `GET`  | `/records/by-city/<cidade>/on-date/<data>`                   | Retorna o registro único de uma cidade em uma data (YYYY-MM-DD).       |
| `GET`  | `/stats/accumulation/yearly/by-city/<cidade>`                | Retorna o acumulado de chuva por ano para uma cidade.                  |
| `GET`  | `/stats/accumulation/monthly/by-city/<cidade>`               | Retorna o acumulado de chuva por mês/ano para uma cidade.              |
| `GET`  | `/stats/extremes/by-city/<cidade>`                           | Retorna o dia mais chuvoso registrado para uma cidade.                 |
| `GET`  | `/forecast/by-city/<cidade>`                                 | **Busca** a previsão em cache para uma cidade (operação rápida).       |
| `POST` | `/forecast/by-city/<cidade>`                                 | **Gera/Atualiza** a previsão em cache para uma cidade (operação lenta). |

## 💡 Modelo de Previsão

Para a tarefa de prever tendências de chuva, foi escolhido um modelo estatístico de séries temporais: **SARIMA (Seasonal AutoRegressive Integrated Moving Average)**.

A escolha foi motivada pelos seguintes fatores:

1.  **Adequação aos Dados:** Dados pluviométricos possuem uma forte **sazonalidade** (padrões que se repetem anualmente). O componente "S" (Seasonal) do SARIMA foi projetado especificamente para capturar e modelar esses ciclos, tornando-o ideal para o problema.

2.  **Interpretabilidade:** Diferente de modelos complexos de Machine Learning (como redes neurais), o SARIMA é um modelo aberto e auto-explicativo. Seus parâmetros e resultados são estatisticamente interpretáveis, o que nos permite entender *como* o modelo está chegando a uma conclusão e facilita o debugging.

3.  **Eficiência com Dados Limitados:** O SARIMA consegue extrair padrões significativos de séries temporais com alguns anos de dados, sem a necessidade de volumes massivos de informação ou de múltiplas variáveis (features) que modelos de ML mais complexos exigiriam.

4.  **Automação com `auto_arima`:** A biblioteca `pmdarima` oferece a funcionalidade `auto_arima`, que automatiza o processo complexo de encontrar os melhores parâmetros (p,d,q)(P,D,Q) para o modelo. Isso torna a implementação robusta e acessível, mesmo sem um conhecimento profundo em econometria.

Em resumo, o SARIMA foi a escolha pragmática e eficaz, oferecendo um excelente equilíbrio entre performance preditiva, interpretabilidade e simplicidade de implementação para este cenário.

## 🔮 Possíveis Melhorias Futuras

  - **Workers em Segundo Plano:** Mover a geração da previsão (tarefa lenta) para uma fila de tarefas com um worker em segundo plano (usando Celery ou RQ) para que o endpoint `POST` retorne uma resposta imediata.
  - **Dashboard Frontend:** Construir a interface do usuário (em React, Vue ou Streamlit) para consumir a API e visualizar os dados.
  - **Autenticação de API:** Implementar um sistema de chaves de API para proteger os endpoints.
  - **Containerização:** Empacotar a aplicação e o banco de dados em contêineres Docker para facilitar o deploy e garantir a reprodutibilidade do ambiente.
  - **Testes Automatizados:** Adicionar testes unitários e de integração para garantir a confiabilidade do código.