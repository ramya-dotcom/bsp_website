/*
 * =====================================================
 * BAHUJAN SAMAJ PARTY WEBSITE - MAIN JAVASCRIPT (FIXED)
 * =====================================================
 * Main functionality for the BSP political party website
 * Handles navigation, timeline, events, and core features
 */

// ===== GLOBAL VARIABLES =====
let currentPage = 'main';
let currentScrollPosition = 0;
let currentTimelineYear = '1988';
let timelineSwiper = null;
let currentLanguage = 'english';
let languageContent = {};

// Timeline Data structure
const timelineData = [
    {
        year: 1988,
        title: "Political Foundation Campaign",
        description: "Manyavar Kanshi Ram campaigns as BSP's 3rd Party candidate for Parliament in Uttar Pradesh, marking the beginning of serious electoral politics for the party.",
        image: "assets/timeline/1988.jpg",
        // portrait: "assets/1988.jpg"
    },
    {
        year: 1991,
        title: "Commitment to Dalit Rights",
        description: "Behen Kumari. Mayawati appears publicly with the statue of Babasaheb Dr. Bhimrao Ambedkar, symbolizing the party's unwavering commitment to Dalit rights and social justice.",
        image: "assets/timeline/1991.jpg",
        // portrait: "assets/1991.jpg"
    },
        {
        year: 1995,
        title: "First Chief Minister Term",
        description: "Behen Kumari. Mayawati becomes Chief Minister of Uttar Pradesh for the first time, appearing with prominent leaders including Manyavar Kanshi Ram, Inder Kumar Gujral, and KR Narayanan.",
        image: "assets/timeline/1995.jpg",
        // portrait: "assets/1997.jpg"
    },
    {
        year: 1997,
        title: "Second Chief Minister Term",
        description: "Placeholder description.",
        image: "assets/timeline/1997.jpg",
        // portrait: "assets/1995.jpg"
    },
    {
        year: 1998,
        title: "National Party Status",
        description: "BSP is declared a national party in the presence of Prime Minister Inder Kumar Gujral, establishing its significance in Indian politics.",
        image: "assets/timeline/1998.jpg",
        // portrait: "assets/1998.jpg"
    },
    {
        year: 2001,
        title: "Massive Delhi Rally",
        description: "Historic BSP rally at Ramlila Grounds in Delhi with Manyavar Kanshi Ram and Behen Kumari. Mayawati, demonstrating the party's growing national influence and mass appeal.",
        image: "assets/timeline/2001.jpg",
        // portrait: "assets/2001.jpg"
    },
    {
        year: 2002,
        title: "Third Term as Chief Minister",
        description: "Behen Kumari. Mayawati becomes CM of Uttar Pradesh again with BJP's support, demonstrating strategic political alliances for governance.",
        image: "assets/timeline/2002.jpg",
        // portrait: "assets/2002.jpg"
    },
    {
        year: 2006,
        title: "Golden Jubilee Celebration",
        description: "Behen Kumari. Mayawati celebrates her 50th birthday with Manyavar Kanshi Ram in New Delhi, marking a significant personal and political milestone.",
        image: "assets/timeline/2006.jpg",
        // portrait: "assets/2006.jpg"
    },
    {
        year: 2007,
        title: "Historic Absolute Majority",
        description: "Behen Kumari. Mayawati wins absolute majority and becomes CM of UP again for the 4th term, taking oath in Lucknow in a landmark political victory.",
        image: "assets/timeline/2007.jpg",
        // portrait: "assets/2007.jpg"
    },
    {
        year: 2008,
        title: "Sarv Samaj Bhaichara Rally",
        description: "Massive rally in Delhi, meetings with Left leaders, and unveiling of statues at Noida's Dalit Prerna Sthal, showcasing party's cultural initiatives.",
        image: "assets/timeline/2008.jpg",
        // portrait: "assets/2008.jpg"
    },
    {
        year: 2009,
        title: "Lok Sabha Campaign",
        description: "Behen Kumari. Mayawati campaigns extensively for Lok Sabha elections with public rallies at Ramlila Grounds and across UP, strengthening democratic participation.",
        image: "assets/timeline/2009.jpg",
        // portrait: "assets/2009.jpg"
    },
    {
        year: 2012,
        title: "Democratic Participation",
        description: "Votes in Lucknow during UP Assembly elections, symbolizing democratic participation and peaceful transfer of power.",
        image: "assets/timeline/2012.jpg",
        // portrait: "assets/2012.jpg"
    },
    {
        year: 2015,
        title: "Parliamentary Presence",
        description: "Behen Kumari. Mayawati attends Monsoon Session of Parliament and responds publicly to RSS Chief's comments on reservation, defending constitutional rights.",
        image: "assets/timeline/2015.jpg",
        // portrait: "assets/2015.jpg"
    },
    {
        year: 2016,
        title: "Ambedkar Anniversary Rally",
        description: "Massive rally in Lucknow on 61st death anniversary of Dr. Ambedkar, with party review meetings to prepare for 2017 elections.",
        image: "assets/timeline/2016.jpg",
        // portrait: "assets/2016.jpg"
    },
    {
        year: 2017,
        title: "Electoral Campaign",
        description: "Behen Kumari. Mayawati waves at supporters in Allahabad ahead of UP Assembly elections, continuing the democratic struggle for representation.",
        image: "assets/timeline/2017.jpg",
        // portrait: "assets/2017.jpg"
    },
    {
        year: 2018,
        title: "Opposition Unity",
        description: "Behen Kumari. Mayawati joins opposition leaders including Rahul Gandhi, Sonia Gandhi, and Kejriwal at Kumaraswamy's oath ceremony in Karnataka.",
        image: "assets/timeline/2018.jpg",
        // portrait: "assets/2018.jpg"
    },
    {
        year: 2019,
        title: "Strategic Alliance",
        description: "Joint rally with Akhilesh Yadav (SP) and Ajit Singh (RLD) in Varanasi before Lok Sabha elections, demonstrating coalition politics for social justice.",
        image: "assets/timeline/2019.jpg",
        // portrait: "assets/2019.jpg"
    }
];

// ===== LANGUAGE PERSISTENCE FUNCTIONS =====

/**
 * Save current language to localStorage for persistence
 * @param {string} language - Language to save
 */
function saveLanguagePreference(language) {
    try {
        localStorage.setItem('bsp_preferred_language', language);
        console.log('Language preference saved:', language);
    } catch (error) {
        console.warn('Could not save language preference:', error);
    }
}

/**
 * Load language preference from localStorage
 * @returns {string} - Saved language or default 'english'
 */
function loadLanguagePreference() {
    try {
        const savedLanguage = localStorage.getItem('bsp_preferred_language');
        return savedLanguage || 'english';
    } catch (error) {
        console.warn('Could not load language preference:', error);
        return 'english';
    }
}

/**
 * Check if we're currently viewing an event detail page
 * @returns {string|null} - Event ID if in detail page, null otherwise
 */
function getCurrentEventId() {
    const eventDetailPage = document.getElementById('eventDetailPage');
    if (eventDetailPage && eventDetailPage.classList.contains('active')) {
        if (currentPage && currentPage.includes('Detail')) {
            // Remove 'events/' prefix if present
            let eventId = currentPage;
            if (eventId.startsWith('events/')) {
                eventId = eventId.replace('events/', '');
            }
            // Remove 'Detail' suffix
            eventId = eventId.replace('Detail', '');
            return eventId;
        }
    }
    return null;
}

/**
 * Check if we're currently viewing FAQ page
 * @returns {boolean} - True if in FAQ page
 */
function isInFAQPage() {
    const faqPage = document.getElementById('faqPage');
    return faqPage && faqPage.classList.contains('active');
}

/**
 * Ensure current language content is maintained across navigation
 * This function checks if the correct language is loaded and reloads if necessary
 */
function ensureLanguageConsistency() {
    console.log('Ensuring language consistency. Current language:', currentLanguage);
    
    // If we're in English, make sure English content is loaded
    if (currentLanguage === 'english') {
        if (!languageContent || !languageContent.nav || languageContent.nav.logoText !== "BAHUJAN SAMAJ PARTY") {
            console.log('English content missing or incorrect, reloading English content');
            languageContent = getEnglishContent();
            // Set gallery translations for gallery.js
            window.galleryTranslations = {
                title: languageContent.gallery?.title || "Photo Gallery",
                description: languageContent.gallery?.description || "Explore BSP's journey through powerful moments and historic achievements"
            };
            updatePageContent();
            if (typeof updateGalleryContent === 'function') updateGalleryContent();
        } else {
            updatePageContent();
        }
    }
    // If we're not in English and don't have the correct language content loaded
    else if (!languageContent || !languageContent.nav || languageContent.nav.logoText === "BAHUJAN SAMAJ PARTY") {
        console.log('Non-English language content missing, reloading language:', currentLanguage);
        switchLanguage(currentLanguage, true); // true flag for internal call
        return; // switchLanguage will handle the rest
    } else {
        // Update page with current content
        updatePageContent();
    }
    
    // Check if we're in an event detail page and update it
    const currentEventId = getCurrentEventId();
    if (currentEventId) {
        console.log('Updating event detail page for event:', currentEventId);
        updateEventDetailForCurrentLanguage(currentEventId);
    }
    
    // Check if we're in FAQ page and update it
    if (isInFAQPage()) {
        console.log('Updating FAQ page content');
        updateFAQContent();
    }
}

/**
 * Get complete English language content
 * @returns {Object} - Complete English language content object
 */
function getEnglishContent() {
    return {
        // Navigation content
        nav: {
            logoText: "BAHUJAN SAMAJ PARTY",
            home: "Home",
            about: "About", 
            vision: "Vision",
            timeline: "Timeline",
            events: "Events",
            updates: "Updates",
            gallery: "Gallery",
            resources: "Resources",
            contact: "Contact",
            faq: "FAQ"
        },

        // Hero section content
        hero: {
            title: "Bahujan Samaj Party",
            subtitle: "Social Transformation & Economic Emancipation",
            description: "Empowering the Scheduled Castes, Scheduled Tribes, and Other Backward Castes through the ideology of Babasaheb Dr. Bhimrao Ambedkar",
            learnMore: "Learn More",
            joinUs: "Join Us"
        },

        // About section content
        about: {
            title: "About BSP",
            description: {
                p1: "The Bahujan Samaj Party stands for the social transformation and economic emancipation of the Bahujan Samaj, which comprises the Scheduled Castes (SC), Scheduled Tribes (ST), and Other Backward Castes (OBC). Inspired by the philosophy of Babasaheb Dr. Bhimrao Ambedkar, we work towards creating an egalitarian society.",
                p2: "Our movement is rooted in the principles of social justice, equality, and fraternity. We strive to empower the marginalized and ensure their rightful place in society.",
                p3: "Join us in our mission to build a just and equitable India for all, following the path shown by Babasaheb Dr. Bhimrao Ambedkar and Manyavar Kanshi Ram."
            },
            mission: {
                title: "Our Mission",
                description: "To achieve social transformation and economic emancipation of the Bahujan Samaj through democratic means and constitutional methods."
            },
            values: {
                title: "Our Values", 
                description: "Equality, justice, brotherhood, and the constitutional principles laid down by Babasaheb Dr. Bhimrao Ambedkar guide our path forward."
            },
            struggle: {
                title: "Our Struggle",
                description: "We continue the struggle for dignity, self-respect, and equal opportunities for all marginalized communities in India."
            }
        },

        // Vision section content
        vision: {
            title: "Vision & Leadership",
            description: "Our vision is to build a society where every individual has equal opportunities regardless of their caste, creed, or background. We are committed to the ideals of Babasaheb Dr. Bhimrao Ambedkar and work towards implementing his vision of a just and equitable society.",
            leaderInspiration: "Ideological Inspiration",
            leaderFounder: "Founder (1984)",
            leaderPresident: "National President",
            leaderNamesInspiration: "Babasaheb Dr. Bhimrao Ambedkar",
            leaderNamesFounder: "Manyavar Kanshi Ram",
            leaderNamesPresident: "Behen Kumari. Mayawati Ji"
        },

        // Timeline section content
        timeline: {
            headerText: "OUR JOURNEY",
            items: [
                {
                    title: "Political Foundation Campaign",
                    description: "Manyavar Kanshi Ram campaigns as BSP's 3rd Party candidate for Parliament in Uttar Pradesh, marking the beginning of serious electoral politics for the party."
                },
                {
                    title: "Commitment to Dalit Rights",
                    description: "Behen Kumari. Mayawati appears publicly with the statue of Babasaheb Dr. Bhimrao Ambedkar, symbolizing the party's unwavering commitment to Dalit rights and social justice."
                },
                {
                    title: "Second Chief Minister Term",
                    description: "Placeholder description."
                },
                {
                    title: "First Chief Minister Term",
                    description: "Behen Kumari. Mayawati becomes Chief Minister of Uttar Pradesh for the first time, appearing with prominent leaders including Manyavar Kanshi Ram, Inder Kumar Gujral, and KR Narayanan."
                },
                {
                    title: "National Party Status",
                    description: "BSP is declared a national party in the presence of Prime Minister Inder Kumar Gujral, establishing its significance in Indian politics."
                },
                {
                    title: "Massive Delhi Rally",
                    description: "Historic BSP rally at Ramlila Grounds in Delhi with Manyavar Kanshi Ram and Behen Kumari. Mayawati, demonstrating the party's growing national influence and mass appeal."
                },
                {
                    title: "Third Term as Chief Minister",
                    description: "Behen Kumari. Mayawati becomes CM of Uttar Pradesh again with BJP's support, demonstrating strategic political alliances for governance."
                },
                {
                    title: "Golden Jubilee Celebration",
                    description: "Behen Kumari. Mayawati celebrates her 50th birthday with Manyavar Kanshi Ram in New Delhi, marking a significant personal and political milestone."
                },
                {
                    title: "Historic Absolute Majority",
                    description: "Behen Kumari. Mayawati wins absolute majority and becomes CM of UP again, taking oath in Lucknow in a landmark political victory."
                },
                {
                    title: "Sarv Samaj Bhaichara Rally",
                    description: "Massive rally in Delhi, meetings with Left leaders, and unveiling of statues at Noida's Dalit Prerna Sthal, showcasing party's cultural initiatives."
                },
                {
                    title: "Lok Sabha Campaign",
                    description: "Behen Kumari. Mayawati campaigns extensively for Lok Sabha elections with public rallies at Ramlila Grounds and across UP, strengthening democratic participation."
                },
                {
                    title: "Democratic Participation",
                    description: "Votes in Lucknow during UP Assembly elections, symbolizing democratic participation and peaceful transfer of power."
                },
                {
                    title: "Parliamentary Presence",
                    description: "Behen Kumari. Mayawati attends Monsoon Session of Parliament and responds publicly to RSS Chief's comments on reservation, defending constitutional rights.",
                    image: "assets/timeline/2015.jpg",
                    // portrait: "assets/2015.jpg"
                },
                {
                    year: 2016,
                    title: "Ambedkar Anniversary Rally",
                    description: "Massive rally in Lucknow on 61st death anniversary of Dr. Ambedkar, with party review meetings to prepare for 2017 elections.",
                    image: "assets/timeline/2016.jpg",
                    // portrait: "assets/2016.jpg"
                },
                {
                    year: 2017,
                    title: "Electoral Campaign",
                    description: "Behen Kumari. Mayawati waves at supporters in Allahabad ahead of UP Assembly elections, continuing the democratic struggle for representation.",
                    image: "assets/timeline/2017.jpg",
                    // portrait: "assets/2017.jpg"
                },
                {
                    year: 2018,
                    title: "Opposition Unity",
                    description: "Behen Kumari. Mayawati joins opposition leaders including Rahul Gandhi, Sonia Gandhi, and Kejriwal at Kumaraswamy's oath ceremony in Karnataka.",
                    image: "assets/timeline/2018.jpg",
                    // portrait: "assets/2018.jpg"
                },
                {
                    year: 2019,
                    title: "Strategic Alliance",
                    description: "Joint rally with Akhilesh Yadav (SP) and Ajit Singh (RLD) in Varanasi before Lok Sabha elections, demonstrating coalition politics for social justice.",
                    image: "assets/timeline/2019.jpg",
                    // portrait: "assets/2019.jpg"
                }
            ]
        },

        // Events section content
        events: {
            title: "Latest Events & News",
            description: "Stay updated with our latest activities, rallies, and announcements.",
            items: [
                {
                    id: "event1",
                    title: "Anticipation Day & Public Gathering",
                    description: "A tribute to K. Amusthraj, highlighting Tamil Nadu’s role in social justice through the BSP's principles.",
                    date: "July 5, 2025",
                    image: "assets\\event_1.jpeg",
                    contentTitle: "Honoring Legacy, Empowering the Future",
                    fullContent: "A powerful and emotionally resonant public gathering, Anticipation Day is being held in solemn remembrance of Thiru. K. Amusthraj, a courageous and unwavering voice in the fight for equality, dignity, and social justice. This event stands as a tribute not only to his legacy but also to the enduring spirit of Tamil Nadu, which has historically resisted caste-based oppression and stood at the forefront of progressive movements in India.\n\nThe gathering will celebrate the immense contributions of Ambedkarite and Periyarist leaders who have paved the way for generations by challenging systemic discrimination and striving for a more egalitarian society. Eminent BSP leaders including Dr. P. Anandhan and R. Boobathi Rajan will address the public to highlight the BSP’s vision for Tamil Nadu.\n\nThe event also marks a renewed call for grassroots mobilization, aiming to strengthen the party's base across the state by engaging local communities and youth. More than just a remembrance, Anticipation Day is a reaffirmation of the BSP’s mission to build a society rooted in equality, justice, and fraternity.",
                    highlights: "Tributes to K. Amusthraj; Speeches by BSP leaders; Celebration of Ambedkarite and Periyarist ideologies; Youth and grassroots mobilization; Call to action for social change and empowerment."
                },
                {
                    id: "event2",
                    title: "Ambedkar Jayanti Celebration",
                    description: "Join us for the grand celebration of Babasaheb Dr. Bhimrao Ambedkar's birth anniversary with rallies and cultural programs across all states.",
                    date: "Dec 2024",
                    category: "BSP Rally",
                    image: "assets\\events_BG.png",
                    contentTitle: "Celebrating the Legacy of Dr. B.R. Ambedkar",
                    fullContent: "Join us for the grand celebration of Dr. B.R. Ambedkar's birth anniversary, a momentous occasion that honors the architect of the Indian Constitution and the champion of social justice. This year's celebration will be held across all states with unprecedented scale and participation.",
                    highlights: "The celebration will feature cultural programs showcasing the rich heritage of the Bahujan community, educational seminars on Dr. Ambedkar's contributions to modern India, and rallies promoting social equality and justice. Distinguished speakers will address the gathering, sharing insights into Dr. Ambedkar's vision for a just and equitable society."
                },
                {
                    id: "event3",
                    title: "Dalit Rights Conference",
                    description: "National conference on Dalit rights and empowerment with prominent leaders and activists.",
                    date: "Oct 2024",
                    category: "Rights Conference",
                    image: "assets\\events_BG.png",
                    contentTitle: "National Conference on Dalit Rights and Empowerment",
                    fullContent: "A comprehensive conference focusing on Dalit rights, empowerment strategies, and social justice initiatives. Prominent leaders, activists, and intellectuals will share their insights on advancing the cause of marginalized communities.",
                    highlights: "The conference will address contemporary challenges faced by Dalits, discuss policy reforms, and chalk out future strategies for ensuring equal rights and opportunities for all sections of society."
                },
                {
                    id: "event4",
                    title: "Youth Wing Formation",
                    description: "Launch of BSP Youth Wing to engage young minds in the party's ideology and future vision.",
                    date: "Sep 2024",
                    category: "Youth Wing",
                    image: "assets\\events_BG.png",
                    contentTitle: "Launch of BSP Youth Wing",
                    fullContent: "Inaugural launch of the BSP Youth Wing to engage young minds in the party's ideology and future vision. This initiative aims to build the next generation of leaders committed to social justice and equality.",
                    highlights: "The Youth Wing will focus on educational programs, leadership development, and creating awareness about constitutional rights among the younger generation. Special emphasis will be placed on digital outreach and modern communication methods."
                }
            ]
        },

        // Contact section content
        contact: {
            title: "Get in Touch",
            description: "Connect with us to be part of the movement for social transformation.",
            infoTitle: "Contact Information",
            formTitle: "Send us a Message",
            nameLabel: "Name",
            emailLabel: "Email",
            subjectLabel: "Subject",
            messageLabel: "Message",
            sendMessage: "Send Message"
        },

        // FAQ section content
        faq: {
            title: "Frequently Asked Questions",
            subtitle: "Common questions about BSP and our movement",
            items: [
                {
                    question: "What is the main ideology of BSP?",
                    answer: "BSP follows the ideology of Babasaheb Dr. Bhimrao Ambedkar, focusing on social transformation and economic emancipation of the Bahujan Samaj (SC, ST, OBC). We believe in creating an egalitarian society based on principles of Liberty, Equality, Fraternity, and Justice."
                },
                {
                    question: "How can I become a member of BSP?",
                    answer: "You can become a BSP member by contacting your local BSP office or through our official website. Membership is open to all who believe in our ideology and are committed to the cause of social justice and equality."
                },
                {
                    question: "What are BSP's key policies?",
                    answer: "Our key policies include: reservation in government jobs and education for SC/ST/OBC, land reforms, economic empowerment programs, educational advancement, healthcare access, and implementation of constitutional provisions for marginalized communities."
                },
                {
                    question: "Who founded BSP and when?",
                    answer: "BSP was founded by Manyavar Kanshi Ram on April 14, 1984 (Dr. Ambedkar's birth anniversary). The party was established to provide political representation to the Bahujan Samaj and implement Dr. Ambedkar's vision of social justice."
                },
                {
                    question: "What is the party symbol and what does it represent?",
                    answer: "The BSP symbol is the elephant, which represents strength, wisdom, and memory. The elephant symbolizes the power of the Bahujan Samaj when united and organized under a common political platform."
                },
                {
                    question: "How does BSP work for women's empowerment?",
                    answer: "BSP strongly advocates for women's rights and empowerment. We support reservation for women in legislatures, equal opportunities in education and employment, and protection against discrimination and violence. Our leadership includes strong women leaders like Behen Kumari. Mayawati."
                }
            ]
        },

        // Button labels
        buttons: {
            readMore: "Read More",
            backToEvents: "Back to Events",
            backToMain: "Back to Main Site", 
            shareEvent: "Share Event",
            // downloadDetails: "Download Details"
        },

        // Event detail page content
        eventDetail: {
            highlightsTitle: "Event Highlights"
        },

        // Loading and message content
        loading: {
            text: "Loading..."
        },

        // User messages
        messages: {
            linkCopied: "Event link copied to clipboard!",
            copyFailed: "Unable to copy link. Please copy manually: ",
            downloadSoon: "Event details download feature will be available soon!",
            messageSent: "Thank you for your message! We will get back to you soon.",
            fillRequired: "Please fill all required fields."
        },

        // Updates section content
        updates: {
            title: "Latest Updates",
            description: "Stay informed with the latest news and updates from the Bahujan Samaj Party."
        },

        // Gallery section content
        gallery: {
            title: "Photo Gallery",
            description: "Explore BSP's journey through powerful moments and historic achievements"
        },

        // Resources section content
        resources: {
            title: "Resources & Downloads",
            description: "Access important documents and educational materials to support understanding of BSP's vision and activities.",
            backToHome: "Back to Main Site",
            categoryBooksTitle: "Books",
            categoryBooksDesc: "Essential reading materials and publications by BSP leaders and about social justice.",
            categoryIdeologyTitle: "Ideology", 
            categoryIdeologyDesc: "Core principles, philosophy, and ideological framework of the Bahujan Samaj Party.",
            resourceBooks: "Download Books Collection",
            resourceIdeology: "Download Ideology Guide",
            externalResourcesTitle: "Useful Links",
            boothLevelAgent1: "Booth Level Agent 1",
            boothLevelAgent2: "Booth Level Agent 2",
            tnElectionDatabase: "TN Election Database",
            integratedGovDirectory: "Integrated Government Online Directory",
            contactResourcesTitle: "Need More Information?",
            contactResourcesDesc: "For additional resources, document requests, or technical support, please don't hesitate to contact our documentation team."
        }
    };
}

// ===== LANGUAGE SWITCHING FUNCTIONALITY (ENHANCED) =====

/**
 * Switch language dynamically by loading appropriate language file
 * @param {string} language - Target language ('english', 'hindi', 'tamil')
 * @param {boolean} isInternalCall - Flag to indicate if this is an internal consistency call
 */
function switchLanguage(language, isInternalCall = false) {
    console.log(`Switching to ${language} language${isInternalCall ? ' (internal)' : ''}`);
    
    // Update current language immediately
    currentLanguage = language;
    
    // Save language preference
    if (!isInternalCall) {
        saveLanguagePreference(language);
    }
    
    // Show loading overlay only for user-initiated switches
    if (!isInternalCall) {
        showLoadingOverlay();
    }
    
    // Update active language button
    document.querySelectorAll('.lang-btn').forEach(btn => {
        btn.classList.remove('active');
    });
    document.getElementById(`btn-${language}`).classList.add('active');
    
    // For English, load English content properly
    if (language === 'english') {
        // Set English content explicitly
        languageContent = getEnglishContent();
        // Set gallery translations for gallery.js
        window.galleryTranslations = {
            title: languageContent.gallery?.title || "Photo Gallery",
            description: languageContent.gallery?.description || "Explore BSP's journey through powerful moments and historic achievements"
        };
        updatePageContent();
        if (typeof updateGalleryContent === 'function') updateGalleryContent();
        if (!isInternalCall) {
            hideLoadingOverlay();
        }
        console.log('English language applied');
        return;
    }
    
    // Remove current language script if exists
    const existingScript = document.querySelector('script[data-language]');
    if (existingScript) {
        existingScript.remove();
    }
    
    // Load the appropriate language file
    const script = document.createElement('script');
    script.src = `./${language}.js`;
    script.setAttribute('data-language', language);
    
    script.onload = function() {
        console.log(`${language} language loaded successfully`);
        // Content will be updated by the loaded language file
        if (language === 'english') {
            window.galleryTranslations = {
                title: languageContent.gallery?.title || "Photo Gallery",
                description: languageContent.gallery?.description || "Explore BSP's journey through powerful moments and historic achievements"
            };
        }
        updatePageContent();
        if (typeof updateGalleryContent === 'function') updateGalleryContent();
        if (!isInternalCall) {
            hideLoadingOverlay();
        }
        
        // Check if we're in an event detail page and update it
        setTimeout(() => {
            const currentEventId = getCurrentEventId();
            if (currentEventId) {
                updateEventDetailForCurrentLanguage(currentEventId);
            }
            
            // Check if we're in FAQ page and update it
            if (isInFAQPage()) {
                updateFAQContent();
            }
        }, 100);
    };
    
    script.onerror = function() {
        console.error(`Failed to load ${language} language file from ./${language}.js`);
        
        // Try alternative path
        script.src = `${language}.js`;
        script.onload = function() {
            console.log(`${language} language loaded successfully (alternative path)`);
            if (language === 'english') {
                window.galleryTranslations = {
                    title: languageContent.gallery?.title || "Photo Gallery",
                    description: languageContent.gallery?.description || "Explore BSP's journey through powerful moments and historic achievements"
                };
            }
            updatePageContent();
            if (typeof updateGalleryContent === 'function') updateGalleryContent();
            if (!isInternalCall) {
                hideLoadingOverlay();
            }
            
            // Check if we're in an event detail page and update it
            setTimeout(() => {
                const currentEventId = getCurrentEventId();
                if (currentEventId) {
                    updateEventDetailForCurrentLanguage(currentEventId);
                }
                
                // Check if we're in FAQ page and update it
                if (isInFAQPage()) {
                    updateFAQContent();
                }
            }, 100);
        };
        
        script.onerror = function() {
            console.error(`Failed to load ${language} language file from both paths`);
            if (!isInternalCall) {
                hideLoadingOverlay();
            }
            
            // Fallback: Load content directly if file loading fails
            loadLanguageFallback(language);
            if (language === 'english') {
                window.galleryTranslations = {
                    title: languageContent.gallery?.title || "Photo Gallery",
                    description: languageContent.gallery?.description || "Explore BSP's journey through powerful moments and historic achievements"
                };
            }
            if (typeof updateGalleryContent === 'function') updateGalleryContent();
        };
    };
    
    document.head.appendChild(script);
}

/**
 * Fallback method to load language content when file loading fails
 * @param {string} language - Target language
 */
function loadLanguageFallback(language) {
    console.log(`Loading ${language} content via fallback method`);
    
    // This is a fallback that loads basic content
    if (language === 'hindi') {
        languageContent = {
            nav: {
                logoText: "बहुजन समाज पार्टी",
                home: "मुख्य पृष्ठ",
                about: "हमारे बारे में",
                vision: "दृष्टिकोण",
                timeline: "समयरेखा",
                events: "कार्यक्रम",
                updates: "अपडेट्स",
                gallery: "गैलरी",
                resources: "संसाधन",
                contact: "संपर्क",
                faq: "सामान्य प्रश्न"
            },
            hero: {
                title: "बहुजन समाज पार्टी",
                subtitle: "सामाजिक परिवर्तन और आर्थिक मुक्ति",
                description: "डॉ. बी.आर. अम्बेडकर की विचारधारा के माध्यम से अनुसूचित जाति, अनुसूचित जनजाति और अन्य पिछड़े वर्गों का सशक्तिकरण",
                learnMore: "और जानें",
                joinUs: "हमसे जुड़ें"
            },
            loading: { text: "लोड हो रहा है..." }
        };
    } else if (language === 'tamil') {
        languageContent = {
            nav: {
                logoText: "பகுஜன் சமாஜ் கட்சி",
                home: "முகப்பு",
                about: "எங்களைப் பற்றி",
                vision: "தொலைநோக்கு",
                timeline: "நேரக்கோடு",
                events: "நிகழ்வுகள்",
                updates: "புதுப்பிப்புகள்",
                gallery: "கேலரி",
                resources: "வளங்கள்",
                contact: "தொடர்பு",
                faq: "கேள்விகள்"
            },
            hero: {
                title: "பகுஜன் சமாஜ் கட்சி",
                subtitle: "சமூக மாற்றம் & பொருளாதார விடுதலை",
                description: "டாக்டர் பி.ஆர். அம்பேத்கரின் கொள்கையின் மூலம் பட்டியல் சாதி, பட்டியல் பழங்குடியினர் மற்றும் பிற பிற்படுத்தப்பட்ட வகுப்பினரின் அதிகாரமளித்தல்",
                learnMore: "மேலும் அறிக",
                joinUs: "எங்களுடன் சேருங்கள்"
            },
            loading: { text: "ஏற்றுகிறது..." }
        };
    } else {
        // Default to English
        languageContent = {
            nav: {
                logoText: "BAHUJAN SAMAJ PARTY",
                home: "Home",
                about: "About",
                vision: "Vision",
                timeline: "Timeline",
                events: "Events",
                updates: "Updates",
                gallery: "Gallery",
                resources: "Resources",
                contact: "Contact",
                faq: "FAQ"
            },
            hero: {
                title: "Bahujan Samaj Party",
                subtitle: "Social Transformation & Economic Emancipation",
                description: "Empowering the Scheduled Castes, Scheduled Tribes, and Other Backward Castes through the ideology of Babasaheb Dr. Bhimrao Ambedkar",
                learnMore: "Learn More",
                joinUs: "Join Us"
            },
            loading: { text: "Loading..." }
        };
    }
    
    // Update content with basic translations
    updatePageContent();
    console.log(`${language} fallback content loaded`);
}

/**
 * Update page content with current language data
 * This function is called by each language file after loading
 */
function updatePageContent() {
    if (!languageContent) {
        console.error('Language content not available');
        return;
    }
    try {
        // Update navigation elements
        updateElement('logo-text', languageContent.nav?.logoText);
        updateElement('nav-home', languageContent.nav?.home);
        updateElement('nav-about', languageContent.nav?.about);
        updateElement('nav-vision', languageContent.nav?.vision);
        updateElement('nav-timeline', languageContent.nav?.timeline);
        updateElement('nav-events', languageContent.nav?.events);
        updateElement('nav-updates', languageContent.nav?.updates);
        updateElement('nav-gallery', languageContent.nav?.gallery);
        updateElement('nav-resources', languageContent.nav?.resources);
        updateElement('nav-contact', languageContent.nav?.contact);
        updateElement('nav-faq', languageContent.nav?.faq);
        
        // Update hero section
        updateElement('hero-title', languageContent.hero?.title);
        updateElement('hero-subtitle', languageContent.hero?.subtitle);
        updateElement('hero-description', languageContent.hero?.description);
        updateElement('btn-learn-more', languageContent.hero?.learnMore);
        updateElement('btn-join-us', languageContent.hero?.joinUs);
        
        // Update about section
        updateElement('about-title', languageContent.about?.title);
        updateElement('about-description-1', languageContent.about?.description?.p1);
        updateElement('about-description-2', languageContent.about?.description?.p2);
        updateElement('about-description-3', languageContent.about?.description?.p3);
        updateElement('mission-title', languageContent.about?.mission?.title);
        updateElement('mission-description', languageContent.about?.mission?.description);
        updateElement('values-title', languageContent.about?.values?.title);
        updateElement('values-description', languageContent.about?.values?.description);
        updateElement('struggle-title', languageContent.about?.struggle?.title);
        updateElement('struggle-description', languageContent.about?.struggle?.description);
        
        // Update vision section
        updateElement('vision-title', languageContent.vision?.title);
        updateElement('vision-description', languageContent.vision?.description);
        updateElement('leader-inspiration', languageContent.vision?.leaderInspiration);
        updateElement('leader-founder', languageContent.vision?.leaderFounder);
        updateElement('leader-president', languageContent.vision?.leaderPresident);
        updateElement('leader-inspiration-name', languageContent.vision?.leaderNamesInspiration);
        updateElement('leader-founder-name', languageContent.vision?.leaderNamesFounder);
        updateElement('leader-president-name', languageContent.vision?.leaderNamesPresident);
        
        // Update events section
        updateElement('events-title', languageContent.events?.title);
        updateElement('events-description', languageContent.events?.description);
        
        //Update Social media section
        updateElement('updates-title', languageContent.updates?.title);
        updateElement('updates-description', languageContent.updates?.description);

        // Update contact section
        updateElement('contact-title', languageContent.contact?.title);
        updateElement('contact-description', languageContent.contact?.description);
        updateElement('contact-info-title', languageContent.contact?.infoTitle);
        updateElement('contact-form-title', languageContent.contact?.formTitle);
        updateElement('form-name-label', languageContent.contact?.nameLabel);
        updateElement('form-email-label', languageContent.contact?.emailLabel);
        updateElement('form-subject-label', languageContent.contact?.subjectLabel);
        updateElement('form-message-label', languageContent.contact?.messageLabel);
        updateElement('btn-send-message', languageContent.contact?.sendMessage);
        
        // Update other elements
        updateElement('btn-back-events', languageContent.buttons?.backToEvents);
        updateElement('btn-back-main', languageContent.buttons?.backToMain);
        updateElement('faq-title', languageContent.faq?.title);
        updateElement('faq-subtitle', languageContent.faq?.subtitle);
        updateElement('loading-text', languageContent.loading?.text);
        
        // Update events, resources and FAQ content
        updateEventsContent();
        updateResourcesContent();
        updateFAQContent();
        
        // Update timeline content if language data includes it
        if (languageContent.timeline) {
            updateTimelineContent();
        }
        
        // Check if we're in an event detail page and update it
        const currentEventId = getCurrentEventId();
        if (currentEventId) {
            updateEventDetailForCurrentLanguage(currentEventId);
        }
        
        console.log('Page content updated successfully for language:', currentLanguage);
        
    } catch (error) {
        console.error('Error updating page content:', error);
    }
}

/**
 * Helper function to update element text content
 * @param {string} elementId - ID of the element to update
 * @param {string} content - New text content
 */
function updateElement(elementId, content) {
    const element = document.getElementById(elementId);
    if (element && content) {
        element.textContent = content;
    }
}

/**
 * Update events section with current language content
 */
function updateEventsContent() {
    const eventsGrid = document.getElementById('eventsGrid');
    if (!eventsGrid) return;
    
    // Clear existing content
    eventsGrid.innerHTML = '';
    
    // Default events if no language content available
    const defaultEvents = [
        {
            id: "event1",
            title: "Ambedkar Jayanti Celebration",
            description: "Join us for the grand celebration of Babasaheb Dr. Bhimrao Ambedkar's birth anniversary with rallies and cultural programs across all states.",
            date: "Dec 2024",
            category: "BSP Rally"
        },
        {
            id: "event2", 
            title: "State Executive Meeting",
            description: "Monthly state executive committee meeting to discuss upcoming strategies and organizational matters.",
            date: "Nov 2024",
            category: "Executive Meet"
        },
        {
            id: "event3",
            title: "Dalit Rights Conference", 
            description: "National conference on Dalit rights and empowerment with prominent leaders and activists.",
            date: "Oct 2024",
            category: "Rights Conference"
        },
        {
            id: "event4",
            title: "Youth Wing Formation",
            description: "Launch of BSP Youth Wing to engage young minds in the party's ideology and future vision.",
            date: "Sep 2024", 
            category: "Youth Wing"
        }
    ];
    
    const events = (languageContent && languageContent.events && languageContent.events.items) 
        ? languageContent.events.items 
        : defaultEvents;
    
    const readMoreText = (languageContent && languageContent.buttons && languageContent.buttons.readMore) 
        ? languageContent.buttons.readMore 
        : 'Read More';
    
    // Create exactly 4 event cards for 2x2 grid
    for (let i = 0; i < 4; i++) {
        const event = events[i] || defaultEvents[i];
        const eventCard = document.createElement('div');
        eventCard.className = 'event-card';
        eventCard.onclick = () => showEventDetail(event.id);
        
        eventCard.innerHTML = `
            <div class="event-thumbnail">
                <div class="event-date-badge">${event.date}</div>
                <span>${event.category}</span>
            </div>
            <div class="event-content">
                <h3>${event.title}</h3>
                <p>${event.description}</p>
                <button class="read-more-btn">${readMoreText}</button>
            </div>
        `;
        
        eventsGrid.appendChild(eventCard);
    }
}

/**
 * Update resources page with current language content
 */
function updateResourcesContent() {
    // Update resources page elements with current language
    updateElement('back-to-home-text', languageContent.resources?.backToHome);
    updateElement('resources-title', languageContent.resources?.title);
    updateElement('resources-description', languageContent.resources?.description);
    updateElement('category-books-title', languageContent.resources?.categoryBooksTitle);
    updateElement('category-books-desc', languageContent.resources?.categoryBooksDesc);
    updateElement('category-ideology-title', languageContent.resources?.categoryIdeologyTitle);
    updateElement('category-ideology-desc', languageContent.resources?.categoryIdeologyDesc);
    updateElement('resource-books', languageContent.resources?.resourceBooks);
    updateElement('resource-ideology', languageContent.resources?.resourceIdeology);
    updateElement('external-resources-title', languageContent.resources?.externalResourcesTitle);
    updateElement('booth-level-agent-1', languageContent.resources?.boothLevelAgent1);
    updateElement('booth-level-agent-2', languageContent.resources?.boothLevelAgent2);
    updateElement('tn-election-database', languageContent.resources?.tnElectionDatabase);
    updateElement('integrated-gov-directory', languageContent.resources?.integratedGovDirectory);
    updateElement('contact-resources-title', languageContent.resources?.contactResourcesTitle);
    updateElement('contact-resources-desc', languageContent.resources?.contactResourcesDesc);
}

/**
 * Update FAQ section with current language content
 */
function updateFAQContent() {
    const faqContainer = document.getElementById('faqContainer');
    if (!faqContainer) return;
    
    faqContainer.innerHTML = '';
    
    // Default FAQ items if no language content available
    const defaultFAQs = [
        {
            question: "What is the main ideology of BSP?",
            answer: "BSP follows the ideology of Babasaheb Dr. Bhimrao Ambedkar, focusing on social transformation and economic emancipation of the Bahujan Samaj (SC, ST, OBC). We believe in creating an egalitarian society based on principles of Liberty, Equality, Fraternity, and Justice."
        },
        {
            question: "How can I become a member of BSP?",
            answer: "You can become a BSP member by contacting your local BSP office or through our official website. Membership is open to all who believe in our ideology and are committed to the cause of social justice and equality."
        },
        {
            question: "What are BSP's key policies?",
            answer: "Our key policies include: reservation in government jobs and education for SC/ST/OBC, land reforms, economic empowerment programs, educational advancement, healthcare access, and implementation of constitutional provisions for marginalized communities."
        }
    ];
    
    const faqs = (languageContent && languageContent.faq && languageContent.faq.items) 
        ? languageContent.faq.items 
        : defaultFAQs;
    
    faqs.forEach((faq, index) => {
        const faqItem = document.createElement('div');
        faqItem.className = 'faq-item';
        
        faqItem.innerHTML = `
            <div class="faq-question" onclick="toggleFAQ(this)">
                ${faq.question}
                <i class="fas fa-chevron-down faq-icon"></i>
            </div>
            <div class="faq-answer">
                <div class="faq-answer-content">
                    <p>${faq.answer}</p>
                </div>
            </div>
        `;
        
        faqContainer.appendChild(faqItem);
    });
}

/**
 * Update timeline content with current language
 */
function updateTimelineContent() {
    if (!languageContent.timeline?.items) return;
    
    // Update timeline data with translated content
    languageContent.timeline.items.forEach((item, index) => {
        if (timelineData[index]) {
            timelineData[index].title = item.title;
            timelineData[index].description = item.description;
        }
    });
    
    // Regenerate timeline if swiper exists
    if (timelineSwiper) {
        generateTimelineSlides();
    }
}

// ===== LOADING OVERLAY FUNCTIONS =====

/**
 * Show loading overlay with animation
 */
function showLoadingOverlay() {
    const overlay = document.getElementById('loadingOverlay');
    if (overlay) {
        overlay.classList.add('active');
        document.body.classList.add('no-scroll');
    }
}

/**
 * Hide loading overlay with animation
 */
function hideLoadingOverlay() {
    const overlay = document.getElementById('loadingOverlay');
    if (overlay) {
        setTimeout(() => {
            overlay.classList.remove('active');
            document.body.classList.remove('no-scroll');
        }, 500); // Small delay for smooth transition
    }
}

// ===== NAVIGATION FUNCTIONS (ENHANCED WITH LANGUAGE PERSISTENCE) =====

/**
 * Toggle mobile hamburger menu
 */
function toggleMenu() {
    const navMenu = document.querySelector('.nav-menu');
    const hamburger = document.querySelector('.hamburger');
    
    if (navMenu && hamburger) {
        navMenu.classList.toggle('active');
        hamburger.classList.toggle('active');
        
        // Add body scroll lock when menu is open
        if (navMenu.classList.contains('active')) {
            document.body.classList.add('no-scroll');
        } else {
            document.body.classList.remove('no-scroll');
        }
    }
}

/**
 * Navigate to home section (ENHANCED)
 */
function goHome() {
    hideEventDetail();
    hideFAQ();
    currentPage = 'main';
    scrollToSection('hero');
    updateHistory('main', 0);
    
    // Ensure language consistency after navigation
    setTimeout(() => {
        ensureLanguageConsistency();
    }, 100);
}

/**
 * Smooth scroll to specific section (ENHANCED)
 * @param {string} sectionId - ID of the target section
 */
function scrollToSection(sectionId) {
    hideEventDetail();
    hideFAQ();

    // Reset current page state when navigating to main sections
    currentPage = 'main';

    const section = document.getElementById(sectionId);
    const mainContainer = document.getElementById('mainContainer');

    if (section && mainContainer) {
        // Store current scroll position
        currentScrollPosition = mainContainer.scrollTop;

        // Calculate target scroll position
        const targetScrollTop = section.offsetTop - 80; // Adjust for fixed navbar

        // Smooth scroll animation
        const startScrollTop = mainContainer.scrollTop;
        const distance = targetScrollTop - startScrollTop;
        const duration = 800;
        let startTime = null;

        function animateScroll(currentTime) {
            if (startTime === null) startTime = currentTime;
            const timeElapsed = currentTime - startTime;
            const progress = Math.min(timeElapsed / duration, 1);

            // Easing function (easeInOutCubic)
            const ease = progress < 0.5
                ? 2 * progress * progress
                : 1 - Math.pow(-2 * progress + 2, 3) / 2;

            mainContainer.scrollTop = startScrollTop + (distance * ease);

            if (progress < 1) {
                requestAnimationFrame(animateScroll);
            } else {
                updateHistory(sectionId || 'main', targetScrollTop);

                // Trigger hash so browser can remember it on reload
                if (sectionId) location.hash = sectionId;

                // Ensure language consistency immediately after navigation animation completes
                ensureLanguageConsistency(); // Removed setTimeout
            }
        }

        requestAnimationFrame(animateScroll);
    }

    // Close mobile menu if open
    const navMenu = document.querySelector('.nav-menu');
    const hamburger = document.querySelector('.hamburger');
    if (navMenu && hamburger) {
        navMenu.classList.remove('active');
        hamburger.classList.remove('active');
        document.body.classList.remove('no-scroll');
    }
}

// ===== TIMELINE FUNCTIONS =====

/**
 * Initialize timeline swiper and content
 */
function initTimeline() {
    console.log('Initializing timeline...');
    
    // Wait for Swiper library to be available
    if (typeof Swiper === 'undefined') {
        console.error('Swiper library not loaded');
        setTimeout(initTimeline, 1000); // Retry after 1 second
        return;
    }
    
    generateTimelineSlides();
    generateYearStrip();
    
    // Initialize Swiper after DOM elements are ready
    setTimeout(() => {
        try {
            initTimelineSwiper();
        } catch (error) {
            console.error('Error initializing timeline swiper:', error);
        }
    }, 100);
}

/**
 * Generate timeline slides HTML
 */
function generateTimelineSlides() {
    const timelineWrapper = document.getElementById('timelineWrapper');
    if (!timelineWrapper) {
        console.error('Timeline wrapper not found');
        return;
    }
    
    timelineWrapper.innerHTML = '';
    
    timelineData.forEach((event, index) => {
        const slide = document.createElement('div');
        slide.className = 'swiper-slide timeline-slide';
        slide.style.backgroundImage = `url('${event.image}')`;
        
        slide.innerHTML = `
            <div class="timeline-slide-content">
                <div class="timeline-header-text">${languageContent.timeline?.headerText || 'OUR JOURNEY'}</div>
                <div class="timeline-year-display">${event.year}</div>
                <h2 class="timeline-slide-title">${event.title}</h2>
                <p class="timeline-slide-description">${event.description}</p>
            </div>
            ${event.portrait ? `<div class="timeline-portrait" style="background-image: url('${event.portrait}')"></div>` : ''}
        `;
        
        timelineWrapper.appendChild(slide);
    });
    
    console.log('Timeline slides generated:', timelineData.length);
}

/**
 * Generate year strip markers
 */
function generateYearStrip() {
    const yearStripTrack = document.getElementById('yearStripTrack');
    if (!yearStripTrack) {
        console.error('Year strip track not found');
        return;
    }
    
    yearStripTrack.innerHTML = '';
    
    timelineData.forEach((event, index) => {
        const yearMarker = document.createElement('div');
        yearMarker.className = `year-marker ${index === 0 ? 'active' : ''}`;
        yearMarker.onclick = () => goToTimelineSlide(index);
        
        yearMarker.innerHTML = `
            <div class="year-number">${event.year}</div>
        `;
        
        yearStripTrack.appendChild(yearMarker);
    });
}

/**
 * Initialize Swiper instance for timeline
 */
function initTimelineSwiper() {
    try {
        timelineSwiper = new Swiper('.timeline-swiper', {
            slidesPerView: 1,
            spaceBetween: 0,
            loop: false,
            speed: 1000,
            autoplay: {
                delay: 10000,
                disableOnInteraction: true,
            },
            navigation: {
                nextEl: '#timelineNext',
                prevEl: '#timelinePrev',
            },
            on: {
                slideChange: function () {
                    updateTimelineYearStrip(this.activeIndex);
                    currentTimelineYear = timelineData[this.activeIndex].year.toString();
                    console.log('Timeline slide changed to:', currentTimelineYear);
                },
                init: function() {
                    console.log('Timeline Swiper initialized successfully');
                    updateTimelineYearStrip(0);
                }
            },
            // Enable touch gestures
            touchRatio: 1,
            touchAngle: 45,
            grabCursor: true,
            // Smooth transitions
            effect: 'slide',
            allowTouchMove: true,
        });
        
        console.log('Swiper instance created successfully');
        
    } catch (error) {
        console.error('Error initializing Swiper:', error);
    }
}

/**
 * Navigate to specific timeline slide
 * @param {number} index - Index of the target slide
 */
function goToTimelineSlide(index) {
    console.log('Going to timeline slide:', index);
    if (timelineSwiper && timelineSwiper.slideTo) {
        timelineSwiper.slideTo(index);
    }
}

/**
 * Update year strip active state and scroll position
 * @param {number} activeIndex - Index of the active slide
 */
function updateTimelineYearStrip(activeIndex) {
    const yearMarkers = document.querySelectorAll('.year-marker');
    
    yearMarkers.forEach((marker, index) => {
        marker.classList.toggle('active', index === activeIndex);
    });
    
    // Scroll year strip to show active year
    const yearStripTrack = document.getElementById('yearStripTrack');
    const activeMarker = yearMarkers[activeIndex];
    
    if (yearStripTrack && activeMarker) {
        const containerWidth = yearStripTrack.parentElement.offsetWidth;
        const markerOffset = activeMarker.offsetLeft;
        const markerWidth = activeMarker.offsetWidth;
        const scrollLeft = markerOffset - (containerWidth / 2) + (markerWidth / 2);
        
        yearStripTrack.style.transform = `translateX(-${Math.max(0, scrollLeft)}px)`;
    }
}

/**
 * Update event detail page content for current language
 * @param {string} eventId - ID of the event to update
 */
function updateEventDetailForCurrentLanguage(eventId) {
    console.log('Updating event detail page for language:', currentLanguage, 'Event ID:', eventId);
    
    // Find event data in current language
    const eventData = languageContent.events?.items?.find(event => event.id === eventId);
    
    if (eventData) {
        // Update the event detail page with translated content
        updateEventDetailPage(eventData);
        console.log('Event detail page updated with', currentLanguage, 'content');
    } else {
        console.warn('Event data not found for ID:', eventId, 'in language:', currentLanguage);
        
        // Fallback: try to find event in English content
        const englishContent = getEnglishContent();
        const fallbackEventData = englishContent.events?.items?.find(event => event.id === eventId);
        
        if (fallbackEventData) {
            updateEventDetailPage(fallbackEventData);
            console.log('Event detail page updated with fallback English content');
        }
    }
}

// ===== EVENT DETAIL FUNCTIONS (ENHANCED) =====

/**
 * Show event detail page (ENHANCED)
 * @param {string} eventId - ID of the event to show
 */
function showEventDetail(eventId) {
    console.log('Showing event detail:', eventId);
    
    const mainContainer = document.getElementById('mainContainer');
    currentScrollPosition = mainContainer.scrollTop;
    
    // Store current page state for language consistency
    currentPage = 'events/' + eventId + 'Detail';
    
    // Find event data
    const eventData = languageContent.events?.items?.find(event => event.id === eventId);
    if (!eventData) {
        console.error('Event data not found for ID:', eventId);
        return;
    }
    
    // Hide main container
    document.getElementById('mainContainer').style.display = 'none';
    
    // Update event detail page content
    updateEventDetailPage(eventData);
    
    // Show detail page
    document.getElementById('eventDetailPage').classList.add('active');
    updateHistory('events/' + eventId + 'Detail', currentScrollPosition);
    
    // Scroll to top
    window.scrollTo({ top: 0, behavior: 'smooth' });
    
    // Ensure language consistency in detail page
    setTimeout(() => {
        ensureLanguageConsistency();
    }, 200);
}

/**
 * Update event detail page with event data
 * @param {Object} eventData - Event data object
 */
function updateEventDetailPage(eventData) {
    // Update header with specific background for each event
    const detailHeader = document.getElementById('eventDetailHeader');
    if (detailHeader) {
        // Set specific background image based on event ID
        let backgroundImage;
        switch(eventData.id) {
            case 'event1':
                backgroundImage = "url('assets/event_1.jpeg')";
                break;
            case 'event2':
                backgroundImage = "url('assets/events_BG.png')"; // Default for event 2
                break;
            case 'event3':
                backgroundImage = "url('assets/events_BG.png')"; // Default for event 3
                break;
            case 'event4':
                backgroundImage = "url('assets/events_BG.png')"; // Default for event 4
                break;
            default:
                backgroundImage = "url('assets/events_BG.png')"; // Default fallback
        }
        detailHeader.style.backgroundImage = backgroundImage;
    }
    
    // Update meta information
    updateElement('eventDetailDate', eventData.date);
    updateElement('eventDetailCategory', eventData.category);
    updateElement('eventDetailTitle', eventData.title);
    
    // Update content
    const detailContent = document.getElementById('eventDetailContent');
    if (detailContent && eventData.fullContent) {
        detailContent.innerHTML = `
            <h2>${eventData.contentTitle || eventData.title}</h2>
            <p>${eventData.fullContent}</p>
            
            <h2>${languageContent.eventDetail?.highlightsTitle || 'Event Highlights'}</h2>
            <p>${eventData.highlights || 'More details about this event will be updated soon.'}</p>
            
            <div class="share-buttons">
                <button class="share-btn" onclick="shareEvent()">
                    <i class="fas fa-share"></i> ${languageContent.buttons?.shareEvent || 'Share Event'}
                </button>
            </div>
        `;
    }
}

/**
 * Hide event detail page and return to main view (ENHANCED)
 */
function hideEventDetail() {
    document.getElementById('mainContainer').style.display = 'block';
    document.getElementById('eventDetailPage').classList.remove('active');
    
    // Reset current page state
    currentPage = 'events';
    
    setTimeout(() => {
        const mainContainer = document.getElementById('mainContainer');
        mainContainer.scrollTop = currentScrollPosition;
        
        // Ensure language consistency after returning to main view
        ensureLanguageConsistency();
    }, 50);
    
    updateHistory('events', currentScrollPosition);
}

// ===== FAQ FUNCTIONS (ENHANCED) =====

/**
 * Show FAQ page (ENHANCED)
 */
function showFAQ() {
    console.log('Showing FAQ page');
         
    // Show FAQ page
    document.getElementById('faqPage').style.display = 'block';

    // Hide main container
    document.getElementById('mainContainer').style.display = 'none';
    document.getElementById('resourcesPage').style.display = 'none';
    
    // Hide any active detail pages
    document.querySelectorAll('.detail-page').forEach(page => {
        page.classList.remove('active');
    });
    
    // Store current page state
    currentPage = 'faq';
    currentScrollPosition = document.getElementById('faqPage').scrollTop;
    updateHistory(currentPage, currentScrollPosition);
    location.hash = currentPage;
    
    // Close mobile menu if open
    const navMenu = document.querySelector('.nav-menu');
    const hamburger = document.querySelector('.hamburger');
    if (navMenu && hamburger) {
        navMenu.classList.remove('active');
        hamburger.classList.remove('active');
        document.body.classList.remove('no-scroll');
    }
    
    // Scroll to top
    window.scrollTo({ top: 0, behavior: 'smooth' });
    
    // Ensure language consistency in FAQ page
    setTimeout(() => {
        ensureLanguageConsistency();
    }, 200);
    
    return false; // Prevent default link behavior
}

/**
 * Hide FAQ page and return to main view (ENHANCED)
 */
function hideFAQ() {
    document.getElementById('mainContainer').style.display = 'block';
    document.getElementById('faqPage').classList.remove('active');
    
    // Reset current page state
    currentPage = 'main';
    
    setTimeout(() => {
        const mainContainer = document.getElementById('mainContainer');
        mainContainer.scrollTop = currentScrollPosition;
        
        // Ensure language consistency after returning to main view
        ensureLanguageConsistency();
    }, 50);
    
    updateHistory('main', currentScrollPosition);
}

/**
 * Toggle FAQ accordion item
 * @param {HTMLElement} element - The FAQ question element clicked
 */
function toggleFAQ(element) {
    const answer = element.nextElementSibling;
    const icon = element.querySelector('.faq-icon');
    const isCurrentlyActive = answer.classList.contains('active');
    
    // Close all other FAQs
    document.querySelectorAll('.faq-answer').forEach(faq => {
        faq.classList.remove('active');
    });
    
    document.querySelectorAll('.faq-question').forEach(question => {
        question.classList.remove('active');
    });
    
    document.querySelectorAll('.faq-icon').forEach(i => {
        i.style.transform = 'rotate(0deg)';
    });
    
    // Toggle current FAQ if it wasn't active
    if (!isCurrentlyActive) {
        answer.classList.add('active');
        element.classList.add('active');
        if (icon) {
            icon.style.transform = 'rotate(180deg)';
        }
    }
}

// ===== RESOURCES FUNCTION =====

function showResources() {
    document.getElementById('resourcesPage').style.display = 'block';
    document.getElementById('mainContainer').style.display = 'none';
    document.getElementById('faqPage').style.display = 'none';
    document.querySelectorAll('.detail-page').forEach(page => {page.classList.remove('active');});
    
    currentPage = 'resources';
    currentScrollPosition = document.getElementById('resourcesPage').scrollTop;
    updateHistory(currentPage, currentScrollPosition);
    location.hash = currentPage;

    // Close mobile menu if open
    const navMenu = document.querySelector('.nav-menu');
    const hamburger = document.querySelector('.hamburger');
    if (navMenu && hamburger) {
        navMenu.classList.remove('active');
        hamburger.classList.remove('active');
        document.body.classList.remove('no-scroll');
    }
    
    // Scroll to top
    window.scrollTo({ top: 0, behavior: 'smooth' });
    
    // Ensure language consistency in FAQ page
    setTimeout(() => {
        ensureLanguageConsistency();
    }, 200);
    
    return false;
}

function hideResources() {
    document.getElementById('resourcesPage').style.display = 'none';
    document.getElementById('mainContainer').style.display = 'block';
}

// ===== HISTORY MANAGEMENT =====

/**
 * Update browser history state
 * @param {string} page - Current page identifier
 * @param {number} scrollPos - Current scroll position
 */
function updateHistory(page, scrollPos = null) {
    currentPage = page;
    if (scrollPos !== null) {
        currentScrollPosition = scrollPos;
    }
    
    const state = { 
        page: page, 
        scrollPosition: currentScrollPosition,
        timelineYear: currentTimelineYear,
        language: currentLanguage
    };
    
    const url = page === 'main' ? `/` : `#${page}`;
    history.pushState(state, '', url);
}

/**
 * Handle browser back/forward navigation (ENHANCED)
 * @param {string} page - Target page
 * @param {number} scrollPos - Target scroll position
 * @param {string} timelineYear - Target timeline year
 * @param {string} language - Target language
 */
function handleBackNavigation(page, scrollPos = 0, timelineYear = '1988', language = 'english') {
    // Switch language if different
    if (language && language !== currentLanguage) {
        switchLanguage(language, true); // true flag for internal call
    }
    
    if (page === 'main') {
        hideEventDetail();
        hideFAQ();
        setTimeout(() => {
            const mainContainer = document.getElementById('mainContainer');
            mainContainer.scrollTop = scrollPos || 0;
            
            // Ensure language consistency after navigation
            ensureLanguageConsistency();
        }, 50);
    } else if (page === 'events') {
        hideEventDetail();
        scrollToSection('events');
    } else if (page.startsWith('events/') && page.includes('Detail')) {
        const eventId = page.split('/')[1].replace('Detail', '');
        showEventDetail(eventId);
    } else if (page === 'faq') {
        showFAQ();
    }
    
    // Update timeline if needed
    if (timelineYear && timelineSwiper) {
        currentTimelineYear = timelineYear;
        const yearIndex = timelineData.findIndex(event => event.year.toString() === timelineYear);
        if (yearIndex !== -1) {
            goToTimelineSlide(yearIndex);
        }
    }
}

// ===== UTILITY FUNCTIONS =====

/**
 * Handle global social media visibility
 */
function updateGlobalSocialVisibility() {
    const globalSocial = document.getElementById('globalSocial');
    const mainContainer = document.getElementById('mainContainer');
    const timelineSection = document.getElementById('timeline');
    
    if (!globalSocial || !mainContainer || !timelineSection) return;
    
    const containerScrollTop = mainContainer.scrollTop;
    const timelineTop = timelineSection.offsetTop - 80;
    const timelineBottom = timelineTop + timelineSection.offsetHeight;
}

/**
 * Share event functionality
 */
function shareEvent() {
    if (navigator.share) {
        navigator.share({
            title: 'BSP Event',
            text: 'Check out this BSP event!',
            url: window.location.href
        }).catch(err => console.log('Error sharing:', err));
    } else {
        // Fallback for browsers without Web Share API
        navigator.clipboard.writeText(window.location.href).then(() => {
            alert(languageContent.messages?.linkCopied || 'Event link copied to clipboard!');
        }).catch(() => {
            alert(languageContent.messages?.copyFailed || 'Unable to copy link. Please copy manually: ' + window.location.href);
        });
    }
}

/**
 * Download event details functionality
 */
function downloadDetails() {
    alert(languageContent.messages?.downloadSoon || 'Event details download feature will be available soon!');
}

// ===== FORM HANDLING =====

/**
 * Initialize contact form
 */
function initContactForm() {
    // ! Put the logic for emailJS here!
    const contactForm = document.getElementById('contactForm');
    if (contactForm) {
        contactForm.addEventListener('submit', function(e) {
            e.preventDefault();
            
            // Basic form validation
            const inputs = this.querySelectorAll('input[required], textarea[required]');
            let isValid = true;
            
            inputs.forEach(input => {
                if (!input.value.trim()) {
                    isValid = false;
                    input.style.borderColor = '#e74c3c';
                } else {
                    input.style.borderColor = '';
                }
            });
            
            if (isValid) {
                alert(languageContent.messages?.messageSent || 'Thank you for your message! We will get back to you soon.');
                this.reset();
            } else {
                alert(languageContent.messages?.fillRequired || 'Please fill all required fields.');
            }
        });
    }
}

// ===== SCROLL EFFECTS =====

/**
 * Initialize scroll effects and navbar behavior
 */
function initScrollEffects() {
    const navbar = document.querySelector('.navbar');
    const mainContainer = document.getElementById('mainContainer');
    
    if (mainContainer) {
        mainContainer.addEventListener('scroll', function() {
            // Navbar background change on scroll
            if (mainContainer.scrollTop > 100) {
                navbar.style.background = 'rgba(34, 65, 154, 0.98)';
                navbar.style.backdropFilter = 'blur(15px)';
            } else {
                navbar.style.background = 'rgba(34, 65, 154, 0.95)';
                navbar.style.backdropFilter = 'blur(10px)';
            }
            
            // Update current scroll position
            currentScrollPosition = mainContainer.scrollTop;
            //localStorage.setItem('scrollPosition', currentScrollPosition);
                        
            // Update global social media visibility
            updateGlobalSocialVisibility();
            
            // Update active navigation item
            updateActiveNavItem();

            // Section-aware URL updater
            const sections = ['hero', 'timeline', 'events', 'updates', 'gallery', 'contact']; // Your top-level section IDs
            let currentVisibleSection = null;

            for (const id of sections) {
                const section = document.getElementById(id);
                if (section) {
                    const rect = section.getBoundingClientRect();
                    // Check if section is mostly in view (adjust as needed)
                    if (rect.top <= 150 && rect.bottom >= 150) {
                        currentVisibleSection = id;
                        break;
                    }
                }
            }

            // If section has changed, update hash and history
            if (currentVisibleSection && location.hash !== `#${currentVisibleSection}`) {
                const scrollPos = mainContainer.scrollTop;
                updateHistory(currentVisibleSection, scrollPos);
                location.hash = currentVisibleSection;
            }
        });
    }
}

/**
 * Update active navigation item based on scroll position
 */
function updateActiveNavItem() {
    const sections = document.querySelectorAll('.section');
    const mainContainer = document.getElementById('mainContainer');
    const scrollPos = mainContainer.scrollTop + 100;
    
    sections.forEach(section => {
        const top = section.offsetTop;
        const height = section.offsetHeight;
        
        if (scrollPos >= top && scrollPos < top + height) {
            // Remove active class from all nav items
            document.querySelectorAll('.nav-menu a').forEach(link => {
                link.classList.remove('active');
            });
            
            // Add active class to current section link
            const activeLink = document.querySelector(`.nav-menu a[onclick="scrollToSection('${section.id}')"]`);
            if (activeLink) {
                activeLink.classList.add('active');
            }
        }
    });
}

// ===== INITIALIZATION (ENHANCED) =====

/**
 * Initialize all website functionality (ENHANCED)
 */
function initWebsite() {
    console.log('Initializing BSP website...');
    
    try {
        // Initialize English content by default
        if (!languageContent || Object.keys(languageContent).length === 0) {
            languageContent = getEnglishContent();
            console.log('English content initialized as default');
        }
        
        // Load saved language preference
        const savedLanguage = loadLanguagePreference();
        if (savedLanguage !== 'english') {
            console.log('Loading saved language preference:', savedLanguage);
            currentLanguage = savedLanguage;
            // Load the saved language
            switchLanguage(savedLanguage, true); // true flag for internal call
        } else {
            // Make sure English is properly set up
            currentLanguage = 'english';
            languageContent = getEnglishContent();
            // Update active language button for English
            document.querySelectorAll('.lang-btn').forEach(btn => {
                btn.classList.remove('active');
            });
            document.getElementById('btn-english').classList.add('active');
        }
        
        // Initialize core components
        initContactForm();
        initScrollEffects();
        updateGlobalSocialVisibility();
        
        // Load default content for events and FAQ
        updateEventsContent();
        updateFAQContent();
        
        // Initialize timeline
        if (typeof Swiper !== 'undefined') {
            console.log('Swiper library loaded successfully');
            initTimeline();
        } else {
            console.warn('Swiper library not loaded, retrying...');
            // Retry timeline initialization
            setTimeout(() => {
                if (typeof Swiper !== 'undefined') {
                    initTimeline();
                } else {
                    console.error('Swiper library failed to load');
                }
            }, 2000);
        }
        
        // Set up browser history handling
        window.addEventListener('popstate', function(event) {
            if (event.state) {
                handleBackNavigation(
                    event.state.page, 
                    event.state.scrollPosition, 
                    event.state.timelineYear,
                    event.state.language
                );
            } else {
                handleBackNavigation('main', 0, '1988', currentLanguage);
            }
        });

        // Handle initial URL hash
        if (window.location.hash) {
            const section = window.location.hash.substring(1);
            setTimeout(() => {
                if (section.startsWith('events/')) {
                    // Example: events/event2Detail
                    const eventId = section.split('/')[1].replace('Detail', '');
                    showEventDetail(eventId);
                } else if (section === 'events') {
                    scrollToSection('events');
                } else if (section === 'faq') {
                    showFAQ();
                } else if (section === 'resources') {
                    showResources();
                } else {
                    scrollToSection(section);
                }
                // Ensure language consistency after initial navigation
                setTimeout(() => {
                    ensureLanguageConsistency();
                }, 200);
            }, 500);
        } else {
            // Only update history to 'main' if there's no hash
            updateHistory('main');
        }
        
        // Enhance scroll behavior
        const mainContainer = document.getElementById('mainContainer');
        if (mainContainer) {
            // Add momentum scrolling for iOS
            mainContainer.style.webkitOverflowScrolling = 'touch';
        }
        
        console.log('BSP website initialized successfully');
                
    } catch (error) {
        console.error('Error initializing website:', error);
    }
}

// ===== CONTACT FORM MODAL LOGIC =====
document.addEventListener('DOMContentLoaded', function() {
  const openBtn = document.getElementById('openContactModalBtn');
  const closeBtn = document.getElementById('closeContactModalBtn');
  const modal = document.getElementById('contactModalOverlay');

  if (openBtn && closeBtn && modal) {
    openBtn.addEventListener('click', function() {
      modal.classList.add('active');
      document.body.classList.add('no-scroll');
    });
    closeBtn.addEventListener('click', function() {
      modal.classList.remove('active');
      document.body.classList.remove('no-scroll');
    });
    // Close modal on overlay click (not modal box)
    modal.addEventListener('click', function(e) {
      if (e.target === modal) {
        modal.classList.remove('active');
        document.body.classList.remove('no-scroll');
      }
    });
    // Optional: Close modal on Escape key
    document.addEventListener('keydown', function(e) {
      if (e.key === 'Escape' && modal.classList.contains('active')) {
        modal.classList.remove('active');
        document.body.classList.remove('no-scroll');
      }
    });
  }
});

// ===== EVENT LISTENERS =====

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    console.log('DOM Content Loaded');
    
    let lang = (typeof loadLanguagePreference === 'function' ? loadLanguagePreference() : null) || 'english';
    let script = document.createElement('script');
    script.src = lang + '.js';
    script.setAttribute('data-lang', lang);
    document.body.appendChild(script);
    
    // Initialize website functionality
    initWebsite();
});

// Handle page visibility changes
document.addEventListener('visibilitychange', function() {
    if (document.hidden) {
        // Pause timeline autoplay when page is hidden
        if (timelineSwiper && timelineSwiper.autoplay) {
            timelineSwiper.autoplay.stop();
        }
    } else {
        // Resume timeline autoplay when page is visible
        if (timelineSwiper && timelineSwiper.autoplay) {
            timelineSwiper.autoplay.start();
        }
        
        // Ensure language consistency when page becomes visible
        setTimeout(() => {
            ensureLanguageConsistency();
        }, 100);
    }
});

// Handle window resize
window.addEventListener('resize', function() {
    // Update timeline layout on resize
    if (timelineSwiper) {
        timelineSwiper.update();
    }
    
    // Update global social visibility
    updateGlobalSocialVisibility();
});

// ===== EXPORT FOR EXTERNAL ACCESS =====
// Make functions available globally for onclick handlers
window.toggleMenu = toggleMenu;
window.goHome = goHome;
window.scrollToSection = scrollToSection;
window.switchLanguage = switchLanguage;
window.showFAQ = showFAQ;
window.hideFAQ = hideFAQ;
window.toggleFAQ = toggleFAQ;
window.showEventDetail = showEventDetail;
window.hideEventDetail = hideEventDetail;
window.shareEvent = shareEvent;