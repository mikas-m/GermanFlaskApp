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

// notes handling

document.addEventListener("DOMContentLoaded", () => {
  const saveBtn = document.querySelector(".bi-save");

  saveBtn.addEventListener("click", async () => {
    const title = document.getElementById("note-title").value.trim();
    const body = document.getElementById("note-body").value.trim();

    if (!title || !body) {
      alert("Bitte gib Titel und Inhalt ein.");
      return;
    }

    const response = await fetch("/notes", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ title, body })
    });

    const data = await response.json();

    if (response.ok) {
      // po želji: dodaj novu bilješku u DOM bez reloada
      location.reload(); // jednostavno rješenje
    } else {
      alert("Fehler: " + (data.error || "Unbekannt"));
    }
  });
});


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

document.addEventListener("DOMContentLoaded", function () {
    let pressTimer = null;
    const LONG_PRESS_DURATION = 600;  // ms

    document.querySelectorAll(".note-header").forEach(function (header) {
        header.addEventListener("mousedown", startPress);
        header.addEventListener("touchstart", startPress);

        header.addEventListener("mouseup", cancelPress);
        header.addEventListener("mouseleave", cancelPress);
        header.addEventListener("touchend", cancelPress);
        header.addEventListener("touchcancel", cancelPress);

        function startPress(e) {
            pressTimer = setTimeout(() => {
                const noteId = header.dataset.noteId;
                openEditModal(noteId);
            }, LONG_PRESS_DURATION);
        }

        function cancelPress(e) {
            clearTimeout(pressTimer);
        }
    });
});

// otvaranje modala
function openEditModal(noteId) {
    const modal = new bootstrap.Modal(document.getElementById("editModal"));
    document.getElementById("edit-note-id").value = noteId;

    // popunjavanje trenutnih vrijednosti
    document.getElementById("edit-title").value =
        document.getElementById(`note-title-${noteId}`).innerText.trim();

    document.getElementById("edit-body").value =
        document.getElementById(`note-body-${noteId}`).innerText.trim();

    modal.show();
}

