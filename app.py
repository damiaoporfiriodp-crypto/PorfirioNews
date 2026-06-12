from flask import Flask, render_template, request, redirect, session
from werkzeug.utils import secure_filename
from models import db, Noticia
import os
from werkzeug.utils import secure_filename
from config import Config
from imagekitio import ImageKit
import re
import unicodedata
import base64

def gerar_slug(texto):

    texto = unicodedata.normalize(
        "NFKD",
        texto
    ).encode(
        "ascii",
        "ignore"
    ).decode(
        "ascii"
    )

    texto = texto.lower()

    texto = re.sub(
        r"[^a-z0-9]+",
        "-",
        texto
    )

    return texto.strip("-")

app = Flask(__name__)

app.secret_key = "porfirionews_admin_2026"

UPLOAD_FOLDER = "static/uploads"

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

app.config.from_object(Config)
imagekit = ImageKit(
    private_key=os.getenv("IMAGEKIT_PRIVATE_KEY"),
    public_key=os.getenv("IMAGEKIT_PUBLIC_KEY"),
    url_endpoint=os.getenv("IMAGEKIT_URL_ENDPOINT")
)

db.init_app(app)

# ==========================
# PORTAL
# ==========================

@app.route("/")
def home():

    noticias = (
        Noticia.query
        .order_by(Noticia.data_publicacao.desc())
        .all()
    )

    return render_template(
        "index.html",
        noticias=noticias
    )


@app.route("/noticia/<slug>")
def ver_noticia(slug):

    noticia = Noticia.query.filter_by(
        slug=slug
    ).first_or_404()

    return render_template(
        "noticia.html",
        noticia=noticia
    )
@app.route("/categoria/<categoria>")
def ver_categoria(categoria):

    noticias = (
        Noticia.query
        .filter_by(categoria=categoria)
        .order_by(Noticia.data_publicacao.desc())
        .all()
    )

    return render_template(
        "categoria.html",
        noticias=noticias,
        categoria=categoria
    )

@app.route("/buscar")
def buscar():

    termo = request.args.get("q", "")

    noticias = (
        Noticia.query
        .filter(
            Noticia.titulo.contains(termo) |
            Noticia.conteudo.contains(termo)
        )
        .order_by(Noticia.data_publicacao.desc())
        .all()
    )

    return render_template(
        "buscar.html",
        noticias=noticias,
        termo=termo
    )


# ==========================
# LOGIN ADMIN
# ==========================

@app.route("/admin", methods=["GET", "POST"])
def admin_login():

    if request.method == "POST":

        usuario = request.form["usuario"]
        senha = request.form["senha"]

        if usuario == "admin" and senha == "admin123":

            session["logado"] = True

            return redirect("/admin/dashboard")

    return render_template("login.html")


# ==========================
# DASHBOARD
# ==========================

@app.route("/admin/dashboard")
def dashboard():

    if not session.get("logado"):
        return redirect("/admin")

    total_noticias = Noticia.query.count()

    noticias_com_imagem = (
        Noticia.query
        .filter(Noticia.imagem.isnot(None))
        .count()
    )

    categorias = (
        db.session.query(Noticia.categoria)
        .distinct()
        .count()
    )

    return render_template(
        "dashboard.html",
        total_noticias=total_noticias,
        noticias_com_imagem=noticias_com_imagem,
        categorias=categorias
    )
# ==========================
# NOVA NOTÍCIA
# ==========================
@app.route("/admin/nova-noticia", methods=["GET", "POST"])
def nova_noticia():

    if not session.get("logado"):
        return redirect("/admin")

    if request.method == "POST":

        slug = gerar_slug(
            request.form["titulo"]
        )

        arquivo = request.files.get("imagem")

        nome_imagem = None

        if arquivo and arquivo.filename:

            arquivo_bytes = arquivo.read()

            arquivo_base64 = base64.b64encode(
                arquivo_bytes
            ).decode("utf-8")

            upload = imagekit.upload_file(
                file=arquivo_base64,
                file_name=secure_filename(
                    arquivo.filename
                )
            )

            nome_imagem = upload.response_metadata.raw["url"]

        noticia = Noticia(
            titulo=request.form["titulo"],
            subtitulo=request.form["subtitulo"],
            categoria=request.form["categoria"],
            autor=request.form["autor"],
            conteudo=request.form["conteudo"],
            imagem=nome_imagem,
            slug=slug
        )

        db.session.add(noticia)
        db.session.commit()

        return redirect("/")

    return render_template("nova_noticia.html")
@app.route("/admin/noticias")
def listar_noticias():

    if not session.get("logado"):
        return redirect("/admin")

    noticias = (
        Noticia.query
        .order_by(Noticia.data_publicacao.desc())
        .all()
    )

    return render_template(
        "listar_noticias.html",
        noticias=noticias
    )

@app.route("/admin/editar/<int:id>", methods=["GET", "POST"])
def editar_noticia(id):

    if not session.get("logado"):
        return redirect("/admin")

    noticia = Noticia.query.get_or_404(id)

    if request.method == "POST":

        noticia.titulo = request.form["titulo"]
        noticia.subtitulo = request.form["subtitulo"]
        noticia.categoria = request.form["categoria"]
        noticia.autor = request.form["autor"]
        noticia.conteudo = request.form["conteudo"]

        db.session.commit()

        return redirect("/admin/noticias")

    return render_template(
        "editar_noticia.html",
        noticia=noticia
    )

@app.route("/admin/excluir/<int:id>")
def excluir_noticia(id):

    if not session.get("logado"):
        return redirect("/admin")

    noticia = Noticia.query.get_or_404(id)

    if noticia.imagem:

        caminho = os.path.join(
            app.config["UPLOAD_FOLDER"],
            noticia.imagem
        )

        if os.path.exists(caminho):
            os.remove(caminho)

    db.session.delete(noticia)
    db.session.commit()

    return redirect("/admin/noticias")

# ==========================
# LOGOUT
# ==========================

@app.route("/logout")
def logout():

    session.clear()

    return redirect("/")


# ==========================
# CRIAÇÃO DO BANCO
# ==========================

with app.app_context():
    db.create_all()


# ==========================
# EXECUÇÃO
# ==========================

if __name__ == "__main__":
    app.run(debug=True)
