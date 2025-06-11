// frontend/js/navigation.js (The final, complete version)

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
            // --- USER IS SIGNED IN ---
            if (authButtons) authButtons.style.display = 'none';
            if (userButton) {
                userButton.style.display = 'flex';
                
                // Create the HTML for the signed-in user, including the new Sign Out button
                userButton.innerHTML = `
                    <div class="text-white me-3">Welcome, ${user.firstName || user.username}</div>
                    <a href="/dashboard.html" class="btn btn-sm btn-outline-light">Dashboard</a>
                    <button id="sign-out-button" class="btn btn-sm btn-secondary ms-2">Sign Out</button>
                `;

                // *** THIS IS THE NEW LOGIC ***
                // Now that the button exists in the HTML, find it and add the click event.
                const signOutButton = document.getElementById('sign-out-button');
                if (signOutButton) {
                    signOutButton.addEventListener('click', async () => {
                        console.log("Signing out...");
                        await Clerk.signOut();
                        // Redirect to the login page after signing out.
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