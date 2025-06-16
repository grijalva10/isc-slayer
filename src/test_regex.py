import re

# Test the improved regex pattern
with open('debug_response_SCB_GL_000078314.html', 'r', encoding='utf-8') as f:
    content = f.read()

policy_number = 'SCB-GL-000078314'

def extract_app_id_from_search_results(html_content: str, policy_number: str):
    """Test the new extraction method"""
    # First, find all TR elements with data-id
    tr_pattern = r'<tr[^>]*class="[^"]*itemRow[^"]*"[^>]*data-id=\'(\d+)\'[^>]*>'
    tr_matches = re.finditer(tr_pattern, html_content, re.IGNORECASE)
    
    for match in tr_matches:
        app_id = match.group(1)
        tr_start = match.end()
        
        # Look for the closing </tr> to define the row content
        tr_end = html_content.find('</tr>', tr_start)
        if tr_end == -1:
            continue
            
        # Check if this row contains our policy number
        row_content = html_content[tr_start:tr_end]
        if policy_number in row_content:
            return app_id
    
    return None

# Test the function
result = extract_app_id_from_search_results(content, policy_number)

if result:
    print(f'✅ SUCCESS! New pattern found app_id: {result}')
    print(f'🎯 Expected: 3346286')
    print(f'✅ Match: {"YES" if result == "3346286" else "NO"}')
else:
    print('❌ New pattern still failed')
    
    # Debug what we find
    tr_pattern = r'<tr[^>]*class="[^"]*itemRow[^"]*"[^>]*data-id=\'(\d+)\'[^>]*>'
    all_matches = re.findall(tr_pattern, content, re.IGNORECASE)
    print(f'Found {len(all_matches)} TR elements: {all_matches}')

# Debug: Find the exact line with our policy number
lines = content.split('\n')
policy_line = None
for i, line in enumerate(lines):
    if policy_number in line and 'searchResultHighlight' in line:
        policy_line = i
        print(f"Found policy at line {i}:")
        print(f"  {line.strip()}")
        
        # Show context around this line
        print("\nContext around policy line:")
        for j in range(max(0, i-5), min(len(lines), i+3)):
            marker = ">>> " if j == i else "    "
            print(f"{marker}{j}: {lines[j].strip()}")
        break

if policy_line:
    # Look for the tr element before the policy line
    for i in range(policy_line, max(0, policy_line-10), -1):
        if '<tr' in lines[i] and 'data-id' in lines[i]:
            print(f"\nFound TR element at line {i}:")
            print(f"  {lines[i].strip()}")
            
            # Extract data-id with a simple pattern
            data_id_match = re.search(r"data-id='(\d+)'", lines[i])
            if data_id_match:
                print(f"✅ SUCCESS! Found app_id: {data_id_match.group(1)}")
            break

# Debug: Show if we can find the pattern parts separately
tr_pattern = r'<tr[^>]*class="[^"]*itemRow[^"]*"[^>]*data-id="(\d+)"'
tr_matches = re.findall(tr_pattern, content)
print(f'Found {len(tr_matches)} tr elements with itemRow class and data-id')
if tr_matches:
    print(f'data-ids found: {tr_matches[:3]}') 