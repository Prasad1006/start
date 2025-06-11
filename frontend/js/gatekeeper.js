async function enforceOnboarding() {
    const Clerk = window.Clerk;
    if (!Clerk.user) return; // Not logged in, do nothing.

    const allowedOnboardingPages = [
        '/onboarding-profile.html',
        '/onboarding-domains.html',
        '/onboarding-skills.html'
    ];
    const currentPage = window.location.pathname;

    try {
        const token = await Clerk.session.getToken();
        const response = await fetch('/api/users/onboarding-status', {
            headers: { 'Authorization': 'Bearer ' + token }
        });
        
        if (!response.ok) throw new Error("Could not check onboarding status.");
        const data = await response.json();

        if (data.status === 'pending' && !allowedOnboardingPages.includes(currentPage)) {
            window.location.href = '/onboarding-profile.html';
        } else if (data.status === 'completed' && allowedOnboardingPages.includes(currentPage)) {
            window.location.href = '/dashboard.html';
        }
    } catch (error) {
        console.error("Gatekeeper check failed:", error);
    }
}