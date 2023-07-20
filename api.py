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

        if dados_alunos:
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
        else:
            # Retorna uma resposta de erro indicando que nenhum aluno foi processado com sucesso
            response = jsonify({'message': 'Nenhum aluno foi processado com sucesso.'})
            return response
    except Exception as e:
        print("Exception in horarios_vagos:", str(e))

    # Retorna uma resposta padrão caso nenhuma outra condição seja atendida
    response = jsonify({'message': 'Erro ao processar a solicitação.'})
    return response
