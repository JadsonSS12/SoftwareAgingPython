#!/bin/bash

# Definição de caminhos
PROJECT_DIR="/home/jadson/Downloads/virtualizacao/Lpython/gemini/https"
JMETER_BIN="/home/jadson/Downloads/apache-jmeter-5.6.3/bin" # Ajuste para o seu caminho do bin do JMeter
cd $PROJECT_DIR

# 1. Ativação do ambiente virutal
source .venv/bin/activate

# Inicia o Gunicorn
gunicorn main:app --workers 4 --worker-class uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000 & [cite: 1]

sleep 10

# 2. Execução do JMeter com geração de relatório HTML
$JMETER_BIN/jmeter -n -t $PROJECT_DIR/test_jmeter.jmx -l resultadosHttpGemini.jtl -e -o ./relatorioHttpgemini_html [cite: 1, 4]

echo "Execução concluída e relatório gerado."