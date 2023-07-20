from flask import Flask, request, jsonify
from flask_cors import CORS
import tabula
import pandas as pd
import re
import time
import threading

app = Flask(__name__)
CORS(app)
app.debug = True

tabela_horarios_vagos = None
lock = threading.Lock()

@app.route('/')
def index():
    return 'Hello, world!'

def processar_arquivo(arquivo):
    global tabela_horarios_vagos
    file = arquivo.stream
    try:
        df = tabula.read_pdf(file, pages='all')[0]
        df = df.iloc[:, :-1]
        df = df.fillna('')

        # Extrair o texto acima da tabela
        texto_acima_tabela = tabula.read_pdf(file, pages='all', area=(0, 0, 500, 500))[0]
        texto_completo = texto_acima_tabela.to_string(index=False, header=False)

        # Extrair nome do aluno em caixa alta
        match_nome = re.search(r"Atestamos que ([A-Z\s]+)", texto_completo)
        nome_aluno = match_nome.group(1).strip() if match_nome else ""

        # Extrair curso do aluno em caixa alta
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

            # Retorna o aluno e seus horários vagos
            return dados_aluno
    except Exception as e:
        print("Exception in processar_arquivo:", str(e))

@app.route('/api/horarios-vagos', methods=['POST'])
def horarios_vagos():
    start_time = time.time()

    try:
        arquivos = request.files.getlist('file')
        dados_alunos = []

        for arquivo in arquivos:
            dados_aluno = processar_arquivo(arquivo)
            if dados_aluno is not None:
                dados_alunos.append(dados_aluno)

        # Cria o DataFrame para exibir a tabela
        df_tabela = pd.DataFrame(list(tabela_horarios_vagos), columns=['Dia', 'Horario'])

        # Converte o DataFrame em um dicionário
        response = {
            'DadosAlunos': dados_alunos,
            'TabelaHorariosVagos': df_tabela.to_dict(orient='records')
        }

        print("1=============", response)

        # Retorna a resposta como JSON
        resp = jsonify(response)

        print("2=============", resp)

        print("--- %s seconds ---" % (time.time() - start_time))

        return resp
    except Exception as e:
        print("Exception in horarios_vagos:", str(e))

    # Retorna uma resposta padrão caso nenhuma outra condição seja atendida
    response = jsonify({'message': 'Erro ao processar a solicitação.'})
    return response

if __name__ == '__main__':
    app.debug = True
    app.run(host='0.0.0.0', port=5000)
