# Cursor Agent Command Reference

## 🚀 **Quick Start Commands**

### **Phase 1: Project Setup**

#### Step 1.1: Create Project Structure
```bash
# Create directories
mkdir -p src data/templates data/output tests

# Create Python files
touch src/__init__.py src/scraper.py src/ui.py src/main.py src/utils.py
touch tests/__init__.py tests/test_scraper.py
touch .env.example .gitignore
```

#### Step 1.2: Create Virtual Environment
```bash
# Create virtual environment
python -m venv venv

# Activate (Windows)
venv\Scripts\activate

# Activate (Linux/Mac)
source venv/bin/activate
```

#### Step 1.3: Create Requirements File
Create `requirements.txt`:
```txt
playwright==1.40.0
pandas==2.1.4
beautifulsoup4==4.12.2
python-dotenv==1.0.0
streamlit==1.29.0
mechanicalsoup==1.3.0
lxml==4.9.3
requests==2.31.0
```

#### Step 1.4: Install Dependencies
```bash
# Install requirements
pip install -r requirements.txt

# Install Playwright browsers
playwright install
```

---

### **Phase 2: Core Implementation Files**

#### Create `.gitignore`
```
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
venv/
env/
.env
.vscode/
*.log
data/output/*.csv
!data/templates/
.DS_Store
node_modules/
```

#### Create `.env.example`
```
# ISC Login Credentials
ISC_USERNAME=your_username
ISC_PASSWORD=your_password

# Application Settings
HEADLESS_MODE=true
LOG_LEVEL=INFO
OUTPUT_DIR=data/output
```

#### Create `src/scraper.py` - Core Scraper Class
```python
import asyncio
import logging
from playwright.async_api import async_playwright
import pandas as pd
from typing import List, Dict, Optional

class ISCScraper:
    def __init__(self, username: str, password: str, headless: bool = True):
        self.username = username
        self.password = password
        self.headless = headless
        self.browser = None
        self.page = None
        
    async def initialize(self):
        """Initialize browser and create page"""
        pass
        
    async def login(self) -> bool:
        """Login to ISC platform"""
        pass
        
    async def search_policy(self, search_term: str, search_type: str) -> List[Dict]:
        """Search for policies by number or name"""
        pass
        
    async def extract_policy_details(self, app_id: str) -> Dict:
        """Extract detailed policy information"""
        pass
        
    async def close(self):
        """Clean up browser resources"""
        pass
```

#### Create `src/utils.py` - Utility Functions
```python
import pandas as pd
import os
from typing import List, Dict

def validate_csv_input(file_path: str) -> bool:
    """Validate input CSV format"""
    pass

def create_csv_template() -> pd.DataFrame:
    """Create downloadable CSV template"""
    pass

def merge_data(original_df: pd.DataFrame, scraped_data: List[Dict]) -> pd.DataFrame:
    """Merge original data with scraped results"""
    pass

def save_output_csv(df: pd.DataFrame, output_path: str) -> bool:
    """Save enriched data to CSV"""
    pass
```

#### Create `src/ui.py` - Streamlit Interface
```python
import streamlit as st
import pandas as pd
import asyncio
from src.scraper import ISCScraper
from src.utils import validate_csv_input, create_csv_template

def main():
    st.title("ISC Slayer - Policy Data Scraper")
    
    # Input section
    with st.sidebar:
        st.header("Configuration")
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        
    # File upload
    uploaded_file = st.file_uploader("Upload CSV", type=['csv'])
    
    # Template download
    if st.button("Download CSV Template"):
        template = create_csv_template()
        st.download_button(
            label="Download Template",
            data=template.to_csv(index=False),
            file_name="isc_template.csv",
            mime="text/csv"
        )
    
    # Start processing
    if st.button("Start Sync"):
        if username and password and uploaded_file:
            # Process data
            pass
        else:
            st.error("Please provide all required inputs")

if __name__ == "__main__":
    main()
```

#### Create `src/main.py` - Entry Point
```python
import streamlit as st
import sys
import os
from pathlib import Path

# Add src directory to path
sys.path.append(str(Path(__file__).parent))

from ui import main

if __name__ == "__main__":
    main()
```

---

### **Phase 3: Implementation Commands**

#### Step 3.1: Implement Login Logic
```python
# In src/scraper.py - login method
async def login(self) -> bool:
    try:
        await self.page.goto("https://isc.onlinemga.com/amp/login")
        await self.page.fill('input[name="username"]', self.username)
        await self.page.fill('input[name="password"]', self.password)
        await self.page.click('input[type="submit"]')
        
        # Wait for redirect and validate
        await self.page.wait_for_load_state("networkidle")
        return "login" not in self.page.url
        
    except Exception as e:
        logging.error(f"Login failed: {e}")
        return False
```

#### Step 3.2: Implement Search Logic
```python
# In src/scraper.py - search_policy method
async def search_policy(self, search_term: str, search_type: str) -> List[Dict]:
    try:
        await self.page.goto("https://isc.onlinemga.com/amp/search/advancedsearch")
        
        if search_type == "company_name":
            await self.page.fill('input[name="company_name"]', search_term)
        elif search_type == "policy_number":
            await self.page.fill('input[name="policy_number"]', search_term)
            
        await self.page.click('input[type="submit"]')
        await self.page.wait_for_load_state("networkidle")
        
        # Parse results
        results = []
        rows = await self.page.query_selector_all('tr.itemRow, tr.cursor, tr.searchRow')
        
        for row in rows:
            app_id = await row.get_attribute('data-id')
            if app_id:
                results.append({'app_id': app_id})
                
        return results
        
    except Exception as e:
        logging.error(f"Search failed for {search_term}: {e}")
        return []
```

#### Step 3.3: Implement Detail Extraction
```python
# In src/scraper.py - extract_policy_details method
async def extract_policy_details(self, app_id: str) -> Dict:
    try:
        await self.page.goto(f"https://isc.onlinemga.com/amp/detail/view/{app_id}")
        await self.page.wait_for_load_state("networkidle")
        
        details = {'app_id': app_id}
        
        # Extract using CSS selectors
        selectors = {
            'status_id': '#item_status_id',
            'product_id': '#item_product_ids',
            'insured_name': '.insuredCompanyName',
            'policy_number': 'dt:has-text("Policy Number:") + dd',
            'carrier': 'dt:has-text("Carrier:") + dd',
            'cost': 'dt:has-text("Cost:") + dd',
            'effective_date': 'dt:has-text("Effective Date:") + dd'
        }
        
        for field, selector in selectors.items():
            element = await self.page.query_selector(selector)
            if element:
                details[field] = await element.text_content()
                
        return details
        
    except Exception as e:
        logging.error(f"Detail extraction failed for {app_id}: {e}")
        return {'app_id': app_id, 'error': str(e)}
```

---

### **Phase 4: Testing Commands**

#### Run the Application
```bash
# Start Streamlit app
streamlit run src/main.py

# Alternative: Run with Python
python -m streamlit run src/main.py
```

#### Create Test Data
```python
# Create data/templates/sample_input.csv
import pandas as pd

sample_data = pd.DataFrame({
    'policy_number': ['POL001', 'POL002', ''],
    'lead_name': ['', '', 'Company ABC'],
    'notes': ['Test policy 1', 'Test policy 2', 'Test lead 3']
})

sample_data.to_csv('data/templates/sample_input.csv', index=False)
```

#### Run Tests
```bash
# Run unit tests
python -m pytest tests/ -v

# Run with coverage
python -m pytest tests/ --cov=src --cov-report=html
```

---

### **Phase 5: Deployment Commands**

#### Create Executable
```bash
# Install PyInstaller
pip install pyinstaller

# Create executable
pyinstaller --onefile --add-data "src;src" src/main.py

# Test executable
dist/main.exe
```

#### Docker Deployment (Optional)
```dockerfile
# Dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY src/ src/
COPY data/ data/

EXPOSE 8501

CMD ["streamlit", "run", "src/main.py", "--server.port=8501", "--server.address=0.0.0.0"]
```

```bash
# Build and run Docker
docker build -t isc-slayer .
docker run -p 8501:8501 isc-slayer
```

---

## 📋 **Execution Checklist**

- [ ] **Phase 1**: Project structure created
- [ ] **Phase 1**: Virtual environment setup
- [ ] **Phase 1**: Dependencies installed
- [ ] **Phase 2**: Core scraper class implemented
- [ ] **Phase 2**: Login functionality working
- [ ] **Phase 2**: Search functionality implemented
- [ ] **Phase 2**: Detail extraction working
- [ ] **Phase 3**: CSV processing implemented
- [ ] **Phase 4**: Streamlit UI created
- [ ] **Phase 4**: File upload working
- [ ] **Phase 4**: Progress tracking implemented
- [ ] **Phase 5**: End-to-end testing completed
- [ ] **Phase 5**: Error handling added
- [ ] **Phase 6**: Documentation updated
- [ ] **Phase 6**: Deployment package created

---

## 🐛 **Common Issues & Solutions**

### **Playwright Issues**
```bash
# Reinstall browsers
playwright install --force

# Check browser installation
playwright install-deps
```

### **Import Errors**
```python
# Add to Python path
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))
```

### **Streamlit Issues**
```bash
# Clear cache
streamlit cache clear

# Run with specific config
streamlit run app.py --server.headless true
```

This command reference provides specific, executable commands that a cursor agent can follow to implement the ISC Slayer tool systematically. 