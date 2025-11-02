document.addEventListener('DOMContentLoaded', function () {
    const inputs = document.querySelectorAll('.code-input');
    const submitButton = document.querySelector('.submit-button');
    const verificationCodeInput = document.getElementById('verificationCode');
    const form = document.getElementById('verificationForm');
    inputs[0].focus();
    inputs.forEach((input, index) => {
        input.addEventListener('input', function (e) {
            const value = e.target.value;
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
        input.addEventListener('paste', function (e) {
            e.preventDefault();
            const pastedData = e.clipboardData.getData('text');
            if (pastedData.match(/^[0-9]{6}$/)) {
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
    form.addEventListener('submit', function (e) {
        e.preventDefault();
        updateVerificationCode();
        const code = verificationCodeInput.value;
        console.log('Отправка кода:', code);
        form.submit();
    });
});