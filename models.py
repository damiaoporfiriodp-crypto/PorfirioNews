from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class Noticia(db.Model):
    __tablename__ = "noticias"

    id = db.Column(db.Integer, primary_key=True)

    titulo = db.Column(db.String(255), nullable=False)

    subtitulo = db.Column(db.String(500))

    conteudo = db.Column(db.Text, nullable=False)

    categoria = db.Column(db.String(100))

    imagem = db.Column(db.String(255))

    autor = db.Column(db.String(100))

    data_publicacao = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )

    destaque = db.Column(
        db.Boolean,
        default=False
    )

    slug = db.Column(
        db.String(255),
        unique=True
    )