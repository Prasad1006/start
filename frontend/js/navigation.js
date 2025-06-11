// frontend/js/navigation.js

// Put your Clerk Publishable Key here
const CLERK_PUBLISHABLE_KEY = "pk_test_dG91Y2hpbmctbW9zcXVpdG8tOTAuY2xlcmsuYWNjb3VudHMuZGV2JA"; // Replace with your actual key

document.addEventListener('DOMContentLoaded', async () => {
    const Clerk = window.Clerk;

    try {
        await Clerk.load({
            // You can customize the appearance of Clerk components here
        });

        const userButton = document.getElementById('user-button');
        const authButtons = document.getElementById('auth-buttons');
        const signOutButton = document.getElementById('sign-out-button');

        Clerk.addListener(({ user }) => {
            if (user) {
                // If user is signed in
                authButtons.style.display = 'none';
                userButton.style.display = 'block';
                userButton.innerHTML = `<a href="/dashboard.html" class="btn btn-outline-light me-2">Dashboard</a> <div class="text-white">Welcome, ${user.firstName || user.username}</div>`;
            } else {
                // If user is signed out
                authButtons.style.display = 'block';
                userButton.style.display = 'none';
            }
        });

        if (signOutButton) {
            signOutButton.addEventListener('click', async () => {
                await Clerk.signOut();
                window.location.href = '/login.html';
            });
        }

    } catch (err) {
        console.error('Clerk error:', err);
    }
});