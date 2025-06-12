// in backend/js/dashboard.js
function addGenerateButtonListeners(token) {
    document.querySelectorAll('.generate-roadmap-btn').forEach(button => {
        button.addEventListener('click', async (e) => {
            const btn = e.currentTarget;
            const skill = btn.dataset.skill;

            btn.disabled = true;
            btn.innerHTML = `<span class="spinner-border spinner-border-sm"></span> Queuing...`;

            try {
                // Call the new, simpler endpoint
                const response = await fetch('/api/roadmaps/request', {
                    method: 'POST',
                    headers: { 
                        'Content-Type': 'application/json',
                        'Authorization': 'Bearer ' + token 
                    },
                    body: JSON.stringify({ skill: skill })
                });

                const responseData = await response.json();
                if (!response.ok) {
                    throw new Error(responseData.detail || "Failed to queue request.");
                }

                btn.classList.remove('btn-outline-primary');
                btn.classList.add('btn-success');
                // Give a more accurate message to the user
                btn.innerHTML = `Queued! Refresh in a minute.`;

            } catch (error) {
                btn.classList.remove('btn-outline-primary');
                btn.classList.add('btn-danger');
                btn.innerHTML = `Error!`;
                btn.disabled = false;
                console.error("Failed to queue roadmap generation:", error);
            }
        });
    });
}