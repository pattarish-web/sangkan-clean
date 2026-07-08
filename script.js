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

    // 2. Interactive Pricing Calculator with Real Cost Structure
    // ต้นทุน: ค่ารถ ฿1,500 + ค่าแรง ฿500/คน + ค่าอุปกรณ์-น้ำยา ฿4/ตร.ม.
    // ราคาขาย = Base Fee (รถ+แรงงาน) + ราคา/ตร.ม. (รวม margin ~40%)
    const serviceType = document.getElementById('serviceType');
    const areaSize = document.getElementById('areaSize');
    const areaVal = document.getElementById('areaVal');
    const totalPrice = document.getElementById('totalPrice');
    const breakdownEl = document.getElementById('priceBreakdown');
    const extras = ['optCarpet', 'optAC', 'optOzone', 'optWindow'];

    // Pricing config per service type
    const pricingConfig = {
        standard: { baseFee: 2500, ratePerSqm: 18, minPrice: 3500, crew: 2, label: 'ทำความสะอาดทั่วไป' },
        deep:     { baseFee: 4000, ratePerSqm: 35, minPrice: 5500, crew: 3, label: 'Big Cleaning' },
        post:     { baseFee: 5500, ratePerSqm: 50, minPrice: 8000, crew: 4, label: 'หลังก่อสร้าง' }
    };

    function calculateCost() {
        if (!serviceType || !areaSize || !totalPrice) return;

        let size = parseInt(areaSize.value, 10);
        if (isNaN(size) || size < 20) {
            size = 20;
            if (areaSize.type === 'number') areaSize.value = 20;
        }
        areaVal.textContent = `${size} ตร.ม.`;

        const selectedOption = serviceType.options[serviceType.selectedIndex];
        const config = pricingConfig[selectedOption.value];

        // Calculate: Base Fee + (sqm × rate)
        let calculatedPrice = config.baseFee + (size * config.ratePerSqm);

        // Apply minimum price
        if (calculatedPrice < config.minPrice) calculatedPrice = config.minPrice;

        // Add extras
        let extraCost = 0;
        extras.forEach(id => {
            const el = document.getElementById(id);
            if (el && el.checked) extraCost += parseFloat(el.value);
        });

        const finalTotal = calculatedPrice + extraCost;

        // Update breakdown text
        if (breakdownEl) {
            breakdownEl.innerHTML = `
                <span>ค่าเดินทาง+ทีมงาน ${config.crew} คน: ฿${config.baseFee.toLocaleString()}</span>
                <span>ค่าบริการ ${size} ตร.ม. × ฿${config.ratePerSqm}: ฿${(size * config.ratePerSqm).toLocaleString()}</span>
                ${extraCost > 0 ? `<span>บริการเสริม: +฿${extraCost.toLocaleString()}</span>` : ''}
            `;
        }

        // Animate price (calculator_result tracked on debounce, not every keystroke)
        totalPrice.style.transform = 'scale(1.05)';
        totalPrice.textContent = `฿${finalTotal.toLocaleString()}`;
        scheduleCalculatorTrack(finalTotal, config.label);
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

    if (serviceType && areaSize) {
        serviceType.addEventListener('change', calculateCost);
        areaSize.addEventListener('input', calculateCost);
        extras.forEach(id => {
            const el = document.getElementById(id);
            if (el) el.addEventListener('change', calculateCost);
        });
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
        fetch('posts.json')
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

    // 6. Navbar scroll effect
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
