// frontend/js/onboarding-logic.js

// Helper function to safely get data from localStorage
function getOnboardingData() {
    try {
        const data = JSON.parse(localStorage.getItem('onboardingData'));
        return data || {};
    } catch (e) {
        return {};
    }
}

// Logic for the domains page (onboarding-domains.html)
async function initializeDomainsPage() {
    const streamSelect = document.getElementById('stream-select');
    const branchSelect = document.getElementById('branch-select');
    const domainsContainer = document.getElementById('domains-container');

    try {
        const response = await fetch('/skills.json');
        if (!response.ok) throw new Error('Network error');
        const skillsData = await response.json();

        // Populate Stream dropdown
        streamSelect.innerHTML = '<option value="">-- Select a Stream --</option>';
        for (const streamName in skillsData) {
            const option = document.createElement('option');
            option.value = streamName;
            option.textContent = streamName;
            streamSelect.appendChild(option);
        }

        // When a stream is selected, populate branches
        streamSelect.addEventListener('change', () => {
            const selectedStream = streamSelect.value;
            branchSelect.innerHTML = '<option value="">-- Select a Branch --</option>';
            domainsContainer.innerHTML = '<p class="text-muted">Please select a branch.</p>';
            if (!selectedStream) { branchSelect.disabled = true; return; }
            
            branchSelect.disabled = false;
            const branches = skillsData[selectedStream];
            for (const branchName in branches) {
                const option = document.createElement('option');
                option.value = branchName;
                option.textContent = branchName;
                branchSelect.appendChild(option);
            }
            if (Object.keys(branches).length === 1) {
                branchSelect.value = Object.keys(branches)[0];
                branchSelect.dispatchEvent(new Event('change'));
            }
        });

        // When a branch is selected, populate domains
        branchSelect.addEventListener('change', () => {
            const selectedStream = streamSelect.value;
            const selectedBranch = branchSelect.value;
            domainsContainer.innerHTML = '';
            if (!selectedStream || !selectedBranch) return;

            const domains = skillsData[selectedStream][selectedBranch].domains;
            for (const domainName in domains) {
                const card = document.createElement('div');
                card.className = 'domain-card p-2 rounded';
                card.textContent = domainName;
                card.dataset.domainName = domainName;
                domainsContainer.appendChild(card);
                card.addEventListener('click', () => card.classList.toggle('selected'));
            }
        });

        // Handle form submission
        document.getElementById('domains-form').addEventListener('submit', (e) => {
            e.preventDefault();
            const onboardingData = getOnboardingData();
            onboardingData.stream = streamSelect.value;
            onboardingData.branch = branchSelect.value;
            onboardingData.selectedDomains = Array.from(domainsContainer.querySelectorAll('.selected')).map(el => el.dataset.domainName);

            if (!onboardingData.stream || !onboardingData.branch || onboardingData.selectedDomains.length === 0) {
                alert('Please make sure to select your stream, branch, and at least one domain.');
                return;
            }
            
            localStorage.setItem('onboardingData', JSON.stringify(onboardingData));
            window.location.href = '/onboarding-skills.html';
        });

    } catch (error) {
        console.error('Failed to initialize domains page:', error);
        domainsContainer.innerHTML = '<p class="text-danger">Could not load page data. Please refresh.</p>';
    }
}


// Logic for the skills page (onboarding-skills.html)
async function initializeSkillsPage() {
    // Wait until Clerk is loaded before we do anything that might need it
    while (!window.Clerk) {
        await new Promise(resolve => setTimeout(resolve, 50));
    }
    await window.Clerk.load();
    
    const accordionContainer = document.getElementById('skills-accordion');
    const onboardingData = getOnboardingData();

    // The rest of the function is the same, building the UI and handling the final submission
    // ... (paste the rest of the initializeSkillsPage function from the previous answer here) ...
}