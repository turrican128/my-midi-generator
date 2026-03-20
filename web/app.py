import sys
import uuid
import re
import subprocess
from pathlib import Path
from flask import Flask, render_template, send_from_directory, abort, request, jsonify

app = Flask(__name__, template_folder='templates', static_folder='static')

PROJECT_ROOT = Path(__file__).parent.parent
OUTPUT_DIR = PROJECT_ROOT / 'output'
OUTPUT_DIR.mkdir(exist_ok=True)

ALLOWED_ROOTS = {'C','C#','D','D#','E','F','F#','G','G#','A','A#','B'}
ALLOWED_SCALES = {'major','minor','dorian','mixolydian','harmonic minor'}
ALLOWED_PRESETS = {'default','romantic','80s','synthwave'}

def _safe_stem(name: str) -> str:
    """Strip non-word chars from a filename stem, limit length."""
    return re.sub(r'[^\w\-]', '_', name)[:40] or 'file'

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

@app.route('/run/harmony', methods=['POST'])
def run_harmony():
    f = request.files.get('file')
    if not f:
        return jsonify({'error': 'No file uploaded'}), 400

    preset = request.form.get('preset', 'synthwave')
    root = request.form.get('root', 'C')
    scale_type = request.form.get('scale_type', 'minor')

    if preset not in ALLOWED_PRESETS:
        return jsonify({'error': f'Invalid preset: {preset}'}), 400
    if root not in ALLOWED_ROOTS:
        return jsonify({'error': f'Invalid root: {root}'}), 400
    if scale_type not in ALLOWED_SCALES:
        return jsonify({'error': f'Invalid scale: {scale_type}'}), 400

    uid = uuid.uuid4().hex[:8]
    stem = _safe_stem(Path(f.filename).stem)
    output_name = f'{uid}_{stem}'
    suffix = Path(f.filename).suffix.lower()
    tmp_path = OUTPUT_DIR / f'tmp_{output_name}{suffix}'

    try:
        f.save(tmp_path)
        out_file = OUTPUT_DIR / f'{output_name}_harmony.mid'
        cmd = [
            sys.executable, str(PROJECT_ROOT / 'src' / 'generate_harmony.py'),
            str(tmp_path),
            '--preset', preset,
            '--scale', root, scale_type,
            '-o', str(out_file)
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, cwd=str(PROJECT_ROOT))
        if result.returncode != 0:
            return jsonify({'error': result.stderr or result.stdout}), 400
        return jsonify({'files': [f'{output_name}_harmony.mid']})
    finally:
        tmp_path.unlink(missing_ok=True)

@app.route('/run/multitrack', methods=['POST'])
def run_multitrack():
    f = request.files.get('file')
    if not f:
        return jsonify({'error': 'No file uploaded'}), 400

    try:
        tempo = int(request.form.get('tempo', 110))
        if not (40 <= tempo <= 300):
            return jsonify({'error': 'Tempo must be between 40 and 300'}), 400
    except ValueError:
        return jsonify({'error': 'Invalid tempo value'}), 400

    uid = uuid.uuid4().hex[:8]
    custom_name = request.form.get('outname', '').strip()
    stem = _safe_stem(custom_name) if custom_name else _safe_stem(Path(f.filename).stem)
    output_name = f'{uid}_{stem}'
    suffix = Path(f.filename).suffix.lower()
    tmp_path = OUTPUT_DIR / f'tmp_{output_name}{suffix}'

    try:
        f.save(tmp_path)
        out_file = OUTPUT_DIR / f'{output_name}.mid'
        cmd = [
            sys.executable, str(PROJECT_ROOT / 'src' / 'multi_track_midi_generator.py'),
            str(tmp_path),
            '--tempo', str(tempo),
            '-o', str(out_file)
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, cwd=str(PROJECT_ROOT))
        if result.returncode != 0:
            return jsonify({'error': result.stderr or result.stdout}), 400
        files = [f'{output_name}.mid']
        log_path = OUTPUT_DIR / f'{output_name}.log'
        if log_path.exists():
            files.append(f'{output_name}.log')
        return jsonify({'files': files})
    finally:
        tmp_path.unlink(missing_ok=True)

@app.route('/run/scale', methods=['POST'])
def run_scale():
    f = request.files.get('file')
    if not f:
        return jsonify({'error': 'No file uploaded'}), 400

    root = request.form.get('root', 'C')
    scale_type = request.form.get('scale_type', 'minor')

    if root not in ALLOWED_ROOTS:
        return jsonify({'error': f'Invalid root: {root}'}), 400
    if scale_type not in ALLOWED_SCALES:
        return jsonify({'error': f'Invalid scale: {scale_type}'}), 400

    uid = uuid.uuid4().hex[:8]
    stem = _safe_stem(Path(f.filename).stem)
    output_name = f'{uid}_{stem}'
    tmp_path = OUTPUT_DIR / f'tmp_{output_name}.mid'

    try:
        f.save(tmp_path)
        out_file = OUTPUT_DIR / f'{output_name}_converted.mid'
        cmd = [
            sys.executable, str(PROJECT_ROOT / 'src' / 'scale_converter.py'),
            str(tmp_path),
            '--scale', root, scale_type,
            '-o', str(out_file)
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, cwd=str(PROJECT_ROOT))
        if result.returncode != 0:
            return jsonify({'error': result.stderr or result.stdout}), 400
        files = [f'{output_name}_converted.mid']
        log_path = OUTPUT_DIR / f'{output_name}_converted.log'
        if log_path.exists():
            files.append(f'{output_name}_converted.log')
        return jsonify({'files': files})
    finally:
        tmp_path.unlink(missing_ok=True)

if __name__ == '__main__':
    app.run(debug=True, port=5000)
