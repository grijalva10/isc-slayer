import pytest
import asyncio
from src.scraper import ISCScraper
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

@pytest.fixture
def scraper():
    username = os.getenv('ISC_USERNAME')
    password = os.getenv('ISC_PASSWORD')
    return ISCScraper(username=username, password=password, headless=True)

@pytest.mark.asyncio
async def test_initialization(scraper):
    """Test scraper initialization"""
    await scraper.initialize()
    assert scraper.browser is not None
    assert scraper.page is not None
    await scraper.close()

@pytest.mark.asyncio
async def test_login(scraper):
    """Test login functionality"""
    await scraper.initialize()
    success = await scraper.login()
    assert success is True
    await scraper.close()

@pytest.mark.asyncio
async def test_search_policy(scraper):
    """Test policy search functionality"""
    await scraper.initialize()
    await scraper.login()
    
    # Test search by policy number
    results = await scraper.search_policy("TEST123", "policy_number")
    assert isinstance(results, list)
    
    # Test search by company name
    results = await scraper.search_policy("Test Company", "company_name")
    assert isinstance(results, list)
    
    await scraper.close()

@pytest.mark.asyncio
async def test_extract_policy_details(scraper):
    """Test policy detail extraction"""
    await scraper.initialize()
    await scraper.login()
    
    # First search for a policy
    results = await scraper.search_policy("TEST123", "policy_number")
    if results:
        app_id = results[0]['app_id']
        details = await scraper.extract_policy_details(app_id)
        assert isinstance(details, dict)
        assert 'app_id' in details
    
    await scraper.close()
