import os
import io
from datetime import datetime
from flask import Flask, render_template, request, jsonify
from dotenv import load_dotenv
import cloudinary
import cloudinary.uploader
import cloudinary.api
from PIL import Image, ImageOps, ImageDraw, ImageFont

load_dotenv()

app = Flask(__name__)

cloudinary.config(
    cloud_name=os.getenv('CLOUD_NAME'),
    api_key=os.getenv('CLOUD_API_KEY'),
    api_secret=os.getenv('CLOUD_API_SECRET')
)

def create_polaroid(image_file):
    # 1. Abre a imagem
    img = Image.open(image_file)
    img = ImageOps.exif_transpose(img) # Corrige rotação do celular
    
    # 2. Redimensiona
    base_width = 1000
    w_percent = (base_width / float(img.size[0]))
    h_size = int((float(img.size[1]) * float(w_percent)))
    img = img.resize((base_width, h_size), Image.Resampling.LANCZOS)
    
    # 3. Cria a Borda (Maior embaixo para caber 3 linhas)
    # Esquerda, Cima, Direita, Baixo
    border = (40, 40, 40, 320) 
    img_with_border = ImageOps.expand(img, border=border, fill='white')
    
    draw = ImageDraw.Draw(img_with_border)
    
    # 4. Carrega a Fonte
    try:
        # Tenta carregar a fonte que você baixou
        font_title = ImageFont.truetype("font.ttf", 90) # Bodas (Grande)
        font_names = ImageFont.truetype("font.ttf", 70) # Nomes (Médio)
        font_date = ImageFont.truetype("font.ttf", 50)  # Data (Menor)
        print("SUCESSO: Fonte font.ttf carregada!")
    except Exception as e:
        # Se der erro, avisa no terminal e usa a feia
        print(f"ERRO: Não achei a fonte font.ttf. Erro: {e}")
        font_title = ImageFont.load_default()
        font_names = ImageFont.load_default()
        font_date = ImageFont.load_default()

    # 5. Define os Textos
    text_1 = "Bodas de Ouro"
    text_2 = "Jonas e Cleide"
    text_3 = datetime.now().strftime('%d/%m/%Y')
    
    # 6. Desenha Centralizado
    W = img_with_border.width
    H = img_with_border.height
    
    # A lógica de posição é: Altura total - Espaço que deixamos embaixo + ajuste
    # Posição Y da primeira linha
    y_pos = H - 250 
    
    # Desenha usando ancora 'mm' (middle-middle) para ficar bem no centro horizontal
    draw.text((W/2, y_pos), text_1, fill="black", font=font_title, anchor="mm")
    draw.text((W/2, y_pos + 80), text_2, fill="black", font=font_names, anchor="mm")
    draw.text((W/2, y_pos + 150), text_3, fill="black", font=font_date, anchor="mm")
    
    output = io.BytesIO()
    img_with_border.save(output, format='JPEG', quality=95)
    output.seek(0)
    return output

@app.route('/')
def index():
    try:
        resources = cloudinary.api.resources(
            type="upload",
            prefix=os.getenv('CLOUDINARY_FOLDER', 'festa_tios'),
            max_results=50,
            direction="desc"
        )
        photos = resources.get('resources', [])
    except:
        photos = []
    return render_template('index.html', photos=photos)

@app.route('/upload', methods=['POST'])
def upload():
    file = request.files.get('photo')
    if not file: return jsonify({'error': 'Erro'}), 400

    try:
        # Processa a Polaroid
        polaroid_img = create_polaroid(file)
        
        # Nome único
        filename = f"bodas_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        # Upload
        polaroid_img.seek(0)
        cloudinary.uploader.upload(
            polaroid_img,
            public_id=filename,
            folder=os.getenv('CLOUDINARY_FOLDER', 'festa_tios'),
            resource_type="image"
        )
        return jsonify({'success': True})
    except Exception as e:
        print(e)
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)