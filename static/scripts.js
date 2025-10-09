// scripts.js

// DOM Ready Handler
document.addEventListener('DOMContentLoaded', function() {
  initializeEventListeners();
  setupNavbarHiding();
});

// General Initialization
function initializeEventListeners() {
  // Generated Card Click
  const generatedCard = document.querySelector('.generated-card');
  if (generatedCard) {
    generatedCard.addEventListener('click', function() {
      this.classList.toggle('clicked');
    });
  }

  // Dictionary Filter
  const searchInput = document.querySelector('#search_input_text');
  if (searchInput) {
    searchInput.addEventListener('input', filter_words);
  }

  // Dictionary Long Press
  if (document.querySelector('.tbody td')) {
    erase();
  }
}

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
function update_value_in_dictionary(element, inputName) {
  let hiddenInput = document.querySelector(`input[name='${inputName}']`);
  hiddenInput.value = element.innerText.trim();
  document.querySelector('.form-dictionary').submit();
}

function focus_row(rowElement) {
  document.querySelectorAll('.word_row').forEach(row => {
    row.classList.remove('active-row');
  }); 
  rowElement.classList.add('active-row');
}


// Word Filtering
function filter_words_dictionary() {
  const filter = document.querySelector('#search_input_text').value.toLowerCase();
  document.querySelectorAll('.word_row').forEach(row => {
    const german = row.querySelector('td:nth-child(2)').innerText.toLowerCase();
    const translated = row.querySelector('td:nth-child(3)').innerText.toLowerCase();
    row.style.display = (german.includes(filter) || translated.includes(filter)) ? '' : 'none';
  });
}


function filter_words_irregular() {
  const filter = document.querySelector('#search_input_text').value.toLowerCase();
  document.querySelectorAll('.word_row').forEach(row => {
    const infinitive = row.querySelector('td:nth-child(1)').innerText.toLowerCase();
    const second_third_infinitive = row.querySelector('td:nth-child(2)').innerText.toLowerCase();
    const preterit = row.querySelector('td:nth-child(3)').innerText.toLowerCase();
    const perfekt = row.querySelector('td:nth-child(4)').innerText.toLowerCase();
    const translation = row.querySelector('td:nth-child(5)').innerText.toLowerCase();
    row.style.display = (infinitive.includes(filter) || second_third_infinitive.includes(filter) || preterit.includes(filter) || perfekt.includes(filter) || translation.includes(filter)) ? '' : 'none';
  });
}


// Notes Handling
function sanitizeId(text) {
  return text.toLowerCase()
    .trim()
    .replace(/\s+/g, '-')
    .replace(/[^a-z0-9\-]/g, '')
    .substring(0, 50);
}

document.getElementById('saveNoteBtn').addEventListener('click', async () => {
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

