// This function will be called by the 'onload' attribute in the main Clerk script tag.
function initializeClerkNavigation() {
    const Clerk = window.Clerk;

    if (!Clerk) {
        console.error("Clerk object is not available.");
        return;
    }

    const userButton = document.getElementById('user-button');
    const authButtons = document.getElementById('auth-buttons');

    Clerk.addListener(({ user }) => {
        if (user) {
            // User is signed in
            if (authButtons) authButtons.style.display = 'none';
            if (userButton) {
                userButton.style.display = 'flex';
                userButton.innerHTML = `
                    <div class="text-white me-3">Welcome, ${user.firstName || user.username}</div>
                    <a href="/dashboard.html" class="btn btn-sm btn-outline-light">Dashboard</a>
                `;
            }
        } else {
            // User is signed out
            if (authButtons) authButtons.style.display = 'block';
            if (userButton) userButton.style.display = 'none';
        }
    });
}