# Usar Python 3.11
FROM python:3.11-slim

# Diretório de trabalho
WORKDIR /app

# Copia todos os arquivos
COPY . .

# Atualiza pip e instala dependências
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# Expõe porta para Render (ping server)
EXPOSE 8080

# Comando para rodar o bot
CMD ["python", "main.py"]
