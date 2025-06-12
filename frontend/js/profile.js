// frontend/js/profile.js

let currentUserData = {}; // Store user data globally on this page

async function initializeProfilePage(clerk) {
    if (!clerk.user) { window.location.href = '/login.html'; return; }
    
    try {
        const token = await clerk.session.getToken();
        const response = await fetch('/api/users/profile', {
            headers: { 'Authorization': 'Bearer ' + token }
        });
        if (!response.ok) throw new Error('Failed to fetch profile.');
        
        currentUserData = await response.json();
        renderProfile(currentUserData);

        document.getElementById('profile-loader').style.display = 'none';
        document.getElementById('profile-details').style.display = 'flex';

    } catch (error) {
        document.getElementById('profile-content-wrapper').innerHTML = `<div class="alert alert-danger">${error.message}</div>`;
    }
    
    // Attach event listeners after rendering
    attachEventListeners(clerk);
}

function renderProfile(data) {
    // Helper function to safely set text or attributes
    const setAttr = (id, attr, value) => {
        const el = document.getElementById(id);
        if (el) el[attr] = value || (attr === 'src' ? 'https://via.placeholder.com/150' : '...');
    };
    const setText = (id, value) => setAttr(id, 'textContent', value);

    setAttr('profile-pic', 'src', data.profilePictureUrl);
    setText('profile-name', data.name);
    setText('profile-username', data.username);
    setText('profile-headline', data.headline);
    setText('profile-goal', data.primaryGoal);
    setText('profile-email', data.email);
    setText('profile-langs', data.preferredLanguages.join(', '));
    setText('profile-points', data.points);
    setText('profile-badges-count', (data.badges || []).length);

    // Render skills
    const learningContainer = document.getElementById('learning-skills-container');
    const teachingContainer = document.getElementById('teaching-skills-container');
    const learningSkills = data.learningProfile?.skillsToLearn || [];
    const teachingSkills = data.tutorProfile?.teachableModules || [];

    learningContainer.innerHTML = learningSkills.length ? learningSkills.map(s => `<span class="badge bg-light text-dark border me-1 mb-1">${s}</span>`).join('') : '<p class="text-muted">No skills selected yet.</p>';
    teachingContainer.innerHTML = teachingSkills.length ? teachingSkills.map(t => `<span class="badge bg-success me-1 mb-1">${t.module}</span>`).join('') : '<p class="text-muted">No skills verified yet.</p>';
}

function attachEventListeners(clerk) {
    const editModal = document.getElementById('edit-details-modal');
    
    // When the "Edit" modal is about to be shown...
    editModal.addEventListener('show.bs.modal', () => {
        // ...populate the form with the user's current data.
        document.getElementById('edit-headline').value = currentUserData.headline;
        // ...populate the select dropdown and set its value...
    });

    // When the "Save" button in the modal is clicked...
    document.getElementById('save-profile-changes').addEventListener('click', async () => {
        const updatedData = {
            headline: document.getElementById('edit-headline').value,
            // ...get other values from the form...
        };

        try {
            const token = await clerk.session.getToken();
            const response = await fetch('/api/users/profile', {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json', 'Authorization': 'Bearer ' + token },
                body: JSON.stringify(updatedData)
            });
            const result = await response.json();
            if (!response.ok) throw new Error(result.detail || 'Update failed.');

            // Success! Update the global data and re-render the page.
            currentUserData = { ...currentUserData, ...result.user };
            renderProfile(currentUserData);
            
            // Close the modal
            bootstrap.Modal.getInstance(editModal).hide();
        } catch (error) {
            alert(`Error: ${error.message}`);
        }
    });
}