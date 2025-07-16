import os
import datetime
from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
import werkzeug

app = Flask(__name__)
CORS(app)

# --- Configuração do Banco de Dados ---
# Tenta carregar a URL do banco de produção a partir de uma variável de ambiente.
# Se não encontrar, usa um banco de dados SQLite local para desenvolvimento.
DATABASE_URL = os.getenv('DATABASE_URL')
if DATABASE_URL:
    app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL
else:
    # Cria um banco de dados local chamado 'talentos.db' na raiz do projeto
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'talentos.db')

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# --- Pasta de Uploads e Configs ---
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'pdf', 'doc', 'docx'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# --- Função para verificar extensão ---
def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# --- Modelo da Tabela Candidato ---
class Candidato(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(150), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    cpf = db.Column(db.String(20), unique=True, nullable=False)
    telefone = db.Column(db.String(20), nullable=False)
    cargo_desejado = db.Column(db.String(150), nullable=False)
    caminho_curriculo = db.Column(db.String(255), nullable=False)
    data_cadastro = db.Column(db.DateTime, default=datetime.datetime.utcnow)

    def __repr__(self):
        return f'<Candidato {self.nome}>'

    def as_dict(self):
       return {c.name: { 'value': getattr(self, c.name).isoformat() } if isinstance(getattr(self, c.name), datetime.datetime) else { 'value': getattr(self, c.name) } for c in self.__table__.columns}

# --- Rota da API de Upload ---
@app.route('/upload', methods=['POST'])
def upload_file():
    # Validação dos campos
    required_fields = ['nome', 'email', 'cpf', 'telefone', 'cargo_desejado']
    form_data = request.form
    
    for field in required_fields:
        if field not in form_data or not form_data[field]:
            return jsonify({'error': f'O campo {field} é obrigatório'}), 400

    if 'curriculo' not in request.files:
        return jsonify({'error': 'Nenhum arquivo de currículo enviado'}), 400

    file = request.files['curriculo']
    if file.filename == '':
        return jsonify({'error': 'Nenhum arquivo de currículo selecionado'}), 400

    if not allowed_file(file.filename):
        return jsonify({'error': 'Tipo de arquivo não permitido. Apenas PDF, DOC e DOCX são aceitos.'}), 400

    # Verifica se CPF ou Email já existem
    if Candidato.query.filter_by(email=form_data['email']).first():
        return jsonify({'error': 'Este email já foi cadastrado.'}), 409
    if Candidato.query.filter_by(cpf=form_data['cpf']).first():
        return jsonify({'error': 'Este CPF já foi cadastrado.'}), 409

    if file:
        try:
            # Salva o arquivo do currículo
            original_filename = werkzeug.utils.secure_filename(file.filename)
            timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
            filename_base, file_extension = os.path.splitext(original_filename)
            unique_filename = f"{form_data['cpf'].replace('.', '').replace('-', '')}_{timestamp}{file_extension}"
            caminho_arquivo = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
            file.save(caminho_arquivo)

            # Cria a nova entrada no banco de dados
            novo_candidato = Candidato(
                nome=form_data['nome'],
                email=form_data['email'],
                cpf=form_data['cpf'],
                telefone=form_data['telefone'],
                cargo_desejado=form_data['cargo_desejado'],
                caminho_curriculo=caminho_arquivo
            )

            db.session.add(novo_candidato)
            db.session.commit()

            return jsonify({'message': 'Cadastro realizado com sucesso!'}), 201

        except Exception as e:
            db.session.rollback()
            # Log do erro no servidor para depuração
            print(f"Erro ao salvar no banco de dados: {e}")
            return jsonify({'error': 'Ocorreu um erro interno ao salvar os dados.'}), 500

    return jsonify({'error': 'Ocorreu um erro inesperado'}), 500

# --- Rota da API para Ler Candidatos (Protegida) ---
@app.route('/candidatos', methods=['GET'])
def get_candidatos():
    # Pega o token de uma variável de ambiente no servidor
    SECRET_KEY = os.getenv('API_SECRET_KEY')
    
    # Se a chave não estiver configurada no servidor, ninguém pode acessar.
    if not SECRET_KEY:
        return jsonify({"error": "Acesso não configurado no servidor"}), 500
        
    # Pega o token enviado pelo cliente no cabeçalho
    auth_header = request.headers.get('Authorization')
    
    if not auth_header or auth_header != f"Bearer {SECRET_KEY}":
        return jsonify({"error": "Acesso não autorizado"}), 401
    
    try:
        candidatos = Candidato.query.order_by(Candidato.data_cadastro.desc()).all()
        # Converte a lista de objetos para uma lista de dicionários
        candidatos_list = [candidato.as_dict() for candidato in candidatos]
        return jsonify(candidatos_list), 200
    except Exception as e:
        print(f"Erro ao buscar candidatos: {e}")
        return jsonify({"error": "Erro interno ao buscar dados"}), 500


if __name__ == '__main__':
    with app.app_context():
        # Inicializa o banco de dados
        db.create_all()
    app.run(debug=True) 