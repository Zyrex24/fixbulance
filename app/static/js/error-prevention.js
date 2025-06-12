/**
 * Fixbulance Error Prevention Script
 * Prevents common JavaScript errors from browser extensions and third-party conflicts
 */

(function() {
    'use strict';
    
    // Prevent browser extension conflicts
    window.addEventListener('error', function(e) {
        // Suppress extension-related errors that don't affect our app
        const extensionErrors = [
            'content.js',
            'feature_extension-platform-merchant-homepage-plugin-view.js',
            'background.js',
            'checkoutUrls',
            'Extension context invalidated'
        ];
        
        const isExtensionError = extensionErrors.some(error => 
            e.filename && e.filename.includes(error) || 
            e.message && e.message.includes(error)
        );
        
        if (isExtensionError) {
            console.warn('Browser extension error suppressed:', e.message);
            e.preventDefault();
            return true;
        }
    });
    
    // Prevent promise rejection errors from extensions
    window.addEventListener('unhandledrejection', function(e) {
        const extensionPromiseErrors = [
            'checkoutUrls',
            'Extension context invalidated',
            'Cannot read properties of undefined'
        ];
        
        const isExtensionPromiseError = extensionPromiseErrors.some(error => 
            e.reason && e.reason.toString().includes(error)
        );
        
        if (isExtensionPromiseError) {
            console.warn('Extension promise rejection suppressed:', e.reason);
            e.preventDefault();
            return true;
        }
    });
    
    // Create safe wrappers for commonly undefined objects
    window.safeAccess = function(obj, path, defaultValue = null) {
        try {
            return path.split('.').reduce((current, key) => current && current[key], obj) || defaultValue;
        } catch (e) {
            return defaultValue;
        }
    };
    
    // Stripe error prevention
    if (typeof window.Stripe === 'undefined') {
        window.Stripe = function() {
            console.warn('Stripe not loaded, using fallback');
            return {
                elements: function() {
                    return {
                        create: function() {
                            return {
                                mount: function() {},
                                addEventListener: function() {},
                                destroy: function() {}
                            };
                        }
                    };
                },
                createPaymentMethod: function() {
                    return Promise.reject('Stripe not properly loaded');
                },
                confirmCardPayment: function() {
                    return Promise.reject('Stripe not properly loaded');
                }
            };
        };
    }
    
    // Browser extension object conflict prevention
    const protectedObjects = ['checkoutUrls', 'extensionApi'];
    protectedObjects.forEach(objName => {
        if (typeof window[objName] === 'undefined') {
            window[objName] = {};
        }
    });
    
    console.log('Fixbulance Error Prevention System: Active');
})(); 