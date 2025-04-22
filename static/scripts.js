// generate random words
function generate_word(button_id) {
    const word_type = button_id === 'generate-german' ? 'generate-german' : 'generate-translation';

    fetch("/checkup/generate_word", {
        method: "POST",
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ 'word_type': word_type })
    })
    .then(response => response.json())
    .then(data => {
        document.querySelector('.generated-word').textContent = data.generated_word;
        document.querySelector('.correct-translation').textContent = data.correct_translation;
    });
}

// function when user click checkbox
document.querySelector('.generated-card').addEventListener('click', function() {
    this.classList.toggle('clicked');
});


// check correct translation
function check_translation() {
    const card = document.querySelector('.generated-card');
    const correct_translation = document.querySelector('.correct-translation').textContent.trim();
    const user_input_field = document.querySelector('.user-input');
    const user_input = user_input_field.value.trim();

    card.classList.remove('correct', 'wrong');

    if (user_input.length > 0) {
        card.classList.add('wrong');
    }

    if (user_input === correct_translation) {
        card.classList.remove('wrong');
        card.classList.add('correct');
    }
}




// update value in dictionary
function update_value_in_dictionary(element, inputName) {
    let hiddenInput = document.querySelector(`input[name='${inputName}']`);
    hiddenInput.value = element.innerText.trim();
    document.querySelector('.form-dictionary').submit();
}




// filter words in dictionary
function filter_words() {
    let input = document.querySelector('#search_input_text');
    let filter = input.value.toLowerCase();

    let rows = document.querySelectorAll('.word_row');

    rows.forEach(row => {
        let german_word = row.querySelector('td:nth-child(2)').innerText.toLowerCase();
        let translated_word = row.querySelector('td:nth-child(3)').innerText.toLowerCase();

        if (german_word.includes(filter) || translated_word.includes(filter)) {
            row.style.display = '';
        } else {
            row.style.display = 'none';
        }
    });
}

let holdTimer;

//erase words from dictionary
function erase() {
    document.querySelectorAll('.tbody td').forEach(line => {
      line.addEventListener('mousedown', (e) => {
        holdTimer = setTimeout(() => {
          if (confirm("Erase this line?")) {
            e.target.remove();
          }
        }, 1000); // 1 second
      });

      line.addEventListener('mouseup', () => {
        clearTimeout(holdTimer);
      });

      line.addEventListener('mouseleave', () => {
        clearTimeout(holdTimer);
      });
    });


}








