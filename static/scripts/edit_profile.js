document.addEventListener('DOMContentLoaded', function () {
    const imageUpload = document.getElementById('imageUpload');
    const imagePreview = document.getElementById('imagePreview');
    const cropCanvas = document.getElementById('cropCanvas');
    const zoomInBtn = document.getElementById('zoomIn');
    const zoomOutBtn = document.getElementById('zoomOut');
    const cropBtn = document.getElementById('cropAvatar'); // Оставляем для совместимости
    const avatarDataInput = document.getElementById('avatarData');
    const previewContainer = document.querySelector('.preview-container');
    const containerSize = 300;
    let scale = 1;
    let offsetX = 0;
    let offsetY = 0;
    let isDragging = false;
    let startX, startY;
    let baseX = 0, baseY = 0;
    let dragX = 0, dragY = 0;

    imageUpload.addEventListener('change', function (e) {
        const file = e.target.files[0];
        if (file && file.size > 5 * 1024 * 1024) {
            alert('Файл слишком большой. Максимальный размер: 5 МБ.');
            return;
        }
        if (file) {
            const reader = new FileReader();
            reader.onload = function (e) {
                imagePreview.src = e.target.result;
                imagePreview.classList.remove('hidden');
                imagePreview.onload = function () {
                    centerImage();
                };
            };
            reader.readAsDataURL(file);
        }
    });

    function centerImage() {
        scale = 1;
        baseX = (containerSize - imagePreview.width) / 2;
        baseY = (containerSize - imagePreview.height) / 2;
        dragX = 0;
        dragY = 0;
        updateImagePosition();
    }

    function updateImagePosition() {
        offsetX = baseX + dragX;
        offsetY = baseY + dragY;
        imagePreview.style.transform = `translate(${offsetX}px, ${offsetY}px) scale(${scale})`;
    }

    const MAX_SCALE = 1.5;
    const MIN_SCALE = 0.5;

    zoomInBtn.addEventListener('click', function () {
        scale = Math.min(scale * 1.1, MAX_SCALE);
        updateImagePosition();
    });

    zoomOutBtn.addEventListener('click', function () {
        scale = Math.max(scale / 1.1, MIN_SCALE);
        updateImagePosition();
    });

    imagePreview.addEventListener('mousedown', function (e) {
        isDragging = true;
        startX = e.clientX - dragX;
        startY = e.clientY - dragY;
        imagePreview.style.cursor = 'grabbing';
    });

    document.addEventListener('mousemove', function (e) {
        if (!isDragging) return;
        dragX = e.clientX - startX;
        dragY = e.clientY - startY;
        updateImagePosition();
    });

    document.addEventListener('mouseup', function () {
        isDragging = false;
        imagePreview.style.cursor = 'grab';
    });

    imagePreview.addEventListener('touchstart', function (e) {
        e.preventDefault();
        isDragging = true;
        startX = e.touches[0].clientX - dragX;
        startY = e.touches[0].clientY - dragY;
        imagePreview.style.cursor = 'grabbing';
    });

    document.addEventListener('touchmove', function (e) {
        if (!isDragging) return;
        e.preventDefault();
        dragX = e.touches[0].clientX - startX;
        dragY = e.touches[0].clientY - startY;
        updateImagePosition();
    });

    document.addEventListener('touchend', function () {
        isDragging = false;
        imagePreview.style.cursor = 'grab';
    });

    document.querySelector('#main-form').addEventListener('submit', function (e) {
        if (!imagePreview.src) {
            alert('Пожалуйста, загрузите изображение сначала');
            return;
        }

        const size = Math.round(previewContainer.clientWidth || containerSize);
        cropCanvas.width = size;
        cropCanvas.height = size;
        const ctx = cropCanvas.getContext('2d');
        ctx.clearRect(0, 0, size, size);

        const imgRect = imagePreview.getBoundingClientRect();
        const contRect = previewContainer.getBoundingClientRect();
        const displayedLeft = imgRect.left - contRect.left;
        const displayedTop = imgRect.top - contRect.top;
        const displayedWidth = imgRect.width;
        const displayedHeight = imgRect.height;

        const interLeft = Math.max(0, displayedLeft);
        const interTop = Math.max(0, displayedTop);
        const interRight = Math.min(size, displayedLeft + displayedWidth);
        const interBottom = Math.min(size, displayedTop + displayedHeight);
        const interWidth = Math.max(0, interRight - interLeft);
        const interHeight = Math.max(0, interBottom - interTop);

        const ratioX = imagePreview.naturalWidth / displayedWidth;
        const ratioY = imagePreview.naturalHeight / displayedHeight;

        const sx = (interLeft - displayedLeft) * ratioX;
        const sy = (interTop - displayedTop) * ratioY;
        const sWidth = interWidth * ratioX;
        const sHeight = interHeight * ratioY;

        if (interWidth > 0 && interHeight > 0) {
            ctx.drawImage(
                imagePreview,
                sx, sy, sWidth, sHeight,
                interLeft, interTop, interWidth, interHeight
            );
        }

        cropCanvas.toBlob(function (blob) {
            if (!blob) {
                alert('Ошибка при создании изображения');
                return;
            }
            const file = new File([blob], 'avatar.png', { type: 'image/png', lastModified: Date.now() });
            const dt = new DataTransfer();
            dt.items.add(file);
            avatarDataInput.files = dt.files;
            // Отправляем форму после обрезки
            document.querySelector('form').submit();
        }, 'image/png', 0.9);
    });

    const save_1 = document.querySelector(".save_1");
    const accept_block = document.getElementById("accept_block");
    const accept_input = document.getElementById('accept_input');
    const accept_final = document.getElementById('cropAvatar');
    const username = '{{ user_data["username"] | e }}';

    save_1.addEventListener("click", function () {
        accept_block.style.display = "block";
    });

    accept_input.addEventListener('input', function () {
        const inputValue = accept_input.value.trim().toLowerCase();
        const usernameValue = username.trim().toLowerCase();
        accept_final.disabled = inputValue !== usernameValue;
    });


});

const avatarEditorDiv = document.getElementById('avatar-editor');
function changeAvatar() {
    avatarEditorDiv.style.display = "block";
}


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
            const inputSelector = `input[name="${selectElement.closest('.input-block').id}"]`;
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