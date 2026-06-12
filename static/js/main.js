function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

function addToCart(productId) {
    fetch('/cart/add/' + productId + '/', {
        method: 'POST',
        headers: {
            'X-CSRFToken': getCookie('csrftoken'),
            'Content-Type': 'application/json',
            'X-Requested-With': 'XMLHttpRequest'
        },
        body: JSON.stringify({quantity: 1})
    })
    .then(function (response) {
        if (!response.ok) throw new Error('HTTP ' + response.status);
        return response.json();
    })
    .then(function (data) {
        const counter = document.getElementById('cart-count');
        if (counter) {
            counter.textContent = data.cart_count > 0 ? '(' + data.cart_count + ')' : '';
        }
        showToast('Товар добавлен в корзину');
    })
    .catch(function () {
        showToast('Не удалось добавить товар');
    });
}

function showToast(message) {
    const existing = document.querySelector('.toast-note');
    if (existing) existing.remove();

    const toast = document.createElement('div');
    toast.className = 'toast-note';
    toast.textContent = message;
    document.body.appendChild(toast);
    requestAnimationFrame(function () {
        toast.classList.add('show');
    });
    setTimeout(function () {
        toast.classList.remove('show');
        setTimeout(function () { toast.remove(); }, 250);
    }, 2500);
}
