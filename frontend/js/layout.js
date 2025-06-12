document.addEventListener('DOMContentLoaded', async () => {
    const pageBody = document.querySelector('body');
    const pageTemplate = document.querySelector('template');
    if (!pageTemplate) return;
    
    const pageContent = pageTemplate.innerHTML;
    const pageTitle = document.title;
    try {
        const response = await fetch('/_base.html');
        if (!response.ok) throw new Error('Could not load base layout.');
        const baseHtml = await response.text();
        document.documentElement.innerHTML = baseHtml;
        document.getElementById('main-content').innerHTML = pageContent;
        document.title = pageTitle;
        const scripts = Array.from(document.body.querySelectorAll('script'));
        for (const oldScript of scripts) {
            const newScript = document.createElement('script');
            for (const attr of oldScript.attributes) {
                newScript.setAttribute(attr.name, attr.value);
            }
            if(oldScript.textContent) newScript.textContent = oldScript.textContent;
            oldScript.parentNode.appendChild(newScript);
            oldScript.remove();
        }
    } catch (error) {
        console.error("Layout loading failed:", error);
    }
});