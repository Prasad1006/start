async function initializeDashboard(clerk) {
    try {
        const token = await clerk.session.getToken();
        const response = await fetch('/api/dashboard', {
            headers: { 'Authorization': 'Bearer ' + token }
        });
        if (!response.ok) throw new Error('Failed to fetch dashboard data.');
        const data = await response.json();
        renderDashboard(data);
    } catch (error) {
        document.getElementById('dashboard-content').innerHTML = `<div class="alert alert-danger">Could not load your dashboard.</div>`;
    }
}

function renderDashboard(data) {
    document.getElementById('welcome-message').textContent = `Welcome, ${data.name}!`;
    document.getElementById('user-points').textContent = data.points;
    const content = document.getElementById('dashboard-content');
    content.innerHTML = `
        <h2 class="h4">My Learning</h2>
        <div class="text-center p-4 border rounded bg-light">
            <p class="mb-2">Your learning roadmaps will appear here soon!</p>
            <a href="/profile.html" class="btn btn-outline-primary">View Your Full Profile</a>
        </div>
    `;
}