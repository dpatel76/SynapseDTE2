// Frontend Console Test Script
// Run this in the browser console to check for errors

(function() {
    console.log('=== Frontend Console Test Started ===');
    
    let errorCount = 0;
    let warningCount = 0;
    let networkErrors = [];
    
    // Override console methods to capture errors
    const originalError = console.error;
    const originalWarn = console.warn;
    
    console.error = function(...args) {
        errorCount++;
        console.log('[TEST] Error captured:', ...args);
        originalError.apply(console, args);
    };
    
    console.warn = function(...args) {
        warningCount++;
        console.log('[TEST] Warning captured:', ...args);
        originalWarn.apply(console, args);
    };
    
    // Monitor network requests
    const originalFetch = window.fetch;
    window.fetch = function(...args) {
        return originalFetch.apply(this, args)
            .then(response => {
                if (response.status === 404) {
                    networkErrors.push({
                        url: args[0],
                        status: 404,
                        timestamp: new Date().toISOString()
                    });
                    console.error('[TEST] 404 Error:', args[0]);
                } else if (!response.ok) {
                    networkErrors.push({
                        url: args[0],
                        status: response.status,
                        timestamp: new Date().toISOString()
                    });
                }
                return response;
            })
            .catch(error => {
                networkErrors.push({
                    url: args[0],
                    error: error.message,
                    timestamp: new Date().toISOString()
                });
                throw error;
            });
    };
    
    // Test navigation function
    window.testNavigation = async function() {
        console.log('\n=== Testing Navigation ===');
        
        const testUrls = [
            '/phases/sample-selection',
            '/phases/scoping',
            '/phases/data-profiling'
        ];
        
        for (const url of testUrls) {
            console.log(`Navigating to ${url}...`);
            window.location.href = url;
            
            // Wait for page to load
            await new Promise(resolve => setTimeout(resolve, 2000));
            
            // Check for React errors
            const reactErrors = document.querySelectorAll('.error-boundary');
            if (reactErrors.length > 0) {
                console.error(`[TEST] React error boundary triggered on ${url}`);
            }
        }
    };
    
    // Summary function
    window.testSummary = function() {
        console.log('\n=== Test Summary ===');
        console.log(`Total Errors: ${errorCount}`);
        console.log(`Total Warnings: ${warningCount}`);
        console.log(`Network Errors: ${networkErrors.length}`);
        
        if (networkErrors.length > 0) {
            console.log('\nNetwork Error Details:');
            networkErrors.forEach(err => {
                console.log(`- ${err.url}: ${err.status || err.error} at ${err.timestamp}`);
            });
        }
        
        if (errorCount === 0 && networkErrors.filter(e => e.status === 404).length === 0) {
            console.log('\n✅ No errors or 404s detected!');
        } else {
            console.log('\n❌ Errors detected - please review above');
        }
    };
    
    console.log('Test setup complete. Use the following commands:');
    console.log('- testNavigation() - Test navigation through all phases');
    console.log('- testSummary() - Show test summary');
    console.log('\nMonitoring console for errors...');
})();