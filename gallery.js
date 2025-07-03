// ...move all JS from <script>...</script> here...

// ===== GALLERY INITIALIZATION =====

let gallerySwiper = null;
let galleryImages = [];
let currentLightboxIndex = 0;
let isLightboxOpen = false;

/**
 * REQUIREMENT 5: Initialize gallery with autoplay and enhanced swipe
 * REQUIREMENT 4: Setup CSS transforms with opacity and blur effects
 * REQUIREMENT 1: Configure captions only for center image
 */
function initGallery() {
    console.log('🎨 Initializing Enhanced BSP Gallery...');

    if (typeof Swiper === 'undefined') {
        console.error('❌ Swiper library not loaded');
        setTimeout(initGallery, 1000);
        return;
    }

    try {
        // Collect gallery images data first
        collectGalleryImages();

        // REQUIREMENT 5: Initialize Swiper with autoplay and enhanced swipe
        gallerySwiper = new Swiper('.gallery-swiper', {
            // Use coverflow effect for 3D transforms
            effect: 'coverflow',
            grabCursor: true,
            centeredSlides: true,
            slidesPerView: 'auto',

            // REQUIREMENT 4: Coverflow settings for angled previews
            coverflowEffect: {
                rotate: 20,          // Angle for side images
                stretch: 0,
                depth: 200,          // 3D depth
                modifier: 1,
                slideShadows: true,
                scale: 0.8,          // Scale for side images
            },

            // REQUIREMENT 5: Enhanced autoplay with swipe
            loop: true,
            speed: 800,
            autoplay: {
                delay: 4000,
                disableOnInteraction: false,
                pauseOnMouseEnter: true,
                waitForTransition: true,
            },

            // Spacing between slides
            spaceBetween: 60,

            // Navigation
            navigation: {
                nextEl: '#galleryNext',
                prevEl: '#galleryPrev',
            },

            // Pagination
            pagination: {
                el: '#galleryPagination',
                clickable: true,
                dynamicBullets: true,
            },

            // REQUIREMENT 5: Enhanced touch/swipe settings
            touchRatio: 1,
            touchAngle: 45,
            allowTouchMove: true,
            resistanceRatio: 0.85,

            // Responsive breakpoints
            breakpoints: {
                320: {
                    coverflowEffect: { rotate: 15, depth: 150, scale: 0.75 },
                    spaceBetween: 40,
                },
                768: {
                    coverflowEffect: { rotate: 18, depth: 175, scale: 0.8 },
                    spaceBetween: 50,
                },
                1024: {
                    coverflowEffect: { rotate: 20, depth: 200, scale: 0.8 },
                    spaceBetween: 60,
                }
            },

            // Event callbacks
            on: {
                init: function () {
                    console.log('✅ Enhanced Gallery Swiper initialized');
                    setTimeout(() => {
                        setupLightboxTriggers();
                        updateSlideVisuals();
                    }, 100);
                },

                slideChange: function () {
                    console.log('🔄 Slide changed to:', this.activeIndex);
                    updateSlideVisuals();
                },

                // REQUIREMENT 5: Autoplay control on interaction
                touchStart: function () {
                    this.autoplay.stop();
                },

                touchEnd: function () {
                    setTimeout(() => {
                        if (!isLightboxOpen) {
                            this.autoplay.start();
                        }
                    }, 2000);
                }
            },

            // Keyboard navigation
            keyboard: {
                enabled: true,
                onlyInViewport: true,
            },

            // Mouse wheel control
            mousewheel: {
                thresholdDelta: 70,
                sensitivity: 1,
            },
        });

        console.log('🎉 Enhanced BSP Gallery initialized successfully');

    } catch (error) {
        console.error('❌ Error initializing gallery:', error);
    }
}

/**
 * Collect gallery images data for lightbox functionality
 */
function collectGalleryImages() {
    const slides = document.querySelectorAll('.gallery-slide');
    galleryImages = [];

    slides.forEach((slide, index) => {
        let imageUrl = slide.getAttribute('data-image') ||
            slide.style.backgroundImage.match(/url\(["']?([^"']*)["']?\)/)?.[1] || '';
        // Fallback: if imageUrl is missing or blank, use a placeholder
        if (!imageUrl) {
            console.warn(`⚠️ Gallery slide ${index + 1} is missing an image. Using placeholder.`);
            imageUrl = 'https://via.placeholder.com/450x550?text=Image+Not+Found';
            slide.style.backgroundImage = `url('${imageUrl}')`;
        }
        galleryImages.push({
            image: imageUrl,
            title: slide.getAttribute('data-title') || `Image ${index + 1}`,
            description: slide.getAttribute('data-description') || '',
            element: slide,
            index: index
        });
    });

    console.log('📷 Collected gallery images:', galleryImages.length);
}

/**
 * REQUIREMENT 2: Setup enhanced lightbox triggers with better click detection
 */
function setupLightboxTriggers() {
    const slides = document.querySelectorAll('.gallery-slide');
    console.log('🔗 Setting up enhanced lightbox triggers');

    slides.forEach((slide, index) => {
        // Enhanced click event
        slide.addEventListener('click', function (e) {
            e.preventDefault();
            e.stopPropagation();
            console.log('🖱️ Image clicked:', index);
            openLightbox(index);
        }, { passive: false });

        // Keyboard accessibility
        slide.addEventListener('keydown', function (e) {
            if (e.key === 'Enter' || e.key === ' ') {
                e.preventDefault();
                openLightbox(index);
            }
        });

        // Enhanced hover effects
        slide.addEventListener('mouseenter', function () {
            if (!isLightboxOpen && this.classList.contains('swiper-slide-active')) {
                this.style.transform += ' scale(1.02)';
            }
        });

        slide.addEventListener('mouseleave', function () {
            if (!isLightboxOpen && this.classList.contains('swiper-slide-active')) {
                this.style.transform = this.style.transform.replace(' scale(1.02)', '');
            }
        });
    });

    console.log('✅ Enhanced lightbox triggers setup complete');
}

/**
 * REQUIREMENT 1 & 4: Update slide visuals with opacity, blur, and caption display
 */
function updateSlideVisuals() {
    const slides = document.querySelectorAll('.gallery-slide');

    slides.forEach(slide => {
        const content = slide.querySelector('.gallery-slide-content');

        if (slide.classList.contains('swiper-slide-active')) {
            // REQUIREMENT 1: Show content only on active slide
            if (content) {
                setTimeout(() => {
                    content.style.transform = 'translateY(0)';
                    content.style.opacity = '1';
                }, 400);
            }
        } else {
            // REQUIREMENT 1: Hide content on non-active slides
            if (content) {
                content.style.transform = 'translateY(100%)';
                content.style.opacity = '0';
            }
        }
    });
    updateGalleryImageCount();
}

// ===== LIGHTBOX FUNCTIONALITY - REQUIREMENT 2 =====

/**
 * REQUIREMENT 2: Enhanced lightbox with centered image, title, and description
 */
function openLightbox(index) {
    console.log('🔍 Opening enhanced lightbox for image:', index);

    if (!galleryImages[index]) {
        console.error('❌ No image data found for index:', index);
        return;
    }

    isLightboxOpen = true;
    currentLightboxIndex = index;
    const imageData = galleryImages[index];

    // Update lightbox content
    const lightboxImage = document.getElementById('lightboxImage');
    const lightboxTitle = document.getElementById('lightboxTitle');
    const lightboxDescription = document.getElementById('lightboxDescription');
    const lightbox = document.getElementById('galleryLightbox');

    if (lightboxImage && lightboxTitle && lightboxDescription && lightbox) {
        // Set loading state
        lightboxImage.style.opacity = '0.5';
        lightboxImage.src = imageData.image;
        lightboxImage.alt = imageData.title;

        // Handle image load
        lightboxImage.onload = function () {
            this.style.opacity = '1';
            console.log('✅ Lightbox image loaded');
        };

        lightboxImage.onerror = function () {
            console.error('❌ Failed to load lightbox image');
            this.src = 'data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iNDAwIiBoZWlnaHQ9IjMwMCIgdmlld0JveD0iMCAwIDQwMCAzMDAiIGZpbGw9Im5vbmUiIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyI+CjxyZWN0IHdpZHRoPSI0MDAiIGhlaWdodD0iMzAwIiBmaWxsPSIjZjBmMGYwIi8+Cjx0ZXh0IHg9IjIwMCIgeT0iMTUwIiB0ZXh0LWFuY2hvcj0ibWlkZGxlIiBmaWxsPSIjOTk5Ij5JbWFnZSBOb3QgQXZhaWxhYmxlPC90ZXh0Pgo8L3N2Zz4=';
            this.style.opacity = '1';
        };

        // REQUIREMENT 2: Set title and description
        lightboxTitle.textContent = imageData.title;
        lightboxDescription.textContent = imageData.description;

        // Show lightbox with animation
        lightbox.style.display = 'flex';
        setTimeout(() => {
            lightbox.classList.add('active');
        }, 10);

        // Prevent body scroll
        document.body.style.overflow = 'hidden';

        // Pause gallery autoplay
        if (gallerySwiper && gallerySwiper.autoplay) {
            gallerySwiper.autoplay.stop();
        }

        console.log('✅ Enhanced lightbox opened');
    }
}

/**
 * Close lightbox and resume gallery
 */
function closeLightbox() {
    console.log('❌ Closing lightbox');

    isLightboxOpen = false;
    const lightbox = document.getElementById('galleryLightbox');

    if (lightbox) {
        lightbox.classList.remove('active');

        setTimeout(() => {
            lightbox.style.display = 'none';
        }, 400);

        document.body.style.overflow = '';

        // REQUIREMENT 5: Resume autoplay
        if (gallerySwiper && gallerySwiper.autoplay) {
            setTimeout(() => {
                gallerySwiper.autoplay.start();
            }, 1000);
        }

        console.log('✅ Lightbox closed, autoplay resumed');
    }
}

/**
 * Navigate to previous image in lightbox
 */
function lightboxPrevious() {
    currentLightboxIndex = (currentLightboxIndex - 1 + galleryImages.length) % galleryImages.length;
    openLightbox(currentLightboxIndex);
}

/**
 * Navigate to next image in lightbox
 */
function lightboxNext() {
    currentLightboxIndex = (currentLightboxIndex + 1) % galleryImages.length;
    openLightbox(currentLightboxIndex);
}

// ===== EVENT LISTENERS =====

/**
 * Setup enhanced lightbox event listeners
 */
function setupLightboxEvents() {
    console.log('🔧 Setting up enhanced lightbox events');

    // Close button
    const closeBtn = document.getElementById('lightboxClose');
    if (closeBtn) {
        closeBtn.addEventListener('click', function (e) {
            e.stopPropagation();
            closeLightbox();
        });
    }

    // Navigation buttons
    const prevBtn = document.getElementById('lightboxPrev');
    const nextBtn = document.getElementById('lightboxNext');

    if (prevBtn) {
        prevBtn.addEventListener('click', function (e) {
            e.stopPropagation();
            lightboxPrevious();
        });
    }

    if (nextBtn) {
        nextBtn.addEventListener('click', function (e) {
            e.stopPropagation();
            lightboxNext();
        });
    }

    // Click outside to close
    const lightbox = document.getElementById('galleryLightbox');
    if (lightbox) {
        lightbox.addEventListener('click', function (e) {
            if (e.target === this) {
                closeLightbox();
            }
        });
    }

    // Enhanced keyboard navigation
    document.addEventListener('keydown', function (e) {
        if (isLightboxOpen) {
            switch (e.key) {
                case 'Escape':
                    e.preventDefault();
                    closeLightbox();
                    break;
                case 'ArrowLeft':
                    e.preventDefault();
                    lightboxPrevious();
                    break;
                case 'ArrowRight':
                    e.preventDefault();
                    lightboxNext();
                    break;
            }
        }
    });

    console.log('✅ Enhanced lightbox events setup complete');
}

// ===== ADDITIONAL FUNCTIONALITY =====

/**
 * Handle responsive updates
 */
function handleResize() {
    if (gallerySwiper) {
        gallerySwiper.update();
        updateSlideVisuals();
    }
}

/**
 * REQUIREMENT 5: Handle visibility changes for autoplay
 */
function handleVisibilityChange() {
    if (gallerySwiper) {
        if (document.hidden) {
            gallerySwiper.autoplay.stop();
        } else if (!isLightboxOpen) {
            gallerySwiper.autoplay.start();
        }
    }
}

// Remove image count display
function updateGalleryImageCount() {
    const counter = document.getElementById('gallery-image-counter');
    if (counter && counter.parentNode) {
        counter.parentNode.removeChild(counter);
    }
}

// ===== LANGUAGE SUPPORT =====

/**
 * Update gallery content for different languages using window.galleryTranslations
 * This function should be called after switching languages.
 */
function updateGalleryContent() {
    const titleElement = document.getElementById('gallery-title');
    const descElement = document.getElementById('gallery-description');
    if (window.galleryTranslations) {
        if (titleElement) titleElement.textContent = window.galleryTranslations.title;
        if (descElement) descElement.textContent = window.galleryTranslations.description;
    }
}

// ===== LANGUAGE SWITCHER SUPPORT =====
window.switchLanguage = function(lang) {
    // Remove all language script tags except Swiper, main.js, and gallery.js
    const scripts = document.querySelectorAll('script[data-lang]');
    scripts.forEach(s => s.remove());

    // Dynamically load the selected language file
    const script = document.createElement('script');
    script.src = lang + '.js';
    script.setAttribute('data-lang', lang);
    script.onload = function() {
        if (typeof updatePageContent === 'function') updatePageContent();
        if (typeof updateGalleryContent === 'function') updateGalleryContent();
    };
    document.body.appendChild(script);

    // Update active button UI
    document.querySelectorAll('.lang-btn').forEach(btn => btn.classList.remove('active'));
    const btn = document.getElementById('btn-' + lang);
    if (btn) btn.classList.add('active');
};

// ===== INITIALIZATION =====

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', function () {
    console.log('🚀 Initializing Enhanced BSP Gallery...');

    setupLightboxEvents();

    setTimeout(() => {
        initGallery();
        updateGalleryImageCount();
    }, 100);

    // Setup event listeners
    window.addEventListener('resize', handleResize);
    document.addEventListener('visibilitychange', handleVisibilityChange);
});

// Export functions for global access
window.initGallery = initGallery;
window.updateGalleryContent = updateGalleryContent;
window.openLightbox = openLightbox;
window.closeLightbox = closeLightbox;

console.log('🎉 Enhanced BSP Gallery Script Loaded Successfully');
