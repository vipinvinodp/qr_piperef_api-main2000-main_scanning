from flask import Flask, request, send_file, jsonify, render_template_string
import qrcode
from PIL import Image
from fpdf import FPDF
import io
import os

app = Flask(__name__)

# Load QR reference data from pipe-separated file
def load_qr_data(file_path="qr_mapping_pipe_separated.txt"):
    qr_data = {}
    if not os.path.exists(file_path):
        return qr_data
    with open(file_path, "r", encoding="utf-8") as f:
        lines = f.readlines()[1:]  # skip header
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

@app.route("/generate_sheet", methods=["POST"])
def generate_sheet():
    try:
        data_list = request.get_json().get("data", [])
        cols, rows = 10, 10
        qr_size = 150
        pdf = FPDF(orientation="P", unit="pt", format="A4")
        pdf.add_page()

        logo = Image.open("doll.png")
        logo_size = 60
        logo.thumbnail((logo_size, logo_size))

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

            x = (idx % cols) * qr_size
            y = (idx // cols) * qr_size

            img_byte = io.BytesIO()
            img_qr.save(img_byte, format="PNG")
            img_byte.seek(0)

            temp_img_path = f"temp_qr_{idx}.png"
            with open(temp_img_path, "wb") as f:
                f.write(img_byte.read())
            pdf.image(temp_img_path, x=x, y=y, w=qr_size, h=qr_size)
            os.remove(temp_img_path)

        output_path = "qr_sheet_output.pdf"
        pdf.output(output_path)
        return send_file(output_path, as_attachment=True, download_name="qr_sheet.pdf", mimetype="application/pdf")

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/view/<code>", methods=["GET"])
def view_code(code):
    qr_data = load_qr_data()
    entry = qr_data.get(code.upper())
    if not entry:
        return f"<h3>No entry found for {code}</h3>", 404

    html_template = """
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
    """
    return render_template_string(html_template, **entry)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
