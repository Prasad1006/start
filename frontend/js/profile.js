// frontend/js/profile.js

async function initializeProfilePage(clerk) {
    if (!clerk.user) {
        // This page is protected; redirect to login if not authenticated.
        window.location.href = '/login.html';
        return;
    }

    const loader = document.getElementById('profile-loader');
    const details = document.getElementById('profile-details');
    const wrapper = document.getElementById('profile-content-wrapper');

    try {
        const token = await clerk.session.getToken();
        
        // Call our simple, secure /api/profile endpoint.
        const response = await fetch(`/api/profile`, {
            headers: { 'Authorization': 'Bearer ' + token }
        });

        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.detail || 'Failed to fetch your profile data.');
        }

        const userData = await response.json();
        
        // If successful, render the profile.
        renderProfile(userData);

        // Hide the loader and show the populated content.
        loader.style.display = 'none';
        details.style.display = 'flex'; // Use 'flex' to make the row layout work correctly.

    } catch (error) {
        console.error('Profile Page Error:', error);
        // If any part of the process fails, show a clear error message.
        wrapper.innerHTML = `<div class="alert alert-danger m-3">Could not load your profile. Error: ${error.message}</div>`;
    }
}

function renderProfile(data) {
    // Helper function to safely set the text content of an element by its ID.
    const setText = (id, text) => {
        const el = document.getElementById(id);
        if (el) el.textContent = text || 'Not provided';
    };

    // Populate all the main profile fields
    setText('profile-name', data.name);
    setText('profile-headline', data.headline);
    setText('profile-username', data.username);
    setText('profile-goal', data.primaryGoal);
    setText('profile-email', data.email);
    setText('profile-langs', data.preferredLanguages.join(', '));
    setText('profile-points', data.points);

    // Update profile picture
    const profilePic = document.getElementById('profile-pic');
    if (profilePic && data.profilePictureUrl) {
        profilePic.src = data.profilePictureUrl;
    }

    // Render badges and key learning profile tags
    const badgesContainer = document.getElementById('profile-badges');
    const learningProfile = data.learningProfile || {};
    if (badgesContainer) {
        let tagsHtml = '';
        if (data.badges && data.badges.length > 0) {
            data.badges.forEach(badge => {
                tagsHtml += `<span class="badge bg-primary me-1 mb-1">${badge}</span>`;
            });
        }
        if (learningProfile.stream) {
            tagsHtml += `<span class="badge bg-secondary me-1 mb-1">${learningProfile.stream}</span>`;
        }
        if (learningProfile.branch) {
            tagsHtml += `<span class="badge bg-secondary me-1 mb-1">${learningProfile.branch}</span>`;
        }
        
        badgesContainer.innerHTML = tagsHtml || '<p class="text-muted">No badges earned yet.</p>';
    }
}