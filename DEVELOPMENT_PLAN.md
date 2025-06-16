# ISC Slayer - Development Plan

## 🎯 **Project Overview**
Build a Python desktop app to automate ISC policy data scraping with GUI interface, CSV processing, and web automation.

---

## 📋 **Step-by-Step Development Plan**

### **Phase 1: Project Setup & Environment**

#### Step 1.1: Create Project Structure
```
isc-slayer/
├── src/
│   ├── __init__.py
│   ├── scraper.py          # Core scraping logic
│   ├── ui.py              # GUI interface
│   ├── main.py            # Application entry point
│   └── utils.py           # Utility functions
├── data/
│   ├── templates/         # CSV templates
│   └── output/           # Generated CSVs
├── tests/
│   ├── __init__.py
│   └── test_scraper.py
├── requirements.txt
├── .env.example
├── .gitignore
└── README.md
```

#### Step 1.2: Create Virtual Environment
- Create Python virtual environment
- Activate virtual environment
- Install base dependencies

#### Step 1.3: Create Requirements File
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

#### Step 1.4: Initialize Playwright
- Install Playwright browsers
- Set up browser automation

---

### **Phase 2: Core Scraping Engine**

#### Step 2.1: Create Base Scraper Class (`src/scraper.py`)
- **ISCScaper** class with initialization
- Browser setup (headless/visible modes)
- Session management
- Error handling and logging

#### Step 2.2: Implement Login Functionality
- Navigate to login URL: `https://isc.onlinemga.com/amp/login`
- Handle login form: `#loginForm`
- Input credentials:
  - Username: `input[name="username"]`
  - Password: `input[name="password"]`
- Submit and validate successful login
- Handle login errors and redirects

#### Step 2.3: Implement Search Functionality
- Navigate to advanced search: `https://isc.onlinemga.com/amp/search/advancedsearch`
- Handle search form: `#advancedSearchForm`
- Implement search by:
  - Policy number
  - Insured name (`input[name="company_name"]`)
- Submit search and handle results

#### Step 2.4: Implement Results Parsing
- Extract search results from table rows:
  - `tr.itemRow`
  - `tr.cursor` 
  - `tr.searchRow`
- Parse table data:
  - Extract `data-id` (app_id)
  - Status (3rd column)
  - Company, state, program, cost, effective date
- Handle pagination if needed

#### Step 2.5: Implement Detail Page Scraping
- Navigate to policy detail: `https://isc.onlinemga.com/amp/detail/view/<app_id>`
- Extract using CSS selectors:
  - `#item_status_id` → Status ID
  - `#item_product_ids` → Product ID
  - `.insuredCompanyName` → Insured Name
  - `dt:contains("Policy Number:") + dd` → Policy Number
  - `dt:contains("Carrier:") + dd` → Carrier
  - `dt:contains("Cost:") + dd` → Total Cost
  - `dt:contains("Effective Date:") + dd` → Policy Dates
  - `dt:contains("Policy Term:") + dd` → Policy Term

---

### **Phase 3: Data Processing**

#### Step 3.1: CSV Input Handler (`src/utils.py`)
- Read CSV files with pandas
- Validate required columns (`policy_number` or `lead_name`)
- Handle missing/empty data
- Data type validation

#### Step 3.2: Data Enrichment Engine
- Merge scraped data with original CSV
- Handle duplicate records
- Data cleaning and formatting
- Create enriched output CSV

#### Step 3.3: CSV Template Generator
- Create downloadable CSV template
- Include required columns and examples
- Format as proper CSV structure

---

### **Phase 4: User Interface**

#### Step 4.1: Create Main UI (`src/ui.py`)
Using Streamlit for modern web-based GUI:

**Input Section:**
- Username input field
- Password input field (masked)
- File upload widget for CSV
- Download CSV template button

**Control Section:**
- Start Sync button
- Stop/Cancel button
- Settings (headless mode toggle)

**Progress Section:**
- Progress bar
- Status messages ("Processing 3 of 20...")
- Current record display
- Time estimates

**Output Section:**
- Results summary
- Download enriched CSV button
- Error log display

#### Step 4.2: Implement Event Handlers
- File upload validation
- Form submission handling
- Progress updates
- Error handling and user feedback

#### Step 4.3: Add Configuration Management
- Environment variables for settings
- User preferences storage
- Session management

---

### **Phase 5: Main Application Logic**

#### Step 5.1: Create Application Entry Point (`src/main.py`)
- Initialize application
- Handle command line arguments
- Launch UI
- Coordinate between UI and scraper

#### Step 5.2: Implement Main Processing Loop
- Read input CSV
- Initialize scraper with credentials
- Process each record:
  - Search by policy number or name
  - Extract details for each result
  - Update progress
  - Handle errors gracefully
- Generate output CSV
- Cleanup and session management

---

### **Phase 6: Error Handling & Resilience**

#### Step 6.1: Implement Robust Error Handling
- Network timeouts and retries
- Login session expiration
- Search result parsing errors
- File I/O errors
- Browser automation failures

#### Step 6.2: Add Logging System
- Configure logging levels
- Log file rotation
- Debug information capture
- User-friendly error messages

#### Step 6.3: Implement Retry Logic
- Exponential backoff for network requests
- Session refresh on authentication errors
- Partial resume capability

---

### **Phase 7: Testing & Validation**

#### Step 7.1: Create Unit Tests (`tests/test_scraper.py`)
- Test scraper initialization
- Mock login functionality
- Test search parsing
- Test data extraction
- Test CSV processing

#### Step 7.2: Integration Testing
- End-to-end workflow testing
- UI functionality testing
- Error scenario testing
- Performance testing

#### Step 7.3: User Acceptance Testing
- Test with sample data
- Validate output accuracy
- UI/UX testing
- Performance benchmarking

---

### **Phase 8: Documentation & Deployment**

#### Step 8.1: Update Documentation
- Complete README with:
  - Installation instructions
  - Usage examples
  - Troubleshooting guide
  - API documentation

#### Step 8.2: Create User Guide
- Step-by-step usage instructions
- CSV format requirements
- Common issues and solutions
- Best practices

#### Step 8.3: Package for Distribution
- Create executable using PyInstaller
- Include all dependencies
- Test on clean Windows environment
- Create installer package

---

## 🛠️ **Implementation Order Priority**

1. **High Priority (Core Functionality)**
   - Steps 1.1-1.4: Project setup
   - Steps 2.1-2.5: Core scraping engine
   - Steps 3.1-3.2: Data processing
   - Step 5.1-5.2: Main application logic

2. **Medium Priority (User Experience)**
   - Steps 4.1-4.3: User interface
   - Steps 6.1-6.3: Error handling
   - Step 3.3: CSV template

3. **Low Priority (Polish & Distribution)**
   - Steps 7.1-7.3: Testing
   - Steps 8.1-8.3: Documentation & deployment

---

## 🔧 **Key Technical Considerations**

### **Browser Automation**
- Use Playwright as primary choice
- Fallback to MechanicalSoup for lightweight scenarios
- Handle dynamic content loading
- Manage browser sessions efficiently

### **Data Handling**
- Use pandas for CSV operations
- Implement data validation
- Handle large datasets efficiently
- Preserve original data integrity

### **UI Framework**
- Streamlit for modern web-based interface
- Real-time progress updates
- Responsive design
- Error feedback integration

### **Security**
- Never store credentials in code
- Use environment variables
- Secure session management
- Input validation and sanitization

---

## 📊 **Expected Output CSV Fields**

**Required Fields:**
- `app_id` - Unique application identifier
- `status` - Current policy status
- `insured_company_name` - Company name
- `policy_number` - Policy number
- `effective_start_date` - Policy start date
- `effective_end_date` - Policy end date
- `carrier` - Insurance carrier
- `cost` - Policy cost
- `product_id` - Product identifier
- `state` - State code
- `program` - Program type

**Plus all original CSV columns preserved**

---

## 🚀 **Ready to Execute**

This plan provides a comprehensive roadmap for building the ISC Slayer tool. Each step is designed to be executed systematically, with clear dependencies and deliverables. The modular approach ensures maintainability and allows for iterative development.

**Next Action:** Begin with Phase 1, Step 1.1 - Create Project Structure 