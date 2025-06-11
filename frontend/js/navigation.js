// frontend/js/navigation.js

function initializeClerkNavigation() {
    const Clerk = window.Clerk;
    if (!Clerk) return;

    const userSection = document.getElementById('user-section');
    const authButtons = document.getElementById('auth-buttons');

    Clerk.addListener(({ user }) => {
        if (user) {
            // USER IS SIGNED IN
            if (authButtons) authButtons.style.display = 'none';
            if (userSection) {
                userSection.style.display = 'block';
                userSection.innerHTML = `
                    <div class="dropdown">
                        <button class="btn btn-dark dropdown-toggle d-flex align-items-center" type="button" data-bs-toggle="dropdown" aria-expanded="false">
                            <img src="${user.imageUrl}" alt="User profile picture" width="32" height="32" class="rounded-circle me-2">
                            <span>${user.firstName || user.username}</span>
                        </button>
                        <ul class="dropdown-menu dropdown-menu-dark dropdown-menu-end">
                            <li><a class="dropdown-item" href="/dashboard.html"><i class="bi bi-speedometer2 me-2"></i>Dashboard</a></li>
                            <li><a class="dropdown-item" href="/profile.html"><i class="bi bi-person-circle me-2"></i>My Profile</a></li>
                            <li><hr class="dropdown-divider"></li>
                            <li><button id="sign-out-button" class="dropdown-item"><i class="bi bi-box-arrow-right me-2"></i>Log Out</button></li>
                        </ul>
                    </div>
                `;

                document.getElementById('sign-out-button').addEventListener('click', async () => {
                    await Clerk.signOut();
                    window.location.href = '/login.html';
                });
            }
        } else {
            // USER IS SIGNED OUT
            if (authButtons) authButtons.style.display = 'block';
            if (userSection) userSection.style.display = 'none';
        }
        
        // This is our hook to run page-specific logic after auth state is known
        if (typeof onClerkReady === 'function') {
            onClerkReady();
        }
    });
}