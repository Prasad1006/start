/**
 * This script acts as the "gatekeeper" for the entire application.
 * It runs on every page and ensures that users who have not completed onboarding
 * cannot access protected pages like the dashboard.
 */
async function enforceOnboarding() {
    const Clerk = window.Clerk;

    // Wait until Clerk is fully loaded and has a session.
    await Clerk.load();

    // The pages that a logged-in but non-onboarded user IS allowed to see.
    const allowedOnboardingPages = [
        '/onboarding-profile.html',
        '/onboarding-domains.html',
        '/onboarding-skills.html'
    ];

    const currentPage = window.location.pathname;

    // If the user is logged in, we need to check their status.
    if (Clerk.user) {
        try {
            const token = await Clerk.session.getToken();
            const response = await fetch('/api/users/onboarding-status', {
                headers: { 'Authorization': 'Bearer ' + token }
            });
            
            if (!response.ok) {
                // If the check fails, we can't be sure, so we do nothing for now.
                // An error will be logged in the console.
                throw new Error("Could not check onboarding status.");
            }

            const data = await response.json();

            // SCENARIO A: The user is logged in, but their profile is PENDING.
            if (data.status === 'pending') {
                // If they are NOT on one of the allowed onboarding pages, force them there.
                if (!allowedOnboardingPages.includes(currentPage)) {
                    window.location.href = '/onboarding-profile.html';
                }
            }
            
            // SCENARIO B: The user is logged in, and their profile is COMPLETED.
            if (data.status === 'completed') {
                // If a completed user somehow lands on an onboarding page, send them to the dashboard.
                if (allowedOnboardingPages.includes(currentPage)) {
                    window.location.href = '/dashboard.html';
                }
            }

        } catch (error) {
            console.error("Gatekeeper check failed:", error);
            // Optional: You could show an error message to the user here.
        }
    }
    // If the user is not logged in, this script does nothing.
    // The individual pages (like dashboard.js) will handle redirecting them to login.
}