# Use uma imagem base Python
FROM python:3.11.4

# Defina o diretório de trabalho no contêiner
WORKDIR /app

# Instale as dependências
RUN pip install --upgrade pip
RUN pip install tabula-py
RUN pip install flask_cors
RUN pip install pandas

# Exponha a porta 5000
EXPOSE 5000

# Execute o comando para iniciar a API
CMD ["python", "api.py"]
