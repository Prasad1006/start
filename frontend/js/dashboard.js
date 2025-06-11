/**
 * This script controls the main user dashboard.
 * It is called by the `onClerkReady` hook in dashboard.html after the user's
 * authentication state has been confirmed by navigation.js and gatekeeper.js.
 */
async function initializeDashboard(clerk) {
    // We can be confident clerk.user exists because the gatekeeper protects this page.
    if (!clerk || !clerk.user) {
        // As a fallback, redirect to login if something went wrong.
        window.location.href = '/login.html';
        return;
    }

    // Personalize the welcome message at the top of the page
    const welcomeMessage = document.getElementById('welcome-message');
    if (welcomeMessage) {
        welcomeMessage.textContent = `Welcome, ${clerk.user.firstName || clerk.user.username}!`;
    }

    try {
        // Get the authentication token from Clerk to make a secure API call
        const token = await clerk.session.getToken();
        
        // Fetch all the necessary data for the dashboard from our single backend endpoint
        const response = await fetch('/api/dashboard', {
            headers: { 'Authorization': 'Bearer ' + token }
        });

        if (!response.ok) {
            // If the API call fails, show an error message to the user.
            const errorData = await response.json();
            throw new Error(errorData.detail || 'Failed to fetch dashboard data.');
        }

        const data = await response.json();
        
        // If the API call is successful, use the data to build the page.
        renderDashboard(data);

    } catch (error) {
        console.error('Dashboard Initialization Error:', error);
        const container = document.getElementById('learning-tracks-container');
        container.innerHTML = `<div class="col-12"><div class="alert alert-danger">Could not load your dashboard. Please try refreshing the page.</div></div>`;
    }
}

/**
 * Takes the data object from the API and populates the HTML.
 * @param {object} data - The data object from the /api/dashboard endpoint.
 */
function renderDashboard(data) {
    // 1. Render the user's total points
    const userPointsEl = document.getElementById('user-points');
    if (userPointsEl) {
        userPointsEl.textContent = data.points || 0;
    }

    // 2. Render the "My Learning" section with a card for each roadmap
    const container = document.getElementById('learning-tracks-container');
    container.innerHTML = ''; // Clear the initial loading spinner

    if (data.learningTracks && data.learningTracks.length > 0) {
        data.learningTracks.forEach(track => {
            const card = document.createElement('div');
            card.className = 'col-md-6 col-lg-4';
            card.innerHTML = `
                <div class="card h-100 shadow-sm">
                    <div class="card-body d-flex flex-column">
                        <h5 class="card-title">${track.skill}</h5>
                        <p class="card-text text-muted">${track.progress_summary}</p>
                        <div class="progress mb-3" style="height: 8px;">
                            <div class="progress-bar" role="progressbar" style="width: ${track.progress_percent}%" aria-valuenow="${track.progress_percent}" aria-valuemin="0" aria-max="100"></div>
                        </div>
                        <div class="mt-auto">
                            <a href="/roadmap.html?skill=${track.skill_slug}" class="btn btn-primary">View Roadmap</a>
                        </div>
                    </div>
                </div>
            `;
            container.appendChild(card);
        });
    } else {
        // If the user has no roadmaps, show a helpful message.
        container.innerHTML = `
            <div class="col-12">
                <div class="text-center p-4 border rounded bg-light">
                    <p class="mb-2">You haven't started a learning path yet!</p>
                    <a href="/profile.html" class="btn btn-success">Add Your First Skill</a>
                </div>
            </div>
        `;
    }
    
    // 3. Conditionally render the "My Teaching" section
    const teachingSection = document.getElementById('teaching-section');
    if (data.isTutor) {
        teachingSection.style.display = 'block';
        const summaryContainer = document.getElementById('teaching-dashboard-summary');
        summaryContainer.innerHTML = `
            <div class="card">
                <div class="card-body">
                    <p>You are a verified tutor! You can help other students and earn points.</p>
                    <a href="/teaching-dashboard.html" class="btn btn-outline-primary">Go to Teaching Dashboard</a>
                </div>
            </div>
        `;
    }
}