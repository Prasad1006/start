// This file will contain the shared logic for the onboarding process.

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
    const branchSelect = document.getElementById('branch-select');
    const streamSelect = document.getElementById('stream-select');
    const domainsContainer = document.getElementById('domains-container');

    try {
        const response = await fetch('/skills.json');
        const skillsData = await response.json();

        // Populate Stream dropdown
        streamSelect.innerHTML = '<option value="">-- Select a Stream --</option>';
        for (const streamName in skillsData) {
            const option = document.createElement('option');
            option.value = streamName;
            option.textContent = streamName;
            streamSelect.appendChild(option);
        }

        // When a stream is selected, populate the branches
        streamSelect.addEventListener('change', () => {
            const selectedStream = streamSelect.value;
            branchSelect.innerHTML = '<option value="">-- Select a Branch --</option>';
            domainsContainer.innerHTML = '<p class="text-muted">Please select a branch.</p>';
            if (!selectedStream) {
                branchSelect.disabled = true;
                return;
            }
            branchSelect.disabled = false;
            const branches = skillsData[selectedStream];
            for (const branchName in branches) {
                const option = document.createElement('option');
                option.value = branchName;
                option.textContent = branchName;
                branchSelect.appendChild(option);
            }
            // If there's only one branch (like for Placement Prep), auto-select it.
            if (Object.keys(branches).length === 1) {
                branchSelect.value = Object.keys(branches)[0];
                branchSelect.dispatchEvent(new Event('change'));
            }
        });

        // When a branch is selected, populate the domains
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
            const selectedStream = streamSelect.value;
            const selectedBranch = branchSelect.value;
            const selectedDomains = Array.from(domainsContainer.querySelectorAll('.selected')).map(el => el.dataset.domainName);

            if (!selectedStream || !selectedBranch || selectedDomains.length === 0) {
                alert('Please select your stream, branch, and at least one domain.');
                return;
            }
            
            const onboardingData = getOnboardingData();
            onboardingData.stream = selectedStream;
            onboardingData.branch = selectedBranch;
            onboardingData.selectedDomains = selectedDomains;
            
            localStorage.setItem('onboardingData', JSON.stringify(onboardingData));
            window.location.href = '/onboarding-skills.html';
        });

    } catch (error) {
        console.error('Failed to initialize domains page:', error);
        domainsContainer.innerHTML = '<p class="text-danger">Could not load page data. Please refresh.</p>';
    }
}