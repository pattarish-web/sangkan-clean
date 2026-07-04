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

        const size = parseInt(areaSize.value, 10);
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

        // Animate price
        totalPrice.style.transform = 'scale(1.05)';
        totalPrice.textContent = `฿${finalTotal.toLocaleString()}`;
        setTimeout(() => { totalPrice.style.transform = 'scale(1)'; }, 200);
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
        question.addEventListener('click', () => {
            const faqItem = question.parentElement;
            faqItem.classList.toggle('active');
            document.querySelectorAll('.faq-item').forEach(item => {
                if (item !== faqItem) item.classList.remove('active');
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

    // 5. Dynamic Blog Loader
    const articlesGrid = document.getElementById('articlesGrid');
    if (articlesGrid) {
        fetch('posts.json?v=' + new Date().getTime(), { cache: "no-store" })
            .then(res => res.json())
            .then(data => {
                // Get latest 3 articles
                const latestArticles = data.slice(-3).reverse();
                if (latestArticles.length > 0) {
                    articlesGrid.innerHTML = latestArticles.map(article => `
                        <article class="article-card">
                            <div class="article-img">
                                <img src="${article.image}" alt="${article.title}">
                                <span class="article-tag">${article.category}</span>
                            </div>
                            <div class="article-body">
                                <h3>${article.title}</h3>
                                <p>${article.description}</p>
                                <a href="blog.html" class="read-more">อ่านต่อ <i class="fa-solid fa-arrow-right"></i></a>
                            </div>
                        </article>
                    `).join('');
                }
                
                // Trigger scroll animation for dynamically loaded articles
                document.querySelectorAll('.article-card').forEach((el, index) => {
                    el.style.opacity = '0';
                    el.style.transform = 'translateY(30px)';
                    el.style.transition = `opacity 0.6s ease ${index * 0.1}s, transform 0.6s ease ${index * 0.1}s`;
                    observer.observe(el);
                });
            })
            .catch(err => {
                console.log('Error loading dynamic posts, using static fallback:', err);
                // Trigger scroll animation for existing static fallback articles
                document.querySelectorAll('.article-card').forEach((el, index) => {
                    el.style.opacity = '0';
                    el.style.transform = 'translateY(30px)';
                    el.style.transition = `opacity 0.6s ease ${index * 0.1}s, transform 0.6s ease ${index * 0.1}s`;
                    observer.observe(el);
                });
            });
    }

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
