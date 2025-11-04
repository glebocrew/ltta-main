class CustomSelect {
    constructor(selectElement, inputSelector) {
        this.select = selectElement;
        this.selectValue = this.select.querySelector('.select_value');
        this.selectDropdown = this.select.querySelector('.select_dropdown');
        this.inputSelector = inputSelector;
        this.findInputElement();
        this.required = this.select.hasAttribute('data-required');
        this.defaultText = this.selectValue.textContent;
        this.init();
    }
    findInputElement() {
        const form = this.select.closest('form');
        if (form) {
            this.facultyInput = form.querySelector(this.inputSelector);
            if (this.facultyInput) return;
        }
        this.facultyInput = document.querySelector(this.inputSelector);
        console.log('Selector:', this.inputSelector, 'Found:', this.facultyInput);
    }
    init() {
        this.select.addEventListener('click', e => {
            if (e.target.classList.contains('select_value') || e.target === this.select) {
                this.toggle();
            }
        });
        this.selectDropdown.addEventListener('click', e => {
            const option = e.target.closest('.select_option');
            if (option) {
                this.setValue(option.textContent);
                this.close();
                e.stopPropagation();
            }
        });
        document.addEventListener('click', e => {
            if (!this.select.contains(e.target)) {
                this.close();
            }
        });
    }
    toggle() {
        this.select.classList.toggle('open');
        this.hideError();
    }
    open() {
        this.select.classList.add('open');
        this.hideError();
    }
    close() {
        this.select.classList.remove('open');
    }
    setValue(value) {
        this.selectValue.textContent = value;
        if (!this.facultyInput) {
            this.findInputElement();
        }
        if (this.facultyInput) {
            this.facultyInput.value = value;
            console.log('Input value set to:', value);
        } else {
            console.error('Input element not found for selector:', this.inputSelector);
        }
        this.hideError();
        this.select.dispatchEvent(new CustomEvent('change', {
            detail: value,
            bubbles: true
        }));
    }
    getValue() {
        return this.selectValue.textContent;
    }
    isValid() {
        if (!this.required) return true;
        const selectedValue = this.selectValue.textContent;
        const invalidValues = [this.defaultText, 'факультет', 'параллель', 'не выбрано'];
        return !invalidValues.includes(selectedValue);
    }
    showError() {
        this.select.classList.add('error');
        let errorElement = this.select.querySelector('.select_error');
        if (!errorElement) {
            errorElement = document.createElement('div');
            errorElement.className = 'select_error';
            errorElement.textContent = 'Пожалуйста, выберите значение';
            this.select.appendChild(errorElement);
        }
    }
    hideError() {
        this.select.classList.remove('error');
        const errorElement = this.select.querySelector('.select_error');
        if (errorElement) {
            errorElement.remove();
        }
    }
    reset() {
        this.selectValue.textContent = this.defaultText;
        if (this.facultyInput) {
            this.facultyInput.value = '';
        }
        this.hideError();
    }
}
document.addEventListener('DOMContentLoaded', () => {
    const selectElements = document.querySelectorAll('.select');
    const selectInstances = [];
    console.log('Found select elements:', selectElements.length);
    selectElements.forEach((selectElement, index) => {
        try {
            const inputSelector = `input[name="${selectElement.closest('.input-block').id}"]`;
            console.log(`Select ${index}: using selector`, inputSelector);
            const selectInstance = new CustomSelect(selectElement, inputSelector);
            selectInstances.push(selectInstance);
        } catch (error) {
            console.error('Error initializing select:', error);
        }
    });
    const forms = document.querySelectorAll('form');
    forms.forEach(form => {
        form.addEventListener('submit', function (e) {
            let isFormValid = true;
            let firstInvalidSelect = null;
            selectInstances.forEach(select => {
                if (select.required && !select.isValid()) {
                    select.showError();
                    isFormValid = false;
                    if (!firstInvalidSelect) {
                        firstInvalidSelect = select.select;
                    }
                }
            });
            if (!isFormValid) {
                e.preventDefault();
                if (firstInvalidSelect) {
                    firstInvalidSelect.scrollIntoView({
                        behavior: 'smooth',
                        block: 'center'
                    });
                }
                console.log('Form validation failed');
            }
        });
    });
    selectInstances.forEach(select => {
        select.select.addEventListener('change', () => {
            select.hideError();
        });
    });
    window.customSelects = selectInstances;
    console.log('Custom selects initialized:', selectInstances.length);
});
window.validateForm = function () {
    if (window.customSelects) {
        let isValid = true;
        window.customSelects.forEach(select => {
            if (select.required && !select.isValid()) {
                select.showError();
                isValid = false;
            }
        });
        return isValid;
    }
    return false;
};
window.resetAllSelects = function () {
    if (window.customSelects) {
        window.customSelects.forEach(select => {
            select.reset();
        });
    }
};

