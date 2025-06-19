document.addEventListener('DOMContentLoaded', function() {
    // Mobile menu functionality
    const mobileMenuBtn = document.querySelector('.mobile-menu-btn');
    const navLinks = document.querySelector('.nav-links');

    if (mobileMenuBtn && navLinks) {
        mobileMenuBtn.addEventListener('click', function() {
            navLinks.classList.toggle('active');
            const isExpanded = navLinks.classList.contains('active');
            mobileMenuBtn.setAttribute('aria-expanded', isExpanded);
            
            // Animate hamburger icon
            const icon = mobileMenuBtn.querySelector('.material-symbols-rounded');
            if (icon) {
                icon.textContent = isExpanded ? 'close' : 'menu';
            }
        });

        // Close mobile menu when clicking outside
        document.addEventListener('click', function(e) {
            if (!mobileMenuBtn.contains(e.target) && !navLinks.contains(e.target)) {
                navLinks.classList.remove('active');
                mobileMenuBtn.setAttribute('aria-expanded', 'false');
                const icon = mobileMenuBtn.querySelector('.material-symbols-rounded');
                if (icon) {
                    icon.textContent = 'menu';
                }
            }
        });
    }

    // Smooth scrolling for anchor links
    const links = document.querySelectorAll('a[href^="#"]');
    
    links.forEach(link => {
        link.addEventListener('click', function(e) {
            e.preventDefault();
            
            const targetId = this.getAttribute('href');
            const targetSection = document.querySelector(targetId);
            
            if (targetSection) {
                targetSection.scrollIntoView({
                    behavior: 'smooth',
                    block: 'start'
                });
            }
        });
    });
});

// Scroll Animation System
class ScrollAnimations {
    constructor() {
        this.animatedElements = new Set();
        this.init();
    }
    
    init() {
        // Create intersection observer for scroll animations
        this.observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting && !this.animatedElements.has(entry.target)) {
                    this.animateElement(entry.target);
                    this.animatedElements.add(entry.target);
                }
            });
        }, {
            threshold: 0.1,
            rootMargin: '0px 0px -50px 0px'
        });
        
        // Observe all scroll-animate elements
        this.observeElements();
        
        // Add stagger animation for brand items
        this.setupBrandAnimations();
        
        // Add form animations
        this.setupFormAnimations();
    }
    
    observeElements() {
        const elements = document.querySelectorAll('.scroll-animate, .scroll-animate-left, .scroll-animate-right, .scroll-animate-scale');
        elements.forEach(el => this.observer.observe(el));
    }
    
    animateElement(element) {
        // Add animate class to trigger CSS transition
        element.classList.add('animate');
        
        // Handle special cases
        if (element.classList.contains('brand-logos')) {
            this.animateBrandItems(element);
        }
        
        if (element.classList.contains('services-section')) {
            this.animateServiceCards(element);
        }
        
        if (element.classList.contains('contact-section')) {
            this.animateContactSection(element);
        }
    }
    
    animateBrandItems(container) {
        const brandItems = container.querySelectorAll('.brand-item');
        brandItems.forEach((item, index) => {
            setTimeout(() => {
                item.classList.add('animate');
            }, index * 100);
        });
    }
    
    animateServiceCards(container) {
        const serviceCards = container.querySelectorAll('.service-card');
        serviceCards.forEach((card, index) => {
            setTimeout(() => {
                card.classList.add('animate');
            }, index * 200);
        });
    }
    
    animateContactSection(container) {
        const contactInfo = container.querySelector('.contact-info');
        const contactForm = container.querySelector('.contact-form');
        const formGroups = container.querySelectorAll('.form-group');
        
        if (contactInfo) {
            setTimeout(() => contactInfo.classList.add('animate'), 100);
        }
        
        if (contactForm) {
            setTimeout(() => contactForm.classList.add('animate'), 200);
        }
        
        formGroups.forEach((group, index) => {
            setTimeout(() => {
                group.classList.add('animate');
            }, 300 + (index * 100));
        });
    }
    
    setupBrandAnimations() {
        const brandItems = document.querySelectorAll('.brand-item');
        brandItems.forEach(item => {
            item.addEventListener('mouseenter', function() {
                this.style.transform = 'translateY(-5px) scale(1.05)';
            });
            
            item.addEventListener('mouseleave', function() {
                if (this.classList.contains('animate')) {
                    this.style.transform = 'translateY(0) scale(1)';
                }
            });
        });
    }
    
    setupFormAnimations() {
        const formInputs = document.querySelectorAll('.form-group select, .form-group input');
        formInputs.forEach(input => {
            input.addEventListener('focus', function() {
                this.parentElement.style.transform = 'scale(1.02)';
                this.style.boxShadow = '0 4px 15px rgba(255, 0, 0, 0.1)';
            });
            
            input.addEventListener('blur', function() {
                this.parentElement.style.transform = 'scale(1)';
                this.style.boxShadow = 'none';
            });
        });
    }
}

// Page Loading Animation
class PageLoader {
    constructor() {
        this.init();
    }
    
    init() {
        // Create loading overlay
        this.createLoadingOverlay();
        
        // Hide loading overlay when page is loaded
        window.addEventListener('load', () => {
            setTimeout(() => {
                this.hideLoadingOverlay();
            }, 500);
        });
    }
    
    createLoadingOverlay() {
        const overlay = document.createElement('div');
        overlay.className = 'loading-overlay';
        overlay.innerHTML = '<div class="loading-spinner"></div>';
        document.body.appendChild(overlay);
    }
    
    hideLoadingOverlay() {
        const overlay = document.querySelector('.loading-overlay');
        if (overlay) {
            overlay.classList.add('fade-out');
            setTimeout(() => {
                overlay.remove();
            }, 500);
        }
    }
}

// Button Animations
class ButtonAnimations {
    constructor() {
        this.init();
    }
    
    init() {
        this.setupButtonHovers();
        this.setupButtonClicks();
    }
    
    setupButtonHovers() {
        const buttons = document.querySelectorAll('.btn-primary, .btn-secondary');
        buttons.forEach(button => {
            button.addEventListener('mouseenter', function() {
                this.style.transform = 'translateY(-2px)';
                this.style.boxShadow = '0 8px 25px rgba(0, 0, 0, 0.15)';
            });
            
            button.addEventListener('mouseleave', function() {
                this.style.transform = 'translateY(0)';
                this.style.boxShadow = '0 4px 15px rgba(0, 0, 0, 0.1)';
            });
        });
    }
    
    setupButtonClicks() {
        const buttons = document.querySelectorAll('.btn-primary, .btn-secondary');
        buttons.forEach(button => {
            button.addEventListener('click', function(e) {
                // Create ripple effect
                const ripple = document.createElement('span');
                const rect = this.getBoundingClientRect();
                const size = Math.max(rect.width, rect.height);
                const x = e.clientX - rect.left - size / 2;
                const y = e.clientY - rect.top - size / 2;
                
                ripple.style.cssText = `
                    position: absolute;
                    width: ${size}px;
                    height: ${size}px;
                    left: ${x}px;
                    top: ${y}px;
                    background: rgba(255, 255, 255, 0.3);
                    border-radius: 50%;
                    transform: scale(0);
                    animation: ripple 0.6s ease-out;
                    pointer-events: none;
                `;
                
                this.appendChild(ripple);
                
                setTimeout(() => {
                    ripple.remove();
                }, 600);
            });
        });
    }
}

// Navbar Scroll Effects
class NavbarEffects {
    constructor() {
        this.navbar = document.querySelector('.navbar');
        this.init();
    }
    
    init() {
        if (!this.navbar) return;
        
        window.addEventListener('scroll', () => {
            this.handleScroll();
        });
        
        this.setupNavLinkHovers();
    }
    
    handleScroll() {
        const scrollY = window.scrollY;
        
        if (scrollY > 100) {
            this.navbar.style.background = 'rgba(255, 255, 255, 0.95)';
            this.navbar.style.backdropFilter = 'blur(10px)';
            this.navbar.style.boxShadow = '0 2px 20px rgba(0, 0, 0, 0.1)';
        } else {
            this.navbar.style.background = 'var(--color-white)';
            this.navbar.style.backdropFilter = 'none';
            this.navbar.style.boxShadow = '0 2px 10px rgba(0, 0, 0, 0.1)';
        }
    }
    
    setupNavLinkHovers() {
        const navLinks = document.querySelectorAll('.nav-link');
        navLinks.forEach(link => {
            link.addEventListener('mouseenter', function() {
                const underline = this.querySelector('::after') || this;
                this.style.color = 'var(--color-red)';
            });
            
            link.addEventListener('mouseleave', function() {
                this.style.color = '';
            });
        });
    }
}

// Device Placeholder Animation
class DeviceAnimation {
    constructor() {
        this.device = document.querySelector('.device-placeholder');
        this.init();
    }
    
    init() {
        if (!this.device) return;
        
        // Add floating animation after hero animations complete
        setTimeout(() => {
            this.device.style.animation = 'float 3s ease-in-out infinite';
        }, 1000);
        
        // Add interactive hover effect
        this.device.addEventListener('mouseenter', function() {
            this.style.transform = 'translateY(-10px) scale(1.05)';
            this.style.transition = 'all 0.3s ease';
        });
        
        this.device.addEventListener('mouseleave', function() {
            this.style.transform = '';
            this.style.transition = '';
        });
    }
}

// Initialize all animations when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    // Initialize all animation systems
    new PageLoader();
    new ScrollAnimations();
    new ButtonAnimations();
    new NavbarEffects();
    new DeviceAnimation();
    
    // Add CSS for ripple animation
    const style = document.createElement('style');
    style.textContent = `
        @keyframes ripple {
            to {
                transform: scale(2);
                opacity: 0;
            }
        }
    `;
    document.head.appendChild(style);
});

// Performance optimization: Throttle scroll events
function throttle(func, limit) {
    let inThrottle;
    return function() {
        const args = arguments;
        const context = this;
        if (!inThrottle) {
            func.apply(context, args);
            inThrottle = true;
            setTimeout(() => inThrottle = false, limit);
        }
    }
}

// Add smooth reveal animation for images when they load
document.addEventListener('DOMContentLoaded', function() {
    const images = document.querySelectorAll('img');
    images.forEach(img => {
        if (img.complete) {
            img.style.opacity = '1';
        } else {
            img.style.opacity = '0';
            img.style.transition = 'opacity 0.5s ease';
            img.addEventListener('load', function() {
                this.style.opacity = '1';
            });
        }
    });
}); 