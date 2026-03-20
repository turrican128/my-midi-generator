import sys
import uuid
from pathlib import Path
from flask import Flask, render_template, send_from_directory, abort

app = Flask(__name__, template_folder='templates', static_folder='static')

PROJECT_ROOT = Path(__file__).parent.parent
OUTPUT_DIR = PROJECT_ROOT / 'output'

ALLOWED_ROOTS = {'C','C#','D','D#','E','F','F#','G','G#','A','A#','B'}
ALLOWED_SCALES = {'major','minor','dorian','mixolydian','harmonic minor'}
ALLOWED_PRESETS = {'default','romantic','80s','synthwave'}

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/download/<filename>')
def download(filename):
    # Prevent path traversal
    safe = OUTPUT_DIR / filename
    if not safe.resolve().is_relative_to(OUTPUT_DIR.resolve()):
        abort(400)
    return send_from_directory(OUTPUT_DIR, filename, as_attachment=True)

if __name__ == '__main__':
    app.run(debug=True, port=5000)
