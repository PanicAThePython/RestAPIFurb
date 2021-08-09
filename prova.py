# Natália Sens Weise
from flask import Flask, jsonify, redirect, make_response
from flask.globals import request
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from flask_jwt_extended import create_access_token
from flask_jwt_extended import jwt_required
from flask_jwt_extended import JWTManager

app = Flask("__name__")
app.config['SECRET_KEY']='teste'
app.config["JWT_SECRET_KEY"] = "secreto" 
app.config['SQLALCHEMY_DATABASE_URI']='sqlite:///prova.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True

jwt = JWTManager(app)
db = SQLAlchemy(app)

class Produto(db.Model):
    __tablename__ = 'Produtos'
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(50))
    preco = db.Column(db.Float)
    comanda_id = db.Column(db.Integer, db.ForeignKey('Comandas.id'), nullable = True)

    def __init__(self, nome="", preco=0.0):
        self.id = None
        self.nome = str(nome)
        self.preco = float(preco)
        self.comanda_id = None

class Usuario(db.Model):

    __tablename__ = 'Usuarios'
    idUsuario = db.Column(db.Integer, primary_key=True)
    senha = db.Column(db.String(30))
    nomeUsuario = db.Column(db.String(50))
    telefoneUsuario = db.Column(db.String(15))
    comanda_id = db.Column(db.Integer, db.ForeignKey('Comandas.id'), nullable = True)

    def __init__(self,  nome="", tel=""):
        self.idUsuario = None
        self.senha = ""
        self.nomeUsuario = str(nome)
        self.telefoneUsuario = str(tel)
        self.comanda_id = None

class Comanda(db.Model):

    __tablename__ = 'Comandas'
    id = db.Column(db.Integer, primary_key=True)
    usuarios = db.relationship('Usuario', lazy = 'select', backref = db.backref('comanda', lazy = 'joined'))
    produtos = db.relationship('Produto', lazy = 'select', backref = db.backref('comanda', lazy = 'joined'))

    def __init__(self, usuarios, produtos):
        self.id = None
        self.usuarios = usuarios
        self.produtos = produtos

if __name__ == "__main__":
    db.create_all()


@app.route("/")
def home():
    return redirect("/comandas")

@app.route("/comandas", methods=["GET"])
def getComandas():
    try:
        comandas = Comanda.query.all()
        resposta = []
        
        for c in comandas:
            for u in c.usuarios:
                dados = {}
                dados['idUsuario'] = int(u.idUsuario)
                dados['nomeUsuario'] = str(u.nomeUsuario)
                dados['telefoneUsuario'] = str(u.telefoneUsuario)

                resposta.append(dados)

        return jsonify({"usuarios": resposta})
    except:
        return make_response("Not Found", 404)
            

@app.route('/comandas/<id>', methods=["GET"])
def getComandaId(id):
    try:
        usuario = db.session.query(Usuario).filter_by(comanda_id = int(id)).first()
        produto = db.session.query(Produto).filter_by(comanda_id = int(id))

        produtos = []
        
        for p in produto:
            dados = {}
            dados['id'] = p.id
            dados['nome'] = p.nome
            dados['preco'] = p.preco
            
            produtos.append(dados)

        resposta = {"idUsuario":int(usuario.idUsuario),
                    "nomeUsuario":str(usuario.nomeUsuario),
                    "telefoneUsuario":str(usuario.telefoneUsuario),
                    "produtos": produtos}

        return jsonify(resposta)
       
    except:
        return make_response("Not Found", 404)

@app.route("/comandas", methods=['POST'])
def setComanda():
    try:
        dados = request.json
        prods = dados['produtos']
        resposta = []
        usuarios = []
        
        for p in prods:
            produto = Produto(str(p['nome']), float(p['preco']))

            db.session.add(produto)
            resposta.append(produto)

        novoUsuario = db.session.query(Usuario).filter_by(idUsuario = int(dados['idUsuario'])).first()
        
        if dados['nomeUsuario'] == novoUsuario.nomeUsuario and dados['telefoneUsuario'] == novoUsuario.telefoneUsuario:
            usuarios.append(novoUsuario)
            novaComanda = Comanda(usuarios, resposta)
            
            db.session.add(novoUsuario)
            db.session.add(novaComanda)
            db.session.commit()
            
            dados['id'] = novaComanda.id
            dados['idUsuario'] = novoUsuario.idUsuario
            dados['nomeUsuario'] = novoUsuario.nomeUsuario
            dados['telefoneUsuario'] = novoUsuario.telefoneUsuario
            
            return jsonify(dados)
        return make_response("The request has semantic errors", 422)
    except:
        return make_response("The request has semantic errors", 422)

@app.route("/comandas/<id>", methods=['PUT'])
def resetComanda(id):
    try:
        prods = db.session.query(Produto).filter_by(comanda_id = int(id)).first()

        dados = request.json
        produto = db.session.query(Produto).get(int(dados['id']))

        if prods.id == produto.id:
            if dados['nome']:
                produto.nome = dados['nome']
            
            if dados['preco']:
                produto.preco = dados['preco']

            db.session.add(produto)
            db.session.commit()

            sucess = {"sucess":{"text":"produto da comanda atualizado"}}
            return jsonify(sucess)

        return make_response("Not Found", 404)

    except:
        return make_response("Not Found", 404)



@app.route("/usuario/<id>", methods=['PUT'])
def resetUsuario(id):
    try:
        usuario = db.session.query(Usuario).filter_by(idUsuario = int(id)).first()
        dados = request.json

        if dados['telefoneUsuario']:
            usuario.telefoneUsuario = dados['telefoneUsuario']
            db.session.add(usuario)
            db.session.commit()

            sucess = {"sucess":{"text":"usuario da comanda atualizado"}}
            return jsonify(sucess)

        return make_response("Not Found", 404)

    except:
        return make_response("Not Found", 404)

@app.route('/usuario', methods=['POST'])
def registrarUsuario():  
    try:
        dados = request.json
        senhaProtegida = generate_password_hash(dados['senha'], method='sha256')

        novoUsuario = Usuario(str(dados['nomeUsuario']), str(dados['telefoneUsuario']))
        novoUsuario.senha = str(senhaProtegida)

        db.session.add(novoUsuario)  
        db.session.commit()    
        
        # sucess = {"sucess":{"text":"usuario registrado com sucesso"}}
        # return jsonify(sucess)
        resposta = {"idUsuario":int(novoUsuario.idUsuario),
                    "nomeUsuario":str(novoUsuario.nomeUsuario),
                    "telefoneUsuario":str(novoUsuario.telefoneUsuario)}

        return jsonify(resposta)
    except:
        return make_response("Request has a semantic error", 422)


@app.route('/login', methods=['POST'])  
def login(): 
    try:
        dados = request.json
        nomeUsuario = dados['nomeUsuario']
        senha = dados['senha']

        usuario = Usuario.query.filter_by(nomeUsuario = dados['nomeUsuario']).first()

        if not check_password_hash(usuario.senha, senha):
            return make_response("Login Invalid", 401)

        acesso = create_access_token(identity=nomeUsuario)
        return jsonify(token=acesso)
    except:
        return make_response('Could Not Verify. Login Is Required',  401)

@app.route("/comandas/<id>", methods=['DELETE'])
@jwt_required(optional=False)
def deleteComanda(id):
    try:
        excluir = db.session.query(Comanda).get(int(id))
        db.session.delete(excluir)
        db.session.commit()
        sucess = {"sucess":{"text":"comanda removida"}}
        return jsonify(sucess)
    except:
        return make_response("Not Found", 404)
    

app.run(port=8080)