# Use uma imagem base Python
FROM python:3.9

# Defina o diretório de trabalho no contêiner
WORKDIR /app

# Copie os arquivos necessários para o diretório de trabalho
COPY api.py requirements.txt ./

# Instale as dependências
RUN pip install --no-cache-dir -r requirements.txt

# Exponha a porta em que a API será executada
EXPOSE 5000

# Execute o comando para iniciar a API
CMD ["python", "api.py"]
