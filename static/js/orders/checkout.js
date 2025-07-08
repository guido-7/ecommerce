// Store suggested address data
const suggestedAddress = {
    {% if suggested_address %}
    street_address: "{{ suggested_address.street_address|escapejs }}",
    city: "{{ suggested_address.city|escapejs }}",
    postal_code: "{{ suggested_address.postal_code|escapejs }}",
    country: "{{ suggested_address.country|escapejs }}"
    {% endif %}
};

function useSuggestedAddress() {
    if (suggestedAddress.street_address) {
        document.getElementById('street_address').value = suggestedAddress.street_address;
        document.getElementById('city').value = suggestedAddress.city;
        document.getElementById('postal_code').value = suggestedAddress.postal_code;
        document.getElementById('country').value = suggestedAddress.country;

        // Add visual feedback
        const inputs = document.querySelectorAll('input[type="text"]');
        inputs.forEach(input => {
            input.classList.add('filled');
            setTimeout(() => {
                input.classList.remove('filled');
            }, 2000);
        });

        // Show success message
        const btn = document.querySelector('.btn-use-suggested');
        const originalText = btn.innerHTML;
        btn.innerHTML = '<i class="fas fa-check me-2"></i>Address Applied!';
        btn.style.background = 'linear-gradient(135deg, #27ae60 0%, #2ecc71 100%)';

        setTimeout(() => {
            btn.innerHTML = originalText;
            btn.style.background = '';
        }, 2000);
    }
}

// Form validation and enhancement
document.addEventListener('DOMContentLoaded', function() {
    const form = document.querySelector('form');
    const inputs = form.querySelectorAll('input[required]');

    inputs.forEach(input => {
        input.addEventListener('blur', function() {
            if (this.value.trim() === '') {
                this.classList.add('form-validation-error');
                this.classList.remove('form-validation-success');
            } else {
                this.classList.add('form-validation-success');
                this.classList.remove('form-validation-error');
            }
        });

        input.addEventListener('focus', function() {
            this.classList.remove('form-validation-error', 'form-validation-success');
        });
    });

    // Form submission enhancement
    form.addEventListener('submit', function(e) {
        const submitBtn = document.querySelector('.btn-submit');
        const originalText = submitBtn.innerHTML;

        submitBtn.innerHTML = '<span><i class="fas fa-spinner fa-spin me-2"></i>Processing...</span>';
        submitBtn.disabled = true;

        // Re-enable after 3 seconds in case of errors
        setTimeout(() => {
            submitBtn.innerHTML = originalText;
            submitBtn.disabled = false;
        }, 3000);
    });
});