document.addEventListener('DOMContentLoaded', function () {
    // Generic handler: show payment mode only if paid_amount > 0
    function setupPaymentVisibility(formSelector) {
        var form = document.querySelector(formSelector);
        if (!form) return;

        var paidInput = form.querySelector('#paid_amount');
        var modeSelect = form.querySelector('#payment_mode') || form.querySelector('#payment_status');
        var statusSelect = form.querySelector('#payment_status') || form.querySelector('#work_status');

        function updateVisibility() {
            var paid = parseFloat(paidInput && paidInput.value) || 0;
            if (modeSelect) {
                if (paid > 0) {
                    modeSelect.parentElement.style.display = '';
                } else {
                    modeSelect.parentElement.style.display = 'none';
                    if (modeSelect.tagName === 'SELECT') modeSelect.value = '';
                }
            }

            if (statusSelect) {
                // If paid > 0 and status is empty, set to Pending
                if (paid > 0 && (statusSelect.value === '' || statusSelect.value === undefined)) {
                    try { statusSelect.value = 'Pending'; } catch (e) {}
                }
                // If paid == 0, ensure status is 'Pending' or blank
                if (paid === 0 && statusSelect.value === 'Paid') {
                    statusSelect.value = 'Pending';
                }
            }
        }

        if (paidInput) {
            paidInput.addEventListener('input', updateVisibility);
            paidInput.addEventListener('change', updateVisibility);
            updateVisibility();
        }
    }

    // Apply to known forms
    setupPaymentVisibility('form.data-form');
    setupPaymentVisibility('#freelancer-work-form');
});