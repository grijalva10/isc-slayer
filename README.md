# ISC Slayer 🎯

**Python desktop app for automating ISC policy data scraping with modern GUI interface.**

## 🚀 **Quick Start**

This repository contains comprehensive development plans and implementation guides for building the ISC Slayer tool.

### **📋 For Cursor Agents**
- **[DEVELOPMENT_PLAN.md](DEVELOPMENT_PLAN.md)** - Complete development roadmap with phases, steps, and technical considerations
- **[CURSOR_AGENT_COMMANDS.md](CURSOR_AGENT_COMMANDS.md)** - Executable commands and code snippets for step-by-step implementation

### **🎯 Project Goals**
Build a tool that:
- Accepts CSV files with only `policy_number` column required (other fields auto-generated)
- Uses headless browser automation (Playwright) for ISC platform interaction
- Provides modern Streamlit-based GUI interface
- Exports enriched CSV data with scraped policy information

### **🛠️ Tech Stack**
- **Backend**: Python 3.11+, Playwright, Pandas
- **Frontend**: Streamlit (web-based GUI)
- **Data**: CSV processing, policy data enrichment
- **Automation**: Headless browser scraping

### **📊 Key Features**
- Secure login handling
- Advanced search capabilities
- Progress tracking and error handling
- CSV template generation
- Batch processing with real-time updates
- Comprehensive error logging

## 🏗️ **Implementation Status**

### **Current Phase: Planning Complete**
- [x] Detailed development plan created
- [x] Technical specifications defined
- [x] Implementation commands documented
- [ ] Project structure setup (Next: Phase 1)

### **Next Steps**
1. Execute Phase 1: Project Setup & Environment
2. Implement Phase 2: Core Scraping Engine
3. Build Phase 3: Data Processing
4. Create Phase 4: User Interface

## 📖 **Quick Reference**

### **Target ISC URLs**
- Login: `https://isc.onlinemga.com/amp/login`
- Search: `https://isc.onlinemga.com/amp/search/advancedsearch`
- Details: `https://isc.onlinemga.com/amp/detail/view/<app_id>`

### **CSV Input Requirements**
- **Required**: Only `policy_number` column
- **Optional**: Any additional columns (will be preserved)
- **Auto-generated**: Missing fields are automatically created as empty columns

### **Expected Output Fields**
- `app_id`, `status`, `applicant_company`
- `policy_number`, `effective_date`, `expiration_date`, `cancellation_date`
- `state`, `program`, `total_cost`
- Plus all original CSV columns preserved

## 🔧 **Development Workflow**

1. **Planning Phase** ✅ Complete
   - Development roadmap created
   - Technical specifications defined
   - Implementation commands documented

2. **Setup Phase** 🔄 Ready to Start
   - Project structure creation
   - Virtual environment setup
   - Dependency installation

3. **Core Development** ⏳ Pending
   - Scraper engine implementation
   - Data processing logic
   - User interface creation

4. **Testing & Deployment** ⏳ Pending
   - Unit and integration testing
   - Error handling refinement
   - Packaging and distribution

## 💻 **For Developers**

### **Immediate Next Action**
Execute the commands in `CURSOR_AGENT_COMMANDS.md` starting with Phase 1, Step 1.1.

### **Development Environment**
- Windows 10/11 compatible
- Python 3.11+ recommended
- PowerShell for terminal commands

### **Architecture**
```
src/
├── scraper.py     # Core automation logic
├── ui.py          # Streamlit interface
├── utils.py       # Data processing utilities
└── main.py        # Application entry point
```

---

**Ready to build the ISC Slayer tool? Start with [CURSOR_AGENT_COMMANDS.md](CURSOR_AGENT_COMMANDS.md) for step-by-step implementation!**