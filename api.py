from flask import Flask, request, jsonify
from flask_cors import CORS
import tabula
import pandas as pd
import re
import time
import threading

app = Flask(__name__)
CORS(app)

tabela_horarios_vagos = None
lock = threading.Lock()

def processar_arquivo(arquivo):
    global tabela_horarios_vagos
    file = arquivo.stream
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

@app.route('/api/horarios-vagos', methods=['POST'])
def horarios_vagos():
    start_time = time.time()

    arquivos = request.files.getlist('file')
    threads = []
    dados_alunos = []

    for arquivo in arquivos:
        thread = threading.Thread(target=lambda: dados_alunos.append(processar_arquivo(arquivo)))
        thread.start()
        threads.append(thread)

    for thread in threads:
        thread.join()

    # Cria o DataFrame para exibir a tabela
    df_tabela = pd.DataFrame(list(tabela_horarios_vagos), columns=['Dia', 'Horario'])

    # Converte o DataFrame em um dicionário
    response = {
        'DadosAlunos': dados_alunos,
        'TabelaHorariosVagos': df_tabela.to_dict(orient='records')
    }

    # Retorna a resposta como JSON
    resp = jsonify(response)

    print("--- %s seconds ---" % (time.time() - start_time))

    return resp

if __name__ == '__main__':
    app.debug = True
    app.run(host='0.0.0.0', port=5000)
