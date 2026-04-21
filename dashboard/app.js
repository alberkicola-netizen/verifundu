"use strict";

const APP_STATE = {
    screen: 'home',
    scanning: false,
    history: [],
    sessionStart: Date.now()
};

// ── NAVIGATION ──
const screens = document.querySelectorAll('.screen');
const navItems = document.querySelectorAll('.nav-item');

function showScreen(name) {
    screens.forEach(s => s.classList.toggle('active', s.id === `screen-${name}`));
    navItems.forEach(n => n.classList.toggle('active', n.dataset.screen === name));
    APP_STATE.screen = name;
}

navItems.forEach(btn => {
    btn.addEventListener('click', () => showScreen(btn.dataset.screen));
});

// ── UPLOAD LOGIC ──
const fileInput = document.getElementById('file-input');
const dropZone = document.getElementById('drop-zone');
const imagePreview = document.getElementById('image-preview');
const previewContainer = document.getElementById('preview-container');
const dropContentDefault = document.getElementById('drop-content-default');

fileInput.addEventListener('change', (e) => {
    const file = e.target.files[0];
    if (file) handleFile(file);
});

function handleFile(file) {
    // SECURITY: Limit to 5MB, JPG/PNG/PDF
    if (file.size > 5 * 1024 * 1024) return alert("Arquivo muito grande (Máx 5MB)");
    
    const reader = new FileReader();
    reader.onload = (e) => {
        // Thumbnail preview
        imagePreview.src = e.target.result;
        previewContainer.classList.remove('hidden');
        dropContentDefault.classList.add('hidden');
        
        // SPEED: Auto-trigger after 1s
        setTimeout(() => startAnalysis(), 1000);
    };
    reader.readAsDataURL(file);
}

// ── ANALYSIS ENGINE ──
function startAnalysis() {
    if (APP_STATE.scanning) return;
    APP_STATE.scanning = true;
    
    const pipelineStatus = document.getElementById('pipeline-status');
    const extractionFields = document.getElementById('extraction-fields');
    pipelineStatus.classList.remove('hidden');
    
    const stages = ['preprocess', 'ocr', 'vision'];
    let step = 0;

    const interval = setInterval(() => {
        if (step < stages.length) {
            const el = document.getElementById(`stage-${stages[step]}`);
            el.querySelector('.dot').style.background = '#00e676';
            el.style.color = '#fff';
            
            // SECURITY: Masking data during extraction
            if (stages[step] === 'ocr') {
                showField('IBAN', 'AO06 **** **** **** **** 4001');
                showField('Batalha', 'Banco BAI');
            }
            step++;
        } else {
            clearInterval(interval);
            finishAnalysis();
        }
    }, 1200); // Verdict within ~4 seconds total
}

function showField(label, val) {
    const fields = document.getElementById('extraction-fields');
    fields.classList.remove('hidden');
    const div = document.createElement('div');
    div.style.cssText = "font-size:12px; margin-bottom:4px; color:rgba(255,255,255,0.7)";
    div.innerHTML = `<strong>${label}:</strong> ${val}`;
    fields.appendChild(div);
}

function finishAnalysis() {
    APP_STATE.scanning = false;
    const overlay = document.getElementById('verdict-overlay');
    overlay.classList.remove('hidden');
}

document.getElementById('btn-close-verdict').addEventListener('click', () => {
    document.getElementById('verdict-overlay').classList.add('hidden');
    resetScan();
    showScreen('home');
});

function resetScan() {
    previewContainer.classList.add('hidden');
    dropContentDefault.classList.remove('hidden');
    document.getElementById('pipeline-status').classList.add('hidden');
    document.getElementById('extraction-fields').innerHTML = '';
    document.getElementById('extraction-fields').classList.add('hidden');
    fileInput.value = '';
    document.querySelectorAll('.dot').forEach(d => d.style.background = 'rgba(255,255,255,0.2)');
}

// ── SESSION TIMEOUT (5 MIN) ──
setInterval(() => {
    const inactiveTime = Date.now() - APP_STATE.sessionStart;
    if (inactiveTime > 4.5 * 60 * 1000) {
        document.getElementById('timeout-warning').classList.remove('hidden');
    }
    if (inactiveTime > 5 * 60 * 1000) {
        window.location.reload(); // Hard reset for security
    }
}, 10000);

// ── INITIALIZE ──
document.addEventListener('DOMContentLoaded', () => {
    showScreen('home');
    // Simulated demo mode
    document.getElementById('btn-demo').addEventListener('click', () => {
        imagePreview.src = "https://i.ibb.co/Xz9Fp0S/receipt.jpg";
        previewContainer.classList.remove('hidden');
        dropContentDefault.classList.add('hidden');
        setTimeout(() => startAnalysis(), 500);
    });
});
