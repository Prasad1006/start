// frontend/js/dashboard.js (fully updated version)
async function initializeDashboard(clerk) {
    try {
        const token = await clerk.session.getToken();
        const response = await fetch('/api/dashboard', {
            headers: { 'Authorization': 'Bearer ' + token }
        });
        if (!response.ok) throw new Error('Failed to fetch dashboard data.');
        const data = await response.json();
        renderDashboard(data, token); // Pass token to the renderer
    } catch (error) {
        document.getElementById('dashboard-content').innerHTML = `<div class="alert alert-danger">Could not load your dashboard.</div>`;
    }
}

function renderDashboard(data, token) {
    document.getElementById('welcome-message').textContent = `Welcome, ${data.name}!`;
    document.getElementById('user-points').textContent = data.points;

    const tracksContainer = document.getElementById('learning-tracks-container');
    if (data.learningTracks && data.learningTracks.length > 0) {
        let tracksHtml = '';
        data.learningTracks.forEach(track => {
            tracksHtml += `
                <div class="col-md-6 col-lg-4 mb-4">
                    <div class="card h-100 shadow-sm">
                        <div class="card-body d-flex flex-column">
                            <h5 class="card-title">${track.skill}</h5>
                            <p class="card-text text-muted flex-grow-1">${track.progress_summary}</p>
                            <div class="progress mb-3">
                                <div class="progress-bar" role="progressbar" style="width: ${track.progress_percent}%"></div>
                            </div>
                            ${
                                track.generated
                                ? `<a href="/roadmap.html?skill=${track.skill_slug}" class="btn btn-primary mt-auto">View Roadmap</a>`
                                : `<button class="btn btn-outline-primary mt-auto generate-roadmap-btn" data-skill="${track.skill}">
                                       <i class="bi bi-stars"></i> Generate AI Roadmap
                                   </button>`
                            }
                        </div>
                    </div>
                </div>
            `;
        });
        tracksContainer.innerHTML = tracksHtml;
    } else {
        tracksContainer.innerHTML = `
            <div class="text-center p-4 border rounded bg-light">
                <p class="mb-2">You haven't selected any skills to learn yet!</p>
                <a href="/profile.html" class="btn btn-outline-primary">Add Skills on Your Profile</a>
            </div>
        `;
    }

    // Add event listeners to all "Generate" buttons
    addGenerateButtonListeners(token);
}

function addGenerateButtonListeners(token) {
    document.querySelectorAll('.generate-roadmap-btn').forEach(button => {
        button.addEventListener('click', async (e) => {
            const btn = e.currentTarget;
            const skill = btn.dataset.skill;

            // Show loading state
            btn.disabled = true;
            btn.innerHTML = `<span class="spinner-border spinner-border-sm"></span> Generating...`;

            try {
                const response = await fetch('/api/roadmaps', {
                    method: 'POST',
                    headers: { 
                        'Content-Type': 'application/json',
                        'Authorization': 'Bearer ' + token 
                    },
                    body: JSON.stringify({ skill: skill })
                });

                if (response.status !== 202) {
                    const errorData = await response.json();
                    throw new Error(errorData.detail || "Failed to start generation.");
                }

                // Show a success state and prompt user to refresh
                btn.classList.remove('btn-outline-primary');
                btn.classList.add('btn-success');
                btn.innerHTML = `Queued! Refreshing...`;
                
                // Refresh the page after a short delay to show the updated status
                setTimeout(() => {
                    window.location.reload();
                }, 2000);

            } catch (error) {
                btn.classList.remove('btn-outline-primary');
                btn.classList.add('btn-danger');
                btn.innerHTML = `Error!`;
                console.error("Failed to generate roadmap:", error);
            }
        });
    });
}