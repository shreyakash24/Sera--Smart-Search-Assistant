from autogen import AssistantAgent, UserProxyAgent
from autogen import register_function
from playwright.sync_api import sync_playwright
import json

llm_config = {
    "config_list": [
        {
            "model": "deepseek/deepseek-r1-0528-qwen3-8b:free",  
            "api_key": "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",
            "base_url": "https://openrouter.ai/api/v1"
        }
    ],
}

system_prompt='''You are a DOM selector extraction assistant. 

You are an Accessibility-Aware Web Automation Agent.
Your job is to analyze a user task together with an accessibility tree (containing only role, name, description, and children) and decide what 
operation to perform and which element to target.

**Your Role

-Interpret the user's intent (e.g., click, type, select, read).
-Locate the best matching element in the accessibility tree.
-Provide a structured answer with reasoning.


**Input structure:
-Accessibilty tree of a webpage contains dictionaries having:
  role-It can be text,button,link,image,textbox,heading,tag,main,etc.
  name-It is the actual content of the role
  description:Description about the element
  readonly-It is either true or false which tells the element with the given role is interactive or only readable.
  value-The value of the element having the role as role&name as name given in accesbilty tree.

**Reasoning Plan:

-Parse the user task
-Identify the operation: click/open/navigate, type/enter/search, choose/select/check, read/get.
-Identify the target concept
-Infer candidate roles by operation
-Remember the date,no of entities selection is of type: radio,option or select.
 examples:
   Click/open/navigate → link, button, menuitem.
   Type/enter/search → textbox, searchbox, combobox,button.
   Choose/select/check → checkbox, radio, option,select. 
   Read/get info → heading, text.
   
-Match by text cues
-Reason about the user task and decide which should be the role,name or description and opeartion accordigly.
-First try exact match on name.
-If none, try substring/fuzzy match.
-If still none, look at description.
-Normalize text (ignore case/extra spaces).

-Return structured output
-Always return a JSON object with:
 example:
   {
  "action": "click | type | select | read",
  "target": {
    "role": "...",
    "name": "...",
    "description": "..."{if there*}
  },
  "reason": "Explain why this element matches the user task",
   }

**Rules:
-For role as textbox ,if readonly is true so instead of 'type' ,the action action u need to perform is 'click'.
-For date selection,no of people,entities selection,etc always click first.
VeryIMP:The selected action should not contain role as 'text leaf' as it cannot be interacted with,unless the task is of just read or extract,
        else for interaction u should look for 'textbox' instead. For elements with almost same name and meaning having both textleaf and textbox ,always select the textbox. 
Always output in proper JSON format only ,so it can be used afterwards using json.loads().
Strictly follow this format only in JSON.
Format:
 {
  "action": "click | type | select | read",
  "target": {
    "role": "...",
    "name": "...",
    "value":"..."{if any*}
    "description": "..."{if there*}
  },
  "reason": "Explain why this element matches the user task",
   }
        
Example1:
User Task:
"Find the cheapest phone and add it to cart, then proceed to checkout."

Accessibility tree snippet:
[{"role":"textbox","name":"Search"},{"role":"button","name":"Search"},{"role":"link","name":"Home"},{"role":"link","name":"Categories"},{"role":"link","name":"Phones"},{"role":"link","name":"Laptops"},{"role":"link","name":"Phone X – $899"},{"role":"link","name":"Phone Y – $499"},{"role":"link","name":"Phone Z – $750"},{"role":"button","name":"Add to Cart"},{"role":"button","name":"Wishlist"},{"role":"link","name":"Cart"},{"role":"button","name":"Checkout"}]

Model Output:
{
  "actions": [
    {
      "action": "click",
      "target": { "role": "link", "name": "Phone Y - $499" },
    },
    {
      "action": "click",
      "target": { "role": "button", "name": "Add to Cart" },
    },
    {
      "action": "click",
      "target": { "role": "link", "name": "Cart" },
    
    },
    {
      "action": "click",
      "target": { "role": "button", "name": "Checkout" },
    }
  ]
}


Example2:
User Task:
"Apply for the 'Software Engineer' position and upload resume with any input name,email number of your choice."

Accessibility Tree:
[{"role":"link","name":"Home"},{"role":"link","name":"Jobs"},{"role":"link","name":"About"},{"role":"textbox","name":"Search Jobs"},{"role":"button","name":"Search"},{"role":"link","name":"Software Engineer"},{"role":"link","name":"Data Scientist"},{"role":"link","name":"Product Manager"},{"role":"textbox","name":"Full Name"},{"role":"textbox","name":"Email"},{"role":"textbox","name":"Phone"},{"role":"textbox","name":"Resume Upload"},{"role":"button","name":"Submit Application"},{"role":"button","name":"Cancel"}]

Model Output:
{
  "actions": [
    {
      "action": "click",
      "target": { "role": "link", "name": "Software Engineer" },
    },
    {
      "action": "type",
      "target": { "role": "textbox", "name": "Full Name" },
      "value": "John Doe",
    },
    {
      "action": "type",
      "target": { "role": "textbox", "name": "Email" },
      "value": "john@example.com",
    },
    {
      "action": "type",
      "target": { "role": "textbox", "name": "Phone" },
      "value": "9876543210",
    },
    {
      "action": "upload",
      "target": { "role": "textbox", "name": "Resume Upload" },
      "value": "resume.pdf",
    },
    {
      "action": "click",
      "target": { "role": "button", "name": "Submit Application" },
    }
  ]
}


'''
# tree={'role': 'WebArea', 'name': 'Online Shopping site in India: Shop Online for Mobiles, Books, Watches, Shoes and More - Amazon.in', 'children': [{'role': 'navigation', 'name': 'Shortcuts menu', 'children': [{'role': 'heading', 'name': 'Skip to', 'level': 2}, {'role': 'link', 'name': 'main content', 'description': "To move between items, use your keyboard's up or down arrows."}, {'role': 'heading', 'name': 'Keyboard shortcuts', 'level': 2}, {'role': 'link', 'name': 'Search, alt, forward slash', 'description': "To move between items, use your keyboard's up or down arrows."}, {'role': 'link', 'name': 'Cart, shift, alt, c', 'description': "To move between items, use your keyboard's up or down arrows."}, {'role': 'link', 'name': 'Home, shift, alt, h', 'description': "To move between items, use your keyboard's up or down arrows."}, {'role': 'link', 'name': 'Your orders, shift, alt, o', 'description': "To move between items, use your keyboard's up or down arrows."}, {'role': 'button', 'name': 'Show/hide shortcuts, shift, alt, z', 'description': "To move between items, use your keyboard's up or down arrows."}, {'role': 'text', 'name': "To move between items, use your keyboard's up or down arrows."}]}, {'role': 'link', 'name': 'Amazon.in'}, {'role': 'button', 'name': 'Delivering to Vasai 401201 Update location'}, {'role': 'text', 'name': 'All'}, {'role': 'combobox', 'name': '', 'description': 'Select the department you want to search in', 'haspopup': 'menu', 'children': [{'role': 'option', 'name': 'All Categories', 'selected': True}, {'role': 'option', 'name': 'Alexa Skills'}, {'role': 'option', 'name': 'Amazon Devices'}, {'role': 'option', 'name': 'Amazon Fashion'}, {'role': 'option', 'name': 'Amazon Fresh Meat'}, {'role': 'option', 'name': 'Amazon Pharmacy'}, {'role': 'option', 'name': 'Appliances'}, {'role': 'option', 'name': 'Apps & Games'}, {'role': 'option', 'name': 'Audible Audiobooks'}, {'role': 'option', 'name': 'Baby'}, {'role': 'option', 'name': 'Beauty'}, {'role': 'option', 'name': 'Books'}, {'role': 'option', 'name': 'Car & Motorbike'}, {'role': 'option', 'name': 'Clothing & Accessories'}, {'role': 'option', 'name': 'Collectibles'}, {'role': 'option', 'name': 'Computers & Accessories'}, {'role': 'option', 'name': 'Deals'}, {'role': 'option', 'name': 'Electronics'}, {'role': 'option', 'name': 'Furniture'}, {'role': 'option', 'name': 'Garden & Outdoors'}, {'role': 'option', 'name': 'Gift Cards'}, {'role': 'option', 'name': 'Grocery & Gourmet Foods'}, {'role': 'option', 'name': 'Health & Personal Care'}, {'role': 'option', 'name': 'Home & Kitchen'}, {'role': 'option', 'name': 'Industrial & Scientific'}, {'role': 'option', 'name': 'Jewellery'}, {'role': 'option', 'name': 'Kindle Store'}, {'role': 'option', 'name': 'Luggage & Bags'}, {'role': 'option', 'name': 'Luxury Beauty'}, {'role': 'option', 'name': 'Movies & TV Shows'}, {'role': 'option', 'name': 'MP3 Music'}, {'role': 'option', 'name': 'Music'}, {'role': 'option', 'name': 'Musical Instruments'}, {'role': 'option', 'name': 'Office Products'}, {'role': 'option', 'name': 'Pet Supplies'}, {'role': 'option', 'name': 'Prime Video'}, {'role': 'option', 'name': 'Shoes & Handbags'}, {'role': 'option', 'name': 'Software'}, {'role': 'option', 'name': 'Sports, Fitness & Outdoors'}, {'role': 'option', 'name': 'Subscribe & Save'}, {'role': 'option', 'name': 'Tools & Home Improvement'}, {'role': 'option', 'name': 'Toys & Games'}, {'role': 'option', 'name': 'Under ₹500'}, {'role': 'option', 'name': 'Video Games'}, {'role': 'option', 'name': 'Watches'}], 'value': 'All Categories'}, {'role': 'searchbox', 'name': 'Search Amazon.in', 'autocomplete': 'list', 'haspopup': 'grid'}, {'role': 'button', 'name': 'Go'}, {'role': 'link', 'name': 'Choose a language for shopping in Amazon India. The current selection is English (EN). '}, {'role': 'button', 'name': 'Expand to Change Language or Country'}, {'role': 'link', 'name': 'Hello, sign in Account & Lists'}, {'role': 'button', 'name': 'Expand Account and Lists'}, {'role': 'link', 'name': 'Returns & Orders'}, {'role': 'link', 'name': '0 items in cart'}, {'role': 'button', 'name': 'Open All Categories Menu'}, {'role': 'link', 'name': 'Fresh Meat'}, {'role': 'link', 'name': 'MX Player'}, {'role': 'link', 'name': 'Sell'}, {'role': 'link', 'name': 'Bestsellers'}, {'role': 'link', 'name': "Today's Deals"}, {'role': 'link', 'name': 'Mobiles'}, {'role': 'link', 'name': 'Prime'}, {'role': 'button', 'name': 'Prime Details'}, {'role': 'link', 'name': 'Customer Service'}, {'role': 'link', 'name': 'Electronics'}, {'role': 'link', 'name': 'Fashion'}, {'role': 'link', 'name': 'New Releases'}, {'role': 'link', 'name': 'Home & Kitchen'}, {'role': 'link', 'name': 'Amazon Pay'}, {'role': 'link', 'name': 'Computers'}, {'role': 'link', 'name': 'Books'}, {'role': 'link', 'name': 'Beauty & Personal Care'}, {'role': 'link', 'name': 'Car & Motorbike'}, {'role': 'link', 'name': 'Home Improvement'}, {'role': 'link', 'name': 'Toys & Games'}, {'role': 'link', 'name': 'Video Games'}, {'role': 'link', 'name': 'Sports, Fitness & Outdoors'}, {'role': 'link', 'name': 'Gift Cards'}, {'role': 'link', 'name': 'Health, Household & Personal Care'}, {'role': 'link', 'name': 'Custom Products'}, {'role': 'link', 'name': 'Grocery & Gourmet Foods'}, {'role': 'link', 'name': 'Baby'}, {'role': 'link', 'name': 'Subscribe & Save'}, {'role': 'link', 'name': 'AmazonBasics'}, {'role': 'link', 'name': 'Pet Supplies'}, {'role': 'link', 'name': 'Audible'}, {'role': 'link', 'name': 'Gift Ideas'}, {'role': 'link', 'name': 'Flights'}, {'role': 'generic', 'name': ''}, {'role': 'link', 'name': 'Previous slide', 'disabled': True}, {'role': 'link', 'name': 'Deals'}, {'role': 'link', 'name': 'Next slide'}, {'role': 'heading', 'name': 'Revamp your home in style', 'level': 2}, {'role': 'link', 'name': 'Cushion covers, bedsheets & more'}, {'role': 'link', 'name': 'Figurines, vases & more'}, {'role': 'link', 'name': 'Home storage'}, {'role': 'link', 'name': 'Lighting solutions'}, {'role': 'link', 'name': 'Revamp your home in style - Explore all'}, {'role': 'heading', 'name': 'Appliances for your home | Up to 55% off', 'level': 2}, {'role': 'link', 'name': 'ACs'}, {'role': 'link', 'name': 'Refrigerators'}, {'role': 'link', 'name': 'Microwaves'}, {'role': 'link', 'name': 'Washing machines'}, {'role': 'link', 'name': 'Appliances for your home | Up to 55% off - See more'}, {'role': 'heading', 'name': 'Starting ₹149 | Headphones', 'level': 2}, {'role': 'link', 'name': 'boAt'}, {'role': 'link', 'name': 'boult'}, {'role': 'link', 'name': 'Noise'}, {'role': 'link', 'name': 'Starting ₹149 | Zebronics'}, {'role': 'link', 'name': 'Starting ₹149 | Headphones - See all offers'}, {'role': 'heading', 'name': 'Sign in for your best experience', 'level': 2}, {'role': 'link', 'name': 'Sign in securely'}, {'role': 'Iframe', 'name': 'Sponsored ad'}, {'role': 'button', 'name': 'Leave feedback on Sponsored advertisement'}, {'role': 'heading', 'name': 'Under ₹499 | Deals on home improvement essentials', 'level': 2}, {'role': 'link', 'name': 'Cleaning'}, {'role': 'link', 'name': 'Bath accessories'}, {'role': 'link', 'name': 'Home tools'}, {'role': 'link', 'name': 'Wallpapers'}, {'role': 'link', 'name': 'Under ₹499 | Deals on home improvement essentials - Explore all'}, {'role': 'heading', 'name': 'Automotive essentials | Up to 60% off', 'level': 2}, {'role': 'link', 'name': 'Cleaning accessories'}, {'role': 'link', 'name': 'Tyre & rim care'}, {'role': 'link', 'name': 'Helmets'}, {'role': 'link', 'name': 'Vacuum cleaner'}, {'role': 'link', 'name': 'Automotive essentials | Up to 60% off - See more'}, {'role': 'heading', 'name': 'Starting ₹199 | Amazon Brands & more', 'level': 2}, {'role': 'link', 'name': 'Starting ₹199 | Bedsheets'}, {'role': 'link', 'name': 'Starting ₹199 | Curtains'}, {'role': 'link', 'name': 'Minimum 40% off | Ironing board & more'}, {'role': 'link', 'name': 'Up to 60% off | Home decor'}, {'role': 'link', 'name': 'Starting ₹199 | Amazon Brands & more - See more'}, {'role': 'heading', 'name': 'Up to 50% off | Baby care & toys | Amazon Brands', 'level': 2}, {'role': 'link', 'name': 'Up to 50% off | Baby diapers & wipes'}, {'role': 'link', 'name': 'Up to 50% off | Ride ons'}, {'role': 'link', 'name': 'Starting ₹649 | RC cars'}, {'role': 'link', 'name': 'Up to 50% off | Baby safety essentials'}, {'role': 'link', 'name': 'Up to 50% off | Baby care & toys | Amazon Brands - See all offers'}, {'role': 'heading', 'name': 'Starting ₹499 | Level up your playtime', 'level': 2}, {'role': 'link', 'name': 'See all offers'}, {'role': 'link', 'name': 'Sony PlayStation5 Gaming Console (Slim)'}, {'role': 'link', 'name': 'Rockstar Games PS5 Video Game ConsoleGrand Theft Auto V'}, {'role': 'link', 'name': 'Sony Ps5 Spiderman 2 Standard Edn.'}, {'role': 'link', 'name': 'PowerA FUSION Pro Wireless Gaming Controller with Lumectra for Xbox Series X/S, Xbox One, PC, Windows 10/11 with Ghost...'}, {'role': 'link', 'name': 'EvoFox Deck Smartphone Gamepad with iPhone/Android, XBOX, HID & Keymap modes | Bluetooth v5.0 | Dual Vibration motors |...'}, {'role': 'link', 'name': 'DualSense Wireless Controller | PlayStation 5 (White)'}, {'role': 'link', 'name': 'Abxylute Handheld Gaming Console Streaming 1080P 7-Inch Portable Console, Compatible with PC PlayStation Xbox Nintendo...'}, {'role': 'link', 'name': 'PowerA Battle Dragon™ Wireless Controller for PC and Cloud Gaming: Magnetic Hall Effect, Asymmetric Rumble Motors, 20h...'}, {'role': 'link', 'name': 'PowerA Enhanced Wired Gaming Controller for Xbox Series X/S, Xbox One, PC, Windows 10/11, Arc Lightning, Blue...'}, {'role': 'link', 'name': 'EvoFox Blaze Ultra Value 8 Button Programmable Gaming Mouse with 1000Hz Polling Rate | Gaming Grade DPI 200 to 12800 |...'}, {'role': 'link', 'name': 'PowerA Wired Gaming Controller for Xbox Series X/S, Xbox One, PC, Windows 10/11, Red (Officially Licensed)'}, {'role': 'link', 'name': 'EvoFox Katana S Mini Wireless Mechanical Keyboard | Tri-Mode (3X BT, 2.4GHz & Wired) Connectivity | Hot-Swappable Red...'}, {'role': 'link', 'name': 'Capcom Resident Evil 4 Remake | Standard Edition | PlayStation 5'}, {'role': 'link', 'name': 'Kreo Mirage Wireless RGB Gaming Controller For PC, PS4, Android, iOS with Bluetooth & USB C Connectivity, Hall effect...'}, {'role': 'link', 'name': 'Ant Esports KM1610 LED Keyboard and Mouse Combo, 104 Keys Rainbow Backlit Keyboard and 7 Colour RGB Mouse, White Gaming...'}, {'role': 'link', 'name': 'viboton Gaming Mouse | Wired USB 2.0, Mouse Gaming | RGB Mice, 3200 DPI LED Backlight 6 Button, 4 Color Breathing Lights...'}, {'role': 'link', 'name': 'ZEBRONICS-Transformer-M with a High-Performance Gold-Plated USB Mouse: 6 Buttons, Multi-Color LED Lights,High-Resolution...'}, {'role': 'link', 'name': 'EvoFox One S Universal 3-Mode Wireless Gaming Controller – HallSense™ Precision Joysticks, Bluetooth 5.0, 2.4GHz & Wired...'}, {'role': 'link', 'name': 'PULSE Explore™ wireless earbuds'}, {'role': 'link', 'name': 'BUYFLUX RGB Gaming Mouse, Wired USB 2.0 Optical Mouse, 4 Colors LED Backlight up to 1200 DPI, Ergonomic Design Mouse for...'}, {'role': 'link', 'name': 'Xbox Game Pass Ultimate : 1 Month Membership (Digital Code)'}, {'role': 'link', 'name': 'Nintendo Switch Lite Handheld Console Game- Coral'}, {'role': 'link', 'name': 'Nintendo Minecraft'}, {'role': 'link', 'name': 'Nintendo Switch Lite Gaming Console - Turquoise'}, {'role': 'link', 'name': 'Ninjadog Astra One Ultra - Hall effect Mobile Game Controller for PC/Mac/Linux/Unix, Android, iOS, Nintendo Switch'}, {'role': 'link', 'name': 'WB Games Hogwarts Legacy, Standard Edition, Nintendo Switch'}, {'role': 'link', 'name': 'Electronic Arts EA Sports FC 25 | Standard Edition | Nintendo Switch'}, {'role': 'link', 'name': 'Nintendo Switch Lite - Blue switch'}, {'role': 'link', 'name': 'Need for Speed Hot Pursuit Remastered (Nintendo Switch)'}, {'role': 'heading', 'name': 'Starting ₹70,348 | Set off on your next great ride', 'level': 2}, {'role': 'link', 'name': 'See all offers'}, {'role': 'link', 'name': 'Bajaj Avenger 220 Cruise Motorcycle/Motorbike - Auburn Black - Ex-Showroom'}, {'role': 'link', 'name': 'KTM Duke 390 Bike Gunmetal Metallic Booking For Ex-Showroom Price'}
# tree={'role': 'document', 'name': 'Flight Booking, Cheap Flights , Air Ticket Booking at Lowest Airfare | MakeMyTrip', 'children': [{'role': 'text container', 'name': '', 'children': [{'role': 'section', 'name': '', 'children': [{'role': 'section', 'name': '', 'children': [{'role': 'section', 'name': '', 'children': [{'role': 'link', 'name': 'Make My Trip', 'children': [{'role': 'img', 'name': 'Make My Trip'}]}, {'role': 'list', 'name': '', 'children': [{'role': 'listitem', 'name': 'List Your Property Grow your business!', 'children': [{'role': 'text container', 'name': ''}, {'role': 'paragraph', 'name': '', 'children': [{'role': 'text leaf', 'name': 'List Your Property'}]}, {'role': 'paragraph', 'name': '', 'children': [{'role': 'text leaf', 'name': 'Grow your business!'}]}]}, {'role': 'listitem', 'name': '\xa0 Introducing myBiz Business Travel Solution', 'children': [{'role': 'text container', 'name': '', 'children': [{'role': 'text leaf', 'name': '\xa0'}]}, {'role': 'paragraph', 'name': '', 'children': [{'role': 'text leaf', 'name': 'Introducing myBiz'}]}, {'role': 'paragraph', 'name': '', 'children': [{'role': 'text leaf', 'name': 'Business Travel Solution'}]}]}, {'role': 'listitem', 'name': '\xa0 My Trips Manage your bookings', 'children': [{'role': 'text container', 'name': '', 'children': [{'role': 'text leaf', 'name': '\xa0'}]}, {'role': 'paragraph', 'name': '', 'children': [{'role': 'text leaf', 'name': 'My Trips'}]}, {'role': 'paragraph', 'name': '', 'children': [{'role': 'text leaf', 'name': 'Manage your bookings'}]}]}, {'role': 'listitem', 'name': '\xa0 Login or Create Account', 'children': [{'role': 'text container', 'name': '', 'children': [{'role': 'text leaf', 'name': '\xa0'}]}, {'role': 'paragraph', 'name': '', 'children': [{'role': 'text leaf', 'name': 'Login or Create Account'}]}]}, {'role': 'listitem', 'name': 'INR | English', 'children': [{'role': 'text container', 'name': '', 'children': [{'role': 'text container', 'name': ''}, {'role': 'text container', 'name': '', 'children': [{'role': 'text leaf', 'name': 'INR'}]}, {'role': 'text leaf', 'name': '|'}, {'role': 'text container', 'name': '', 'children': [{'role': 'text leaf', 'name': 'English'}]}, {'role': 'text container', 'name': ''}]}]}]}, {'role': 'text container', 'name': ''}, {'role': 'landmark', 'name': '', 'children': [{'role': 'list', 'name': '', 'children': [{'role': 'listitem', 'name': 'Flights', 'children': [{'role': 'text container', 'name': '', 'children': [{'role': 'link', 'name': 'Flights', 'children': [{'role': 'text container', 'name': ''}, {'role': 'text container', 'name': '', 'children': [{'role': 'text leaf', 'name': 'Flights', 'value': 'https://www.makemytrip.com/flights/'}]}], 'value': 'https://www.makemytrip.com/flights/'}]}]}, {'role': 'listitem', 'name': 'Hotels', 'children': [{'role': 'text container', 'name': '', 'children': [{'role': 'link', 'name': 'Hotels', 'children': [{'role': 'text container', 'name': ''}, {'role': 'text container', 'name': '', 'children': [{'role': 'text leaf', 'name': 'Hotels', 'value': 'https://www.makemytrip.com/hotels/'}]}], 'value': 'https://www.makemytrip.com/hotels/'}]}]}, {'role': 'listitem', 'name': 'Homestays & Villas', 'children': [{'role': 'text container', 'name': '', 'children': [{'role': 'link', 'name': 'Homestays & Villas', 'children': [{'role': 'text container', 'name': ''}, {'role': 'text container', 'name': '', 'children': [{'role': 'text leaf', 'name': 'Homestays & Villas', 'value': 'https://www.makemytrip.com/homestays/'}]}], 'value': 'https://www.makemytrip.com/homestays/'}]}]}, {'role': 'listitem', 'name': 'Holiday Packages', 'children': [{'role': 'text container', 'name': '', 'children': [{'role': 'link', 'name': 'Holiday Packages', 'children': [{'role': 'text container', 'name': ''}, {'role': 'text container', 'name': '', 'children': [{'role': 'text leaf', 'name': 'Holiday Packages', 'value': 'https://www.makemytrip.com/holidays-india/'}]}], 'value': 'https://www.makemytrip.com/holidays-india/'}]}]}, {'role': 'listitem', 'name': 'Trains', 'children': [{'role': 'text container', 'name': '', 'children': [{'role': 'link', 'name': 'Trains', 'children': [{'role': 'text container', 'name': ''}, {'role': 'text container', 'name': '', 'children': [{'role': 'text leaf', 'name': 'Trains', 'value': 'https://www.makemytrip.com/railways/'}]}], 'value': 'https://www.makemytrip.com/railways/'}]}]}, {'role': 'listitem', 'name': 'Buses', 'children': [{'role': 'text container', 'name': '', 'children': [{'role': 'link', 'name': 'Buses', 'children': [{'role': 'text container', 'name': ''}, {'role': 'text container', 'name': '', 'children': [{'role': 'text leaf', 'name': 'Buses', 'value': 'https://www.makemytrip.com/bus-tickets/'}]}], 'value': 'https://www.makemytrip.com/bus-tickets/'}]}]}, {'role': 'listitem', 'name': 'Cabs', 'children': [{'role': 'text container', 'name': '', 'children': [{'role': 'link', 'name': 'Cabs', 'children': [{'role': 'text container', 'name': ''}, {'role': 'text container', 'name': '', 'children': [{'role': 'text leaf', 'name': 'Cabs', 'value': 'https://www.makemytrip.com/cabs/'}]}], 'value': 'https://www.makemytrip.com/cabs/'}]}]}, {'role': 'listitem', 'name': 'Tours & Attractions new', 'children': [{'role': 'text container', 'name': '', 'children': [{'role': 'link', 'name': 'Tours & Attractions', 'children': [{'role': 'text container', 'name': ''}, {'role': 'text container', 'name': '', 'children': [{'role': 'text leaf', 'name': 'Tours & Attractions', 'value': 'https://www.makemytrip.com/toursandattractions'}]}], 'value': 'https://www.makemytrip.com/toursandattractions'}]}, {'role': 'text container', 'name': '', 'children': [{'role': 'text leaf', 'name': 'new'}]}]}, {'role': 'listitem', 'name': 'Visa new', 'children': [{'role': 'text container', 'name': '', 'children': [{'role': 'link', 'name': 'Visa', 'children': [{'role': 'text container', 'name': ''}, {'role': 'text container', 'name': '', 'children': [{'role': 'text leaf', 'name': 'Visa', 'value': 'https://visa.makemytrip.com/'}]}], 'value': 'https://visa.makemytrip.com/'}]}, {'role': 'text container', 'name': '', 'children': [{'role': 'text leaf', 'name': 'new'}]}]}, {'role': 'listitem', 'name': 'Cruise new', 'children': [{'role': 'text container', 'name': '', 'children': [{'role': 'link', 'name': 'Cruise', 'children': [{'role': 'text container', 'name': ''}, {'role': 'text container', 'name': '', 'children': [{'role': 'text leaf', 'name': 'Cruise', 'value': 'https://www.makemytrip.com/cruise/'}]}], 'value': 'https://www.makemytrip.com/cruise/'}]}, {'role': 'text container', 'name': '', 'children': [{'role': 'text leaf', 'name': 'new'}]}]}, {'role': 'listitem', 'name': 'Forex Card & Currency', 'children': [{'role': 'text container', 'name': '', 'children': [{'role': 'link', 'name': 'Forex Card & Currency', 'children': [{'role': 'text container', 'name': ''}, {'role': 'text container', 'name': '', 'children': [{'role': 'text leaf', 'name': 'Forex Card & Currency', 'value': 'https://www.makemytrip.com/forex/'}]}], 'value': 'https://www.makemytrip.com/forex/'}]}]}, {'role': 'listitem', 'name': 'Travel Insurance', 'children': [{'role': 'text container', 'name': '', 'children': [{'role': 'link', 'name': 'Travel Insurance', 'children': [{'role': 'text container', 'name': ''}, {'role': 'text container', 'name': '', 'children': [{'role': 'text leaf', 'name': 'Travel Insurance', 'value': 'https://www.makemytrip.com/insurance/'}]}], 'value': 'https://www.makemytrip.com/insurance/'}]}]}]}]}]}, {'role': 'list', 'name': '', 'children': [{'role': 'listitem', 'name': 'One Way', 'children': [{'role': 'text container', 'name': ''}, {'role': 'text leaf', 'name': 'One Way'}]}, {'role': 'listitem', 'name': 'Round Trip', 'children': [{'role': 'text container', 'name': ''}, {'role': 'text leaf', 'name': 'Round Trip'}]}, {'role': 'listitem', 'name': 'Multi City', 'children': [{'role': 'text container', 'name': ''}, {'role': 'text leaf', 'name': 'Multi City'}]}]}, {'role': 'paragraph', 'name': '', 'children': [{'role': 'text leaf', 'name': 'Book'}, {'role': 'text leaf', 'name': '\xa0'}, {'role': 'link', 'name': 'International', 'children': [{'role': 'text leaf', 'name': 'International', 'value': 'https://www.makemytrip.com/international-flights/'}], 'value': 'https://www.makemytrip.com/international-flights/'}, {'role': 'text leaf', 'name': '\xa0'}, {'role': 'text leaf', 'name': 'and'}, {'role': 'text leaf', 'name': '\xa0'}, {'role': 'link', 'name': 'Domestic Flights', 'children': [{'role': 'text leaf', 'name': 'Domestic Flights', 'value': 'https://www.makemytrip.com/flights/'}], 'value': 'https://www.makemytrip.com/flights/'}]}, {'role': 'section', 'name': '', 'children': [{'role': 'label', 'name': 'From Delhi DEL, Delhi Airport India', 'children': [{'role': 'text container', 'name': '', 'children': [{'role': 'text leaf', 'name': 'From'}]}, {'role': 'textbox', 'name': 'From DEL, Delhi Airport India', 'readonly': True, 'children': [{'role': 'text leaf', 'name': 'Delhi'}], 'value': 'Delhi'}, {'role': 'paragraph', 'name': 'DEL, Delhi Airport India', 'children': [{'role': 'text container', 'name': '', 'children': [{'role': 'text leaf', 'name': 'DEL, Delhi Airport India'}]}]}]}, {'role': 'text container', 'name': '', 'children': [{'role': 'text leaf', 'name': '⇌'}]}, {'role': 'label', 'name': 'To Bengaluru BLR, Bengaluru International Airport India', 'children': [{'role': 'text container', 'name': '', 'children': [{'role': 'text leaf', 'name': 'To'}]}, {'role': 'textbox', 'name': 'To BLR, Bengaluru International Airport India', 'readonly': True, 'children': [{'role': 'text leaf', 'name': 'Bengaluru'}], 'value': 'Bengaluru'}, {'role': 'paragraph', 'name': 'BLR, Bengaluru International Airport India', 'children': [{'role': 'text container', 'name': '', 'children': [{'role': 'text leaf', 'name': 'BLR, Bengaluru International Airport India'}]}]}]}, {'role': 'label', 'name': "Departure Saturday, 30 Aug 2025 31 Aug'25 Sunday", 'children': [{'role': 'text container', 'name': '', 'children': [{'role': 'text leaf', 'name': 'Departure'}]}, {'role': 'textbox', 'name': "Departure 31 Aug'25 Sunday", 'readonly': True, 'children': [{'role': 'text leaf', 'name': 'Saturday, 30 Aug 2025'}], 'value': 'Saturday, 30 Aug 2025'}, {'role': 'paragraph', 'name': '', 'children': [{'role': 'text leaf', 'name': '31'}, {'role': 'text leaf', 'name': ' '}, {'role': 'text leaf', 'name': 'Aug'}, {'role': 'statictext', 'name': "'"}, {'role': 'text leaf', 'name': '25'}]}, {'role': 'paragraph', 'name': '', 'children': [{'role': 'text leaf', 'name': 'Sunday'}]}]}, {'role': 'section', 'name': '', 'children': [{'role': 'label', 'name': 'Return Tap to add a return date for bigger discounts', 'children': [{'role': 'text container', 'name': '', 'children': [{'role': 'text leaf', 'name': 'Return'}]}, {'role': 'paragraph', 'name': '', 'children': [{'role': 'text leaf', 'name': 'Tap to add a return date for bigger discounts'}]}]}]}, {'role': 'label', 'name': 'Travellers & Class 0 Infant, 0 Adult, 1 Children 1\xa0Traveller Economy/Premium Economy', 'children': [{'role': 'text container', 'name': '', 'children': [{'role': 'text leaf', 'name': 'Travellers & Class'}]}, {'role': 'textbox', 'name': 'Travellers & Class 1\xa0Traveller Economy/Premium Economy', 'readonly': True, 'children': [{'role': 'text leaf', 'name': '0 Infant, 0 Adult, 1 Children'}], 'value': '0 Infant, 0 Adult, 1 Children'}, {'role': 'paragraph', 'name': '', 'children': [{'role': 'text leaf', 'name': '1'}, {'role': 'text leaf', 'name': '\xa0'}, {'role': 'text leaf', 'name': 'Traveller'}]}, {'role': 'paragraph', 'name': '', 'children': [{'role': 'text leaf', 'name': 'Economy/Premium Economy'}]}]}]}, {'role': 'section', 'name': '', 'children': [{'role': 'section', 'name': '', 'children': [{'role': 'text leaf', 'name': 'Select a special fare'}]}, {'role': 'section', 'name': '', 'children': [{'role': 'text leaf', 'name': 'EXTRA SAVINGS'}]}]}, {'role': 'section', 'name': '', 'children': [{'role': 'section', 'name': '', 'children': [{'role': 'text container', 'name': '', 'children': [{'role': 'radio', 'name': '', 'checked': True}, {'role': 'text container', 'name': ''}]}]}]}]}]}]}]}

# tree={'role': 'document', 'name': 'Flight Booking, Cheap Flights , Air Ticket Booking at Lowest Airfare | MakeMyTrip', ' children': [{'role': 'img', 'name': 'Make My Trip'}, {'role': 'text leaf', 'name': 'List Your Property'}, {'role': 'text leaf', 'name': 'Grow your business!'}, {'role': 'text leaf', 'name': 'Introducing myBiz'}, {'role': 'text leaf', 'name': 'Business Travel Solution'}, {'role': 'text leaf', 'name': 'My Trips'}, {'role': 'text leaf', 'name': 'Manage your bookings'}, {'role': 'text leaf', 'name': 'Login or Create Account'}, {'role': 'text leaf', 'name': 'INR'}, {'role': 'text leaf', 'name': '|'}, {'role': 'text leaf', 'name': 'English'}, {'role': 'link', 'name': 'Flights', 'value': 'https://www.makemytrip.com/flights/'}, {'role': 'link', 'name': 'Hotels', 'value': 'https://www.makemytrip.com/hotels/'}, {'role': 'link', 'name': 'Homestays & Villas', 'value': 'https://www.makemytrip.com/homestays/'}, {'role': 'link', 'name': 'Holiday Packages', 'value': 'https://www.makemytrip.com/holidays-india/'}, {'role': 'link', 'name': 'Trains', 'value': 'https://www.makemytrip.com/railways/'}, {'role': 'link', 'name': 'Buses', 'value': 'https://www.makemytrip.com/bus-tickets/'}, {'role': 'link', 'name': 'Cabs', 'value': 'https://www.makemytrip.com/cabs/'}, {'role': 'link', 'name': 'Tours & Attractions', 'value': 'https://www.makemytrip.com/toursandattractions'}, {'role': 'text leaf', 'name': 'new'}, {'role': 'link', 'name': 'Visa', 'value': 'https://visa.makemytrip.com/'}, {'role': 'text leaf', 'name': 'new'}, {'role': 'link', 'name': 'Cruise', 'value': 'https://www.makemytrip.com/cruise/'}, {'role': 'text leaf', 'name': 'new'}, {'role': 'link', 'name': 'Forex Card & Currency', 'value': 'https://www.makemytrip.com/forex/'}, {'role': 'link', 'name': 'Travel Insurance', 'value': 'https://www.makemytrip.com/insurance/'}, {'role': 'text leaf', 'name': 'One Way'}, {'role': 'text leaf', 'name': 'Round Trip'}, {'role': 'text leaf', 'name': 'Multi City'}, {'role': 'text leaf', 'name': 'Book'}, {'role': 'link', 'name': 'International', 'value': 'https://www.makemytrip.com/international-flights/'}, {'role': 'text leaf', 'name': 'and'}, {'role': 'link', 'name': 'Domestic Flights', 'value': 'https://www.makemytrip.com/flights/'}, {'role': 'text leaf', 'name': 'From'}, {'role': 'textbox', 'name': 'From DEL, Delhi Airport India', 'readonly': True, 'value': 'Delhi'}, {'role': 'text leaf', 'name': 'DEL, Delhi Airport India'}, {'role': 'text leaf', 'name': '⇌'}, {'role': 'text leaf', 'name': 'To'}, {'role': 'textbox', 'name': 'To BLR, Bengaluru International Airport India', 'readonly': True, 'value': 'Bengaluru'}, {'role': 'text leaf', 'name': 'BLR, Bengaluru International Airport India'}, {'role': 'text leaf', 'name': 'Departure'}, {'role': 'textbox', 'name': "Departure 31 Aug'25 Sunday", 'readonly': True, 'value': 'Saturday, 30 Aug 2025'}, {'role': 'text leaf', 'name': '31'}, {'role': 'text leaf', 'name': 'Aug'}, {'role': 'statictext', 'name': "'"}, {'role': 'text leaf', 'name': '25'}, {'role': 'text leaf', 'name': 'Sunday'}, {'role': 'text leaf', 'name': 'Return'}, {'role': 'text leaf', 'name': 'Tap to add a return date for bigger discounts'}, {'role': 'text leaf', 'name': 'Travellers & Class'}, {'role': 'textbox', 'name': 'Travellers & Class 1\xa0Traveller Economy/Premium Economy', 'readonly': True, 'value': '0 Infant, 0 Adult, 1 Children'}, {'role': 'text leaf', 'name': '1'}, {'role': 'text leaf', 'name': 'Traveller'}, {'role': 'text leaf', 'name': 'Economy/Premium Economy'}, {'role': 'text leaf', 'name': 'Select a special fare'}, {'role': 'text leaf', 'name': 'EXTRA SAVINGS'}, {'role': 'radio', 'name': '', 'checked': True}, {'role': 'text leaf', 'name': 'Regular'}, {'role': 'text leaf', 'name': 'Regular fares'}, {'role': 'radio', 'name': ''}, {'role': 'text leaf', 'name': 'Student'}, {'role': 'text leaf', 'name': 'Extra discounts/baggage'}, {'role': 'radio', 'name': ''}, {'role': 'text leaf', 'name': 'Senior Citizen'}, {'role': 'text leaf', 'name': 'Up to ₹ 600 off'}, {'role': 'radio', 'name': ''}, {'role': 'text leaf', 'name': 'Armed Forces'}, {'role': 'text leaf', 'name': 'Up to ₹ 600 off'}, {'role': 'radio', 'name': ''}, {'role': 'text leaf', 'name': 'Doctor and Nurses'}, {'role': 'text leaf', 'name': 'Up to ₹ 600 off'}, {'role': 'button', 'name': 'Flight Tracker'}, {'role': 'checkbox', 'name': ''}, {'role': 'text leaf', 'name': 'Add FlexiFly'}, {'role': 'text leaf', 'name': '100% refund on cancellation or Zero date change charges'}, {'role': 'text leaf', 'name': 'View Details'}, {'role': 'text leaf', 'name': 'SEARCH'}, {'role': 'text leaf', 'name': 'Ask me anything'}, {'role': 'text leaf', 'name': 'Explore More'}, {'role': 'img', 'name': 'Where2Go_image'}, {'role': 'text leaf', 'name': 'Where2Go'}, {'role': 'img', 'name': 'Insurance_image'}, {'role': 'text leaf', 'name': 'Insurance'}, {'role': 'text leaf', 'name': 'For International Trips'}, {'role': 'img', 'name': "<span class='latoBold blackText font14'>Explore International Flights</span>_image"}, {'role': 'text leaf', 'name': 'Explore International Flights'}, {'role': 'text leaf', 'name': 'Cheapest Flights to Paris, Bali, Tokyo & more'}, {'role': 'img', 'name': 'MICE_image'}, {'role': 'text leaf', 'name': 'MICE'}, {'role': 'text leaf', 'name': 'Offsites, Events & Meetings'}, {'role': 'img', 'name': 'Gift Cards_image'}, {'role': 'text leaf', 'name': 'Gift Cards'}, {'role': 'heading', 'name': 'Experience Flying with our Airline Partners', 'level': 2}, {'role': 'heading', 'name': 'Offers', 'level': 2}, {'role': 'text leaf', 'name': 'All Offers'}, {'role': 'text leaf', 'name': 'Flights'}, {'role': 'text leaf', 'name': 'Hotels'}, {'role': 'text leaf', 'name': 'Holidays'}, {'role': 'text leaf', 'name': 'Trains'}, {'role': 'text leaf', 'name': 'Visa'}, {'role': 'text leaf', 'name': 'Cabs'}, {'role': 'text leaf', 'name': 'Bank Offers'}, {'role': 'text leaf', 'name': 'VIEW ALL'}, {'role': 'button', 'name': 'Previous'}, {'role': 'section', 'name': '', 'children': [{'role': 'section', 'name': '', 'children': [{'role': 'text leaf', 'name': 'INTL FLIGHTS'}, {'role': 'text leaf', 'name': "T&C'S APPLY"}, {'role': 'text leaf', 'name': 'LIVE NOW: Pay Day Sale by Akasa Air! '}, {'role': 'text leaf', 'name': 'with flight fares starting @ ₹1,399*. '}, {'role': 'text leaf', 'name': 'BOOK NOW'}]}, {'role': 'section', 'name': '', 'children': [{'role': 'text leaf', 'name': 'INTL FLIGHTS'}, {'role': 'text leaf', 'name': "T&C'S APPLY"}, {'role': 'text leaf', 'name': 'LIVE NOW:'}, {'role': 'text leaf', 'name': 'Up to 35% OFF* on your international trips.'}, {'role': 'text leaf', 'name': 'BOOK NOW'}]}]}, {'role': 'section', 'name': '', 'children': [{'role': 'section', 'name': '', 'children': [{'role': 'text leaf', 'name': 'DOM HOTELS'}, {'role': 'text leaf', 'name': "T&C'S APPLY"}, {'role': 'text leaf', 'name': 'Hotels in Spotlight:'}, {'role': 'text leaf', 'name': 'Luxury Stays Chosen by Our Experts for Your Next Relaxing Break.'}, {'role': 'text leaf', 'name': 'EXPLORE NOW'}]}, {'role': 'section', 'name': '', 'children': [{'role': 'text leaf', 'name': 'RAILS'}, {'role': 'text leaf', 'name': "T&C'S APPLY"}, {'role': 'text leaf', 'name': 'Avoid Waitlists for Diwali Train Bookings'}, {'role': 'text leaf', 'name': 'with Seat Availability Forecast to see when tickets are likely to sell out.'}, {'role': 'text leaf', 'name': 'BOOK NOW'}]}]}, {'role': 'section', 'name': '', 'children': [{'role': 'section', 'name': '', 'children': [{'role': 'text leaf', 'name': 'CABS'}, {'role': 'text leaf', 'name': "T&C'S APPLY"}, {'role': 'text leaf', 'name': 'Grab up to 15% OFF*'}, {'role': 'text leaf', 'name': 'on Buses, Cabs & Trains for big savings this Ganesh Chaturthi!'}, {'role': 'text leaf', 'name': 'BOOK NOW'}]}, {'role': 'section', 'name': '', 'children': [{'role': 'text leaf', 'name': 'INTL FLIGHTS'}, {'role': 'text leaf', 'name': "T&C'S APPLY"}, {'role': 'text leaf', 'name': 'FOR INTERNATIONAL FLIGHTS:'}, {'role': 'text leaf', 'name': 'Grab Up to ₹15,000 OFF*'}, {'role': 'text leaf', 'name': 'BOOK NOW'}]}]}, {'role': 'button', 'name': 'Next'}, {'role': 'section', 'name': '', 'children': [{'role': 'text leaf', 'name': 'Planning to book an international flight?'}]}, {'role': 'section', 'name': '', 'children': [{'role': 'text leaf', 'name': 'Complete your web check-in on MakeMyTrip in easy steps. '}]}, {'role': 'heading', 'name': 'Download App Now !', 'level': 3}, {'role': 'text leaf', 'name': 'Use code '}, {'role': 'text leaf', 'name': 'WELCOMEMMT'}, {'role': 'text leaf', 'name': ' and get '}, {'role': 'text leaf', 'name': 'FLAT 12%'}, {'role': 'text leaf', 'name': ' OFF* on your first domestic flight booking'}, {'role': 'text leaf', 'name': '+91\xa0 —'}, {'role': 'textbox', 'name': 'Enter Mobile number '}, {'role': 'button', 'name': 'GET APP LINK'}, {'role': 'img', 'name': 'QR Scanner'}, {'role': 'text leaf', 'name': 'Chennai Flights'}, {'role': 'text leaf', 'name': 'Via -'}, {'role': 'link', 'name': 'Delhi,', 'value': 'https://www.makemytrip.com/flights/new_delhi-chennai-cheap-airtickets.html'}, {'role': 'link', 'name': 'Mumbai,', 'value': 'https://www.makemytrip.com/flights/mumbai-chennai-cheap-airtickets.html'}, {'role': 'link', 'name': 'Coimbatore,', 'value': 'https://www.makemytrip.com/flights/coimbatore-chennai-cheap-airtickets.html'}, {'role': 'link', 'name': 'Madurai', 'value': 'https://www.makemytrip.com/flights/madurai-chennai-cheap-airtickets.html'}, {'role': 'text leaf', 'name': 'Goa Flights'}, {'role': 'text leaf', 'name': 'Via - '}, {'role': 'link', 'name': 'Delhi', 'value': 'https://www.makemytrip.com/flights/new_delhi-goa-cheap-airtickets.html'}, {'role': 'text leaf', 'name': ', '}, {'role': 'link', 'name': 'Mumbai,', 'value': 'https://www.makemytrip.com/flights/mumbai-goa-cheap-airtickets.html'}, {'role': 'link', 'name': 'Bangalore,', 'value': 'https://www.makemytrip.com/flights/bangalore-goa-cheap-airtickets.html'}, {'role': 'link', 'name': 'Ahmedabad', 'value': 'https://www.makemytrip.com/flights/ahmedabad-goa-cheap-airtickets.html'}, {'role': 'text leaf', 'name': 'Mumbai Flights'}, {'role': 'text leaf', 'name': 'Via - '}, {'role': 'link', 'name': 'Delhi', 'value': 'https://www.makemytrip.com/flights/new_delhi-mumbai-cheap-airtickets.html'}, {'role': 'text leaf', 'name': ', '}, {'role': 'link', 'name': 'Bangalore,', 'value': 'https://www.makemytrip.com/flights/bangalore-mumbai-cheap-airtickets.html'}, {'role': 'link', 'name': 'Chennai,', 'value': 'https://www.makemytrip.com/flights/chennai-mumbai-cheap-airtickets.html'}, {'role': 'link', 'name': 'Ahmedabad', 'value': 'https://www.makemytrip.com/flights/ahmedabad-mumbai-cheap-airtickets.html'}, {'role': 'text leaf', 'name': 'Hyderabad Flights'}, {'role': 'text leaf', 'name': 'Via - '}, {'role': 'link', 'name': 'Chennai', 'value': 'https://www.makemytrip.com/flights/chennai-hyderabad-cheap-airtickets.html'}, {'role': 'text leaf', 'name': ', '}, {'role': 'link', 'name': 'Mumbai', 'value': 'https://www.makemytrip.com/flights/mumbai-hyderabad-cheap-airtickets.html'}, {'role': 'text leaf', 'name': ', '}, {'role': 'link', 'name': 'Bangalore', 'value': 'https://www.makemytrip.com/flights/bangalore-hyderabad-cheap-airtickets.html'}, {'role': 'text leaf', 'name': ', '}, {'role': 'link', 'name': 'Delhi', 'value': 'https://www.makemytrip.com/flights/new_delhi-hyderabad-cheap-airtickets.html'}, {'role': 'text leaf', 'name': 'Delhi Flights'}, {'role': 'text leaf', 'name': 'Via - '}, {'role': 'link', 'name': 'Mumbai', 'value': 'https://www.makemytrip.com/flights/mumbai-new_delhi-cheap-airtickets.html'}, {'role': 'text leaf', 'name': ', '}, {'role': 'link', 'name': 'Pune', 'value': 'https://www.makemytrip.com/flights/pune-new_delhi-cheap-airtickets.html'}, {'role': 'text leaf', 'name': ', '}, {'role': 'link', 'name': 'Bangalore', 'value': 'https://www.makemytrip.com/flights/bangalore-new_delhi-cheap-airtickets.html'}]}
with open("accessibility_tree.json", "r", encoding="utf-8") as f:
    tree = json.load(f)

url="https://www.makemytrip.com/flights/"

executor = AssistantAgent(
    name="executor",
    llm_config=llm_config,
    system_message=system_prompt
)

user_task="Select from as Bombay and To as delhi for flight travel  and the departure date to be 2 september 2025 for 2 passengers "
accesibility_tree=tree

actions = executor.generate_reply(
    messages=[
        {
            "role": "user",
            "content": f"User Task: {user_task}\nDOM:\n{accesibility_tree}\n\n\nOutput:"
        }
    ]
)
print(actions)
print(type(actions))
# user_proxy = UserProxyAgent(
#     name="user_proxy",
#     human_input_mode="TERMINATE",
#     max_consecutive_auto_reply=3,
#     code_execution_config=False,
#     llm_config=llm_config
#     )


class BrowserController:
    def __init__(self):
        self.playwright = sync_playwright().start()
        self.browser = self.playwright.firefox.launch(headless=False)
        self.page = self.browser.new_page()

    def goto(self, url: str):
        self.page.goto(url)

    def perform_action(self, action: dict):
        act = action["action"]
        target = action.get("target", {})
        role = target.get("role")
        name = target.get("name")

        if act == "type":
            locator = self.page.get_by_role(role, name=name)
            locator.fill(action["value"])
        elif act == "click":
            locator = self.page.get_by_role(role, name=name)
            locator.click(force=True)
        elif act in ["select", "choose", "check"]:
            locator = self.page.get_by_role(role, name=name)
            locator.select_option(action["value"])
    
    def accesibility_tree(self):
        snapshot =  self.page.accessibility.snapshot()
        
        with open("accessibility_tree.json", "w", encoding="utf-8") as f:
            json.dump(snapshot, f, ensure_ascii=False, indent=2)

    def close(self):
        self.browser.close()
        self.playwright.stop()


controller = BrowserController()


def execute_actions(actions: dict):
    controller.goto(url)
    if isinstance(actions, str):
         try:
             actions = json.loads(actions,strict=False)
         except Exception as e:
             print("Failed to parse actions:", e) 
             return

    for step in actions["actions"]:
        controller.perform_action(step)

print("started executing..")

# register_function(
#     execute_actions,
#     caller=executor,
#     executor=user_proxy,  
#     name="execute_actions",
#     description="Execute browser actions with Playwright."
# )

# result = user_proxy.initiate_chat(
#     executor,
#     message=f"Perform these actions on the browser:\n{actions}"
# )
execute_actions(actions)
print("executed")

next_tree=controller.accesibility_tree()
controller.close()


