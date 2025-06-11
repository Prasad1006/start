// frontend/js/profile.js
async function initializeProfilePage(clerk) {
    if (!clerk.user) {
        window.location.href = '/login.html';
        return;
    }

    try {
        const token = await clerk.session.getToken();
        
        // We can reuse the same onboarding API endpoint if we add logic to it,
        // or create a new one like GET /api/profile. Let's assume a new one.
        // We'll use the Clerk username for the URL.
        const response = await fetch(`/api/users/${clerk.user.username}`, {
            headers: { 'Authorization': 'Bearer ' + token }
        });

        if (!response.ok) throw new Error('Failed to fetch profile data.');

        const userData = await response.json();
        renderProfile(userData);

    } catch (error) {
        console.error('Profile Page Error:', error);
        document.getElementById('main-content').innerHTML = `<div class="alert alert-danger">Could not load your profile.</div>`;
    }
}

function renderProfile(data) {
    // Helper to safely set text content
    const setText = (id, text) => {
        const el = document.getElementById(id);
        if (el) el.textContent = text || 'N/A';
    };

    setText('profile-name', data.name);
    setText('profile-headline', data.headline);
    setText('profile-username', data.username);
    setText('profile-goal', data.primaryGoal);
    setText('profile-email', data.email);
    setText('profile-langs', data.preferredLanguages.join(', '));
    setText('profile-points', data.points);

    const profilePic = document.getElementById('profile-pic');
    if (profilePic && data.profilePictureUrl) {
        profilePic.src = data.profilePictureUrl;
    }

    // Render badges
    const badgesContainer = document.getElementById('profile-badges');
    if (badgesContainer && data.badges && data.badges.length > 0) {
        badgesContainer.innerHTML = ''; // Clear default text
        data.badges.forEach(badgeName => {
            const badgeEl = document.createElement('span');
            badgeEl.className = 'badge bg-info me-1';
            badgeEl.textContent = badgeName;
            badgesContainer.appendChild(badgeEl);
        });
    }
}