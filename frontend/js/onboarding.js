// A helper function to safely get data from localStorage at the start of each step.
function getOnboardingData() {
    try {
        const data = JSON.parse(localStorage.getItem('onboardingData'));
        return data || {};
    } catch (e) {
        // If localStorage is corrupted, start with a fresh object.
        return {};
    }
}

// ===================================================================================
// STEP 1: LOGIC FOR THE PROFILE PAGE (onboarding-profile.html)
// ===================================================================================
function handleProfileStep() {
    document.getElementById('profile-form').addEventListener('submit', function(e) {
        e.preventDefault();
        
        // Collect data from the form
        const onboardingData = {
            username: document.getElementById('username').value,
            headline: document.getElementById('headline').value,
            primaryGoal: document.getElementById('primaryGoal').value,
            preferredLanguages: Array.from(document.querySelectorAll('input[name="preferred-language"]:checked')).map(el => el.value),
        };

        // Save to localStorage and proceed to the next step
        localStorage.setItem('onboardingData', JSON.stringify(onboardingData));
        window.location.href = '/onboarding-domains.html';
    });
}

// ===================================================================================
// STEP 2: LOGIC FOR THE DOMAINS PAGE (onboarding-domains.html)
// ===================================================================================
async function handleDomainsStep() {
    const streamSelect = document.getElementById('stream-select');
    const branchSelect = document.getElementById('branch-select');
    const domainsContainer = document.getElementById('domains-container');

    try {
        const response = await fetch('/skills.json');
        if (!response.ok) throw new Error(`Network response was not ok: ${response.statusText}`);
        const skillsData = await response.json();

        // Populate the "Stream" dropdown (BTech, Placement Prep, etc.)
        streamSelect.innerHTML = '<option value="">-- Select a Stream --</option>';
        for (const streamName in skillsData) {
            streamSelect.add(new Option(streamName, streamName));
        }

        // When a stream is selected, update the "Branch" dropdown
        streamSelect.addEventListener('change', () => {
            const selectedStream = streamSelect.value;
            branchSelect.innerHTML = '<option value="">-- Select a Branch --</option>';
            domainsContainer.innerHTML = '<p class="text-muted">Please select a branch.</p>';
            branchSelect.disabled = !selectedStream;
            if (!selectedStream) return;
            
            const branches = skillsData[selectedStream];
            for (const branchName in branches) {
                branchSelect.add(new Option(branchName, branchName));
            }
            // If there's only one branch (like for Placement Prep), auto-select it and trigger the next step.
            if (Object.keys(branches).length === 1) {
                branchSelect.value = Object.keys(branches)[0];
                branchSelect.dispatchEvent(new Event('change'));
            }
        });

        // When a branch is selected, show the clickable domain cards
        branchSelect.addEventListener('change', () => {
            const stream = streamSelect.value;
            const branch = branchSelect.value;
            domainsContainer.innerHTML = ''; // Clear previous content
            if (!stream || !branch) return;

            const domains = skillsData[stream][branch].domains;
            for (const domainName in domains) {
                const card = document.createElement('div');
                card.className = 'domain-card p-2 rounded';
                card.textContent = domainName;
                card.dataset.domainName = domainName; // Store the name for later retrieval
                domainsContainer.appendChild(card);
                card.addEventListener('click', () => card.classList.toggle('selected'));
            }
        });

        // Handle form submission for this step
        document.getElementById('domains-form').addEventListener('submit', (e) => {
            e.preventDefault();
            const onboardingData = getOnboardingData();
            
            onboardingData.stream = streamSelect.value;
            onboardingData.branch = branchSelect.value;
            onboardingData.selectedDomains = Array.from(domainsContainer.querySelectorAll('.selected')).map(el => el.dataset.domainName);

            if (!onboardingData.branch || onboardingData.selectedDomains.length === 0) {
                alert('Please make sure to select your branch and at least one domain.');
                return;
            }
            
            localStorage.setItem('onboardingData', JSON.stringify(onboardingData));
            window.location.href = '/onboarding-skills.html';
        });

    } catch (error) {
        console.error('Domains page initialization failed:', error);
        domainsContainer.innerHTML = '<div class="alert alert-danger">Could not load required data. Please refresh the page.</div>';
    }
}


// ===================================================================================
// STEP 3: LOGIC FOR THE SKILLS PAGE (onboarding-skills.html)
// ===================================================================================
async function handleSkillsStep() {
    // Wait for Clerk.js to be fully loaded and ready
    while (!window.Clerk) {
        await new Promise(resolve => setTimeout(resolve, 50));
    }
    await window.Clerk.load();
    
    const accordionContainer = document.getElementById('skills-accordion');
    const onboardingData = getOnboardingData();

    if (!onboardingData || !onboardingData.branch || !onboardingData.selectedDomains) {
        accordionContainer.innerHTML = '<div class="alert alert-warning">Onboarding data seems to be missing. Please <a href="/onboarding-profile.html" class="alert-link">start over</a>.</div>';
        document.getElementById('submit-btn').disabled = true;
        return;
    }

    // Build the UI from skills.json
    try {
        const response = await fetch('/skills.json');
        if (!response.ok) throw new Error('Failed to load skills data.');
        const skillsData = await response.json();

        const allDomainsData = skillsData[onboardingData.stream][onboardingData.branch].domains;
        
        accordionContainer.innerHTML = ''; // Clear the loading spinner
        onboardingData.selectedDomains.forEach((domainName, index) => {
            const domain = allDomainsData[domainName];
            if (!domain) return;
            const skills = domain.skills;
            const accordionId = `accordion-${index}`;
            let skillsHtml = '';
            skills.forEach(skill => {
                skillsHtml += `<div class="row border-bottom py-2 align-items-center"><div class="col-sm-5 col-12">${skill}</div><div class="col-sm-3 col-6 text-center"><input class="form-check-input" type="checkbox" name="learn" value="${skill}"></div><div class="col-sm-4 col-6 text-center"><input class="form-check-input" type="checkbox" name="teach" value="${skill}"></div></div>`;
            });
            const accordionItem = `<div class="accordion-item"><h2 class="accordion-header"><button class="accordion-button" type="button" data-bs-toggle="collapse" data-bs-target="#collapse-${accordionId}">${domainName}</button></h2><div id="collapse-${accordionId}" class="accordion-collapse collapse show"><div class="accordion-body p-2"><div class="row fw-bold text-muted mb-2 d-none d-sm-flex"><div class="col-5">Skill</div><div class="col-3 text-center"><i class="bi bi-book-fill"></i> Learn</div><div class="col-4 text-center"><i class="bi bi-easel-fill"></i> Teach</div></div>${skillsHtml}</div></div></div>`;
            accordionContainer.innerHTML += accordionItem;
        });
    } catch(e) {
        console.error("Error building skills UI:", e);
        accordionContainer.innerHTML = `<div class="alert alert-danger">Could not load skill information. Please refresh.</div>`;
    }
    
    // Attach the final, robust form submission logic
    document.getElementById('skills-form').addEventListener('submit', async function(e) {
        e.preventDefault();
        const submitBtn = document.getElementById('submit-btn');
        const errorEl = document.getElementById('error-message');
        submitBtn.disabled = true;
        submitBtn.innerHTML = '<span class="spinner-border spinner-border-sm"></span> Saving...';
        errorEl.style.display = 'none';

        onboardingData.skillsToLearn = Array.from(document.querySelectorAll('input[name="learn"]:checked')).map(el => el.value);
        onboardingData.skillsToTeach = Array.from(document.querySelectorAll('input[name="teach"]:checked')).map(el => el.value);

        try {
            if (!window.Clerk || !window.Clerk.session) throw new Error("Authentication session not found. Please log in again.");
            
            const token = await window.Clerk.session.getToken();
            
            const response = await fetch('/api/users/onboard', {
                method: 'POST',
                headers: {'Content-Type': 'application/json', 'Authorization': 'Bearer ' + token},
                body: JSON.stringify(onboardingData)
            });

            const responseData = await response.json();
            if (!response.ok) {
                throw new Error(responseData.error || responseData.detail || 'An unknown server error occurred.');
            }

            localStorage.removeItem('onboardingData');
            
            submitBtn.classList.remove('btn-success');
            submitBtn.classList.add('btn-primary');
            submitBtn.innerText = 'Success! Redirecting...';
            setTimeout(() => {
                window.location.href = '/dashboard.html';
            }, 1000);

        } catch (error) {
            errorEl.innerText = `Error: ${error.message}`;
            errorEl.style.display = 'block';
            submitBtn.disabled = false;
            submitBtn.innerText = 'Complete Profile & Enter';
        }
    });
}