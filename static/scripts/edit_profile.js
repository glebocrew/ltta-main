document.addEventListener("DOMContentLoaded", () => {
    const imageUpload = document.getElementById("imageUpload");
    const imagePreview = document.getElementById("imagePreview");
    const cropCanvas = document.getElementById("cropCanvas");
    const previewContainer = document.querySelector(".preview-container");
    const avatarDataInput = document.getElementById("avatarData");
    const avatarEditor = document.getElementById("avatar-editor");

    const containerSize = 300;
    let scale = 1, offsetX = 0, offsetY = 0, dragX = 0, dragY = 0;
    let isDragging = false, startX, startY;

    // Загружаем фото
    imageUpload.addEventListener("change", e => {
        const file = e.target.files[0];
        if (!file) return;
        if (file.size > 5 * 1024 * 1024) {
            alert("Файл слишком большой (макс 5 МБ)");
            return;
        }
        const reader = new FileReader();
        reader.onload = ev => {
            imagePreview.src = ev.target.result;
            imagePreview.classList.remove("hidden");
            imagePreview.onload = centerImage;
        };
        reader.readAsDataURL(file);
    });

    function centerImage() {
        scale = 1;
        dragX = dragY = 0;
        updateImagePosition();
    }

    function updateImagePosition() {
        offsetX = dragX;
        offsetY = dragY;
        imagePreview.style.transform = `translate(${offsetX}px, ${offsetY}px) scale(${scale})`;
    }

    // Масштаб
    document.getElementById("zoomIn").onclick = () => {
        scale = Math.min(scale * 1.1, 1.5);
        updateImagePosition();
    };
    document.getElementById("zoomOut").onclick = () => {
        scale = Math.max(scale / 1.1, 0.5);
        updateImagePosition();
    };

    // Перетаскивание
    imagePreview.addEventListener("mousedown", e => {
        isDragging = true;
        startX = e.clientX - dragX;
        startY = e.clientY - dragY;
    });
    document.addEventListener("mousemove", e => {
        if (!isDragging) return;
        dragX = e.clientX - startX;
        dragY = e.clientY - startY;
        updateImagePosition();
    });
    document.addEventListener("mouseup", () => { isDragging = false; });

window.closeAvatarEditor = function() {
    const imagePreview = document.getElementById("imagePreview");
    const cropCanvas = document.getElementById("cropCanvas");
    const avatarDataInput = document.getElementById("avatarData");
    const avatarEditor = document.getElementById("avatar-editor");

    const size = 300; // размер аватара
    cropCanvas.width = size;
    cropCanvas.height = size;
    const ctx = cropCanvas.getContext("2d");

    ctx.clearRect(0, 0, size, size);

    // Используем dragX, dragY и scale
    ctx.drawImage(
        imagePreview,
        0, 0, imagePreview.naturalWidth, imagePreview.naturalHeight, // исходное изображение
        dragX, dragY, imagePreview.naturalWidth * scale, imagePreview.naturalHeight * scale // позиция и масштаб
    );

    // Проверка прозрачности
    const imageData = ctx.getImageData(0, 0, size, size);
    const pixels = imageData.data;
    let hasOpaque = false;
    for (let i = 3; i < pixels.length; i += 4) {
        if (pixels[i] !== 0) {
            hasOpaque = true;
            break;
        }
    }

    if (!hasOpaque) {
        avatarEditor.style.display = "none";
        return;
    }

    cropCanvas.toBlob(blob => {
        const file = new File([blob], "avatar.png", { type: "image/png" });
        const dt = new DataTransfer();
        dt.items.add(file);
        avatarDataInput.files = dt.files;

        document.querySelector(".avatar").src = URL.createObjectURL(blob);
        avatarEditor.style.display = "none";
    }, "image/png", 0.9);
};

    window.changeAvatar = () => avatarEditor.style.display = "block";
});

document.getElementById("main-form").addEventListener("submit", function (e) {
    // если есть загруженный аватар — режем и прикрепляем
    if (imagePreview.src && !imagePreview.classList.contains("hidden")) {
        e.preventDefault(); // блокируем только чтобы успеть создать файл

        const size = 300;
        cropCanvas.width = size;
        cropCanvas.height = size;
        const ctx = cropCanvas.getContext("2d");

        ctx.clearRect(0, 0, size, size);
        ctx.drawImage(imagePreview, offsetX, offsetY,
                      imagePreview.width * scale, imagePreview.height * scale);

        cropCanvas.toBlob(function (blob) {
            if (!blob) {
                alert("Ошибка при создании изображения");
                return;
            }
            const file = new File([blob], "avatar.png", { type: "image/png" });
            const dt = new DataTransfer();
            dt.items.add(file);
            avatarDataInput.files = dt.files;

            // теперь отправляем форму по-настоящему
            e.target.submit();
        }, "image/png", 0.9);
    }
    // если аватар не меняли → форма сразу уходит, preventDefault не нужен
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


// });

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
        form.addEventListener('submit', function (e) {
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

// Вспомогательная функция для ручной валидации
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

// Вспомогательная функция для сброса всех селектов
window.resetAllSelects = function () {
    if (window.customSelects) {
        window.customSelects.forEach(select => {
            select.reset();
        });
    }

};

function showConfirmation() {
    document.getElementById("confirmDialog").style.display = "block";
    document.getElementById("overlay").style.display = "block";
    document.getElementById("usernameConfirm").value = "";
    document.getElementById("confirmSave").disabled = true;
}

function hideConfirmation() {
    document.getElementById("confirmDialog").style.display = "none";
    document.getElementById("overlay").style.display = "none";
}

function submitForm() {
    document.getElementById("main-form").submit();
}

document.getElementById("usernameConfirm").addEventListener("keypress", e => {
    if (e.key === "Enter" && !document.getElementById("confirmSave").disabled) {
        submitForm();
    }
});