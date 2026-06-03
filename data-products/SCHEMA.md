# Data Products — Schema Reference

Each dataset is described below with its key columns, date range, and notes on structure.

---

## prescribers.csv
**29 MB · Best starting point — links all other datasets by prescriber**

| Column | Description |
|--------|-------------|
| `prescriber_number_code` | Unique numeric prescriber identifier (joins to `*_bydates.csv` files) |
| `prescriber_name` | Full prescriber name |
| `prescriber_letter_code` | Alternate letter-based identifier |
| `Address` | Prescriber practice address |
| `Territory` | Sales territory name |
| `PDRP` | Prescriber Data Restriction Program flag |
| `duexis` | Flag: prescribes Duexis |
| `exalgo` | Flag: prescribes Exalgo |
| `pennsaid` | Flag: prescribes Pennsaid |
| `sumavel` | Flag: prescribes Sumavel |
| `xartemis` | Flag: prescribes Xartemis XR |

---

## insys_authorized_rx.csv / insys_authorized_rx.csv.zip
**4.6 GB (CSV) · 693 MB (compressed) · Insys prescription transaction records**

| Column | Description |
|--------|-------------|
| `Date_of_Service` | Date prescription was dispensed |
| `Processing_Date` | Date prescription was processed |
| `NDC` | National Drug Code |
| `Quantity_Dispensed` | Units dispensed |
| `Days_Supply` | Days of supply |
| `Pharmacy_REMS_ID` | Pharmacy identifier in REMS program |
| `Pharmacy_Name` | Pharmacy name |
| `Prescriber_REMS_ID` | Prescriber identifier in REMS program |
| `Prescriber_Last_Name` | Prescriber last name |
| `New_Repeat` | New vs. repeat prescription flag |
| `Times_on_Subsys` | Number of times patient has been on Subsys |
| `Proc_Rel` | Process-related field |
| `SSP` | Sales specialist identifier |
| `DM` | District manager |
| `FSD` | Field sales director |
| `Class` | Prescriber classification |
| `ASD` | Area sales director |
| `RM` | Regional manager |
| `RD` | Regional director |
| `PDRP` | Prescriber Data Restriction Program flag |
| `WAC_Revenue` | Wholesale acquisition cost revenue |
| `Field_Sales` | Field sales rep |
| `Unique_Rxer` | Unique prescriber flag |
| `Unique_Rxer_by_WK` | Unique prescriber by week |
| `Decile` | Prescriber decile ranking |
| `Month` | Month of service |
| `Strength` | Drug strength |
| `Units` | Unit of measure |
| `Quarter` | Quarter of service |
| `Q_Rxer_Count` | Quarterly prescriber count |
| `Territory_Name` | Sales territory name |
| `Region_Name` | Sales region name |
| `RSM` | Regional sales manager |
| `SSP_Email` | Sales specialist email |
| `RSM_Email` | Regional sales manager email |
| `Total_Rejected_Transactions` | Count of rejected transactions |
| `Flag` | Exception flag |
| `Flag_Count` | Number of flags |
| `Patient_ID` | De-identified patient identifier |
| `Region_Code` | Region code |
| `IC` | Incentive compensation field |
| `Territory_Code` | Territory code |
| `Rx_Code` | Prescription code |
| `Week_Code` | Week identifier |
| `Status` | Prescription status |

---

## mnk_customer_orders.csv / mnk_customer_orders.csv.zip
**38 MB (CSV) · 3.6 MB (compressed) · Mallinckrodt customer order records**

| Column | Description |
|--------|-------------|
| `order_number` | Unique order identifier |
| `order_held` | Whether order was held for review |
| `hold_code` | Reason code for hold |
| `bill_to_customer` | Billing customer ID |
| `bill_to_customer_name` | Billing customer name |
| `segment` | Market segment |
| `ship_to_customer` | Ship-to customer ID |
| `ship_to_customer_name` | Ship-to customer name |
| `dea_number` | DEA registration number |
| `item_number` | Product item number |
| `item_description` | Product description |
| `item_description2` | Additional product description |
| `quantity_ordered` | Units ordered |
| `factor_x_18_mth_qty_avg` | 18-month average quantity factor |
| `current_month_order_qty` | Current month order quantity |
| `factor_x_18_mth_number_orders` | 18-month average order count factor |
| `current_month_number_orders` | Current month order count |
| `segment_high` | Segment order quantity high threshold |
| `segment_low` | Segment order quantity low threshold |
| `segment_avg` | Segment order quantity average |
| `new_customer_flag` | Flag: new customer |
| `new_item_flag` | Flag: new item for this customer |
| `qty_threshold_limit_flag` | Flag: quantity exceeds threshold |
| `irregular_order_flag` | Flag: irregular order pattern |
| `hold_description` | Human-readable hold reason |
| `report_date` | Date of report |
| `report_time` | Time of report |
| `document_type` | Order document type |
| `line_number` | Order line number |
| `business_unit` | Business unit |
| `uom` | Unit of measure |
| `extended_price` | Total line price |
| `comments` | Analyst comments |
| `som_analyst_recommendation` | Suspicious order monitoring analyst recommendation |
| `mcsc_dgrc_recommendation` | MCSC/DGRC committee recommendation |
| `date_of_release` | Date order was released from hold |
| `ship_to_dea_number` | Ship-to DEA number |
| `test` | Test record flag |
| `estimated_annual_volume` | Estimated annual volume for customer |
| `award_percent` | Award percentage |

---

## Prescription-by-date datasets
**Wide-format CSVs: one row per prescriber, one column per week**

These share a common structure: fixed identifier columns followed by weekly prescription and market-share columns spanning the dataset's date range.

### Common identifier columns

| Column | Description |
|--------|-------------|
| `Prescriber.Name` / `Prescriber Name` | Prescriber full name |
| `Address` | Prescriber practice address |
| `Territory` | Sales territory |
| `PDRP` | Prescriber Data Restriction Program flag |
| `prescriber_code` | Unique prescriber identifier (last column; joins to `prescribers.csv`) |
| `*-x13wk-total-*` | 13-week rolling total for drug and market |
| `Exception` | Exception flag for unusual patterns |

### Weekly columns (repeated per date)
- `YYYY-MM-DD-{drug}` — weekly script count for the named drug
- `YYYY-MM-DD-{drug}-market` — weekly total market scripts for the same therapeutic class

### Dataset-specific notes

| File | Drug | Date range | Notes |
|------|------|------------|-------|
| `duexis_bydates.csv` | Duexis (ibuprofen/famotidine) | 2012-07 – 2013-07 | |
| `exalgo_bydates.csv` | Exalgo (hydromorphone ER) | 2012-07 – 2014-06 | Includes `Territory` column |
| `pennsaid_bydates.csv` | Pennsaid 1.5% & 2.0% (diclofenac) | 2012 – 2014 | Two drug columns per week (1.5% and 2.0% formulations) |
| `sumavel_bydates.csv` | Sumavel DosePro (sumatriptan) | 2012-08 – 2014-01 | |
| `xartemis_bydates.csv` | Xartemis XR (oxycodone/acetaminophen) | 2014-01 – 2014-07 | Includes `Territory` column |

---

## Bulk archive datasets (ZIP)

| File | Contents |
|------|----------|
| `insys_full_dedup.zip` | Full deduplicated Insys document collection |
| `mallinckrodt_full_dedup.zip` | Full deduplicated Mallinckrodt document collection (61 GB) |
| `mckinsey_full_dedup.zip` | Full deduplicated McKinsey document collection |
| `mnk_prescriber_records.zip` | Mallinckrodt prescriber records |
| `image_collection_version_1.zip` | Document images (see `oida-image-collection-metadata-version-1.csv.gz` for metadata) |

See the `.readme.txt` file alongside each ZIP for source and processing notes.
