document.addEventListener('DOMContentLoaded', async () => {
    const pageBody = document.querySelector('body');
    const pageTemplate = document.querySelector('template');

    if (!pageTemplate) return;
    
    const pageContent = pageTemplate.innerHTML;
    const pageTitle = document.title;
    
    // Find the specific script for this page
    const pageScriptTag = document.querySelector('script[data-page-script]');

    try {
        const response = await fetch('/_base.html');
        if (!response.ok) throw new Error('Could not load base layout.');
        const baseHtml = await response.text();

        document.documentElement.innerHTML = baseHtml;
        
        document.getElementById('main-content').innerHTML = pageContent;
        document.title = pageTitle;

        // This is the core logic change.
        // The main Clerk loader in _base.html now takes full responsibility.
        // We will define a generic function that it can call.
        if (pageScriptTag && window.Clerk) {
             Clerk.addListener(({ user }) => {
                if (user) {
                    // Check which page-specific initializer function exists and call it.
                    if (typeof initializeDashboard === 'function') {
                        initializeDashboard(Clerk);
                    } else if (typeof initializeProfilePage === 'function') {
                        initializeProfilePage(Clerk);
                    }
                    // Add other initializers here for other pages like profile.js
                }
            });
        }

        // Re-run the main script loader from the new base template
        const clerkScript = document.body.querySelector('script[data-clerk-script]');
        if (clerkScript) {
            const newClerkScript = document.createElement('script');
            for (const attr of clerkScript.attributes) {
                newClerkScript.setAttribute(attr.name, attr.value);
            }
            clerkScript.parentNode.appendChild(newClerkScript);
            clerkScript.remove();
        }

    } catch (error) {
        console.error("Layout loading failed:", error);
        pageBody.innerHTML = `<div class="alert alert-danger m-5">Error: The page layout could not be loaded. Please try refreshing.</div>`;
    }
});

// We are moving the Clerk listener logic to be more centralized.
// Let's adjust navigation.js to only handle the UI parts.