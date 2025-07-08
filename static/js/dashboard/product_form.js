class ImageManager {
    constructor() {
        this.imageCount = 0;
        this.container = document.getElementById('imageContainer');
        this.addBtn = document.getElementById('addImageBtn');
        this.form = document.getElementById('productForm');
        this.hasExistingImages = {{ existing_images|length|default:0 }};
        this.existingImagesCount = this.hasExistingImages;

        this.init();
    }

    init() {
        // Se non ci sono immagini esistenti, aggiungi la prima immagine obbligatoria
        if (this.existingImagesCount === 0) {
            this.addImageField();
        }

        // Event listeners
        this.addBtn.addEventListener('click', () => this.addImageField());
        this.form.addEventListener('submit', (e) => this.validateForm(e));
    }

    addImageField() {
        this.imageCount++;

        const imageRow = document.createElement('div');
        imageRow.className = 'image-row';
        imageRow.dataset.imageId = this.imageCount;

        const isFirstAndNoExisting = this.imageCount === 1 && this.existingImagesCount === 0;
        const requiredAttr = isFirstAndNoExisting ? 'required' : '';
        const requiredLabel = isFirstAndNoExisting ? '<span class="required-indicator">*</span>' : '';

        imageRow.innerHTML = `
            <div class="row align-items-center">
                <div class="col-md-3">
                    <label class="form-label fw-bold">
                        Nuova Immagine ${this.imageCount} ${requiredLabel}
                    </label>
                </div>
                <div class="col-md-6">
                    <input type="file"
                           class="form-control image-input"
                           name="image_${this.imageCount}"
                           accept="image/*"
                           ${requiredAttr}
                           onchange="imageManager.previewImage(this, ${this.imageCount})">
                </div>
                <div class="col-md-2">
                    <div id="preview_${this.imageCount}" class="image-preview-container"></div>
                </div>
                <div class="col-md-1 text-end">
                    ${(this.imageCount > 1 || this.existingImagesCount > 0) ? `
                        <button type="button"
                                class="delete-btn"
                                onclick="imageManager.removeImageField(${this.imageCount})"
                                title="Rimuovi immagine">
                            <i class="fas fa-trash"></i>
                        </button>
                    ` : ''}
                </div>
            </div>
        `;

        this.container.appendChild(imageRow);

        // Animazione di entrata
        setTimeout(() => {
            imageRow.style.opacity = '0';
            imageRow.style.transform = 'translateY(-20px)';
            imageRow.style.transition = 'all 0.3s ease';

            setTimeout(() => {
                imageRow.style.opacity = '1';
                imageRow.style.transform = 'translateY(0)';
            }, 10);
        }, 10);
    }

    removeImageField(imageId) {
        const imageRow = document.querySelector(`[data-image-id="${imageId}"]`);
        if (imageRow) {
            // Controlla se è l'ultima immagine rimasta e non ci sono immagini esistenti
            const remainingNewImages = this.container.querySelectorAll('.image-row').length;
            const existingImagesCount = document.querySelectorAll('.existing-image:not(.marked-for-deletion)').length;

            if (remainingNewImages <= 1 && existingImagesCount === 0) {
                alert('È richiesta almeno una immagine per il prodotto!');
                return;
            }

            // Animazione di uscita
            imageRow.style.transition = 'all 0.3s ease';
            imageRow.style.opacity = '0';
            imageRow.style.transform = 'translateX(-100%)';

            setTimeout(() => {
                imageRow.remove();
                this.renumberImages();
            }, 300);
        }
    }

    renumberImages() {
        const imageRows = this.container.querySelectorAll('.image-row');
        imageRows.forEach((row, index) => {
            const newNumber = index + 1;
            const label = row.querySelector('label');
            const input = row.querySelector('input');
            const preview = row.querySelector('.image-preview-container');

            // Aggiorna etichetta
            const isFirstAndNoExisting = newNumber === 1 && this.existingImagesCount === 0;
            if (isFirstAndNoExisting) {
                label.innerHTML = `Nuova Immagine ${newNumber} <span class="required-indicator">*</span>`;
                input.setAttribute('required', '');
            } else {
                label.innerHTML = `Nuova Immagine ${newNumber}`;
                input.removeAttribute('required');
            }

            // Aggiorna attributi
            input.name = `image_${newNumber}`;
            preview.id = `preview_${newNumber}`;
            row.dataset.imageId = newNumber;

            // Aggiorna pulsante delete
            const deleteBtn = row.querySelector('.delete-btn');
            if (deleteBtn) {
                deleteBtn.setAttribute('onclick', `imageManager.removeImageField(${newNumber})`);
            }
        });

        this.imageCount = imageRows.length;
    }

    previewImage(input, imageId) {
        const previewContainer = document.getElementById(`preview_${imageId}`);

        if (input.files && input.files[0]) {
            const reader = new FileReader();

            reader.onload = (e) => {
                previewContainer.innerHTML = `
                    <img src="${e.target.result}"
                         class="image-preview"
                         alt="Anteprima">
                `;
            }

            reader.readAsDataURL(input.files[0]);
        } else {
            previewContainer.innerHTML = '';
        }
    }

    validateForm(e) {
        // Controlla immagini esistenti non eliminate
        const activeExisting = this.existingImagesCount -
            document.querySelectorAll('.marked-for-deletion').length;

        // Controlla nuove immagini caricate
        let hasNewImage = false;
        this.container.querySelectorAll('.image-input').forEach(input => {
            if (input.files && input.files.length > 0) {
                hasNewImage = true;
            }
        });

        if (activeExisting === 0 && !hasNewImage) {
            e.preventDefault();
            alert('È necessario caricare almeno una immagine del prodotto!');
            // Scroll alla sezione immagini
            document.querySelector('.form-section:nth-child(2)').scrollIntoView({
                behavior: 'smooth'
            });
            return false;
        }
    }
}

// Gestione sconto
class DiscountManager {
    constructor() {
        this.discountToggle = document.getElementById('discountToggle');
        this.discountFields = document.getElementById('discountFields');
        this.discountToggleText = document.getElementById('discountToggleText');
        this.priceInput = document.querySelector('[name="price"]');
        this.discountedPriceInput = document.querySelector('[name="discounted_price"]');
        this.priceComparison = document.getElementById('priceComparison');

        this.init();
    }

    init() {
        // Verifica se c'è già un valore per il prezzo scontato
        if (this.discountedPriceInput.value) {
            this.showDiscountFields();
        }

        // Event listeners
        this.discountToggle.addEventListener('click', () => this.toggleDiscount());
        this.priceInput.addEventListener('input', () => this.updatePriceComparison());
        this.discountedPriceInput.addEventListener('input', () => this.updatePriceComparison());
        this.discountedPriceInput.addEventListener('blur', () => this.validateDiscountPrice());
    }

    toggleDiscount() {
        if (this.discountFields.classList.contains('active')) {
            this.hideDiscountFields();
        } else {
            this.showDiscountFields();
        }
    }

    showDiscountFields() {
        this.discountFields.classList.add('active');
        this.discountToggleText.textContent = 'Rimuovi Sconto';
        this.discountToggle.innerHTML = '<i class="fas fa-times me-2"></i>' + this.discountToggleText.textContent;
        this.discountedPriceInput.classList.add('form-control');
        this.updatePriceComparison();
    }

    hideDiscountFields() {
        this.discountFields.classList.remove('active');
        this.discountToggleText.textContent = 'Applica Sconto';
        this.discountToggle.innerHTML = '<i class="fas fa-percent me-2"></i>' + this.discountToggleText.textContent;
        this.discountedPriceInput.value = '';
        this.discountedPriceInput.classList.remove('is-invalid', 'is-valid');
        const errorDiv = document.getElementById('discountPriceError');
        errorDiv.style.display = 'none';
        this.priceComparison.style.display = 'none';
    }

    updatePriceComparison() {
        const originalPrice = parseFloat(this.priceInput.value) || 0;
        const discountedPrice = parseFloat(this.discountedPriceInput.value) || 0;

        // Validate discount price when updating comparison
        this.validateDiscountPrice();

        if (originalPrice > 0 && discountedPrice > 0 && discountedPrice < originalPrice) {
            const savings = originalPrice - discountedPrice;
            const savingsPercent = ((savings / originalPrice) * 100).toFixed(0);

            document.getElementById('originalPriceDisplay').textContent = `Original price: €${originalPrice.toFixed(2)}`;
            document.getElementById('discountedPriceDisplay').textContent = `Discounted price: €${discountedPrice.toFixed(2)}`;
            document.getElementById('savingsDisplay').textContent = `Savings: €${savings.toFixed(2)} (${savingsPercent}%)`;

            this.priceComparison.style.display = 'block';
        } else {
            this.priceComparison.style.display = 'none';
        }
    }

    validateDiscountPrice() {
        const originalPrice = parseFloat(this.priceInput.value) || 0;
        const discountedPrice = parseFloat(this.discountedPriceInput.value) || 0;

        // Reset previous validation state
        this.discountedPriceInput.classList.remove('is-invalid', 'is-valid');
        const errorDiv = document.getElementById('discountPriceError');
        errorDiv.style.display = 'none';

        if (discountedPrice > 0) {
            if (discountedPrice >= originalPrice) {
                this.discountedPriceInput.classList.add('is-invalid');
                errorDiv.style.display = 'block';
                return false;
            } else {
                this.discountedPriceInput.classList.add('is-valid');
            }
        }
        return true;
    }
}

// Funzione per marcare le immagini esistenti per l'eliminazione
function markImageForDeletion(imageId, button) {
    const existingImageDiv = button.parentElement;
    const hiddenInput = document.getElementById(`delete_${imageId}`);

    // Se stiamo per eliminare (non è ancora marcato)
    if (!existingImageDiv.classList.contains('marked-for-deletion')) {
        // Conta immagini esistenti attive
        const activeExisting = document.querySelectorAll('.existing-image:not(.marked-for-deletion)').length;

        // Controlla nuove immagini
        let hasNewImage = false;
        document.querySelectorAll('.image-input').forEach(input => {
            if (input.files && input.files.length > 0) {
                hasNewImage = true;
            }
        });

        // Se è l'ultima immagine esistente e non ci sono nuove immagini
        if (activeExisting === 1 && !hasNewImage) {
            alert('È richiesta almeno una immagine per il prodotto!');
            return;
        }
    }

    // Toggle stato di eliminazione
    if (existingImageDiv.classList.contains('marked-for-deletion')) {
        // Ripristina immagine
        existingImageDiv.classList.remove('marked-for-deletion');
        existingImageDiv.style.opacity = '1';
        button.innerHTML = '<i class="fas fa-times"></i>';
        button.title = 'Elimina immagine';
        hiddenInput.value = '';
    } else {
        // Marca per eliminazione
        existingImageDiv.classList.add('marked-for-deletion');
        existingImageDiv.style.opacity = '0.5';
        button.innerHTML = '<i class="fas fa-undo"></i>';
        button.title = 'Ripristina immagine';
        hiddenInput.value = imageId;
    }
}

// Inizializza i manager
const imageManager = new ImageManager();
const discountManager = new DiscountManager();

// Validazione in tempo reale del form
document.addEventListener('DOMContentLoaded', function() {
    const form = document.getElementById('productForm');
    const inputs = form.querySelectorAll('input[required], select[required], textarea[required]');

    inputs.forEach(input => {
        // Applica le classi Bootstrap ai campi del form
        if (input.type !== 'file') {
            input.classList.add('form-control');
        }
        if (input.tagName === 'SELECT') {
            input.classList.add('form-select');
        }

        input.addEventListener('blur', function() {
            if (this.value.trim() === '') {
                this.classList.add('is-invalid');
            } else {
                this.classList.remove('is-invalid');
                this.classList.add('is-valid');
            }
        });
    });

    // Validazione form prima del submit
    form.addEventListener('submit', function(e) {
        // Validazione prezzo scontato
        if (!discountManager.validateDiscountPrice()) {
            e.preventDefault();
            return false;
        }
    });
});