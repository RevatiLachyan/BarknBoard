
function handleNavigation(action) {
    if (action === 'create_account' || action === 'login') {
        document.getElementById('guestForm').action = action;
        document.getElementById('guestForm').submit();
    } else {
        window.location.href = action;
    }
}
