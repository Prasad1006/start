// frontend/js/navigation.js (The New, Clean Version)

// This function will run after the main Clerk script on the page has loaded.
// It assumes 'window.Clerk' already exists.
function setupClerkUI() {
    const Clerk = window.Clerk;

    if (!Clerk) {
        console.error("Clerk object not found. Make sure the Clerk script is loaded before navigation.js");
        return;
    }

    const userButton = document.getElementById('user-button');
    const authButtons = document.getElementById('auth-buttons');
    const signOutButton = document.getElementById('sign-out-button'); // This might be on other pages

    // This listener will automatically update the UI whenever the user's state changes (login, logout, etc.)
    Clerk.addListener(({ user }) => {
        if clean up all the relevant files to use the modern, recommended `onload` pattern.

#### **Step 1: Fix `navigation.js`**

This file should **not** declare the key. It should just contain the logic that needs to run *after* Clerk is loaded.

**Action:** Open `frontend/js/navigation.js` and replace its **entire content** with this:

```javascript
// frontend/js/navigation.js

// We wrap our entire logic in a function.
// This function will be called by the 'onload' attribute in the main Clerk script tag.
function initializeClerkNavigation() {
    const Clerk = window.Clerk;

    // This code will only run AFTER Clerk is loaded, preventing errors.
    try {
        const userButton = document.getElementById('user-button');
        const authButtons = document.getElementById('auth-buttons');
        
        // This listener will update the UI whenever the user's login state changes.
        Clerk.addListener(({ user }) => {
            if (user) {
                // User is signed in
                authButtons.style.display = 'none';
                userButton.style.display = 'flex'; // Use flex for better alignment
                // Create a more robust user button with a dropdown
                userButton.innerHTML = `
                    <div class="text-white me-3">Welcome, ${user.firstName || user.username}</div>
                    <a href="/dashboard.html" class="btn btn-sm btn-outline-light">Dashboard</a>
                `;
            } else {
                // User is signed out
                authButtons.style.display = 'block';
                userButton.style.display = 'none';
            }
        });

    } catch (err) {
        console.error('Clerk navigation setup error:', err);
    }
}