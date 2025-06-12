async function initializeDashboard(clerk) {
    try {
        const token = await clerk.session.getToken();
        const response = await fetch('/api/dashboard', { headers: { 'Authorization': 'Bearer ' + token } });
        if (!response.ok) throw new Error('Failed to fetch dashboard data.');
        const data = await response.json();
        renderDashboard(data, token);
    } catch (error) {
        document.getElementById('dashboard-content').innerHTML = `<div class="alert alert-danger">${error.message}</div>`;
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
                            ${ track.generated ? 
                                `<a href="/roadmap.html?skill=${track.skill_slug}" class="btn btn-primary mt-auto">View Roadmap</a>` :
                                `<button class="btn btn-outline-primary mt-auto generate-roadmap-btn" data-skill="${track.skill}">
                                     <i class="bi bi-stars"></i> Generate AI Roadmap
                                 </button>`
                            }
                        </div>
                    </div>
                </div>`;
        });
        tracksContainer.innerHTML = tracksHtml;
    } else {
        tracksContainer.innerHTML = `<div class="text-center p-4 border rounded bg-light"><p>No skills selected.</p></div>`;
    }
    addGenerateButtonListeners(token);
}

function addGenerateButtonListeners(token) {
    document.querySelectorAll('.generate-roadmap-btn').forEach(button => {
        button.addEventListener('click', async (e) => {
            const btn = e.currentTarget;
            const skill = btn.dataset.skill;
            btn.disabled = true;
            btn.innerHTML = `<span class="spinner-border spinner-border-sm"></span> Queuing...`;

            try {
                const response = await fetch('/api/roadmaps', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json', 'Authorization': 'Bearer ' + token },
                    body: JSON.stringify({ skill: skill })
                });
                if (!response.ok) {
                    const errorData = await response.json();
                    throw new Error(errorData.detail || "Server error.");
                }
                btn.classList.remove('btn-outline-primary');
                btn.classList.add('btn-success');
                btn.innerHTML = `Queued! Refresh in a minute...`;
            } catch (error) {
                btn.classList.remove('btn-outline-primary');
                btn.classList.add('btn-danger');
                btn.innerHTML = `Error!`;
                btn.disabled = false;
                console.error("Failed to request roadmap:", error);
            }
        });
    });
}