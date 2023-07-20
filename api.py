from flask import Flask, request, jsonify
from flask_cors import CORS
import tabula
import pandas as pd
import re
import threading
from werkzeug.utils import secure_filename
import os
import logging

app = Flask(__name__)
CORS(app)

tabela_horarios_vagos = None
lock = threading.Lock()

UPLOAD_FOLDER = os.path.join(os.getcwd(), 'uploads')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Configurar o objeto de logger
logger = logging.getLogger('app')
logger.setLevel(logging.DEBUG)

# Criar um manipulador de arquivo para escrever as mensagens de log em um arquivo
log_file = 'app.log'
file_handler = logging.FileHandler(log_file)
file_handler.setLevel(logging.DEBUG)

# Criar um formato para as mensagens de log
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
file_handler.setFormatter(formatter)

# Adicionar o manipulador de arquivo ao logger
logger.addHandler(file_handler)


@app.route('/')
def index():
    return 'Hello, world!'


def processar_arquivo(arquivo):
    global tabela_horarios_vagos
    file = arquivo.stream
    filename = secure_filename(file.filename)
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(file_path)

    df = tabula.read_pdf(file_path, pages='all')[0]
    df = df.iloc[:, :-1]
    df = df.fillna('')

    texto_acima_tabela = tabula.read_pdf(file_path, pages='all', area=(0, 0, 500, 500))[0]
    texto_completo = texto_acima_tabela.to_string(index=False, header=False)

    match_nome = re.search(r"Atestamos que ([A-Z\s]+)", texto_completo)
    nome_aluno = match_nome.group(1).strip() if match_nome else ""

    match_curso = re.search(r"curso de ([A-Z\s]+)", texto_completo)
    curso_aluno = match_curso.group(1).strip() if match_curso else ""

    horarios_vagos = []
    for indice, linha in df.iterrows():
        horario = linha.iloc[0]
        for coluna in df.columns[1:]:
            dia = coluna.strip()
            horario_vago = linha[coluna]
            if not horario_vago:
                horarios_vagos.append((dia, horario))

    with lock:
        global tabela_horarios_vagos
        if tabela_horarios_vagos is None:
            tabela_horarios_vagos = set(horarios_vagos)
        else:
            tabela_horarios_vagos = tabela_horarios_vagos.intersection(set(horarios_vagos))

        dados_aluno = {
            'Nome': nome_aluno,
            'Curso': curso_aluno
        }

        os.remove(file_path)

        return dados_aluno


@app.route('/api/horarios-vagos', methods=['POST'])
def horarios_vagos():
    try:
        arquivos = request.files.getlist('file')
        dados_alunos = []

        for arquivo in arquivos:
            dados_aluno = processar_arquivo(arquivo)
            if dados_aluno is not None:
                dados_alunos.append(dados_aluno)

        df_tabela = pd.DataFrame(list(tabela_horarios_vagos), columns=['Dia', 'Horario'])
        response = {
            'DadosAlunos': dados_alunos,
            'TabelaHorariosVagos': df_tabela.to_dict(orient='records')
        }

        return jsonify(response)

    except Exception as e:
        logger.exception("Exceção na função horarios_vagos")  # Registrar exceção com traceback completo

        response = {
            'message': 'Erro ao processar a solicitação.'
        }
        return jsonify(response)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
