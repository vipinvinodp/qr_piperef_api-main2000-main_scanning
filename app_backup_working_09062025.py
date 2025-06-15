from flask import Flask, request, send_file, jsonify, render_template_string
import qrcode
from PIL import Image, ImageDraw, ImageFont
import io
import os

app = Flask(__name__)

def load_qr_data(file_path="qr_mapping_pipe_separated.txt"):
    qr_data = {}
    if not os.path.exists(file_path):
        return qr_data
    with open(file_path, "r", encoding="utf-8") as f:
        lines = f.readlines()[1:]
        for line in lines:
            parts = line.strip().split("|")
            if len(parts) == 4:
                title, location, use, category = parts
                qr_data[title.upper()] = {
                    "title": title,
                    "location": location,
                    "use": use,
                    "category": category
                }
    return qr_data

@app.route("/view/<code>", methods=["GET"])
def view_code(code):
    qr_data = load_qr_data()
    entry = qr_data.get(code.upper())
    if not entry:
        return f"<h3>No entry found for {code}</h3>", 404

    html_template = '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>{{ title }}</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 40px; }
            h2 { color: #4CAF50; }
            .label { font-weight: bold; }
            .info { margin-top: 15px; }
        </style>
    </head>
    <body>
        <h2>{{ title }}</h2>
        <div class="info"><span class="label">Where to keep:</span> {{ location }}</div>
        <div class="info"><span class="label">Use:</span> {{ use }}</div>
        <div class="info"><span class="label">Category:</span> {{ category }}</div>
    </body>
    </html>
    '''
    return render_template_string(html_template, **entry)

@app.route("/generate_sheet", methods=["POST"])
def generate_sheet():
    try:
        data_list = request.get_json().get("data", [])
        cols, rows = 10, 10
        qr_size = 150
        page_width = cols * qr_size
        page_height = rows * qr_size
        sheet = Image.new("RGB", (page_width, page_height), "white")

        logo = Image.open("doll.png")
        logo_size = 60
        logo.thumbnail((logo_size, logo_size))

        try:
            font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 16)
        except:
            font = ImageFont.load_default()

        for idx, item in enumerate(data_list[:100]):
            code = item.get("X1", "AVX")
            qr_url = f"https://qr-piperef-api-main100.onrender.com/view/{code}"

            qr = qrcode.QRCode(
                version=2,
                error_correction=qrcode.constants.ERROR_CORRECT_H,
                box_size=2,
                border=1
            )
            qr.add_data(qr_url)
            qr.make(fit=True)
            img_qr = qr.make_image(fill_color="black", back_color="white").convert("RGB")
            img_qr = img_qr.resize((qr_size, qr_size))

            pos = ((qr_size - logo_size) // 2, (qr_size - logo_size) // 2)
            img_qr.paste(logo, pos, mask=logo if logo.mode == 'RGBA' else None)

            draw = ImageDraw.Draw(img_qr)
            text = code
            bbox = draw.textbbox((0, 0), text, font=font)
            text_width, text_height = bbox[2] - bbox[0], bbox[3] - bbox[1]
            text_x = (qr_size - text_width) // 2
            text_y = pos[1] + logo_size - text_height  # bottom align with logo bottom
            draw.text((text_x, text_y), text, font=font, fill="green")

            x = (idx % cols) * qr_size
            y = (idx // cols) * qr_size
            sheet.paste(img_qr, (x, y))

        output = io.BytesIO()
        sheet.save(output, format="PNG")
        output.seek(0)
        return send_file(output, mimetype="image/png")

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
