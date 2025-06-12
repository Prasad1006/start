function initializeClerkNavigation() {
    const Clerk = window.Clerk;
    if (!Clerk) return;
    const userSection = document.getElementById('user-section');
    const authButtons = document.getElementById('auth-buttons');

    Clerk.addListener(({ user }) => {
        if (user) {
            if (authButtons) authButtons.style.display = 'none';
            if (userSection) {
                userSection.style.display = 'block';
                userSection.innerHTML = `
                    <div class="dropdown">
                        <button class="btn btn-dark dropdown-toggle d-flex align-items-center" type="button" data-bs-toggle="dropdown" aria-expanded="false">
                            <img src="${user.imageUrl}" alt="User profile" width="32" height="32" class="rounded-circle me-2">
                            <span>Hi, ${user.firstName || user.username}</span>
                        </button>
                        <ul class="dropdown-menu dropdown-menu-dark dropdown-menu-end">
                            <li><a class="dropdown-item" href="/dashboard.html">Dashboard</a></li>
                            <li><a class="dropdown-item" href="/profile.html">My Profile</a></li>
                            <li><hr class="dropdown-divider"></li>
                            <li><button id="sign-out-button" class="dropdown-item">Log Out</button></li>
                        </ul>
                    </div>`;
                document.getElementById('sign-out-button').addEventListener('click', () => Clerk.signOut({ redirectUrl: '/login.html' }));
            }
        } else {
            if (authButtons) authButtons.style.display = 'block';
            if (userSection) userSection.style.display = 'none';
        }
        if (typeof onClerkReady === 'function') {
            onClerkReady();
        }
    });
}