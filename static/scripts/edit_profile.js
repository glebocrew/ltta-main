document.addEventListener("DOMContentLoaded", () => {
    const imageUpload = document.getElementById("imageUpload");
    const imagePreview = document.getElementById("imagePreview");
    const cropCanvas = document.getElementById("cropCanvas");
    const previewContainer = document.querySelector(".preview-container");
    const avatarDataInput = document.getElementById("avatarData");
    const avatarEditor = document.getElementById("avatar-editor");
    const containerSize = 300;
    let scale = 1,
        offsetX = 0,
        offsetY = 0,
        dragX = 0,
        dragY = 0;
    let isDragging = false,
        startX,
        startY;
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
    document.getElementById("zoomIn").onclick = () => {
        scale = Math.min(scale * 1.1, 1.5);
        updateImagePosition();
    };
    document.getElementById("zoomOut").onclick = () => {
        scale = Math.max(scale / 1.1, 0.5);
        updateImagePosition();
    };
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
    document.addEventListener("mouseup", () => {
        isDragging = false;
    });
    window.closeAvatarEditor = function () {
        const imagePreview = document.getElementById("imagePreview");
        const cropCanvas = document.getElementById("cropCanvas");
        const avatarDataInput = document.getElementById("avatarData");
        const avatarEditor = document.getElementById("avatar-editor");
        const size = 300;
        cropCanvas.width = size;
        cropCanvas.height = size;
        const ctx = cropCanvas.getContext("2d");
        ctx.clearRect(0, 0, size, size);
        ctx.drawImage(imagePreview, 0, 0, imagePreview.naturalWidth, imagePreview.naturalHeight, dragX, dragY, imagePreview.naturalWidth * scale, imagePreview.naturalHeight * scale);
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
            const file = new File([blob], "avatar.png", {
                type: "image/png"
            });
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
    if (imagePreview.src && !imagePreview.classList.contains("hidden")) {
        e.preventDefault();
        const size = 300;
        cropCanvas.width = size;
        cropCanvas.height = size;
        const ctx = cropCanvas.getContext("2d");
        ctx.clearRect(0, 0, size, size);
        ctx.drawImage(imagePreview, offsetX, offsetY, imagePreview.width * scale, imagePreview.height * scale);
        cropCanvas.toBlob(function (blob) {
            if (!blob) {
                alert("Ошибка при создании изображения");
                return;
            }
            const file = new File([blob], "avatar.png", {
                type: "image/png"
            });
            const dt = new DataTransfer();
            dt.items.add(file);
            avatarDataInput.files = dt.files;
            e.target.submit();
        }, "image/png", 0.9);
    }
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