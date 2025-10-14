// DOM Ready Handler
document.addEventListener('DOMContentLoaded', function () {
  initializeEventListeners();
  setupNavbarHiding();
  setupLongPressEditing();
});

// General Initialization
function initializeEventListeners() {
  const searchInputInsert = document.querySelector('#search_input_text_insert');
  if (searchInputInsert) {
    searchInputInsert.addEventListener('input', filterWordsDictionary);
  }

  const searchInputIrregular = document.querySelector('#search_input_text_irregular');
  if (searchInputIrregular) {
    searchInputIrregular.addEventListener('input', filterWordsIrregular);
  }

  const searchInputSchweiz = document.querySelector('#search_input_text_schweiz');
  if (searchInputSchweiz) {
    searchInputSchweiz.addEventListener('input', filterWordsSchweiz);
  }
}



// treba postaviti funkciju za long press i promjenu riječi u riječniku







// Navbar Handling
function setupNavbarHiding() {
  function hideNavbars() {
    document.querySelectorAll('.navbar').forEach(nav => nav.style.display = 'none');
  }

  function showNavbars() {
    document.querySelectorAll('.navbar').forEach(nav => nav.style.display = '');
  }

  document.querySelectorAll('input, textarea, select').forEach(el => {
    el.addEventListener('focus', hideNavbars);
    el.addEventListener('blur', showNavbars);
  });
}

// Dictionary Update
function updateValueInDictionary(element, inputName) {
  const hiddenInput = document.querySelector(`input[name='${inputName}']`);
  if (hiddenInput) {
    hiddenInput.value = element.innerText.trim();
    document.querySelector('.form-dictionary').submit();
  }
}

function focusRow(rowElement) {
  document.querySelectorAll('.word_row').forEach(row => {
    row.classList.remove('active-row');
  });
  rowElement.classList.add('active-row');
}

// Word Filtering
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
    const infinitive = row.querySelector('td:nth-child(1)').innerText.toLowerCase();
    const second_third_infinitive = row.querySelector('td:nth-child(2)').innerText.toLowerCase();
    const preterit = row.querySelector('td:nth-child(3)').innerText.toLowerCase();
    const perfekt = row.querySelector('td:nth-child(4)').innerText.toLowerCase();
    const translation = row.querySelector('td:nth-child(5)').innerText.toLowerCase();
    row.style.display = (
      infinitive.includes(filter) ||
      second_third_infinitive.includes(filter) ||
      preterit.includes(filter) ||
      perfekt.includes(filter) ||
      translation.includes(filter)
    ) ? '' : 'none';
  });
}

function filterWordsSchweiz() {
  const filter = document.querySelector('#search_input_text_schweiz').value.toLowerCase();
  document.querySelectorAll('.word_row').forEach(row => {
    const schweiz = row.querySelector('td:nth-child(2)').innerText.toLowerCase();
    const german = row.querySelector('td:nth-child(3)').innerText.toLowerCase();
    const translation = row.querySelector('td:nth-child(4)').innerText.toLowerCase();
    row.style.display = (schweiz.includes(filter) || german.includes(filter) || translation.includes(filter)) ? '' : 'none';
  });
}


function toggleVisibility(td) {
  const div = td.querySelector('div');
  if (div) {
    if (div.style.display === 'none') {
      div.style.display = 'block';
    } else {
      div.style.display = 'none';
    }
  }
}


function sanitizeId(text) {
  return text.toLowerCase()
    .trim()
    .replace(/\s+/g, '-')
    .replace(/[^a-z0-9\-]/g, '')
    .substring(0, 50);
}

const saveNoteBtn = document.getElementById('saveNoteBtn');
if (saveNoteBtn) {
  saveNoteBtn.addEventListener('click', async () => {
    const titleInput = document.getElementById('note-title');
    const bodyInput = document.getElementById('note-body');

    const title = titleInput.value.trim();
    const body = bodyInput.value.trim();

    try {
      const response = await fetch('/notes', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ title, body })
      });

      if (!response.ok) {
        throw new Error('Failed to save note');
      }

      const newNote = await response.json();
      const accordion = document.getElementById('accordion-notes');

      const accordionItem = document.createElement('div');
      accordionItem.classList.add('accordion-item');
      accordionItem.innerHTML = `
        <h2 class="accordion-header" id="heading-${newNote.id}">
          <button class="accordion-button collapsed" type="button" data-bs-toggle="collapse" data-bs-target="#collapse-${newNote.id}" aria-expanded="false" aria-controls="collapse-${newNote.id}">
            ${newNote.title}
          </button>
        </h2>
        <div id="collapse-${newNote.id}" class="accordion-collapse collapse" aria-labelledby="heading-${newNote.id}" data-bs-parent="#accordion-notes">
          <div class="accordion-body">
            ${newNote.body.replace(/\n/g, '<br>')}
          </div>
        </div>
      `;

      accordion.appendChild(accordionItem);
      titleInput.value = '';
      bodyInput.value = '';

      const modalEl = document.getElementById('new-card-note');
      const modal = bootstrap.Modal.getInstance(modalEl);
      modal.hide();

    } catch (error) {
      alert('Error saving note: ' + error.message);
    }
  });
}
