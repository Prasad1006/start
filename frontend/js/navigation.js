function initializeClerkNavigation() {
    const Clerk = window.Clerk;

    if (!Clerk) {
        console.error("Clerk object is not available. This can happen if the script is loaded in the wrong order.");
        return;
    }

    const userButton = document.getElementById('user-button');
    const authButtons = document.getElementById('auth-buttons');

    Clerk.addListener(({ user }) => {
        if (user) {
            // --- USER IS SIGNED IN ---
            if (authButtons) authButtons.style.display = 'none';
            if (userButton) {
                userButton.style.display = 'flex';
                userButton.innerHTML = `
                    <div class="navbar-text text-white me-3">Welcome, ${user.firstName || user.username}</div>
                    <a href="/dashboard.html" class="btn btn-sm btn-outline-light">Dashboard</a>
                    <button id="sign-out-button" class="btn btn-sm btn-secondary ms-2">Sign Out</button>
                `;

                const signOutButton = document.getElementById('sign-out-button');
                if (signOutButton) {
                    signOutButton.addEventListener('click', async () => {
                        await Clerk.signOut();
                        window.location.href = '/login.html';
                    });
                }
            }
        } else {
            // --- USER IS SIGNED OUT ---
            if (authButtons) authButtons.style.display = 'block';
            if (userButton) userButton.style.display = 'none';
        }
    });
}