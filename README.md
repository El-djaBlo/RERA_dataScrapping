# RERA Data Scraping Task

## Overview

This project was created to automate the extraction of data from the RERA website for the top 6 projects listed. Due to the dynamic and interactive nature of the site (clicking through tabs, navigating links, etc.), a combination of **Selenium** and **BeautifulSoup** was used.

---

## How It Works

1. **Selenium** is used to handle navigation:

   * Clicks through the required tabs and links.
   * Saves the HTML of each relevant page locally.

2. **BeautifulSoup** is then used to parse and extract the required data from the saved `.html` files.

3. Once data is extracted:

   * The temporary `.html` file is deleted to keep the directory clean.
   * The process repeats for each of the top 6 projects.

4. The final data is saved in a CSV file.

---

## Output

* A `.csv` file containing the extracted data is included in the ZIP.

> **Note:** For the 3rd entry (project named **BARSANA**), the promoter name is shown as `"not found"`.
> This is because the website incorrectly spells **"Proprietary"** as **"Propietory"**, which caused it to be missed during extraction.

---

## How to Run

To execute the script:

```bash
python "_location_/DataScrapping_RERA.py"
```

>  **Do not use the `-u` flag** when running the script — it may cause issues with how the output appears on the terminal.

