import requests
from bs4 import BeautifulSoup
from openpyxl import Workbook
from time import sleep

# Base URL for scraping
base_url = "https://www.fatsecret.co.in/calories-nutrition/search?q=sweets&pg={}"

# Function to remove units from nutrition info and return as a list of values
def clean_nutrition_info(nutrition_info):
    values = []
    parts = nutrition_info.split('|')
    for part in parts:
        value = part.split(':')[1].strip()
        # Remove any non-numeric characters (letters and symbols)
        numeric_value = ''.join(c for c in value if c.isdigit() or c == '.')
        values.append(numeric_value)
    return values

# Function to save data to an Excel file
def save_to_excel(data, filename='fish_nutrition.xlsx'):
    # Create a new Workbook
    wb = Workbook()
    ws = wb.active
    ws.title = "Vegetable Nutrition"

    # Add headers
    headers = ['Vegetable', 'Calories', 'Fat', 'Carbs', 'Protein']
    ws.append(headers)

    # Add data rows
    for veg, info in data:
        # Ensure the info list has 4 elements
        while len(info) < 4:
            info.append('')

        ws.append([veg] + info)

    # Save the workbook to a file
    wb.save(filename)
    print(f"Data saved to {filename}")

# Function to process a single page of search results
def process_page(page):
    url = base_url.format(page)
    response = requests.get(url)

    if response.status_code != 200:
        print(f"Failed to retrieve page {page}. Status code: {response.status_code}")
        return
    
    soup = BeautifulSoup(response.content, 'html.parser')
    vegetables_info = []

    # Find all table rows containing vegetable information
    rows = soup.find_all('tr')

    for row in rows:
        # Extract vegetable name
        name_tag = row.find('a', class_='prominent')
        if not name_tag:
            continue
        
        name = name_tag.text.strip()
        
        # Check if the row contains nutrition information per 100g
        nutrition_info_div = row.find('div', class_='smallText greyText greyLink')

        if nutrition_info_div and 'Per 100 g' in nutrition_info_div.text:
            # Extract nutrition info
            nutrition_info = nutrition_info_div.text.strip()
            cleaned_info = clean_nutrition_info(nutrition_info)
            print(cleaned_info)
            vegetables_info.append((name, cleaned_info))
        else:
            # If "Per 100 g" not found, go to detail page
            detail_url = "https://www.fatsecret.com" + name_tag['href']
            detail_response = requests.get(detail_url)

            if detail_response.status_code != 200:
                print(f"Failed to retrieve detail page for {name}. Status code: {detail_response.status_code}")
                continue

            detail_soup = BeautifulSoup(detail_response.content, 'html.parser')

            # Find the table with class generic
            table = detail_soup.find('table', class_='generic')

            if table:
                # Look for the anchor tag with "100 g"
                anchor_100g = table.find('a', string='100 g')

                if anchor_100g:
                    nutrition_url = "https://www.fatsecret.com" + anchor_100g['href']
                    nutrition_response = requests.get(nutrition_url)

                    if nutrition_response.status_code != 200:
                        print(f"Failed to retrieve nutrition page for {name}. Status code: {nutrition_response.status_code}")
                        continue

                    nutrition_soup = BeautifulSoup(nutrition_response.content, 'html.parser')

                    # Extract nutritional values from the factPanel
                    fact_panel = nutrition_soup.find('div', class_='factPanel')

                    if fact_panel:
                        facts = fact_panel.find_all('td', class_='fact')
                        if len(facts) >= 4:
                            calories = facts[0].find('div', class_='factValue').text.strip()
                            fat = facts[1].find('div', class_='factValue').text.strip()
                            carbs = facts[2].find('div', class_='factValue').text.strip()
                            protein = facts[3].find('div', class_='factValue').text.strip()

                            nutrition_info = f"Calories: {calories} | Fat: {fat} | Carbs: {carbs} | Protein: {protein}"
                            cleaned_info = clean_nutrition_info(nutrition_info)
                            print(cleaned_info)
                            vegetables_info.append((name, cleaned_info))
                            
        

    # Save the collected data to an Excel file after processing each page
    save_to_excel(vegetables_info, filename=f'sweets_nutrition_page_{page}.xlsx')
    
    sleep(10)

# Process each page individually
for page in range(2,16):
    process_page(page)
