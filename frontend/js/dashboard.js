// frontend/js/dashboard.js

async function initializeDashboard(clerk) {
    if (!clerk.user) {
        // This is a protected page, redirect if not logged in
        window.location.href = '/login.html';
        return;
    }

    // Personalize the welcome message
    const welcomeMessage = document.getElementById('welcome-message');
    if (welcomeMessage) {
        welcomeMessage.textContent = `Welcome, ${clerk.user.firstName || clerk.user.username}!`;
    }

    try {
        const token = await clerk.session.getToken();
        
        // This is the API call to our backend to get all dashboard data
        const response = await fetch('/api/dashboard', {
            headers: { 'Authorization': 'Bearer ' + token }
        });

        if (!response.ok) {
            throw new Error('Failed to fetch dashboard data.');
        }

        const data = await response.json();
        renderDashboard(data);

    } catch (error) {
        console.error('Dashboard Error:', error);
        const container = document.getElementById('learning-tracks-container');
        container.innerHTML = `<div class="alert alert-danger">Could not load your dashboard. Please try refreshing the page.</div>`;
    }
}

function renderDashboard(data) {
    // Render user points
    const userPointsEl = document.getElementById('user-points');
    if (userPointsEl) {
        userPointsEl.textContent = data.points || 0;
    }

    // Render Learning Tracks
    const container = document.getElementById('learning-tracks-container');
    container.innerHTML = ''; // Clear the loading spinner

    if (data.learningTracks && data.learningTracks.length > 0) {
        data.learningTracks.forEach(track => {
            const card = document.createElement('div');
            card.className = 'col-md-6 col-lg-4';
            card.innerHTML = `
                <div class="card h-100">
                    <div class="card-body">
                        <h5 class="card-title">${track.skill}</h5>
                        <p class="card-text text-muted">${track.progress_summary}</p>
                        <div class="progress mb-3">
                            <div class="progress-bar" role="progressbar" style="width: ${track.progress_percent}%" aria-valuenow="${track.progress_percent}" aria-valuemin="0" aria-max="100"></div>
                        </div>
                        <a href="/roadmap.html?skill=${track.skill_slug}" class="btn btn-primary">View Roadmap</a>
                    </div>
                </div>
            `;
            container.appendChild(card);
        });
    } else {
        container.innerHTML = `<p>You haven't started learning any skills yet. Go to the "Skills" page to add one!</p>`;
    }
    
    // Render Teaching Section (if user is a tutor)
    const teachingSection = document.getElementById('teaching-section');
    if (data.isTutor) {
        teachingSection.style.display = 'block';
        // ... logic to render teaching summary ...
    }
}