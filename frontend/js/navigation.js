/**
 * This function initializes the dynamic navigation bar for the entire site.
 * It listens for changes in the user's authentication state from Clerk.js
 * and updates the UI accordingly.
 */
function initializeClerkNavigation() {
    const Clerk = window.Clerk;
    // If Clerk.js hasn't loaded for some reason, we stop to prevent errors.
    if (!Clerk) {
        console.error("Clerk.js not loaded. Cannot initialize navigation.");
        return;
    }

    // Get the HTML containers we will be manipulating
    const userSection = document.getElementById('user-section');
    const authButtons = document.getElementById('auth-buttons');

    // This is the core magic: Clerk's listener fires whenever the user logs in or out.
    Clerk.addListener(({ user }) => {
        if (user) {
            // --- SCENARIO 1: USER IS SIGNED IN ---
            
            // First, hide the "Log In" and "Sign Up" buttons.
            if (authButtons) authButtons.style.display = 'none';
            
            // Then, show the user section and build the personalized dropdown menu.
            if (userSection) {
                userSection.style.display = 'block';
                
                // We use a Bootstrap 5 Dropdown component for a professional look.
                // The HTML is injected dynamically right here.
                userSection.innerHTML = `
                    <div class="dropdown">
                        <button class="btn btn-dark dropdown-toggle d-flex align-items-center" type="button" data-bs-toggle="dropdown" aria-expanded="false">
                            <img src="${user.imageUrl}" alt="User profile picture" width="32" height="32" class="rounded-circle me-2">
                            <span>Hi, ${user.firstName || user.username}</span>
                        </button>
                        <ul class="dropdown-menu dropdown-menu-dark dropdown-menu-end">
                            <li><a class="dropdown-item" href="/dashboard.html"><i class="bi bi-speedometer2 me-2"></i>Dashboard</a></li>
                            <li><a class="dropdown-item" href="/profile.html"><i class="bi bi-person-circle me-2"></i>My Profile</a></li>
                            <li><hr class="dropdown-divider"></li>
                            <li><button id="sign-out-button" class="dropdown-item"><i class="bi bi-box-arrow-right me-2"></i>Log Out</button></li>
                        </ul>
                    </div>
                `;

                // IMPORTANT: We must add the event listener for the logout button AFTER we've created it.
                const signOutButton = document.getElementById('sign-out-button');
                if (signOutButton) {
                    signOutButton.addEventListener('click', () => {
                        // Use Clerk's signOut method and redirect the user to the login page.
                        Clerk.signOut({ redirectUrl: '/login.html' });
                    });
                }
            }
        } else {
            // --- SCENARIO 2: USER IS SIGNED OUT ---
            
            // Show the "Log In" and "Sign Up" buttons.
            if (authButtons) authButtons.style.display = 'block';
            // Hide the personalized user section.
            if (userSection) userSection.style.display = 'none';
        }

        // This is our special hook to run any page-specific logic AFTER the navigation is ready.
        if (typeof onClerkReady === 'function') {
            onClerkReady();
        }
    });
}