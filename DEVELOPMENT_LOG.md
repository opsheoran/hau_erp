# ERP Development Workflow & Progress Log

## 1. Master Template Integration Workflow
This workflow was established on 23/02/2026 to ensure 100% data accuracy and parity with the legacy ERP system.

### Step 1: Database-Wide Discovery
- **Identify candidate tables**: Search the entire schema for keywords related to the module (e.g., 'employee', 'sal_', 'gpf_').
- **Filter temporary/dated data**: Programmatically exclude tables with suffixes like `_bak`, `_temp`, `_2021`, etc., to avoid using obsolete data sources.
- **Verify row activity**: Check row counts to confirm which tables are actively being used in the current production cycle.

### Step 2: Temporal Verification
- **Audit "Latest" state**: Query date-based columns (`lastupdateddate`, `effectivedate`, `dated`) across primary tables to ensure entries are current (up to Feb 2026).
- **Confirm active session**: For financial data, identify the latest `fk_finid` (e.g., `CO-18` for 2025-26) to pull relevant balances.

### Step 3: Deep Field Mapping
- **Section-by-section analysis**: Match every single field in the HTML template to a specific `Table.Column`.
- **Join Resolution**: Identify where data is spread across multiple tables (e.g., `SAL_Employee_Mst` for basics vs. `gpf_employee_details` for identifiers).
- **Fallback Logic**: Establish priority for fields stored in multiple places (e.g., using `BMS_BM10_Details` if `SAL_EmployeeOther_Details` is empty).

### Step 4: Technical Standardization
- **Date Casing**: Always use `CONVERT(varchar, Column, 23)` in SQL to match HTML5 `input type="date"` (YYYY-MM-DD).
- **ID Casting**: Ensure `head_id` comparisons are type-safe (casting to `int` or `bigint` as needed).
- **Dynamic Overrides**: Calculate totals and summary fields based on real-time transaction data rather than just static master records.

### Step 5: Reference Documentation
- **Technical Reference File**: On completion of each template, generate a `[MODULE]_TECHNICAL_REFERENCE.txt` file.
- **Permanent Mapping**: Store the list of "Verified Latest Tables" to eliminate search time for subsequent related templates.

---

## 2. Completed Modules & Verified Tables

### Employee Master (Completed 23/02/2026)
*Refer to `EMPLOYEE_MASTER_TECHNICAL_REFERENCE.txt` for detailed column mapping.*

**Verified Active Tables:**
- `SAL_Employee_Mst` (Primary Master)
- `SAL_EmployeeOther_Details` (Extended Demographics)
- `SAL_Salary_Master` (Income Tax & Net Pay - Verified active for Feb 2026)
- `gpf_employee_details` (GPF Identifiers & Types)
- `GPF_Balance_Mst` (Active Balances)
- `SAL_LoanTransaction_Details` (Real-time GPF Advance Installments)
- `SAL_FirstAppointment_Details` (Appointment Order Numbers)
- `SAL_FMAeffective_Trn` (Medical Allowance Effective Dates)
- `BMS_BM10_Details` (Retirement Fallback & Grade Strings)

---

## 3. Mandatory Future Actions
1. **Never assume a table name**: Always perform Step 1 (Discovery) for new modules to find the "Production" version of a table.
2. **Auto-Populate References**: Every new template must produce a corresponding mapping file.
3. **Daily Backups**: Perform a timestamped ZIP backup after every major template completion.

---

## 4. Current Focus (Leave Management)
**Scope note (24/02/2026):** From this point onward, focus only on the **Leave Management module** workstreams. Avoid unrelated module changes unless explicitly requested.

**Live template references currently available locally:**
- `leave/leave dashboar.html` (saved from `UMM/Admin_Home.aspx?MID=NzU=`) + assets in `leave/leave dashboar_files/`.

If additional live Leave pages are needed for pixel-perfect parity, export/save them into `leave/` before implementing changes so field-to-column mapping can be verified against the exact UI.
