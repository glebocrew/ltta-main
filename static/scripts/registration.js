class CustomSelect {
    constructor(selectElement, inputSelector) {
        this.select = selectElement;
        this.selectValue = this.select.querySelector('.select_value');
        this.selectDropdown = this.select.querySelector('.select_dropdown');
        
        // Сохраняем селектор для повторного использования
        this.inputSelector = inputSelector;
        // Ищем input элемент
        this.findInputElement();
        
        this.required = this.select.hasAttribute('data-required');
        this.defaultText = this.selectValue.textContent;
        
        this.init();
    }
    
    // Метод для поиска input элемента
    findInputElement() {
        // Сначала ищем в форме, затем во всем документе
        const form = this.select.closest('form');
        if (form) {
            this.facultyInput = form.querySelector(this.inputSelector);
            if (this.facultyInput) return;
        }
        
        // Если не нашли в форме, ищем во всем документе
        this.facultyInput = document.querySelector(this.inputSelector);
        
        // Логирование для отладки
        console.log('Selector:', this.inputSelector, 'Found:', this.facultyInput);
    }
    
    init() {
        // Открытие/закрытие по клику на заголовок
        this.select.addEventListener('click', (e) => {
            if (e.target.classList.contains('select_value') || e.target === this.select) {
                this.toggle();
            }
        });
        
        // Выбор опции
        this.selectDropdown.addEventListener('click', e => {
            const option = e.target.closest('.select_option');
            if (option) {
                this.setValue(option.textContent);
                this.close();
                e.stopPropagation();
            }
        });
        
        // Закрытие при клике вне селекта
        document.addEventListener('click', (e) => {
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
        
        // Перепроверяем и находим input элемент
        if (!this.facultyInput) {
            this.findInputElement();
        }
        
        // Заполняем input значение
        if (this.facultyInput) {
            this.facultyInput.value = value;
            console.log('Input value set to:', value);
        } else {
            console.error('Input element not found for selector:', this.inputSelector);
        }
        
        this.hideError();
        
        // Отправляем кастомное событие
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
        
        // Сбрасываем значение input
        if (this.facultyInput) {
            this.facultyInput.value = '';
        }
        
        this.hideError();
    }
}

// Инициализация всех селектов на странице
document.addEventListener('DOMContentLoaded', () => {
    const selectElements = document.querySelectorAll('.select');
    const selectInstances = [];
    
    console.log('Found select elements:', selectElements.length);
    
    // Инициализируем каждый селект
    selectElements.forEach((selectElement, index) => {
        try {
            // Получаем селектор из data-атрибута или используем дефолтный
            const inputSelector = selectElement.dataset.target || '.dropdown-input';
            console.log(`Select ${index}: using selector`, inputSelector);
            
            const selectInstance = new CustomSelect(selectElement, inputSelector);
            selectInstances.push(selectInstance);
        } catch (error) {
            console.error('Error initializing select:', error);
        }
    });
    
    // Валидация при отправке форм
    const forms = document.querySelectorAll('form');
    forms.forEach(form => {
        form.addEventListener('submit', function(e) {
            let isFormValid = true;
            let firstInvalidSelect = null;
            
            // Проверяем все селекты
            selectInstances.forEach(select => {
                if (select.required && !select.isValid()) {
                    select.showError();
                    isFormValid = false;
                    
                    // Запоминаем первый невалидный селект для прокрутки
                    if (!firstInvalidSelect) {
                        firstInvalidSelect = select.select;
                    }
                }
            });
            
            // Если форма не валидна, предотвращаем отправку
            if (!isFormValid) {
                e.preventDefault();
                
                // Прокручиваем к первому ошибочному полю
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
    
    // Сбрасываем ошибки при изменении значений
    selectInstances.forEach(select => {
        select.select.addEventListener('change', () => {
            select.hideError();
        });
    });
    
    // Делаем экземпляры доступными глобально для отладки
    window.customSelects = selectInstances;
    console.log('Custom selects initialized:', selectInstances.length);
});

// Вспомогательная функция для ручной валидации
window.validateForm = function() {
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

// Вспомогательная функция для сброса всех селектов
window.resetAllSelects = function() {
    if (window.customSelects) {
        window.customSelects.forEach(select => {
            select.reset();
        });
    }
};