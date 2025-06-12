<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Dashboard - Learn N Teach</title>
</head>
<body>
    <template>
        <div class="container py-4">
            <div class="d-flex justify-content-between align-items-center mb-4">
                <h1 id="welcome-message" class="fw-light">Loading...</h1>
                <div class="d-flex align-items-center">
                    <span class="fw-bold me-2 text-muted">My Points:</span>
                    <span id="user-points" class="badge bg-success fs-5">...</span>
                </div>
            </div>

            <div id="dashboard-content">
                <h2 class="h4 border-bottom pb-2 mb-4">My Learning Roadmaps</h2>
                <div id="learning-tracks-container" class="row">
                    <!-- The loading spinner that shows initially -->
                    <div class="text-center p-5"><div class="spinner-border text-primary" role="status"></div></div>
                </div>
            </div>
        </div>
    </template>
    

    <script src="/js/layout.js"></script>

  
    <script src="/js/dashboard.js"></script>
    
   
    <script>
        // This function is automatically called by navigation.js once Clerk is ready.
        function onClerkReady() {
             if (window.Clerk && window.Clerk.user) {
                // By the time this runs, dashboard.js has been loaded and parsed,
                // so the initializeDashboard function is guaranteed to exist.
                initializeDashboard(window.Clerk);
            }
        }
    </script>
</body>
</html>