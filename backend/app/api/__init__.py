from flask import Blueprint

# O primeiro argumento é o nome do blueprint.
# O segundo é o nome do módulo/pacote, __name__ é o padrão.
api_bp = Blueprint('api', __name__)

# Importamos as rotas no final para evitar importações circulares.
# Este é um padrão comum em Flask.
from . import routes