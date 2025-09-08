document.addEventListener('DOMContentLoaded', function () {
    const inputs = document.querySelectorAll('.code-input');
    const submitButton = document.querySelector('.submit-button');
    const verificationCodeInput = document.getElementById('verificationCode');
    const form = document.getElementById('verificationForm');

    // Фокус на первый инпут при загрузке
    inputs[0].focus();

    inputs.forEach((input, index) => {
        // Обработка ввода
        input.addEventListener('input', function (e) {
            const value = e.target.value;

            // Если введена цифра - переходим к следующему полю
            if (value.match(/[0-9]/)) {
                e.target.classList.add('filled');

                if (index < inputs.length - 1) {
                    inputs[index + 1].focus();
                }

                updateVerificationCode();
                checkAllFilled();
            } else {
                e.target.value = '';
            }
        });

        // Обработка удаления
        input.addEventListener('keydown', function (e) {
            if (e.key === 'Backspace' && !e.target.value && index > 0) {
                inputs[index - 1].focus();
                inputs[index - 1].value = '';
                inputs[index - 1].classList.remove('filled');
                updateVerificationCode();
                checkAllFilled();
            } else if (e.key === 'Backspace' && e.target.value) {
                e.target.value = '';
                e.target.classList.remove('filled');
                updateVerificationCode();
                checkAllFilled();
            }
        });

        // Обработка вставки
        input.addEventListener('paste', function (e) {
            e.preventDefault();
            const pastedData = e.clipboardData.getData('text');

            if (pastedData.match(/^[0-9]{6}$/)) {
                // Заполняем все поля из буфера обмена
                pastedData.split('').forEach((char, i) => {
                    if (inputs[i]) {
                        inputs[i].value = char;
                        inputs[i].classList.add('filled');
                    }
                });

                if (inputs[pastedData.length - 1]) {
                    inputs[pastedData.length - 1].focus();
                }

                updateVerificationCode();
                checkAllFilled();
            }
        });
    });

    function updateVerificationCode() {
        const code = Array.from(inputs).map(input => input.value).join('');
        verificationCodeInput.value = code;
    }

    function checkAllFilled() {
        const allFilled = Array.from(inputs).every(input => input.value !== '');
        submitButton.disabled = !allFilled;
    }

    // Обработка отправки формы
    form.addEventListener('submit', function (e) {
        e.preventDefault();

        // Обновляем код перед отправкой (на всякий случай)
        updateVerificationCode();

        const code = verificationCodeInput.value;
        console.log('Отправка кода:', code);

        // Отправляем форму
        form.submit();
    });
});