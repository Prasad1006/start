// frontend/js/roadmap.js (new file)
async function initializeRoadmapPage(clerk) {
    const loader = document.getElementById('roadmap-loader');
    const content = document.getElementById('roadmap-content');
    const errorContainer = document.getElementById('roadmap-error');
    
    // Get skill slug from URL
    const params = new URLSearchParams(window.location.search);
    const skillSlug = params.get('skill');

    if (!skillSlug) {
        loader.style.display = 'none';
        errorContainer.textContent = 'Error: No skill specified in the URL. Please return to the dashboard.';
        errorContainer.style.display = 'block';
        return;
    }

    try {
        const token = await clerk.session.getToken();
        const response = await fetch(`/api/roadmaps/${skillSlug}`, {
            headers: { 'Authorization': 'Bearer ' + token }
        });

        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.detail || 'Failed to fetch roadmap data.');
        }

        const data = await response.json();
        renderRoadmap(data);
        
        loader.style.display = 'none';
        content.style.display = 'block';

    } catch (error) {
        loader.style.display = 'none';
        errorContainer.textContent = `Error: ${error.message}`;
        errorContainer.style.display = 'block';
    }
}

function renderRoadmap(data) {
    document.getElementById('roadmap-skill-title').textContent = data.skill;
    
    const accordionContainer = document.getElementById('weekly-plan-accordion');
    let accordionHtml = '';

    if (data.weeklyPlan && data.weeklyPlan.length > 0) {
        data.weeklyPlan.forEach((week, index) => {
            accordionHtml += `
                <div class="accordion-item">
                    <h2 class="accordion-header">
                        <button class="accordion-button ${index > 0 ? 'collapsed' : ''}" type="button" data-bs-toggle="collapse" data-bs-target="#collapse-${index}">
                            <strong>Week ${week.week}:</strong> ${week.topic}
                        </button>
                    </h2>
                    <div id="collapse-${index}" class="accordion-collapse collapse ${index === 0 ? 'show' : ''}" data-bs-parent="#weekly-plan-accordion">
                        <div class="accordion-body">
                            <p>${week.description}</p>
                            <div class="mt-3">
                                <button class="btn btn-outline-success btn-sm disabled"><i class="bi bi-check-circle"></i> Mark as Complete</button>
                                <button class="btn btn-primary btn-sm ms-2 disabled"><i class="bi bi-search"></i> Find a Tutor</button>
                            </div>
                        </div>
                    </div>
                </div>
            `;
        });
    } else {
        accordionHtml = '<p class="text-center text-muted">This roadmap does not have any weekly modules defined yet.</p>';
    }

    accordionContainer.innerHTML = accordionHtml;
}