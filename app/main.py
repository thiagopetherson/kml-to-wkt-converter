from flask import Flask, request, render_template, send_file
from shapely.geometry import MultiPolygon
from utils import extract_all_possible_polygons
import io

# Inicializa o app Flask (equivalente ao instanciar uma aplicação Laravel/Lumen)
app = Flask(__name__)

# Define a rota principal ("/"), aceitando GET e POST
@app.route("/", methods=["GET", "POST"])
def index():
    wkt_output = ""  # Inicializa o WKT como string vazia

    if request.method == "POST":
        kml_content = ""

        # Se o usuário enviou um arquivo via formulário
        if "kml_file" in request.files and request.files["kml_file"].filename:
            # Lê o conteúdo do arquivo .kml enviado
            kml_content = request.files["kml_file"].read().decode("utf-8")
        else:
            # Ou pega o conteúdo colado no textarea (kml_text)
            kml_content = request.form.get("kml_text", "")

        # Extrai todos os polígonos válidos do KML (função definida em utils.py)
        polygons = extract_all_possible_polygons(kml_content)

        # Trata os casos possíveis
        if not polygons:
            wkt_output = "Nenhuma geometria válida encontrada no KML."
        elif len(polygons) == 1:
            wkt_output = polygons[0].wkt  # Apenas 1 polígono - retorna como POLYGON
        else:
            try:
                # Tenta agrupar todos como MULTIPOLYGON, mantendo divisões
                multi = MultiPolygon(polygons)
                wkt_output = multi.wkt
            except Exception:
                # Fallback: se erro, tenta unir os polígonos como um só (pode apagar divisões internas)
                from shapely.ops import unary_union
                wkt_output = unary_union(polygons).wkt

        # Se o botão "download" foi clicado
        if "download" in request.form:
            return send_file(
                io.BytesIO(wkt_output.encode("utf-8")),  # Converte string para arquivo em memória
                mimetype="text/plain",
                as_attachment=True,
                download_name="output.wkt"
            )

    # Renderiza o HTML, passando o WKT (se houver)
    return render_template("index.html", wkt=wkt_output)


# Executa o servidor Flask na porta 5000
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
