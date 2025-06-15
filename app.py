from flask import Flask, request, jsonify, render_template_string
import psycopg2
import os

app = Flask(__name__)

# Use environment variable on Render.com for secure DB connection
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://qrmappinguser:VM0EIqWngW5BZMzNGb7D1ZnHXSYnmPkJ@dpg-d17dqe2dbo4c73fqu71g-a.oregon-postgres.render.com/qr_mapping_db_av1")

def get_connection():
    return psycopg2.connect(DATABASE_URL, sslmode='require')

@app.route('/get_qr_details')
def get_qr_details():
    title = request.args.get('title')
    if not title:
        return jsonify({'error': 'Missing title parameter'}), 400

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT title, location, use, category FROM qr_mapping WHERE title = %s", (title,))
            row = cur.fetchone()
            if row:
                return jsonify(dict(zip(['title', 'location', 'use', 'category'], row)))
            return jsonify({'error': 'Title not found'}), 404

@app.route('/update_qr_details', methods=['POST'])
def update_qr_details():
    data = request.json
    if not all(k in data for k in ('title', 'location', 'use', 'category')):
        return jsonify({'error': 'Missing one or more required fields'}), 400

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                UPDATE qr_mapping
                SET location = %s,
                    use = %s,
                    category = %s
                WHERE title = %s
            """, (data['location'], data['use'], data['category'], data['title']))
            
            if cur.rowcount == 0:
                return jsonify({'error': 'Title not found'}), 404
            
            conn.commit()
    return jsonify({'message': 'Details updated successfully'})

@app.route('/edit_qr')
def edit_qr():
    return render_template_string("""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Edit QR Details</title>
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
            body { font-family: Arial; padding: 20px; }
            input, textarea { width: 100%; padding: 10px; margin: 5px 0; }
            button { padding: 10px 20px; margin-top: 10px; }
        </style>
    </head>
    <body>
        <h2>Edit QR Details</h2>
        <input type="text" id="title" placeholder="Enter title and press Fetch">
        <button onclick="fetchDetails()">Fetch</button>
        <textarea id="location" placeholder="Location"></textarea>
        <textarea id="use" placeholder="Use"></textarea>
        <textarea id="category" placeholder="Category"></textarea>
        <button onclick="updateDetails()">Update</button>
        <p id="response"></p>
        <script>
            function fetchDetails() {
                const title = document.getElementById('title').value;
                fetch(`/get_qr_details?title=${title}`)
                .then(res => res.json())
                .then(data => {
                    if (data.error) return alert(data.error);
                    document.getElementById('location').value = data.location;
                    document.getElementById('use').value = data.use;
                    document.getElementById('category').value = data.category;
                });
            }

            function updateDetails() {
                const title = document.getElementById('title').value;
                const location = document.getElementById('location').value;
                const use = document.getElementById('use').value;
                const category = document.getElementById('category').value;

                fetch('/update_qr_details', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({ title, location, use, category })
                })
                .then(res => res.json())
                .then(data => {
                    document.getElementById('response').innerText = data.message || data.error;
                });
            }
        </script>
    </body>
    </html>
    """)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
