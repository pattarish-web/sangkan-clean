import re

with open('index.html', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Fix line links
content = content.replace('@@SangkanClean', '@SangkanClean')

# 2. Fix Netlify og/twitter images
content = content.replace('https://sangkan-cleaning.netlify.app/logo.png', 'https://sangkanclean.com/logo.png')

# 3. Replace the entire schema blocks (Lines 37 to 117 roughly)
# First we find the start of the first schema and the end of the second schema
# The first schema starts at: <!-- Schema.org: LocalBusiness -->
# The second schema ends at: </script>\n\n    <!-- FAQ Schema Markup (SEO) -->

start_marker = "<!-- Schema.org: LocalBusiness -->"
end_marker = "<!-- FAQ Schema Markup (SEO) -->"

start_idx = content.find(start_marker)
end_idx = content.find(end_marker)

if start_idx != -1 and end_idx != -1:
    new_schema = """<!-- Schema.org Markup (SEO) -->
    <script type="application/ld+json">
    {
      "@context": "https://schema.org",
      "@graph": [
        {
          "@type": "LocalBusiness",
          "name": "Sangkan Clean สั่งการคลีน บริการทำความสะอาด สั่งได้ดั่งใจ",
          "description": "สั่งการคลีน บริการทำความสะอาด สั่งได้ดั่งใจ Big Cleaning แม่บ้านประจำ ทำความสะอาดบ้าน คอนโด ออฟฟิศ โรงงาน",
          "url": "https://sangkanclean.com/",
          "telephone": "+66636865134",
          "email": "pattarish@gmail.com",
          "image": "https://sangkanclean.com/logo.png",
          "priceRange": "฿฿",
          "address": {
            "@type": "PostalAddress",
            "streetAddress": "กรุงเทพมหานคร",
            "addressLocality": "กรุงเทพมหานคร",
            "addressRegion": "กรุงเทพมหานคร",
            "postalCode": "10110",
            "addressCountry": "TH"
          },
          "openingHoursSpecification": {
            "@type": "OpeningHoursSpecification",
            "dayOfWeek": ["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"],
            "opens": "08:00",
            "closes": "18:00"
          },
          "serviceArea": {
            "@type": "Place",
            "name": "กรุงเทพมหานคร และปริมณฑล"
          },
          "sameAs": [
            "https://www.facebook.com/61592039062581",
            "https://line.me/ti/p/@sangkanclean"
          ]
        },
        {
          "@type": "WebSite",
          "name": "Sangkan Clean",
          "url": "https://sangkanclean.com/",
          "potentialAction": {
            "@type": "SearchAction",
            "target": "https://sangkanclean.com/?s={search_term_string}",
            "query-input": "required name=search_term_string"
          }
        }
      ]
    }
    </script>

    <!-- Google Fonts -->
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=Noto+Sans+Thai:wght@300;400;500;600;700;800&display=swap" rel="stylesheet">
    
    <!-- FontAwesome -->
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    
    <!-- Custom CSS -->
    <link rel="stylesheet" href="style.css">

    """
    
    content = content[:start_idx] + new_schema + content[end_idx:]

with open('index.html', 'w', encoding='utf-8') as f:
    f.write(content)
