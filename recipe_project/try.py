import pandas as pd
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright
import time

def scrape_apartments(url, filename="apartment_listings.csv"):
    """
    Launches a browser, navigates to the URL, extracts apartment 
    address and price data, and saves to CSV.
    """
    results = []

    with sync_playwright() as p:
        # Launch Chromium (Chrome's engine)
        browser = p.chromium.launch(headless=True) # Set to False to watch it work
        
        # Set a real browser fingerprint (User Agent)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        
        page = context.new_page()
        
        print(f"Opening: {url}")
        try:
            # Navigate and wait for the network to go quiet
            page.goto(url, wait_until="networkidle", timeout=60000)
            
            # Scroll down slowly to trigger "lazy loaded" listings
            page.evaluate("window.scrollBy(0, 800)")
            time.sleep(2) 

            # Grab the rendered HTML
            html_content = page.content()
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Find the property data containers based on your snippet
            cards = soup.find_all('div', {'data-testid': 'property-card-data'})
            
            print(f"Found {len(cards)} apartment listings on this page.")

            for card in cards:
                entry = {}
                
                # 1. Extract Address
                address_tag = card.find('address')
                if address_tag:
                    entry['Address'] = address_tag.get_text(strip=True)
                else:
                    continue

                # 2. Extract Price Inventory (Studio, 1bd, 2bd, etc.)
                # In your HTML, inventory boxes are inside 'PropertyCardInventorySet'
                # which is usually a sibling or nearby the card data
                parent = card.find_parent()
                inventory_boxes = parent.find_all('div', {'data-testid': 'PropertyCardInventoryBox'})
                
                if inventory_boxes:
                    for box in inventory_boxes:
                        # Extract the price (e.g. C$2,050+) and type (e.g. Studio)
                        spans = box.find_all('span')
                        if len(spans) >= 2:
                            price = spans[0].get_text(strip=True)
                            label = spans[1].get_text(strip=True)
                            entry[f'Price_{label}'] = price
                
                # 3. Fallback for single-price listings
                summary_price = card.find('span', {'data-test': 'property-card-price'})
                if summary_price:
                    entry['Summary_Price'] = summary_price.get_text(strip=True)

                results.append(entry)

        except Exception as e:
            print(f"Error during scrape: {e}")
        finally:
            browser.close()

    # --- Exporting to CSV ---
    if results:
        df = pd.DataFrame(results)
        
        # Ensure Address is the first column for readability
        cols = ['Address'] + [c for c in df.columns if c != 'Address']
        df = df[cols]
        
        df.to_csv(filename, index=False, encoding='utf-8')
        print(f"Success! Data saved to: {filename}")
    else:
        print("No data extracted. Verify the URL or check if the site layout changed.")

if __name__ == "__main__":
    # Insert the link you want to check here
    link = input("Enter the apartment search URL: ")
    if link:
        scrape_apartments(link)