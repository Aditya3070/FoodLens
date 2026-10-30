
document.addEventListener('DOMContentLoaded', () => {
    const toggle = document.querySelector('.nav-toggle');
    const nav = document.querySelector('.nav-links');

    // Mobile navigation toggle
    if (toggle && nav) {
        toggle.addEventListener('click', () => {
            const open = nav.classList.toggle('nav-open');
            toggle.setAttribute('aria-expanded', String(open));
        });
    }

    // Close flash messages
    document.querySelectorAll('.flash-close').forEach(button => {
        button.addEventListener('click', () => {
            button.closest('.flash').remove();
        });
    });

    // Image upload elements
    const input = document.getElementById('file-input');
    const drop = document.getElementById('dropzone');
    const preview = document.getElementById('preview');
    const title = document.getElementById('drop-title');
    const hint = document.getElementById('drop-hint');

    // Validate and preview the selected image
    function showFile(file) {
        if (!file) return;

        if (!['image/jpeg', 'image/png'].includes(file.type)) {
            alert('Please select a JPG or PNG image.');

            if (input) {
                input.value = '';
            }

            return;
        }

        if (file.size > 8 * 1024 * 1024) {
            alert('Please choose an image smaller than 8 MB.');
            input.value = '';
            return;
        }

        const reader = new FileReader();

        reader.onload = event => {
            preview.src = event.target.result;
            preview.hidden = false;

            if (title) {
                title.textContent = file.name;
            }

            if (hint) {
                hint.textContent = 'Image ready to analyze';
            }

            drop.classList.add('has-file');
        };

        reader.readAsDataURL(file);
    }

    // Handle file selection and drag-and-drop
    if (input) {
        input.addEventListener('change', () => {
            showFile(input.files[0]);
        });

        if (drop) {
            ['dragenter', 'dragover'].forEach(eventName => {
                drop.addEventListener(eventName, event => {
                    event.preventDefault();
                    drop.classList.add('drag-active');
                });
            });

            ['dragleave', 'drop'].forEach(eventName => {
                drop.addEventListener(eventName, event => {
                    event.preventDefault();
                    drop.classList.remove('drag-active');
                });
            });

            drop.addEventListener('drop', event => {
                const file = event.dataTransfer.files[0];

                if (file) {
                    try {
                        const dataTransfer = new DataTransfer();
                        dataTransfer.items.add(file);
                        input.files = dataTransfer.files;
                    } catch (_) {
                        // Continue with preview if assignment is unsupported.
                    }

                    showFile(file);
                }
            });
        }
    }

    // Image upload form submission
    const form = document.getElementById('upload-form');
    const submit = document.getElementById('submit-btn');
    const loading = document.getElementById('loading-message');

    if (form) {
        form.addEventListener('submit', event => {
            if (!input || !input.files.length) {
                event.preventDefault();
                alert('Please choose a label image first.');
                return;
            }

            if (submit) {
                submit.disabled = true;
                submit.innerHTML =
                    '<span class="spinner"></span> Analyzing…';
            }

            if (loading) {
                loading.hidden = false;
            }
        });
    }

    // Ingredients character counter
    const ingredients = document.getElementById('ingredients-input');
    const count = document.getElementById('char-count');

    if (ingredients && count) {
        const update = () => {
            count.textContent = ingredients.value.length;
        };

        ingredients.addEventListener('input', update);
        update();
    }

    // Manual ingredients form submission
    const manualForm = document.getElementById('manual-form');
    const manualSubmit = document.getElementById('manual-submit');
    const manualLoading = document.getElementById('manual-loading');

    if (manualForm) {
        manualForm.addEventListener('submit', event => {
            if (!ingredients || ingredients.value.trim().length < 3) {
                event.preventDefault();
                alert('Please enter an ingredients list.');
                return;
            }

            if (manualSubmit) {
                manualSubmit.disabled = true;
                manualSubmit.innerHTML =
                    '<span class="spinner"></span> Analyzing…';
            }

            if (manualLoading) {
                manualLoading.hidden = false;
            }
        });
    }
});
