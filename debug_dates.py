import re
from bs4 import BeautifulSoup

# HTML snippet from the user
html_content = '''
<div class="col-md-3 col-lg-3 col-xs-3 app-info-summary-col-2" id="cluster_info">
    <dl class="dl-horizontal marginBottom-sm">
        <dt>Create Date:</dt> <dd>  05/12/2025  4:04 AM</dd>
    </dl>
    <dl class="dl-horizontal marginBottom-sm">
        <dt>Bind Date:</dt>
        <dd>
            06/13/2025 12:39 PM
        </dd>
    </dl>
</div>
<div class="col-md-3 col-lg-3 col-xs-3 app-info-summary-col-2" id="cluster_info">
    <dl class="dl-horizontal marginBottom-sm">
        <dt>Policy Number:</dt>
        <dd class=""><span id="policy_number_selector_80">ISCPC04000058472</span> </dd>
    </dl>
    <dl class="dl-horizontal marginBottom-sm">
        <dt>Policy Term:</dt> <dd>07/11/2025 - 07/11/2026</dd>
    </dl>
    <dl class="dl-horizontal marginBottom-sm">
    </dl>
</div>
'''

# Test different extraction methods
print("Testing HTML parsing methods for policy term extraction...")

# Method 1: BeautifulSoup
soup = BeautifulSoup(html_content, 'html.parser')

# Find dt containing "Policy Term:" and get the next dd
dt_elements = soup.find_all('dt')
for dt in dt_elements:
    if dt.get_text(strip=True) == 'Policy Term:':
        dd = dt.find_next_sibling('dd')
        if dd:
            policy_term = dd.get_text(strip=True)
            print(f"Method 1 (BeautifulSoup): Found policy term: '{policy_term}'")
            
            # Extract dates
            dates = [date.strip() for date in policy_term.split('-')]
            if len(dates) == 2:
                effective_date = dates[0].strip()
                expiration_date = dates[1].strip()
                print(f"  Effective Date: '{effective_date}'")
                print(f"  Expiration Date: '{expiration_date}'")

# Method 2: Regex on full HTML
pattern = r'Policy Term:.*?<dd[^>]*>([^<]+)</dd>'
match = re.search(pattern, html_content, re.DOTALL)
if match:
    policy_term = match.group(1).strip()
    print(f"Method 2 (Regex): Found policy term: '{policy_term}'")
    
    dates = [date.strip() for date in policy_term.split('-')]
    if len(dates) == 2:
        effective_date = dates[0].strip()
        expiration_date = dates[1].strip()
        print(f"  Effective Date: '{effective_date}'")
        print(f"  Expiration Date: '{expiration_date}'")

# Method 3: More robust regex for date patterns
date_pattern = r'Policy Term:.*?(\d{2}/\d{2}/\d{4})\s*-\s*(\d{2}/\d{2}/\d{4})'
match = re.search(date_pattern, html_content)
if match:
    effective_date = match.group(1)
    expiration_date = match.group(2)
    print(f"Method 3 (Date Pattern Regex): Found dates: '{effective_date}' - '{expiration_date}'")

print("\nCompleted testing.") 