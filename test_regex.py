import re

try:
    print("Starting regex test...")
    
    # Read the saved HTML content
    with open('debug_page_content.html', 'r', encoding='utf-8') as f:
        page_content = f.read()
    
    print(f"HTML content loaded: {len(page_content)} characters")
    
    # Test the current regex patterns
    patterns = [
        r'Policy Term:.*?(\d{2}/\d{2}/\d{4})\s*-\s*(\d{2}/\d{2}/\d{4})',
        r'<dt[^>]*>Policy Term:</dt>\s*<dd[^>]*>([^<]+)</dd>',
        r'(\d{2}/\d{2}/\d{4})\s*-\s*(\d{2}/\d{2}/\d{4})',
        r'Policy Term:</dt>\s*<dd[^>]*>([^<]+)</dd>',
        r'Policy Term:</dt>[^<]*<dd[^>]*>([^<]+)</dd>'
    ]
    
    print("Testing regex patterns on actual HTML content...")
    
    for i, pattern in enumerate(patterns, 1):
        print(f"\nPattern {i}: {pattern}")
        try:
            matches = re.findall(pattern, page_content, re.DOTALL)
            if matches:
                print(f"  Found {len(matches)} matches:")
                for match in matches:
                    print(f"    {match}")
            else:
                print("  No matches found")
        except Exception as e:
            print(f"  ERROR: {e}")
    
    # Let's also check what's around the Policy Term text
    print("\n=== Context around Policy Term ===")
    start_pos = page_content.find('Policy Term:')
    if start_pos != -1:
        context = page_content[start_pos-50:start_pos+150]
        print(f"Context: {repr(context)}")
    else:
        print("Policy Term: not found")
    
    # Test with more specific search
    print("\n=== Search for exact line ===")
    target_line = '<dt>Policy Term:</dt> <dd>07/11/2025 - 07/11/2026</dd>'
    if target_line in page_content:
        print("Exact line found in content!")
    else:
        print("Exact line NOT found - checking variations...")
        # Try different variations
        variations = [
            'Policy Term:</dt> <dd>07/11/2025 - 07/11/2026</dd>',
            'Policy Term:</dt><dd>07/11/2025 - 07/11/2026</dd>',
            '>Policy Term:</dt> <dd>07/11/2025',
            'Policy Term:</dt>',
            '07/11/2025 - 07/11/2026'
        ]
        
        for var in variations:
            if var in page_content:
                print(f"  Found variation: {var}")
            else:
                print(f"  NOT found: {var}")
    
    print("\nTest completed successfully!")

except Exception as e:
    print(f"ERROR: {e}")
    import traceback
    traceback.print_exc() 