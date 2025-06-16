import re

# Test the simple approach
with open('debug_response_SCB_GL_000078314.html', 'r', encoding='utf-8') as f:
    content = f.read()

# Simple extraction - just find first data-id
match = re.search(r"data-id='(\d+)'", content)

if match:
    print(f'✅ SUCCESS! Found app_id: {match.group(1)}')
else:
    print('❌ Failed - no data-id found')
    
    # Debug: check what data-id patterns exist
    single_quote = re.findall(r"data-id='(\d+)'", content)
    double_quote = re.findall(r'data-id="(\d+)"', content) 
    print(f"Single quotes: {single_quote}")
    print(f"Double quotes: {double_quote}") 