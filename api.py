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
