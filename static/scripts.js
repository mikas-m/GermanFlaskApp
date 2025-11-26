
// MAIN INITIALIZER
let csrfToken = null;
document.addEventListener('DOMContentLoaded', function () {
    csrfToken = document.querySelector('meta[name="csrf-token"]').getAttribute('content');
    initializeEventListeners();
    setupNavbarHiding();
    setupLongPressEditing();
    setupNoteSaving();
    setupEditSaving();
    setupLongPressEditingDictionary();
    autoDismissFlashAlerts(1500);
});

// CSRF helper for fetch requests
function getCsrfToken() {
    const meta = document.querySelector('meta[name="csrf-token"]');
    return meta ? meta.getAttribute('content') : null;
}

async function fetchWithCsrf(url, options = {}) {
    options.headers = options.headers || {};
    const token = getCsrfToken();
    if (token) options.headers['X-CSRFToken'] = token;
    return fetch(url, options);
}





// CSRF TOKEN SETUP FOR FETCH
async function postJSON(url, data) {
    try {
        const res = await fetch(url, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrfToken
            },
            body: JSON.stringify(data)
        });
        const json = await res.json();
        return { ok: res.ok, data: json };
    } catch (err) {
        console.error("POST request failed:", err);
        return { ok: false, data: { error: "Server error" } };
    }
}

// SEARCH INPUT EVENT SETUP
function initializeEventListeners() {
    const inputInsert = document.querySelector('#search_input_text_insert');
    if (inputInsert) inputInsert.addEventListener('input', filterWordsDictionary);

    const inputIrregular = document.querySelector('#search_input_text_irregular');
    if (inputIrregular) inputIrregular.addEventListener('input', filterWordsIrregular);

    const inputSchweiz = document.querySelector('#search_input_text_schweiz');
    if (inputSchweiz) inputSchweiz.addEventListener('input', filterWordsSchweiz);
}



// FILTER FUNCTIONS
function filterWordsDictionary() {
    const filter = document.querySelector('#search_input_text_insert').value.toLowerCase();

    document.querySelectorAll('.word_row').forEach(row => {
        const german = row.querySelector('td:nth-child(2)').innerText.toLowerCase();
        const translated = row.querySelector('td:nth-child(3)').innerText.toLowerCase();

        row.style.display = (german.includes(filter) || translated.includes(filter)) ? '' : 'none';
    });
}

function filterWordsIrregular() {
    const filter = document.querySelector('#search_input_text_irregular').value.toLowerCase();

    document.querySelectorAll('.word_row').forEach(row => {
        const fields = Array.from(row.querySelectorAll('td')).map(td => td.innerText.toLowerCase());
        row.style.display = fields.some(field => field.includes(filter)) ? '' : 'none';
    });
}

function filterWordsSchweiz() {
    const filter = document.querySelector('#search_input_text_schweiz').value.toLowerCase();

    document.querySelectorAll('.word_row').forEach(row => {
        const fields = Array.from(row.querySelectorAll('td')).map(td => td.innerText.toLowerCase());
        row.style.display = fields.some(field => field.includes(filter)) ? '' : 'none';
    });
}



// NAVBAR HIDING ON INPUT FOCUS
function setupNavbarHiding() {
    const inputs = document.querySelectorAll('input, textarea, select');
    if (!inputs.length) return;

    const hideNavbars = () => document.querySelectorAll('.navbar').forEach(nav => nav.style.display = 'none');
    const showNavbars = () => document.querySelectorAll('.navbar').forEach(nav => nav.style.display = '');

    inputs.forEach(el => {
        el.addEventListener('focus', hideNavbars);
        el.addEventListener('blur', showNavbars);
    });
}



// LONG PRESS INLINE EDIT FOR DICTIONARY WORDS (pointer-based)
function setupLongPressEditingDictionary() {
    const LONG_PRESS_DURATION = 600;
    const editableCells = document.querySelectorAll('.editable-word');

    editableCells.forEach(cell => {
        let pressTimer = null;
        let pointerDown = false;

        const startPress = (ev) => {
            console.debug('long-press start on', cell, 'event:', ev && ev.type);
            if (ev && ev.preventDefault) ev.preventDefault();
            pointerDown = true;
            cell.style.userSelect = 'none';

            pressTimer = setTimeout(() => {
                if (pointerDown) {
                    console.debug('long-press threshold reached for', cell);
                    enableInlineEdit(cell);
                }
            }, LONG_PRESS_DURATION);
        };

        const cancelPress = () => {
            pointerDown = false;
            clearTimeout(pressTimer);
            cell.style.userSelect = '';
        };

        if (window.PointerEvent) {
            cell.addEventListener('pointerdown', startPress);
            cell.addEventListener('pointerup', cancelPress);
            cell.addEventListener('pointerleave', cancelPress);
            cell.addEventListener('pointercancel', cancelPress);
        } else {
            cell.addEventListener('mousedown', startPress);
            cell.addEventListener('mouseup', cancelPress);
            cell.addEventListener('mouseleave', cancelPress);
            cell.addEventListener('touchstart', startPress, { passive: false });
            cell.addEventListener('touchend', cancelPress);
            cell.addEventListener('touchcancel', cancelPress);
        }

        cell.addEventListener('dblclick', () => {
            console.debug('dblclick triggers enableInlineEdit on', cell);
            enableInlineEdit(cell);
        });
    });
}



// LONG PRESS FOR EDITING NOTES
function setupLongPressEditing() {
    const headers = document.querySelectorAll('.note-header');
    if (!headers.length) return;

    const LONG_PRESS_DURATION = 600;

    headers.forEach(header => {
        let pressTimer = null;
        let pointerDown = false;

        const startPress = (ev) => {
            pointerDown = true;
            if (ev && ev.preventDefault) ev.preventDefault();
            pressTimer = setTimeout(() => {
                if (pointerDown) openEditModal(header.dataset.noteId);
            }, LONG_PRESS_DURATION);
        };

        const cancelPress = () => {
            pointerDown = false;
            clearTimeout(pressTimer);
        };

        if (window.PointerEvent) {
            header.addEventListener('pointerdown', startPress);
            header.addEventListener('pointerup', cancelPress);
            header.addEventListener('pointerleave', cancelPress);
            header.addEventListener('pointercancel', cancelPress);
        } else {
            header.addEventListener('mousedown', startPress);
            header.addEventListener('mouseup', cancelPress);
            header.addEventListener('mouseleave', cancelPress);
            header.addEventListener('touchstart', startPress, { passive: false });
            header.addEventListener('touchend', cancelPress);
            header.addEventListener('touchcancel', cancelPress);
        }
    });
}



// OPEN NOTES EDIT MODAL
function openEditModal(noteId) {
    const modalElement = document.getElementById('edit-modal');
    if (!modalElement) return;

    const modal = new bootstrap.Modal(modalElement);

    const titleEl = document.getElementById(`note-title-${noteId}`);
    const bodyEl = document.getElementById(`note-body-${noteId}`);

    document.getElementById('edit-note-id').value = noteId;
    document.getElementById('edit-title').value = titleEl?.innerText.trim() || '';
    document.getElementById('edit-body').value = bodyEl?.innerText.trim() || '';

    modal.show();
}



// SAVE TO CREATE NEW NOTE
function setupNoteSaving() {
    const saveBtn = document.getElementById('saveNoteBtn');
    if (!saveBtn) return;

    saveBtn.addEventListener('click', async () => {
        const title = document.getElementById('note-title').value.trim();
        const body = document.getElementById('note-body').value.trim();
        if (!title || !body) return alert('Bitte gib Titel und Inhalt ein.');

            try {
                const response = await fetchWithCsrf('/notes', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json', 'X-CSRFToken': csrfToken },
                body: JSON.stringify({ title, body })
            });
            const data = await response.json();
            if (response.ok) {
                await showTemporaryMessage(data.message || 'Notiz erstellt', (data.category || 'success'));
                if (data.reload) location.reload();
            } else {
                await showTemporaryMessage(data.error || data.message || 'Fehler: unbekannt', 'error');
            }
        } catch (err) {
            alert('Verbindungsfehler.');
        }
    });
}



// SAVE TO EDIT NOTE
function setupEditSaving() {
    const btn = document.getElementById('saveEditBtn');
    if (!btn) return;

    btn.addEventListener('click', async () => {
        const id = document.getElementById('edit-note-id').value;
        const title = document.getElementById('edit-title').value.trim();
        const body = document.getElementById('edit-body').value.trim();

        if (!title || !body) return alert('Bitte fülle alle Felder aus.');

            try {
                const res = await fetchWithCsrf('/notes/edit', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json', 'X-CSRFToken': csrfToken },
                body: JSON.stringify({ id, title, body })
            });

            const data = await res.json();
            if (res.ok) {
                await showTemporaryMessage(data.message || 'Notiz aktualisiert', (data.category || 'success'));
                if (data.reload) location.reload();
                else {
                    const modalEl = document.getElementById('edit-modal');
                    const instance = bootstrap.Modal.getInstance(modalEl);
                    if (instance) instance.hide();
                }
            } else {
                await showTemporaryMessage(data.error || data.message || 'Fehler', 'error');
            }
        } catch (err) {
            alert('Verbindungsfehler.');
        }
    });
}



// ENABLE INLINE EDITING
function enableInlineEdit(cell) {
    if (!cell) return;
    // Safety: don't allow inline edits for irregular table cells or cells marked non-editable
    if (cell.closest && cell.closest('.table-irregular')) return;
    if (cell.dataset && cell.dataset.editable === 'false') return;
    console.debug('enableInlineEdit called for', cell);

    cell.dataset.disableToggle = '1';
    cell.style.userSelect = '';

    const div = cell.querySelector('div');
    if (!div) return;

    const oldValue = div.innerText.trim();
    const wordId = cell.dataset.wordId;
    const column = cell.dataset.column;
    const table = cell.dataset.table || 'GermanWords';

    div.setAttribute('contenteditable', 'true');
    div.focus();

    try {
        const range = document.createRange();
        range.selectNodeContents(div);
        const sel = window.getSelection();
        sel.removeAllRanges();
        sel.addRange(range);
    } catch (e) {}

    div.style.outline = '2px solid #17a2b8';
    div.style.borderRadius = '4px';
    div.style.padding = '2px 4px';

    const finishEditing = (revert = false) => {
        div.removeAttribute('contenteditable');
        div.style.outline = '';
        div.style.padding = '';
        delete cell.dataset.disableToggle;
        cell.style.userSelect = '';

        if (revert) div.innerText = oldValue;
    };

    const saveChanges = async () => {
        const newValue = div.innerText.trim();
        finishEditing(newValue === oldValue || newValue === '');
        if (newValue === oldValue || newValue === '') return;

            try {
                const result = await fetchWithCsrf('/dictionary/update', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json', 'X-CSRFToken': csrfToken },
                body: JSON.stringify({ id: wordId, column: column, value: newValue, table: table })
            });

            const data = await result.json();
            if (result.ok) {
                await showTemporaryMessage(data.message || 'Saved', (data.category || 'success'));
                if (data.reload) location.reload();
            } else {
                div.innerText = oldValue;
                await showTemporaryMessage(data.error || 'Save failed', 'error');
            }
        } catch (err) {
            div.innerText = oldValue;
            showTemporaryMessage('Server error', 'error');
        }
    };

    div.addEventListener('blur', () => saveChanges(), { once: true });

    const onKey = (e) => {
        if (e.key === 'Enter') {
            e.preventDefault();
            div.blur();
        } else if (e.key === 'Escape') {
            e.preventDefault();
            finishEditing(true);
            div.removeEventListener('keydown', onKey);
        }
    };

    div.addEventListener('keydown', onKey);
}



// UTILITIES
function toggleVisibility(td) {
    if (td.dataset && td.dataset.disableToggle === '1') return;
    const div = td.querySelector('div');
    if (div) div.style.display = div.style.display === 'none' ? 'block' : 'none';
}



// MESSAGE DISPLAY
function showTemporaryMessage(text, type = 'info', durationMs = 1500) {
    return new Promise((resolve) => {
        const msg = document.createElement('div');
    msg.className = 'inline-temp-msg';
    msg.style.position = 'fixed';
    msg.style.right = '16px';
    msg.style.bottom = '16px';
    msg.style.padding = '8px 12px';
    msg.style.borderRadius = '6px';
    msg.style.color = '#fff';
    msg.style.zIndex = 9999;
    msg.style.background = type === 'success' ? '#28a745' : (type === 'error' ? '#dc3545' : '#17a2b8');
    msg.innerText = text;

        document.body.appendChild(msg);

        setTimeout(() => {
            msg.style.transition = 'opacity 300ms ease-out';
            msg.style.opacity = '0';
            setTimeout(() => { msg.remove(); resolve(); }, 350);
        }, durationMs);
    });
}



function autoDismissFlashAlerts(timeoutMs = 1500) {
    const alerts = document.querySelectorAll('.alert.alert-dismissible');
    if (!alerts.length) return;

    alerts.forEach(el => {
        setTimeout(() => {
            try {
                if (window.bootstrap && bootstrap.Alert && bootstrap.Alert.getOrCreateInstance) {
                    const inst = bootstrap.Alert.getOrCreateInstance(el);
                    inst.close();
                    return;
                }
            } catch (e) {
            }

            el.style.transition = 'opacity 300ms ease-out, transform 300ms ease-out';
            el.style.opacity = '0';
            el.style.transform = 'translateY(-6px)';
            setTimeout(() => el.remove(), 350);
        }, timeoutMs);
    });
}