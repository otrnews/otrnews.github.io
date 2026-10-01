"""
OTR News store: ebooks and other digital products.

The store page appears at otrnews.com/store/ (and "Store" shows in the menu) as soon as one item is listed below.
Checkout and delivery happen on your store platform (Shopify/LodoShop, Kajabi, Gumroad, Stripe Payment Link, etc.).
Paste that product's checkout link as "url".

Cover images: upload them to the images/ folder in the repo, then put "/images/your-file.jpg" as "cover".

Copy this example, remove the # signs, and fill it in:

#   {
#       "slug": "owner-operator-startup-guide",          # web address: otrnews.com/store/owner-operator-startup-guide/
#       "title": "The Owner-Operator Startup Guide",
#       "subtitle": "Get your authority, insurance, and first loads",
#       "price": "$19.99",
#       "url": "https://lodoshop.com/products/owner-operator-startup-guide",
#       "cover": "/images/startup-guide-cover.jpg",
#       "pages": "84 pages, PDF",
#       "description": "Two to four sentences on who it's for and what they'll be able to do after reading it.",
#       "inside": ["What's inside, point 1", "Point 2", "Point 3"],
#   },
"""

EBOOKS = [
    {
        'slug': 'cdl-inspection-study-pack',
        'title': 'CDL Inspection Study Pack',
        'subtitle': 'Every inspection guide and checklist in one bundle, for less than buying them separately',
        'price': '$19.99',
        'url': 'https://www.mycdlcoach.com/offers/KbexLKiH/checkout',
        'cover': 'https://kajabi-storefronts-production.kajabi-cdn.com/kajabi-storefronts-production/file-uploads/themes/2164511746/settings_images/fd8234-1760-4e5-1bac-15f3a40a11fc_812416c8-c32f-4808-874b-9be40bf52442.png',
        'pages': 'Digital download, print-friendly and mobile-ready',
        'description': 'The essential guides and checklists drivers use to learn truck inspections and prepare for the CDL skills test, bundled together. Built for CDL students, new drivers, and anyone learning proper inspection procedures.',
        'inside': ['Class A Pre-Trip Inspection Study Guide', '4-Point Brake Check Guide', 'Comprehensive Pre-Trip Inspection Checklist', 'En-Route Inspection Checklist', 'Post-Trip DVIR Checklist', 'CDL Truck Driver Career Guide'],
    },
    {
        'slug': 'cdl-study-guide-2026-2027',
        'title': 'CDL Study Guide 2026–2027',
        'subtitle': 'With practice questions',
        'price': '$19.99',
        'url': 'https://www.mycdlcoach.com/offers/2qbTGyec/checkout',
        'cover': 'https://kajabi-storefronts-production.kajabi-cdn.com/kajabi-storefronts-production/file-uploads/themes/2165459837/settings_images/6e12c75-200-3de3-8164-ccfb20cf2a3_6ad91446-8f48-4f8e-9340-5dadd3fa1f8c.png',
        'pages': 'Digital download',
        'description': 'A study guide with practice questions to help you prepare for your CDL knowledge tests.',
    },
    {
        'slug': 'class-a-pre-trip-brake-check-guide',
        'title': 'Class A CDL Pre-Trip Inspection & 4-Point Brake Check Study Guide',
        'subtitle': 'A visual, step-by-step guide for the CDL skills test',
        'price': '$8.99',
        'url': 'https://www.mycdlcoach.com/offers/iDqqKoGN/checkout',
        'cover': 'https://kajabi-storefronts-production.kajabi-cdn.com/kajabi-storefronts-production/file-uploads/themes/2165159078/settings_images/5dcf028-78ee-d6eb-8ce7-bdfd6b7adfd_7cda4b62-2f88-4792-b3f5-2bddd1612831.jpeg',
        'pages': 'Digital download',
        'description': 'A visual study guide that helps CDL students identify truck components and complete the full pre-trip inspection and brake check on the CDL skills test.',
        'inside': ['How to perform a complete Class A pre-trip inspection', 'The 4-point brake check procedure used during testing', 'Labeled diagrams of key truck components and inspection points', "An inspection order that's easy to remember", 'What examiners look for during the inspection portion'],
    },
    {
        'slug': 'pre-trip-inspection-checklist',
        'title': 'Comprehensive CDL Pre-Trip Inspection Checklist',
        'subtitle': 'Fillable, printable daily checklist',
        'price': '$4.99',
        'url': 'https://www.mycdlcoach.com/offers/o6KzvXL2/checkout',
        'cover': 'https://kajabi-storefronts-production.kajabi-cdn.com/kajabi-storefronts-production/file-uploads/themes/2164511780/settings_images/f10852-c5f-8713-72f-4f6661712bc_33f6d3c1-4397-4e8f-b688-6f8d1c7a5587.png',
        'pages': 'Printable and digital checklist',
        'description': 'A fillable, signature-ready pre-trip inspection checklist for daily recordkeeping. Print it or use it on your phone to stay organized and audit-ready.',
    },
    {
        'slug': 'en-route-inspection-checklist',
        'title': 'En-Route Inspection Checklist for CDL Drivers',
        'subtitle': 'Quick checks at fuel stops and breaks',
        'price': '$4.99',
        'url': 'https://www.mycdlcoach.com/offers/tBJNowSL/checkout',
        'cover': 'https://kajabi-storefronts-production.kajabi-cdn.com/kajabi-storefronts-production/file-uploads/themes/2164511755/settings_images/0222e3c-7586-fc71-70d0-a04ea4d40c7b_f56f7ad2-5908-41a7-8fc3-42ec3ed445b3.png',
        'pages': 'PDF checklist',
        'description': 'A checklist for quick en-route inspections during fuel stops and breaks, to help catch mechanical problems before they turn into breakdowns or roadside violations.',
    },
    {
        'slug': 'post-trip-inspection-checklist',
        'title': 'Post-Trip Inspection Checklist (DVIR)',
        'subtitle': 'Fillable, signature-ready post-trip form',
        'price': '$4.99',
        'url': 'https://www.mycdlcoach.com/offers/3ds2FMFe/checkout',
        'cover': 'https://kajabi-storefronts-production.kajabi-cdn.com/kajabi-storefronts-production/file-uploads/themes/2164511753/settings_images/ac727b8-a68b-0427-2af8-47ea87ca713_5cf481fc-f375-4305-97ad-b55373497a17.png',
        'pages': 'Printable and digital checklist',
        'description': 'A fillable post-trip inspection checklist for your daily driver vehicle inspection report (DVIR). Print it or use it on your phone for daily logs, inspections, and audits.',
    },
    {
        'slug': 'trucking-business-startup-guide',
        'title': 'Trucking Business Startup Guide',
        'subtitle': 'For new owner-operators and small fleets',
        'price': '$24.99',
        'url': 'https://www.mycdlcoach.com/offers/QbTWMoUX/checkout',
        'cover': 'https://kajabi-storefronts-production.kajabi-cdn.com/kajabi-storefronts-production/file-uploads/themes/2165463309/settings_images/885714b-d3bf-7d27-5585-30ff8f0e088_82108321-fb49-4a79-9dda-b5e888466370.png',
        'pages': 'Digital download',
        'description': 'A guide for drivers starting their own trucking business.',
    },
    {
        'slug': 'trucking-business-starter-kit',
        'title': 'Trucking Business Starter Kit',
        'subtitle': 'Templates, forms & compliance pack',
        'price': '$19.99',
        'url': 'https://www.mycdlcoach.com/offers/hf997qVL/checkout',
        'cover': 'https://kajabi-storefronts-production.kajabi-cdn.com/kajabi-storefronts-production/file-uploads/themes/2165500553/settings_images/c7f30fd-eef1-e412-b4cc-71cd14154db0_1faa96e7-474d-4fb3-a8a5-0f5549f14903.jpeg',
        'pages': 'Digital download',
        'description': 'Templates, forms, and a compliance pack for running a small trucking business.',
    },
    {
        'slug': 'owner-operator-startup-checklist',
        'title': 'Owner Operator Startup Checklist',
        'subtitle': 'Step by step to your own authority',
        'price': '$9.99',
        'url': 'https://www.mycdlcoach.com/offers/Ao2AEYic/checkout',
        'cover': '',
        'pages': 'Digital download',
        'description': 'A checklist for drivers getting set up as owner-operators.',
    },
    {
        'slug': 'trucking-insurance-guide',
        'title': 'Trucking Insurance Guide',
        'subtitle': 'For owner-operators and small fleets',
        'price': '$9.99',
        'url': 'https://www.mycdlcoach.com/offers/3kXtTMfM/checkout',
        'cover': 'https://kajabi-storefronts-production.kajabi-cdn.com/kajabi-storefronts-production/file-uploads/themes/2165500667/settings_images/374d7a3-d5b-4ee-7af-80d3cacf475_a0cfb57b-b7f5-4ab8-a8bc-da41e36aad44.jpeg',
        'pages': 'Digital download',
        'description': 'A guide to insurance for trucking companies, owner-operators, and small fleets.',
    },
    {
        'slug': 'freight-dispatching-blueprint-2026',
        'title': 'Freight Dispatching Blueprint 2026',
        'subtitle': 'Ebook, or ebook + audiobook',
        'price': '$29.99',
        'url': 'https://www.mycdlcoach.com/offers/ymzFCUNZ/checkout',
        'options': [{'label': 'Ebook', 'price': '$29.99', 'url': 'https://www.mycdlcoach.com/offers/ymzFCUNZ/checkout'}, {'label': 'Ebook + Audiobook', 'price': '$79.99', 'url': 'https://www.mycdlcoach.com/offers/moxiyyDP/checkout'}],
        'cover': 'https://kajabi-storefronts-production.kajabi-cdn.com/kajabi-storefronts-production/file-uploads/themes/2164912830/settings_images/d2db8b-5e73-182-0fe5-e7851bd5718_Screenshot_17-2-2026_10504_www.canva.com.jpeg',
        'pages': 'Digital download',
        'description': "Learn how freight dispatchers work in today's trucking industry. This guide covers load boards, negotiating with brokers, dispatcher agreements, and the tools used to manage freight and carriers.",
    },
]
