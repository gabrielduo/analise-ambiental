"""
============================================
Arquivo: app.py
--------------------------------------------
Aplicação Flask para análise ambiental:
- Rota “/”: exibe a página principal com classificação de qualidade do ar e estatísticas.
- Rota “/report_error”: recebe relatório de erro (texto + imagem) e salva em uploads/.
- Utiliza compressão de resposta (Flask-Compress) e gestão de uploads com secure_filename.
- Carrega funções de utils (classificação, meteorologia, visualizações Plotly e gradientes).
- Configura caminhos para bancos CSV e inicializa pasta de uploads.
- Permite execução standalone em modo debug.
============================================
"""

from flask import Flask, render_template, request, jsonify
from flask_compress import Compress
from werkzeug.utils import secure_filename
import os

from config import (
    DATABASE_PATH,          # Caminho para o banco de dados de qualidade do ar
    NEW_DATABASE_PATH,      # Caminho para CSV usado nos gradientes
    METEOROLOGY_PATH,       # Caminho para o banco de dados de meteorologia
    SQLALCHEMY_DATABASE_URI # (não utilizado diretamente aqui)
)
from utils.classifica import classify_air
from utils.met import get_meteorologia
from utils.visualization_plotly import generate_plotly_html
from utils.visualization_gradient import (
    generate_gradient_image,
    generate_max_gradient_image,
    generate_min_gradient_image
)

# --- Inicialização da aplicação Flask e compressão de resposta ---
app = Flask(__name__)
Compress(app)

# --- Pasta para armazenar relatórios de erro enviados via form ---
# --- Futuramente vou alterar isso e os erros serão enviados de outra forma ---
UPLOADS_FOLDER = os.path.join(app.root_path, 'uploads')
os.makedirs(UPLOADS_FOLDER, exist_ok=True)


@app.route("/", methods=["GET", "POST"])
def index():
    """
    Rota principal que serve o template 'index.html'.
    - Em GET: exibe valores padrão de data, hora e estação.
    - Em POST (form de estatísticas): recebe 'metric' para gerar gráfico Plotly.
    """
    # valores padrão (para primeira carga da página)
    default_date    = '2024-12-31'
    default_hour    = '23'
    default_station = 'EAMA11'
    default_time    = f"{default_hour}:30:00"

    # chama o utilitário de classificação de qualidade do ar
    result = classify_air(
        default_date,
        default_time,
        default_station,
        database_path=DATABASE_PATH
    )

    # inicializa variáveis de estatísticas
    graph_html = None
    metric     = None

    # gera sempre as três imagens de gradiente (média, máximo e mínimo)
    gradient_url     = generate_gradient_image(csv_path=NEW_DATABASE_PATH)
    gradient_max_url = generate_max_gradient_image(csv_path=NEW_DATABASE_PATH)
    gradient_min_url = generate_min_gradient_image(csv_path=NEW_DATABASE_PATH)

    # se for POST e estiver vindo um parâmetro 'metric', gera o gráfico correspondente
    if request.method == "POST" and "metric" in request.form:
        m = request.form.get("metric", "").lower()
        if m in ("mp10", "mp2.5"):
            metric     = m
            graph_html = generate_plotly_html(metric)

    # Renderiza o template 'index.html' com todos os dados necessários para a view principal
    return render_template(
        "index.html",
        result            = result,            # Dicionário com resultado da classificação padrão de qualidade do ar
        selected_date     = default_date,      # Data atualmente selecionada/exibida no formulário
        selected_hour     = default_hour,      # Hora atualmente selecionada/exibida no formulário
        selected_station  = default_station,   # Estação atualmente selecionada/exibida no formulário
        graph_html        = graph_html,        # HTML do gráfico Plotly (ou None se não houver gráfico)
        metric            = metric,            # Métrica selecionada para o gráfico (mp10, mp2.5 ou None)
        gradient_url      = gradient_url,      # URL da imagem de gradiente média
        gradient_max_url  = gradient_max_url,  # URL da imagem de gradiente de valor máximo
        gradient_min_url  = gradient_min_url   # URL da imagem de gradiente de valor mínimo
    )

@app.route('/classificar', methods=['POST'])
def classificar():
    """
    Rota que processa a submissão do formulário de classificação (modo template).
    Recebe 'input_date', 'input_hour' e 'station', executa classify_air e re-renderiza index.html.
    """
    input_date = request.form.get('input_date')
    input_hour = request.form.get('input_hour')
    input_time = f"{input_hour}:30:00" if input_hour else "23:30:00"
    station    = request.form.get('station')

    # sempre gera as imagens de gradiente atualizadas
    grad_med = generate_gradient_image(csv_path=NEW_DATABASE_PATH)
    grad_max = generate_max_gradient_image(csv_path=NEW_DATABASE_PATH)
    grad_min = generate_min_gradient_image(csv_path=NEW_DATABASE_PATH)

    # Validação de campos obrigatórios: data, hora e estação devem estar presentes
    if not input_date or not input_hour or not station:
        # Se algum estiver ausente, renderiza novamente 'index.html' exibindo mensagem de erro
        return render_template(
            'index.html',
            result            = {"error": "Preencha data, hora e estação para classificar."},  # Mensagem de validação
            selected_date     = input_date,     # Mantém os valores já preenchidos para não limpar o formulário
            selected_hour     = input_hour,
            selected_station  = station,
            graph_html        = None,           # Sem gráfico Plotly quando há erro na validação
            metric            = None,           # Sem métrica selecionada
            gradient_url      = grad_med,       # URLs dos gradientes ainda gerados para manter a UI consistente
            gradient_max_url  = grad_max,
            gradient_min_url  = grad_min
        )

    # efetua a classificação real
    result = classify_air(
        input_date,
        input_time,
        station,
        database_path=DATABASE_PATH
    )
    return render_template(
        'index.html',
        result            = result,
        selected_date     = input_date,
        selected_hour     = input_hour,
        selected_station  = station,
        graph_html        = None,
        metric            = None,
        gradient_url      = grad_med,
        gradient_max_url  = grad_max,
        gradient_min_url  = grad_min
    )

@app.route('/classificar/json', methods=['POST'])
def classificar_json():
    """
    Rota que serve a API JSON para classificação de qualidade do ar.
    Útil para chamadas AJAX (ex: no modo inline).
    Retorna JSON com o resultado ou erro 400 se faltarem parâmetros.
    """
    # Obtém a data enviada no formulário (espera-se 'YYYY-MM-DD')
    input_date = request.form.get('input_date')
    # Obtém a hora enviada no formulário (espera-se 'HH')
    input_hour = request.form.get('input_hour')
    # Obtém o código da estação enviada no formulário
    station    = request.form.get('station')

    # Validação: se faltar qualquer parâmetro obrigatório, retorna erro 400 com mensagem JSON
    if not input_date or not input_hour or not station:
        return jsonify({'error': 'Data, hora e estação são obrigatórios.'}), 400

    # Chama a função que realiza a classificação, montando o timestamp no formato "HH:30:00"
    result = classify_air(
        input_date,
        f"{input_hour}:30:00",    # Concatena minuto fixo ":30:00" à hora
        station,
        database_path=DATABASE_PATH
    )

    # Retorna o resultado da classificação como JSON para o cliente
    return jsonify(result)

@app.route('/meteorologia', methods=['POST'])
def meteorologia():
    """
    Rota que serve a API JSON para dados meteorológicos.
    Recebe 'input_date' e 'input_hour' via POST e retorna JSON produzido por get_meteorologia().
    """
    # Obtém a data enviada no formulário (formato 'YYYY-MM-DD')
    input_date = request.form.get('input_date')
    # Obtém a hora enviada no formulário (formato 'HH')
    input_hour = request.form.get('input_hour')

    # Se faltar data ou hora, retorna erro 400 e mensagem JSON
    if not input_date or not input_hour:
        return jsonify({"error": "Data e hora são obrigatórias."}), 400

    # Chama a função que busca os dados meteorológicos no banco especificado
    result = get_meteorologia(
        input_date,
        input_hour,
        database_path=METEOROLOGY_PATH
    )

    # Retorna os dados meteorológicos como JSON para o cliente
    return jsonify(result)

@app.route('/sobre-iqar')
def sobre_iqar():
    """
    Rota que renderiza a explicação do IQAr no mesmo template 'index.html'.
    Passa a flag 'explicacao=True' para o template saber que deve exibir o conteúdo de ajuda.
    """
    # Gera a imagem de gradiente para visualização de média
    grad_med = generate_gradient_image(csv_path=NEW_DATABASE_PATH)
    # Gera a imagem de gradiente para visualização de valor máximo
    grad_max = generate_max_gradient_image(csv_path=NEW_DATABASE_PATH)
    # Gera a imagem de gradiente para visualização de valor mínimo
    grad_min = generate_min_gradient_image(csv_path=NEW_DATABASE_PATH)

    # Renderiza o template 'index.html', indicando que deve exibir a seção de explicação do IQAr
    return render_template(
        'index.html',
        explicacao        = True,       # sinaliza para o template mostrar o conteúdo de ajuda
        graph_html        = None,       # sem gráfico Plotly nesta rota
        metric            = None,       # sem métrica selecionada
        gradient_url      = grad_med,   # URL da imagem de gradiente média
        gradient_max_url  = grad_max,   # URL da imagem de gradiente máximo
        gradient_min_url  = grad_min    # URL da imagem de gradiente mínimo
    )

@app.route('/report_error', methods=['POST'])
def report_error():
    """
    Rota para upload de relatórios de erro.
    Recebe texto e arquivo opcional, salva em pasta numerada em 'uploads/' e retorna JSON de confirmação.
    """
    # Obtém o texto do relatório e o arquivo enviado (opcional)
    error_text = request.form.get('error_text')
    error_file = request.files.get('error_file')

    # Se não houver texto, retorna erro 400 em JSON
    if not error_text:
        return jsonify({'error': 'O texto do erro é obrigatório.'}), 400

    # Lista todas as pastas existentes em UPLOADS_FOLDER que comecem com 'error_'
    # encontra a próxima pasta 'error_N'
    existing = [
        d for d in os.listdir(UPLOADS_FOLDER)
        if os.path.isdir(os.path.join(UPLOADS_FOLDER, d)) and d.startswith("error_")
    ]
    # Determina o maior número já usado para não sobrescrever
    max_num = 0
    for d in existing:
        try:
            # Extrai o número após 'error_' e atualiza max_num se for maior
            num = int(d.split("_")[1])
            if num > max_num:
                max_num = num
        except ValueError:
            # Ignora pastas com nome inesperado
            continue

    # cria diretório para este relatório
    new_num = max_num + 1
    new_dir = os.path.join(UPLOADS_FOLDER, f"error_{new_num}")
    os.makedirs(new_dir, exist_ok=True)

    # salva o texto
    error_txt = os.path.join(new_dir, "error.txt")
    with open(error_txt, "w", encoding="utf-8") as f:
        f.write(error_text)

    # salva o arquivo de imagem, se houver
    image_path = None
    if error_file:
        fn = secure_filename(error_file.filename)
        image_path = os.path.join(new_dir, fn)
        error_file.save(image_path)

    # retorna JSON com informações sobre o upload
    return jsonify({
        'message':         'Erro reportado com sucesso!',
        'error_dir':       os.path.basename(new_dir),
        'error_text_file': os.path.basename(error_txt),
        'image_path':      image_path and os.path.basename(image_path)
    }), 200


if __name__ == '__main__':
    # executa a aplicação em modo debug
    app.run(debug=True)
