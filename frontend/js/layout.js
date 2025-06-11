document.addEventListener('DOMContentLoaded', async () => {
    const pageBody = document.querySelector('body');
    const pageTemplate = document.querySelector('template');

    // If a page doesn't have a <template> tag, it doesn't use the base layout.
    if (!pageTemplate) return;
    
    const pageContent = pageTemplate.innerHTML;
    const pageTitle = document.title;

    try {
        const response = await fetch('/_base.html');
        if (!response.ok) throw new Error('Could not load base layout.');
        const baseHtml = await response.text();

        // Replace the entire document with the base layout's HTML
        document.documentElement.innerHTML = baseHtml;
        
        // Inject the unique content and title from the original page
        document.getElementById('main-content').innerHTML = pageContent;
        document.title = pageTitle;

        // Re-execute scripts from the loaded base template
        const scripts = Array.from(document.body.querySelectorAll('script'));
        for (const oldScript of scripts) {
            const newScript = document.createElement('script');
            // Copy all attributes (src, async, data-*, etc.)
            for (const attr of oldScript.attributes) {
                newScript.setAttribute(attr.name, attr.value);
            }
            // If the script has inline content, copy it
            if(oldScript.textContent) {
                newScript.textContent = oldScript.textContent;
            }
            // Append the new script to the body to execute it, then remove the old one
            oldScript.parentNode.appendChild(newScript);
            oldScript.remove();
        }
    } catch (error) {
        console.error("Layout loading failed:", error);
        pageBody.innerHTML = `<div class="alert alert-danger m-5">Error: The page layout could not be loaded. Please try refreshing.</div>`;
    }
});