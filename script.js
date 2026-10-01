document.addEventListener('DOMContentLoaded', () => {
    // 1. Mobile Navigation Menu Toggle
    const menuToggle = document.getElementById('menuToggle');
    const navMenu = document.getElementById('navMenu');

    if (menuToggle && navMenu) {
        menuToggle.addEventListener('click', () => {
            navMenu.classList.toggle('active');
            const icon = menuToggle.querySelector('i');
            icon.className = navMenu.classList.contains('active') ? 'fa-solid fa-xmark' : 'fa-solid fa-bars';
        });
    }

    // Close menu when clicking a nav link
    document.querySelectorAll('.nav-link').forEach(link => {
        link.addEventListener('click', () => {
            if (navMenu && navMenu.classList.contains('active')) {
                navMenu.classList.remove('active');
                menuToggle.querySelector('i').className = 'fa-solid fa-bars';
            }
        });
    });

    // 2. Big Cleaning pricing calculator
    const propertyType = document.getElementById('propertyType');
    const areaSize = document.getElementById('areaSize');
    const areaVal = document.getElementById('areaVal');
    const totalPrice = document.getElementById('totalPrice');
    const breakdownEl = document.getElementById('priceBreakdown');
    const carpetArea = document.getElementById('carpetArea');
    const sofaSeats = document.getElementById('sofaSeats');
    const ozoneOption = document.getElementById('optOzone');
    const propertyLabels = {
        house: 'บ้าน',
        condo: 'คอนโด',
        office: 'สำนักงาน/ร้านค้า',
        factory: 'โรงงาน/โกดัง'
    };
    const priceTiers = {
        house: [35, 30, 28, 26, 24, 22],
        condo: [40, 35, 32, 30, 28, 25],
        office: [35, 32, 28, 26, 24, 22],
        factory: [30, 28, 26, 24, 22, 20]
    };
    const tierUpperBounds = [50, 100, 200, 300, 500, 1000];

    function calculateCost() {
        if (!propertyType || !areaSize || !areaVal || !totalPrice) return;

        const size = parseInt(areaSize.value, 10);
        areaVal.textContent = `${size} ตร.ม.`;

        if (size > 1000) {
            totalPrice.textContent = 'สอบถามราคา';
            if (breakdownEl) {
                breakdownEl.innerHTML = '<span>พื้นที่เกิน 1,000 ตร.ม. ต้องประเมินหน้างาน กรุณาติดต่อเพื่อขอใบเสนอราคา</span>';
            }
            clearTimeout(calculatorTrackTimer);
            return;
        }

        const property = propertyType.value;
        const tierIndex = tierUpperBounds.findIndex(bound => size <= bound);
        const rate = priceTiers[property][tierIndex];
        const areaPrice = size * rate;
        const basePrice = Math.max(6000, areaPrice);
        const addOns = [];
        const carpetSqm = Math.max(0, Number(carpetArea && carpetArea.value) || 0);
        const sofaCount = Math.max(0, Number(sofaSeats && sofaSeats.value) || 0);

        if (carpetSqm > 0) addOns.push({ label: `ซักพรม ${carpetSqm} ตร.ม.`, price: carpetSqm * 30 });
        if (sofaCount > 0) addOns.push({ label: `ซักโซฟา ${sofaCount} ที่นั่ง`, price: sofaCount * 500 });
        if (ozoneOption && ozoneOption.checked) addOns.push({ label: 'อบโอโซนพร้อม Big Cleaning (ราคาเริ่มต้น)', price: 1290 });

        const addOnTotal = addOns.reduce((total, addOn) => total + addOn.price, 0);
        const finalTotal = basePrice + addOnTotal;
        if (breakdownEl) {
            breakdownEl.innerHTML = `
                <span>Big Cleaning (${propertyLabels[property]}): ${size} ตร.ม. × ฿${rate}/ตร.ม. = ฿${areaPrice.toLocaleString()}${areaPrice < 6000 ? ' (คิดขั้นต่ำ ฿6,000)' : ''}</span>
                ${addOns.map(addOn => `<span>${addOn.label}: +฿${addOn.price.toLocaleString()}</span>`).join('')}
            `;
        }

        // Animate price (calculator_result tracked on debounce, not every keystroke)
        totalPrice.style.transform = 'scale(1.05)';
        totalPrice.textContent = `฿${finalTotal.toLocaleString()}`;
        scheduleCalculatorTrack(finalTotal, `Big Cleaning - ${propertyLabels[property]}`);
        setTimeout(() => { totalPrice.style.transform = 'scale(1)'; }, 200);
    }

    let calculatorTrackTimer;
    function scheduleCalculatorTrack(value, service) {
        clearTimeout(calculatorTrackTimer);
        calculatorTrackTimer = setTimeout(() => {
            if (typeof trackEvent === 'function') {
                trackEvent('calculator_result', { event_category: 'engagement', value: value, service: service });
            }
        }, 600);
    }

    if (propertyType && areaSize) {
        propertyType.addEventListener('change', calculateCost);
        areaSize.addEventListener('input', calculateCost);
        if (carpetArea) carpetArea.addEventListener('input', calculateCost);
        if (sofaSeats) sofaSeats.addEventListener('input', calculateCost);
        if (ozoneOption) ozoneOption.addEventListener('change', calculateCost);
        calculateCost();
    }

    // 3. FAQ Accordion
    document.querySelectorAll('.faq-question').forEach(question => {
        const answerId = 'faq-answer-' + Math.random().toString(36).slice(2, 8);
        const answer = question.nextElementSibling;
        if (answer) {
            answer.id = answerId;
            question.setAttribute('aria-expanded', 'false');
            question.setAttribute('aria-controls', answerId);
        }
        question.addEventListener('click', () => {
            const faqItem = question.parentElement;
            const isActive = faqItem.classList.toggle('active');
            question.setAttribute('aria-expanded', isActive ? 'true' : 'false');
            document.querySelectorAll('.faq-item').forEach(item => {
                if (item !== faqItem) {
                    item.classList.remove('active');
                    const btn = item.querySelector('.faq-question');
                    if (btn) btn.setAttribute('aria-expanded', 'false');
                }
            });
        });
    });

    // 4. Scroll-based animations (simple intersection observer)
    const observerOptions = { threshold: 0.15, rootMargin: '0px 0px -50px 0px' };
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.style.opacity = '1';
                entry.target.style.transform = 'translateY(0)';
                observer.unobserve(entry.target);
            }
        });
    }, observerOptions);

    // Animate cards on scroll
    const animatedElements = document.querySelectorAll(
        '.service-card-mini, .why-card, .loc-card, .client-logo-item, .faq-item'
    );
    animatedElements.forEach((el, index) => {
        el.style.opacity = '0';
        el.style.transform = 'translateY(30px)';
        el.style.transition = `opacity 0.6s ease ${index % 4 * 0.1}s, transform 0.6s ease ${index % 4 * 0.1}s`;
        observer.observe(el);
    });

    // 5. Load latest blog posts on homepage
    const articlesGrid = document.getElementById('articlesGrid');
    if (articlesGrid) {
        fetch('posts-index.json')
            .then(r => r.json())
            .then(posts => {
                const latest = posts.slice().reverse().slice(0, 3);
                articlesGrid.innerHTML = latest.map(p => `
                    <article class="article-card">
                        <div class="article-img">
                            <img src="${p.image}" alt="${p.title}" loading="lazy" width="400" height="240">
                            <span class="article-tag">${p.category || 'บทความ'}</span>
                        </div>
                        <div class="article-body">
                            <h3>${p.title}</h3>
                            <p>${p.description}</p>
                            <a href="blog/${p.slug || 'post'}.html" class="read-more">อ่านต่อ <i class="fa-solid fa-arrow-right"></i></a>
                        </div>
                    </article>`).join('');
                articlesGrid.querySelectorAll('.article-card').forEach((el, i) => {
                    el.style.opacity = '0';
                    el.style.transform = 'translateY(30px)';
                    el.style.transition = `opacity 0.6s ease ${i * 0.1}s, transform 0.6s ease ${i * 0.1}s`;
                    observer.observe(el);
                });
            })
            .catch(() => { articlesGrid.innerHTML = '<p style="grid-column:1/-1;text-align:center;"><a href="blog.html">ดูบทความทั้งหมด</a></p>'; });
    }

    // 6. Blog Scroll Animation (fallback for static cards)
    document.querySelectorAll('.article-card').forEach((el, index) => {
        el.style.opacity = '0';
        el.style.transform = 'translateY(30px)';
        el.style.transition = `opacity 0.6s ease ${index * 0.1}s, transform 0.6s ease ${index * 0.1}s`;
        observer.observe(el);
    });

    // 7. Navbar scroll effect
    let lastScroll = 0;
    const navbar = document.querySelector('.navbar');
    window.addEventListener('scroll', () => {
        const currentScroll = window.scrollY;
        if (currentScroll > 100) {
            navbar.style.boxShadow = '0 4px 6px rgba(0,0,0,0.07)';
        } else {
            navbar.style.boxShadow = 'none';
        }
        lastScroll = currentScroll;
    });
});
