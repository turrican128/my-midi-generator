// ── Tab switching ──────────────────────────────────────────────────────────
document.querySelectorAll('.tab').forEach(tab => {
  tab.addEventListener('click', () => {
    document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
    document.querySelectorAll('.panel').forEach(p => p.classList.remove('active'));
    tab.classList.add('active');
    document.getElementById('panel-' + tab.dataset.tab).classList.add('active');
  });
});

// ── Drop zones ─────────────────────────────────────────────────────────────
document.querySelectorAll('.drop-zone').forEach(zone => {
  const input = zone.querySelector('.file-input');
  const accepts = (zone.dataset.accept || '').split(',').map(s => s.trim().toLowerCase());

  function setFile(file) {
    if (!accepts.some(ext => file.name.toLowerCase().endsWith(ext))) {
      showError(zone, `Wrong file type. Expected: ${accepts.join(' or ')}`);
      return;
    }
    clearError(zone);
    zone.classList.add('has-file');
    zone.querySelector('.dz-filename').textContent = file.name;
    zone.querySelector('.dz-title').textContent = '▶ FILE LOADED';
    zone._file = file;

    // Enable generate button for this panel
    const panel = zone.closest('.panel');
    panel.querySelector('.gen-btn').disabled = false;

    // Auto-fill output name if multitrack
    const nameInput = panel.querySelector('#mt-outname');
    if (nameInput && !nameInput.value) {
      nameInput.value = file.name.replace(/\.[^.]+$/, '');
    }
  }

  zone.addEventListener('dragover', e => {
    e.preventDefault();
    zone.classList.add('drag-over');
  });
  zone.addEventListener('dragleave', () => zone.classList.remove('drag-over'));
  zone.addEventListener('drop', e => {
    e.preventDefault();
    zone.classList.remove('drag-over');
    const file = e.dataTransfer.files[0];
    if (file) setFile(file);
  });
  input.addEventListener('change', () => {
    if (input.files[0]) setFile(input.files[0]);
    input.value = '';
  });
});

// ── Tempo slider ───────────────────────────────────────────────────────────
const tempoSlider = document.getElementById('mt-tempo');
const tempoVal    = document.getElementById('mt-tempo-val');
if (tempoSlider) {
  function updateSlider() {
    const pct = ((tempoSlider.value - tempoSlider.min) / (tempoSlider.max - tempoSlider.min) * 100).toFixed(1);
    tempoSlider.style.setProperty('--pct', pct + '%');
    tempoVal.textContent = tempoSlider.value;
  }
  tempoSlider.addEventListener('input', updateSlider);
  updateSlider();
}

// ── Generate buttons ───────────────────────────────────────────────────────
document.querySelectorAll('.gen-btn').forEach(btn => {
  btn.addEventListener('click', async () => {
    const panel  = btn.closest('.panel');
    const zone   = panel.querySelector('.drop-zone');
    const file   = zone._file;
    const route  = btn.dataset.route;
    const errEl  = panel.querySelector('.error-msg');
    const outList = panel.querySelector('.output-list');

    if (!file) return;

    // Build form data
    const fd = new FormData();
    fd.append('file', file);
    panel.querySelectorAll('select[name], input[name]').forEach(el => {
      fd.append(el.name, el.value);
    });
    // Tempo from slider (no name attribute on slider)
    if (route === '/run/multitrack') {
      fd.append('tempo', tempoSlider.value);
    }

    // Loading state
    const orig = btn.textContent;
    btn.disabled = true;
    btn.textContent = '⏳ GENERATING...';
    errEl.textContent = '';
    outList.innerHTML = '';

    try {
      const res  = await fetch(route, { method: 'POST', body: fd });
      const data = await res.json();

      if (!res.ok) {
        errEl.textContent = '✗ ERROR: ' + (data.error || 'Unknown error');
        return;
      }

      // Render output files
      data.files.forEach(fname => {
        const item = document.createElement('div');
        item.className = 'output-item';
        item.innerHTML = `
          <span class="output-fname">${fname}</span>
          <a class="output-dl" href="/download/${encodeURIComponent(fname)}" download="${fname}">⟶ DOWNLOAD</a>
        `;
        outList.appendChild(item);
      });
    } catch (err) {
      errEl.textContent = '✗ NETWORK ERROR: ' + err.message;
    } finally {
      btn.disabled = false;
      btn.textContent = orig;
    }
  });
});

// ── Helpers ────────────────────────────────────────────────────────────────
function showError(zone, msg) {
  const panel = zone.closest('.panel');
  const errEl = panel.querySelector('.error-msg');
  if (errEl) errEl.textContent = '✗ ' + msg;
}

function clearError(zone) {
  const panel = zone.closest('.panel');
  const errEl = panel.querySelector('.error-msg');
  if (errEl) errEl.textContent = '';
}
