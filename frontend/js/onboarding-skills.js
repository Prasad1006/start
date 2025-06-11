async function initializeOnboardingForm() {
    const accordionContainer = document.getElementById('skills-accordion');
    const onboardingData = JSON.parse(localStorage.getItem('onboardingData'));

    if (!onboardingData || !onboardingData.branch) {
        accordionContainer.innerHTML = '<p class="text-danger">Onboarding data missing. Please <a href="/onboarding-profile.html">start over</a>.</p>';
        document.getElementById('submit-btn').disabled = true;
        return;
    }
    try {
        const response = await fetch('/skills.json');
        const skillsData = await response.json();
        const branches = skillsData[onboardingData.branch];
        const firstBranchName = Object.keys(branches)[0];
        const allDomainsData = branches[firstBranchName].domains;
        onboardingData.selectedDomains.forEach((domainName, index) => {
            const domain = allDomainsData[domainName];
            if (!domain) return;
            const skills = domain.skills;
            const accordionId = `accordion-${index}`;
            let skillsHtml = '';
            skills.forEach(skill => {
                skillsHtml += `<div class="row border-bottom py-2 align-items-center"><div class="col-sm-5 col-12">${skill}</div><div class="col-sm-3 col-6 text-center"><input class="form-check-input" type="checkbox" name="learn" value="${skill}"></div><div class="col-sm-4 col-6 text-center"><input class="form-check-input" type="checkbox" name="teach" value="${skill}"></div></div>`;
            });
            const accordionItem = `<div class="accordion-item"><h2 class="accordion-header"><button class="accordion-button" type="button" data-bs-toggle="collapse" data-bs-target="#collapse-${accordionId}">${domainName}</button></h2><div id="collapse-${accordionId}" class="accordion-collapse collapse show"><div class="accordion-body p-2"><div class="row fw-bold text-muted mb-2 d-none d-sm-flex"><div class="col-5">Skill</div><div class="col-3 text-center">Learn</div><div class="col-4 text-center">Teach</div></div>${skillsHtml}</div></div></div>`;
            accordionContainer.innerHTML += accordionItem;
        });
    } catch(e) { console.error("Error building skills UI", e); }
    
    document.getElementById('skills-form').addEventListener('submit', async function(e) {
        e.preventDefault();
        const submitBtn = document.getElementById('submit-btn');
        const errorMessageEl = document.getElementById('error-message');
        submitBtn.disabled = true;
        submitBtn.innerHTML = '<span class="spinner-border spinner-border-sm"></span> Saving...';
        errorMessageEl.style.display = 'none';

        onboardingData.skillsToLearn = Array.from(document.querySelectorAll('input[name="learn"]:checked')).map(el => el.value);
        onboardingData.skillsToTeach = Array.from(document.querySelectorAll('input[name="teach"]:checked')).map(el => el.value);

        try {
            await window.Clerk.load();
            if (!window.Clerk.session) throw new Error("Authentication session not found.");
            
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
            window.location.href = '/dashboard.html';

        } catch (error) {
            errorMessageEl.innerText = error.message;
            errorMessageEl.style.display = 'block';
            submitBtn.disabled = false;
            submitBtn.innerText = 'Complete Profile & Enter';
        }
    });
}