from .extensions import db

class PluviometricData(db.Model):
    """
    Modelo de dados para armazenar os registros diários de precipitação.
    """
    __tablename__ = 'pluviometric_data'

    id = db.Column(db.Integer, primary_key=True)
    data = db.Column(db.Date, nullable=False, index=True)
    precipitacao_mm = db.Column(db.Float, nullable=False)
    cidade = db.Column(db.String(100), nullable=False)
    estado = db.Column(db.String(2), nullable=False)
    estacao_codigo = db.Column(db.String(10), nullable=False, index=True)

    # Restrição para garantir que não haja entradas duplicadas para a mesma
    # estação no mesmo dia.
    __table_args__ = (
        db.UniqueConstraint('data', 'estacao_codigo', name='_data_estacao_uc'),
    )

    def __repr__(self):
        """
        Representação em string do objeto
        """
        return f"<PluviometricData {self.estacao_codigo} em {self.data}: {self.precipitacao_mm}mm>"