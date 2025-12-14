For Pima County (Tucson area), you are in luck. Pima County has one of the more advanced GIS and Open Data infrastructures in the country, making "Tier 1" access easier than in most other markets.

Here is your **Pima County Distressed Data Master List**, broken down by the specific office, the data they hold, and the direct access method (API/Bulk/Search).

### **1\. Pima County Assessor (Ownership & Property Specs)**

* **Data:** Property owner names, mailing addresses (for finding absentee owners), square footage, year built.  
* **The "API" Connection:** Pima County uses an **ArcGIS Hub (Open Data Portal)**. You do not need a login. You can query this database programmatically using GeoJSON or REST APIs.  
  * **Direct Link:** [Pima County Geospatial Data Portal](https://gisopendata.pima.gov/)  
  * **Specific Dataset to Grab:** Look for "Parcels \- Regional."  
  * **Bulk Method:** On the dataset page, click the "API Resources" tab to get the GeoJSON endpoint, or click "Download" for the full CSV/Shapefile.

### **2\. Pima County Recorder (Pre-Foreclosure, Liens, Divorce Judgments)**

* **Data:** Notices of Default, Lis Pendens, Mechanics Liens, Judgments.  
* **Access Method:** They do not have a free public API, but they offer a **Subscription Service** for bulk image access and data.  
  * **Public Search (Manual):** [Pima County Recorder Public Search](https://www.recorder.pima.gov/PublicSearch)  
  * **Bulk/FTP Access:** You must set up a "Business Account" for FTP access to daily recordings.  
  * **Search Terms:**  
    * *Pre-Foreclosure:* "NOTICE OF TRUSTEE SALE" or "SUBSTITUTION OF TRUSTEE"  
    * *Liens:* "MECHANICS LIEN" or "HOA LIEN"

### **3\. Pima County Treasurer (Tax Delinquency)**

* **Data:** Unpaid property taxes, tax lien certificates (properties about to be lost to tax sale).  
* **Access Method:** Pima County holds an annual tax lien sale (usually online in Feb/March), but you can find delinquent properties year-round.  
  * **Search Portal:** [Pima County Treasurer Property Search](https://www.to.pima.gov/propertySearch/)  
  * **The "Backdoor" List:** Look for the **"CP Buyers List"** (Certificate of Purchase) or the **"Assignment List"**. These are properties that already have a lien sold on them (high distress).  
  * **Bulk Option:** They publish the "Tax Lien Sale List" as a downloadable Excel/PDF file usually starting in January.

### **4\. Pima County Superior Court (Probate & Eviction)**

* **Data:** Probate cases (deceased owners), Eviction filings (Forcible Detainer), Divorce decrees requiring property sale.  
* **Access Method:** Operated by the **Clerk of the Superior Court**.  
  * **Online Search:** [Pima County Superior Court Records Search](https://www.google.com/search?q=https://www.agave.cosc.pima.gov/) (Note: This system is often nicknamed "Agave").  
  * **Probate Strategy:** Search for Case Type "PB" (Probate). You are looking for "Petition for Appointment of Personal Representative."  
  * **Bulk Access:** They generally do not offer an API. You often have to pay for a bulk data request or use a scraper on the Agave system (be careful with rate limits).

### **5\. City of Tucson Code Enforcement (Code Violations)**

* **Data:** Tall weeds, structural issues, junk vehicles, zoning violations.  
* **The "API" Connection:** The City of Tucson has its own Open Data portal (separate from the County) which is excellent for code violations.  
  * **Direct Link:** [Tucson Open Data Portal](https://gisdata.tucsonaz.gov/)  
  * **Dataset to Search:** Look for "Code Enforcement Violations" or "Property Research Online (PRO) Data."  
  * **API:** Like the County, this is an ArcGIS Hub. You can pull the "Code Violations" layer via GeoJSON API updated daily.

### **6\. The "Invisible" Lists (FOIA Required)**

These are not online and require you to email the specific department with a Freedom of Information Act (Public Records) Request.

* **Water Shutoffs:**  
  * **Agency:** **Tucson Water** (Public Records Request Dept).  
  * **Request:** "A list of all residential properties with water service currently disconnected due to non-payment for more than 30 days."  
* **Fire Damaged Properties:**  
  * **Agency:** **Tucson Fire Department**.  
  * **Request:** "A list of all residential structure fires reported in the last 60 days."

### **Summary Cheat Sheet for Pima County**

| Distress Signal | Source Name | Access Type | URL/Action |
| :---- | :---- | :---- | :---- |
| **Ownership/Mailing** | Pima County GIS | **API / Bulk CSV** | [gisopendata.pima.gov](https://gisopendata.pima.gov/) |
| **Code Violations** | Tucson Open Data | **API / Bulk CSV** | [gisdata.tucsonaz.gov](https://gisdata.tucsonaz.gov/) |
| **Pre-Foreclosure** | County Recorder | Manual / FTP | [recorder.pima.gov](https://www.recorder.pima.gov/) |
| **Tax Delinquency** | County Treasurer | Search / Excel | [to.pima.gov](https://www.to.pima.gov/) |
| **Probate** | Superior Court | Manual Search | [agave.cosc.pima.gov](https://www.google.com/search?q=https://www.agave.cosc.pima.gov/) |
| **Water Shutoff** | Tucson Water | **FOIA Email** | Email Public Records Dept |

**Would you like me to generate the exact text you need to copy/paste for a FOIA request to Tucson Water to get that shutoff list?**