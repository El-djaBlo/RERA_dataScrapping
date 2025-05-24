from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoAlertPresentException, TimeoutException
from bs4 import BeautifulSoup
import time
import os
import pandas as pd
from selenium.webdriver.common.action_chains import ActionChains

# Step 1: Extract the top 6 project links
def extract_project_links():
    driver = webdriver.Edge()
    driver.get("https://rera.odisha.gov.in/projects/project-list")
    driver.maximize_window()
    time.sleep(5)
    # to counter location access popups
    try:
        allow_btn = driver.find_element(By.ID, "btnModalOK")
        allow_btn.click()
        print("Popup dismissed.")
        time.sleep(2)
    except:
        print("No popup.")

    buttons = driver.find_elements(By.XPATH, "//a[contains(@class, 'btn') and contains(text(), 'View Details')]")[:6]
    project_links = []

    for i in range(len(buttons)):
        buttons = driver.find_elements(By.XPATH, "//a[contains(@class, 'btn') and contains(text(), 'View Details')]")[:6]
        button = buttons[i]
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", button)
        time.sleep(1)

        try:
            WebDriverWait(driver, 10).until(EC.element_to_be_clickable(button)).click()
        except:
            driver.execute_script("arguments[0].click();", button)

        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "//a[contains(text(), 'Project Overview')]"))
        )
        project_links.append(driver.current_url)
        driver.back()
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "//a[contains(text(), 'View Details')]"))
        )

    driver.quit()
    print("Collected project links:", project_links)
    return project_links

# Step 2: Save pages as HTML for a single project
def save_pages_as_html(url, index, overview_file_prefix="project_overview", promoter_file_prefix="promoter_details"):
    driver = webdriver.Edge()
    overview_file = f"{overview_file_prefix}_{index}.html"
    promoter_file = f"{promoter_file_prefix}_{index}.html"
    
    try:
        driver.get(url)
        try:
            alert = driver.switch_to.alert
            alert.dismiss()
        except NoAlertPresentException:
            pass
        
        # Wait for the Project Overview tab to load
        WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.XPATH, "//label[contains(text(), 'RERA Regd. No.')]"))
        )
        WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.XPATH, "//label[contains(text(), 'Project Name')]"))
        )
        
        # Wait until the Project Name and RERA Regd. No. are fully loaded (not '--' or empty)
        try:
            WebDriverWait(driver, 60).until(
                lambda d: d.find_element(By.XPATH, "//label[contains(text(), 'Project Name')]/following-sibling::strong").text.strip() not in ["", "--"]
            )
            WebDriverWait(driver, 60).until(
                lambda d: d.find_element(By.XPATH, "//label[contains(text(), 'RERA Regd. No.')]/following-sibling::strong").text.strip() not in ["", "--"]
            )
        except TimeoutException:
            print(f"Warning: Project Overview data for project {index} did not load within 60 seconds. Proceeding with available data.")

        
        # Save the Project Overview tab content
        overview_html = driver.page_source
        with open(overview_file, "w", encoding="utf-8") as f:
            f.write(overview_html)
        print(f"Project Overview page saved as {overview_file}")
        
        # Switch to Promoter Details tab
        promoter_tab = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.LINK_TEXT, "Promoter Details"))
        )
        promoter_tab.click()
        
        # Wait for Promoter Details content to load
        WebDriverWait(driver, 30).until(
            EC.presence_of_element_located((By.XPATH, "//label[contains(text(), 'Company Name')] | //label[contains(text(), 'Proprietary Name')]"))
        )
        
        time.sleep(2)
        promoter_html = driver.page_source
        with open(promoter_file, "w", encoding="utf-8") as f:
            f.write(promoter_html)
        print(f"Promoter Details page saved as {promoter_file}")
        
        return overview_file, promoter_file
    
    except Exception as e:
        print(f"An error occurred while saving the pages for {url}: {e}")
        return None, None
    finally:
        driver.quit()

# Step 3: Extract data from HTML files and delete them
def extract_data_from_html(overview_file, promoter_file):
    if not os.path.exists(overview_file) or not os.path.exists(promoter_file):
        print(f"Error: One or both HTML files do not exist. Skipping extraction.")
        return None
    
    data = {
        "RERA Registration Number": "Not found",
        "Project Name": "Not found",
        "Promoter Name": "Not found",
        "Address": "Not found",
        "GST Number": "Not found"
    }
    
    try:
        # Extract from Project Overview tab
        with open(overview_file, "r", encoding="utf-8") as f:
            overview_soup = BeautifulSoup(f, "html.parser")
        
        rera_label = overview_soup.find("label", string=lambda text: "RERA Regd. No." in text if text else False)
        if rera_label:
            rera_no = rera_label.find_next("strong").text.strip()
            data["RERA Registration Number"] = rera_no
        else:
            print("RERA Regd. No. label not found in Project Overview HTML")
            print("HTML snippet:", str(overview_soup.find("label", string=lambda text: "RERA Regd. No." in text if text else False)))
        
        project_label = overview_soup.find("label", string=lambda text: "Project Name" in text if text else False)
        if project_label:
            project_name = project_label.find_next("strong").text.strip()
            data["Project Name"] = project_name
        else:
            print("Project Name label not found in Project Overview HTML")
            print("HTML snippet:", str(overview_soup.find("label", string=lambda text: "Project Name" in text if text else False)))
        
        # Extract from Promoter Details tab
        with open(promoter_file, "r", encoding="utf-8") as f:
            promoter_soup = BeautifulSoup(f, "html.parser")
        
        # Promoter Name (check both "Company Name" and "Proprietary Name")
        promoter_label = promoter_soup.find("label", string=lambda text: "Company Name" in text if text else False)
        if not promoter_label:
            promoter_label = promoter_soup.find("label", string=lambda text: "Proprietary Name" in text if text else False)
        if promoter_label:
            promoter_name = promoter_label.find_next("strong").text.strip()
            data["Promoter Name"] = promoter_name
        else:
            print("Neither Company Name nor Proprietary Name label found in Promoter Details HTML")
            print("HTML snippet (Company Name):", str(promoter_soup.find("label", string=lambda text: "Company Name" in text if text else False)))
            print("HTML snippet (Proprietary Name):", str(promoter_soup.find("label", string=lambda text: "Proprietary Name" in text if text else False)))
        
        # Address (check both "Registered Office Address" and "Permanent Address")
        address_label = promoter_soup.find("label", string=lambda text: "Registered Office Address" in text if text else False)
        if not address_label:
            address_label = promoter_soup.find("label", string=lambda text: "Permanent Address" in text if text else False)
        if address_label:
            address = address_label.find_next("strong").text.strip()
            data["Address"] = address
        else:
            print("Neither Registered Office Address nor Permanent Address label found in Promoter Details HTML")
            print("HTML snippet (Registered Office Address):", str(promoter_soup.find("label", string=lambda text: "Registered Office Address" in text if text else False)))
            print("HTML snippet (Permanent Address):", str(promoter_soup.find("label", string=lambda text: "Permanent Address" in text if text else False)))
        
        gst_label = promoter_soup.find("label", string=lambda text: "GST No." in text if text else False)
        if gst_label:
            gst_no = gst_label.find_next("strong").text.strip()
            data["GST Number"] = gst_no
        else:
            print("GST No. label not found in Promoter Details HTML")
            print("HTML snippet:", str(promoter_soup.find("label", string=lambda text: "GST No." in text if text else False)))
        
        # Delete the HTML files after extraction
        try:
            os.remove(overview_file)
            os.remove(promoter_file)
            print(f"Deleted HTML files: {overview_file}, {promoter_file}")
        except Exception as e:
            print(f"Error deleting HTML files: {e}")
        
        return data
    
    except Exception as e:
        print(f"An error occurred while extracting data: {e}")
        return None

# Step 4: Main function
def main():
    project_links = extract_project_links()
    all_data = []
    
    for i, url in enumerate(project_links, start=1):
        print(f"\nProcessing project {i}/{len(project_links)}: {url}")
        overview_file, promoter_file = save_pages_as_html(url, i)
        if overview_file and promoter_file:
            data = extract_data_from_html(overview_file, promoter_file)
            if data:
                all_data.append(data)
    
    if all_data:
        df = pd.DataFrame(all_data)
        csv_file = "scraped_rera_data.csv"
        df.to_csv(csv_file, index=False)
        print(f"\nAll data saved to {csv_file}")
    else:
        print("No data was scraped.")

if __name__ == "__main__":
    main()