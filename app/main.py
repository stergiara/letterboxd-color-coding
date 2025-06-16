# app/main.py
from flask import Flask, request, send_file, jsonify
import os, tempfile, zipfile
from .downloaders import download_posters

app = Flask(__name__, static_folder=None)
app.config['MAX_CONTENT_LENGTH'] = 10 * 1024 * 1024  # 10 MB

@app.route('/upload', methods=['POST'])
def upload_and_zip():
    f = request.files.get('file')
    if not f or not f.filename.endswith('.csv'):
        return jsonify(error="Please upload a .csv"), 400

    tmp = tempfile.mkdtemp()
    csv_path = os.path.join(tmp, 'input.csv')
    f.save(csv_path)

    out_dir = os.path.join(tmp, 'covers')
    downloaded = download_posters(csv_path, out_dir)

    if not downloaded:
        return jsonify(error="No posters downloaded"), 500

    # Create zip
    zip_path = os.path.join(tmp, 'posters.zip')
    with zipfile.ZipFile(zip_path, 'w') as z:
        for img in downloaded:
            z.write(img, arcname=os.path.basename(img))

    return send_file(zip_path, mimetype='application/zip',
                     as_attachment=True, download_name='posters.zip')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
