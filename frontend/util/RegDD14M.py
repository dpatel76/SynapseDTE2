import pandas as pd
import re
from typing import Dict, List, Tuple
import csv
from collections import defaultdict

class FRY14MDictionaryExtractor:
    """
    Extracts and creates a master data dictionary for FR Y-14M schedules
    """
    
    def __init__(self):
        self.schedules = {
            'A': 'Domestic First Lien Closed-end 1-4 Family Residential Loan',
            'B': 'Domestic Home Equity Loan and Home Equity Line',
            'C': 'Address Matching Loan Level',
            'D': 'Domestic Credit Card'
        }
        
        self.all_data_elements = []
        self.schedule_counts = defaultdict(int)
        
    def parse_schedule_a(self, content: str) -> List[Dict]:
        """Parse Schedule A - First Lien data elements"""
        elements = []
        
        # Schedule A.1 - Loan Level Table
        schedule_a1_elements = [
            (1, "Loan Number", "M142", "Loan Number", "Static", "Mandatory", "Character(32)"),
            (2, "Loan Closing Date", "M143", "Loan Closing Date", "Dynamic", "Mandatory", "YYYYMMDD"),
            (3, "First Payment Date", "M144", "First Payment Date", "Dynamic", "Mandatory", "YYYYMMDD"),
            (4, "Property State", "9200", "Property State", "Dynamic", "Mandatory", "Character(2)"),
            (5, "Property ZIP Code", "9220", "Property Zip Code", "Dynamic", "Mandatory", "Character(5)"),
            (6, "Original Loan Amount Disbursed", "M147", "Original Loan Amount Disbursed", "Static", "Mandatory", "Whole Number"),
            (7, "Original Property Value", "M148", "Original Property Value", "Static", "Mandatory", "Whole Number"),
            (8, "Original LTV", "M149", "Original LTV", "Static", "Mandatory", "Numeric, to 2 decimals"),
            (9, "Original Combined LTV", "M150", "Original Combined LTV", "Static", "Optional", "Numeric, to 2 decimals"),
            (10, "Income Documentation", "M151", "Income Documentation", "Static", "Optional", "Character(1)"),
            (11, "Debt to Income (DTI) Back-End at Origination", "M152", "Debt to Income (DTI) Back-End", "Static", "Optional", "Whole Number"),
            (12, "Debt to Income (DTI) Front-End at Origination", "M153", "DTI Ratio (Front-end) at origination", "Static", "Mandatory", "Whole Number"),
            (13, "Origination Credit Bureau Score", "M154", "Credit Bureau Score", "Static", "Mandatory", "Whole Number"),
            (14, "Occupancy", "M155", "Occupancy", "Static", "Mandatory", "Character(1)"),
            (15, "Credit Class", "M156", "Credit Class", "Static", "Mandatory", "Character(1)"),
            (16, "Loan Type", "M157", "Loan Type", "Static", "Mandatory", "Character(1)"),
            (17, "Lien Position at Origination", "M158", "Lien Position at Origination", "Static", "Mandatory", "Character(1)"),
            (18, "Loan Source", "M159", "Loan Source", "Static", "Mandatory", "Character(1)"),
            (19, "Product Type - Current", "M160", "Product Type", "Dynamic", "Mandatory", "Character(2)"),
            (20, "Loan Purpose Coding", "M161", "Loan Purpose Coding", "Static", "Mandatory", "Character(1)"),
            (21, "Number of Units", "M162", "Number of Units", "Static", "Mandatory", "Character(1)"),
            (22, "Mortgage Insurance Coverage Percent at Origination", "M163", "Mortgage Insurance Coverage Percent", "Static", "Mandatory", "Numeric, to 2 decimal places"),
            (23, "Property Type", "M164", "Property Type", "Static", "Mandatory", "Character(1)"),
            (24, "Balloon Flag", "M165", "Balloon Flag", "Static", "Mandatory", "Character(1)"),
            (25, "Balloon Term", "M166", "Balloon Term", "Static", "Mandatory", "Whole Number"),
            (27, "Interest Only at Origination", "M168", "Interest Only at Origination Flag", "Static", "Mandatory", "Character(1)"),
            (28, "Recourse Flag", "M169", "Recourse Flag", "Static", "Mandatory", "Character(1)"),
            (29, "ARM Initial Rate", "M170", "ARM Initial Rate", "Static", "Mandatory", "Numeric, up to 5 decimals"),
            (30, "ARM Initial Rate Period", "M171", "ARM Initial Rate Period", "Static", "Mandatory", "Whole Number"),
            (31, "ARM Periodic Interest Reset Period", "M172", "ARM Periodic Interest Reset Period", "Static", "Mandatory", "Whole Number"),
            (32, "ARM Index", "M173", "ARM Index", "Static", "Mandatory", "Character(2)"),
            (33, "ARM Margin at Origination", "M174", "ARM margin", "Static", "Mandatory", "Numeric, up to 5 decimals"),
            (34, "ARM Negative Amortization % Limit", "M175", "ARM negative amortization % limit", "Static", "Mandatory", "Numeric, up to 5 decimals"),
            (35, "ARM Periodic Rate Cap", "M176", "ARM periodic rate cap", "Static", "Mandatory", "Numeric, up to 5 decimals"),
            (36, "ARM Periodic Rate Floor", "M177", "ARM Periodic Rate Floor", "Static", "Mandatory", "Numeric, up to 5 decimals"),
            (37, "ARM Lifetime Rate Cap", "M178", "ARM Lifetime Rate Cap", "Static", "Mandatory", "Numeric, up to 5 decimals"),
            (38, "ARM Lifetime Rate Floor", "M179", "ARM Lifetime Rate Floor", "Static", "Mandatory", "Numeric, up to 5 decimals"),
            (39, "ARM Periodic Pay Cap", "M180", "ARM Periodic Pay Cap", "Static", "Mandatory", "Numeric, up to 5 decimals"),
            (40, "ARM Periodic Pay Floor", "M181", "ARM Periodic Pay Floor", "Static", "Mandatory", "Numeric, up to 5 decimals"),
            (41, "Option ARM Flag", "M182", "Option ARM at Origination", "Static", "Mandatory", "Character(1)"),
            (42, "Negative Amortization Flag", "M183", "Negative Amortization Flag", "Static", "Mandatory", "Character(1)"),
            (43, "Original Loan Term", "M184", "Original Loan Term", "Static", "Mandatory", "Whole Number"),
            (44, "Original Interest Rate", "M185", "Original Interest Rate", "Static", "Mandatory", "Numeric, up to 5 decimal places"),
            (45, "Principal and Interest (P&I) Amount at Origination", "M186", "Principal and Interest (P&I) Amount at Origination", "Static", "Optional", "Whole Number"),
            (46, "Pre-Payment Penalty Flag", "M187", "Pre-payment Penalty Flag", "Static", "Mandatory", "Character(1)"),
            (47, "Pre-Payment Penalty Term", "M188", "Pre-Payment Penalty Term", "Static", "Mandatory", "Whole Number"),
            (48, "Current Credit Bureau Score", "M189", "Current Credit Bureau Score", "Dynamic", "Mandatory", "Whole Number"),
            (49, "Interest Only in Reporting Month", "M190", "Interest Only in Reporting Month", "Dynamic", "Mandatory", "Character(1)"),
            (50, "Investor Type", "M191", "Investor Type", "Dynamic", "Mandatory", "Character(1)"),
            (52, "Option ARM in Reporting Month", "M193", "Option ARM in Reporting Month", "Dynamic", "Mandatory", "Character(1)"),
            (53, "Bankruptcy flag", "M194", "Bankruptcy flag", "Dynamic", "Mandatory", "Character(1)"),
            (54, "Bankruptcy Chapter", "M195", "Bankruptcy Chapter", "Dynamic", "Mandatory", "Character(2)"),
            (55, "Next Payment Due Date", "M196", "Next payment due date", "Dynamic", "Mandatory", "YYYYMMDD"),
            (56, "Current Interest Rate", "M197", "Current Interest Rate", "Dynamic", "Mandatory", "Numeric, up to 5 decimals"),
            (57, "Remaining Term", "M198", "Remaining Term", "Dynamic", "Mandatory", "Whole Number"),
            (59, "Principal and Interest (P&I) Amount Current", "M200", "Principal and Interest (P&I) Amount Current", "Dynamic", "Mandatory", "Whole Number"),
            (60, "Unpaid Principal Balance", "M201", "Unpaid Principal Balance", "Dynamic", "Mandatory", "Whole Number"),
            (61, "Foreclosure Sale Date", "M202", "Foreclosure Sale Date", "Dynamic", "Mandatory", "YYYYMMDD"),
            (62, "Foreclosure Referral Date", "M203", "Foreclosure Referral Date", "Dynamic", "Mandatory", "YYYYMMDD"),
            (63, "Foreclosure Suspended", "M204", "Foreclosure Suspended", "Dynamic", "Mandatory", "Character(1)"),
            (64, "Paid-in-Full Coding", "M205", "Paid-in-Full Coding", "Dynamic", "Mandatory", "Character(1)"),
            (65, "Foreclosure Status", "M206", "Foreclosure Status", "Dynamic", "Mandatory", "Character(1)"),
            (66, "Repurchase Type", "M207", "Loan Repurchase Type", "Dynamic", "Mandatory", "Character(1)"),
            (67, "Repurchase Request Date", "M208", "Repurchase Request Date", "Dynamic", "Mandatory", "YYYYMMDD"),
            (68, "Refreshed Property Value", "M209", "Refreshed property value", "Dynamic", "Optional", "Whole Number"),
            (69, "Refreshed Property Valuation Method", "M210", "Refreshed Property Valuation Method", "Dynamic", "Optional", "Character(1)"),
            (70, "Most Recent Property Valuation Date", "M211", "Most Recent Property Valuation Date", "Dynamic", "Optional", "YYYYMMDD"),
            (71, "Refreshed CLTV After Modification", "M212", "Refreshed CLTV After Modification", "Dynamic", "Optional", "Numeric, up to 2 decimals"),
            (72, "Refreshed DTI Ratio (Back-end)", "M213", "Refreshed DTI Ratio (Back-end)", "Dynamic", "Optional", "Whole Number"),
            (73, "Refreshed DTI Ratio (Front-end)", "M214", "Refreshed DTI Ratio (Front-end)", "Dynamic", "Optional", "Whole Number"),
            (74, "Modification Type", "M215", "Modification Type", "Dynamic", "Mandatory", "Numeric"),
            (75, "Last Modified Date", "M216", "Last Modified Date", "Dynamic", "Mandatory", "YYYYMMDD"),
            (77, "Workout Type Completed", "M218", "Workout Type Completed", "Dynamic", "Mandatory", "Numeric"),
            (82, "Delinquent Amount Capitalized", "M223", "Delinquent Amount Capitalized", "Dynamic", "Mandatory", "Whole Number"),
            (84, "Step Modification Flag", "M225", "Step Modification Flag", "Dynamic", "Mandatory", "Character(1)"),
            (85, "Loss Mitigation Performance Status", "M226", "Loss Mitigation Performance Status", "Dynamic", "Mandatory", "Character(1)"),
            (87, "Deferred Amount", "M228", "Deferred Amount", "Dynamic", "Mandatory", "Whole Number"),
            (89, "Principal Write-Down Amount", "M230", "Principal Write-Down Amount", "Dynamic", "Mandatory", "Whole Number"),
            (91, "Interest Type Conversion Duration", "M233", "Interest Type Conversion Duration", "Dynamic", "Mandatory", "Character(1)"),
            (92, "Purchased Credit Deteriorated Status", "M234", "Purchased Credit Deteriorated Status", "Dynamic", "Mandatory", "Character(1)"),
            (93, "Total Debt at Time of any Involuntary Termination", "M235", "Total Debt at Time of any Involuntary Termination", "Dynamic", "Mandatory", "Whole Number"),
            (94, "Net Recovery Amount", "M236", "Net Recovery Amount", "Dynamic", "Mandatory", "Whole Number"),
            (95, "Credit Enhanced Amount", "M237", "Credit Enhanced Amount", "Dynamic", "Mandatory", "Whole Number"),
            (96, "Troubled Debt Restructure Flag", "M238", "Troubled Debt Restructure Flag", "Dynamic", "Mandatory", "Character(1)"),
            (97, "Reported as Bank Owned Flag", "M239", "Reported as Bank-Owned Flag", "Dynamic", "Mandatory", "Character(1)"),
            (99, "Interest Rate Frozen", "M232", "Interest Rate Frozen", "Dynamic", "Mandatory", "Character(1)"),
            (103, "Interest Rate Before Modification", "M932", "Interest Rate Before Modification", "Dynamic", "Mandatory", "Numeric, up to 5 decimals"),
            (104, "Interest Rate After Modification", "M933", "Interest Rate After Modification", "Dynamic", "Mandatory", "Numeric, up to 5 decimals"),
            (111, "Original Property Valuation Method(appraisal method)", "M940", "Original Property Valuation Method", "Static", "Mandatory", "Character(1)"),
            (112, "Third Party Sale Flag", "M941", "Third Party Sale Flag", "Dynamic", "Mandatory", "Character(1)"),
            (113, "Escrow Amount Current", "M268", "Escrow Amount Current", "Dynamic", "Mandatory", "Whole Number"),
            (115, "Remodified Flag", "M943", "Remodified Flag", "Dynamic", "Mandatory", "Character(1)"),
            (116, "Mortgage Insurance Company", "M944", "Mortgage Insurance Company", "Dynamic", "Mandatory", "Numeric"),
            (117, "Interest Type at Origination", "M244", "Interest Type at Origination", "Static", "Mandatory", "Character(1)"),
            (118, "Entity Serviced", "M945", "Entity Serviced", "Static", "Mandatory", "Character(1)"),
            (121, "Sales Price of Property", "M948", "Sales Price of Property", "Dynamic", "Mandatory", "Whole Number"),
            (124, "Commercial Loan Flag", "M951", "Commercial Loan Flag", "Static", "Mandatory", "Character(1)"),
            (125, "Probability of Default – PD", "M114", "Probability of Default (PD)", "Dynamic", "Optional", "Numeric, up to 5 decimals"),
            (126, "Loss Given Default – LGD", "M115", "Loss Given Default (LGD)", "Dynamic", "Optional", "Numeric, up to 5 decimals"),
            (127, "Expected Loss Given Default – ELGD", "M116", "Expected Loss Given Default (ELGD)", "Dynamic", "Optional", "Numeric, up to 5 decimals"),
            (128, "Exposure at Default – EAD", "M117", "Exposure at Default (EAD)", "Dynamic", "Optional", "Whole Number"),
            (129, "Entity Type", "M952", "Entity Type", "Dynamic", "Mandatory", "Whole number"),
            (130, "HFI FVO/HFS Flag", "M953", "Portfolio HFI FVO / HFS Flag", "Dynamic", "Mandatory", "Character(1)"),
            (131, "Interest Only Term – Original", "M954", "Interest Only Term – Original", "Static", "Mandatory", "Whole Number"),
            (132, "Interest Type - Current", "M248", "Interest Type - Current", "Dynamic", "Mandatory", "Character(1)"),
            (133, "Product Type – Origination", "M955", "Product Type – Origination", "Static", "Mandatory", "Character(2)"),
            (134, "Origination Credit Bureau Score Vendor", "R036", "Credit Bureau Score Vendor", "Static", "Mandatory", "Character(1)"),
            (135, "Origination Credit Bureau Score Version", "R037", "Credit Bureau Score Version", "Static", "Mandatory", "Character(30)"),
            (136, "Current Credit Bureau Score Vendor", "R038", "Credit Bureau Score Vendor", "Dynamic", "Optional", "Character(1)"),
            (137, "Current Credit Bureau Score Version", "R039", "Credit Bureau Score Version", "Dynamic", "Optional", "Character(30)"),
            (138, "Current Credit Bureau Score Date", "S382", "Credit Bureau Score Date", "Dynamic", "Optional", "YYYYMMDD"),
            (139, "Serviced by Others (SBO) Flag", "R622", "Serviced by Others Flag", "Dynamic", "Mandatory", "Character(1)"),
            (140, "Reporting As of Month Date", "R623", "Reporting As of Month Date", "Dynamic", "Mandatory", "YYYYMM"),
            (141, "National Bank RSSD ID", "JA26", "National Bank RSSD ID", "Dynamic", "Mandatory", "Whole Number"),
            (142, "Actual Payment Amount", "M259", "Actual Payment Amount", "Dynamic", "Mandatory", "Whole Number"),
            (143, "Workout Type Started", "PG60", "Workout Type Started", "Dynamic", "Mandatory", "Numeric"),
            (144, "Fair Value Amount", "PG61", "Fair Value Amount", "Dynamic", "Mandatory", "Whole Number")
        ]
        
        # Schedule A.2 - Portfolio Level Table
        schedule_a2_elements = [
            (1, "Portfolio Segment ID", "M240", "Portfolio Segment ID", "Dynamic", "Mandatory", "Character(1)"),
            (2, "Unpaid Principal Balance", "M201", "Unpaid Principal Balance", "Dynamic", "Mandatory", "Whole Number"),
            (3, "Loss / Write-down Amount", "M241", "Loss / Write-down Amount", "Dynamic", "Mandatory", "Whole Number")
        ]
        
        # Process A.1 elements
        for item in schedule_a1_elements:
            element = {
                'Report Name': 'FR Y-14M',
                'Schedule Name': 'Schedule A.1 - Domestic First Lien Closed-end 1-4 Family Residential Loan (Loan Level)',
                'Line Item #': item[0],
                'Line Item Name': item[1],
                'Technical Line Item Name': item[1],
                'MDRM': item[2],
                'Description': item[3],
                'Static or Dynamic': item[4],
                'Mandatory or Optional': item[5],
                'Format': item[6],
                '# of reports or schedules used in': 1,
                'Other Schedule Reference': ''
            }
            elements.append(element)
            
        # Process A.2 elements
        for item in schedule_a2_elements:
            element = {
                'Report Name': 'FR Y-14M',
                'Schedule Name': 'Schedule A.2 - Domestic First Lien Closed-end 1-4 Family Residential Loan (Portfolio Level)',
                'Line Item #': item[0],
                'Line Item Name': item[1],
                'Technical Line Item Name': item[1],
                'MDRM': item[2],
                'Description': item[3],
                'Static or Dynamic': item[4],
                'Mandatory or Optional': item[5],
                'Format': item[6],
                '# of reports or schedules used in': 1,
                'Other Schedule Reference': ''
            }
            elements.append(element)
            
        return elements
    
    def parse_schedule_b(self, content: str) -> List[Dict]:
        """Parse Schedule B - Home Equity data elements"""
        elements = []
        
        # Schedule B.1 - Loan/Line Level Table
        schedule_b1_elements = [
            (1, "Loan Number", "M142", "Loan Number", "Static", "Mandatory", "Character(32)"),
            (2, "Loan Closing Date", "M143", "Loan Closing Date", "Static", "Mandatory", "YYYYMMDD"),
            (3, "First Payment Date", "M144", "First Payment Date", "Dynamic", "Mandatory", "YYYYMMDD"),
            (4, "Property State", "9200", "Property State", "Dynamic", "Mandatory", "Character(2)"),
            (5, "Property ZIP Code", "9220", "Property Zip Code", "Dynamic", "Mandatory", "Character(5)"),
            (6, "Original Loan Amount Disbursed", "M147", "Original Loan Amount Disbursed", "Static", "Mandatory", "Whole Number"),
            (7, "Original Loan / Line Commitment", "M242", "Original Loan / Line Commitment", "Static", "Mandatory", "Whole Number"),
            (8, "Original Property Value", "M148", "Original Property Value", "Static", "Mandatory", "Whole Number"),
            (9, "Original Combined LTV", "M150", "Original Combined LTV", "Static", "Mandatory", "Numeric, to 2 decimals"),
            (10, "Income Documentation", "M151", "Income Documentation", "Static", "Optional", "Character(1)"),
            (11, "Debt to Income (DTI) Back-End at Origination", "M152", "Debt to Income (DTI) Back-End", "Static", "Optional", "Whole Number"),
            (12, "Debt to Income (DTI) Front-End at Origination", "M153", "Debt to Income (DTI) Front-End", "Static", "Mandatory", "Whole Number"),
            (13, "Origination Credit Bureau Score", "M154", "Credit Bureau Score", "Static", "Mandatory", "Whole Number"),
            (14, "Current Credit Bureau Score", "M189", "Current Credit Bureau Score", "Dynamic", "Mandatory", "Whole Number"),
            (15, "Occupancy", "M155", "Owner Occupancy Flag", "Static", "Mandatory", "Character(1)"),
            (16, "Lien Position at Origination", "M158", "Lien Position at Origination", "Static", "Mandatory", "Character(1)"),
            (17, "Home Equity Line Type", "M243", "Home Equity Line Type", "Static", "Mandatory", "Character(1)"),
            (18, "Number of Units", "M162", "Number of Units", "Static", "Mandatory", "Character(1)"),
            (19, "Property Type", "M164", "Property Type", "Static", "Mandatory", "Character(1)"),
            (20, "Interest Type at Origination", "M244", "Interest Type at Origination", "Static", "Mandatory", "Character(1)"),
            (21, "Interest Only at Origination", "M168", "Interest Only at Origination", "Static", "Mandatory", "Character(1)"),
            (22, "Interest Only in Reporting Month", "M190", "Interest Only in Reporting Month", "Dynamic", "Mandatory", "Character(1)"),
            (23, "Loan Source", "M159", "Loan Source", "Static", "Mandatory", "Character(1)"),
            (24, "Credit Class", "M156", "Credit Class", "Static", "Mandatory", "Character(1)"),
            (25, "Loan / Line Owner", "M245", "Loan / Line Owner", "Dynamic", "Mandatory", "Character(1)"),
            (26, "ARM Initial Rate Period", "M171", "ARM initial rate adjustment period", "Static", "Mandatory", "Whole Number"),
            (27, "ARM Payment Reset Frequency", "M246", "ARM Payment Reset Frequency", "Static", "Mandatory", "Whole Number"),
            (28, "Allowable Draw Period", "M247", "Draw Period", "Static", "Mandatory", "Whole Number"),
            (29, "ARM Index", "M173", "ARM Index", "Static", "Mandatory", "Character(2)"),
            (30, "ARM Margin at Origination", "M174", "ARM margin", "Static", "Mandatory", "Numeric, to 5 decimals"),
            (31, "ARM Periodic Rate Cap", "M176", "ARM Periodic Rate Cap", "Static", "Mandatory", "Numeric, to 5 decimals"),
            (32, "ARM Periodic Rate Floor", "M177", "ARM Periodic Rate Floor", "Static", "Mandatory", "Numeric, to 5 decimals"),
            (33, "ARM Lifetime Rate Cap", "M178", "ARM Lifetime Rate Cap", "Static", "Mandatory", "Numeric, to 5 decimals"),
            (34, "ARM Lifetime Rate Floor", "M179", "ARM Lifetime Rate Floor", "Static", "Mandatory", "Numeric, to 5 decimals"),
            (37, "Original Loan/Line Term", "M184", "Original Loan/Line Term", "Static", "Mandatory", "Whole Number"),
            (38, "Bankruptcy Flag", "M194", "Bankruptcy flag", "Dynamic", "Mandatory", "Character(1)"),
            (39, "Next Payment Due Date", "M196", "Next payment due date", "Dynamic", "Mandatory", "YYYYMMDD"),
            (40, "Original Interest Rate", "M185", "Original Interest Rate", "Static", "Mandatory", "Numeric, to 5 decimals"),
            (41, "Current Interest Rate", "M197", "Current Interest Rate", "Dynamic", "Mandatory", "Numeric, to 5 decimals"),
            (42, "Interest Type - Current", "M248", "Interest Type in Current Month", "Dynamic", "Mandatory", "Character(1)"),
            (43, "Principal and Interest (P&I) Amount Current", "M200", "Principal and Interest (P&I) Amount Current", "Dynamic", "Mandatory", "Whole Number"),
            (44, "Unpaid Principal Balance", "M201", "Unpaid Principal Balance", "Dynamic", "Mandatory", "Whole Number"),
            (45, "Monthly Draw Amount", "M249", "Monthly Draw Amount", "Dynamic", "Mandatory", "Whole Number"),
            (46, "Current Credit Limit", "M250", "Current Credit Line Amount", "Dynamic", "Mandatory", "Whole Number"),
            (47, "Loan Status (MBA method)", "M251", "Loan Status", "Dynamic", "Mandatory", "Character(1)"),
            (48, "Foreclosure Referral Date", "M203", "Foreclosure Referral Date", "Dynamic", "Mandatory", "YYYYMMDD"),
            (49, "Foreclosure Sale Date", "M202", "Foreclosure Sale Date", "Dynamic", "Mandatory", "YYYYMMDD"),
            (50, "Pre-Payment Penalty Flag", "M187", "Pre-Payment Penalty Flag", "Static", "Mandatory", "Character(1)"),
            (51, "Pre-Payment Penalty Term", "M188", "Pre-Payment Penalty Term", "Static", "Mandatory", "Whole Number"),
            (53, "Foreclosure Status", "M206", "Foreclosure Status", "Dynamic", "Mandatory", "Character(1)"),
            (54, "Liquidation Status", "M252", "Liquidation Status", "Dynamic", "Mandatory", "Character(1)"),
            (55, "Troubled Debt Restructure Date", "N185", "Troubled Debt Restructure", "Dynamic", "Mandatory", "YYYYMMDD"),
            (58, "Interest Rate Frozen", "M232", "Interest Rate Frozen", "Dynamic", "Mandatory", "Character(1)"),
            (59, "Principal Deferred", "M227", "Principal Deferred", "Dynamic", "Mandatory", "Character(1)"),
            (60, "Purchased Credit Deteriorated Status", "M234", "Purchased Credit Deteriorated Status", "Dynamic", "Mandatory", "Character(1)"),
            (61, "Workout Type Completed", "M218", "Workout Type Completed / Executed", "Dynamic", "Mandatory", "Numeric"),
            (62, "First Mortgage Serviced In House", "M253", "First Mortgage Serviced In House", "Dynamic", "Mandatory", "Character(1)"),
            (63, "Settlement Negotiated Amount", "M254", "Settlement Negotiated Amount", "Dynamic", "Mandatory", "Whole Number"),
            (64, "Credit Line Frozen Flag", "M255", "Credit Line Frozen Flag", "Dynamic", "Mandatory", "Character(1)"),
            (65, "Locked Amount – Amortizing – LOC", "M256", "Locked Amount – Amortizing – LOC", "Dynamic", "Mandatory", "Whole Number"),
            (66, "Locked Amount – Interest Only – LOC", "M257", "Locked Amount – Interest Only – LOC", "Dynamic", "Mandatory", "Whole Number"),
            (68, "Actual Payment Amount", "M259", "Actual Payment Amount", "Dynamic", "Mandatory", "Whole Number"),
            (69, "Lockout Feature Flag", "M260", "Lockout Feature Flag", "Static", "Mandatory", "Character(1)"),
            (70, "Credit Line Closed Flag", "M261", "Credit Line Closed Flag", "Dynamic", "Mandatory", "Character(1)"),
            (72, "Term modification", "M263", "Term modification", "Dynamic", "Mandatory", "Character(1)"),
            (73, "Principal Write-down", "M229", "Principal Write-down", "Dynamic", "Mandatory", "Character(1)"),
            (74, "Line Re-age", "M264", "Line Re-age", "Dynamic", "Mandatory", "Character(1)"),
            (75, "Loan Extension", "M265", "Loan Extension", "Dynamic", "Mandatory", "Character(1)"),
            (76, "Current Combined LTV", "M266", "Current Combined LTV", "Dynamic", "Optional", "Numeric, to 2 decimals"),
            (77, "Modification Type", "M215", "Modification Type", "Dynamic", "Mandatory", "Numeric"),
            (78, "Last Modified Date", "M216", "Last Modified Date", "Dynamic", "Mandatory", "YYYYMMDD"),
            (79, "Refreshed Property Value", "M209", "Refreshed property value", "Dynamic", "Optional", "Whole Number"),
            (80, "Refreshed Property Valuation Method", "M210", "Refreshed Property Valuation Method", "Dynamic", "Optional", "Character(1)"),
            (81, "Refreshed Property Valuation Date", "M267", "Refreshed Property Valuation Date", "Dynamic", "Optional", "YYYYMMDD"),
            (83, "Loan Purpose Coding", "M161", "Loan Purpose Coding", "Static", "Mandatory", "Character(1)"),
            (84, "Remaining Term", "M198", "Remaining Term", "Dynamic", "Mandatory", "Whole Number"),
            (85, "Bankruptcy Chapter", "M195", "Bankruptcy Chapter", "Dynamic", "Mandatory", "Character(2)"),
            (86, "Accrual Status", "M957", "Accrual Status", "Dynamic", "Mandatory", "Character(1)"),
            (87, "Foreclosure Suspended", "M204", "Foreclosure Suspended", "Dynamic", "Mandatory", "Character(1)"),
            (88, "Property Valuation Method at Origination (appraisal method)", "M940", "Property Valuation Method at Origination", "Static", "Mandatory", "Character(1)"),
            (89, "Loss Mitigation Performance Status", "M226", "Loss Mitigation Performance Status", "Dynamic", "Mandatory", "Character(1)"),
            (90, "Other Modification Action Type", "M958", "Other Modification Action Type", "Dynamic", "Mandatory", "Character(1)"),
            (92, "Third Party Sale Flag", "M941", "Third Party Sale Flag", "Dynamic", "Mandatory", "Character(1)"),
            (95, "Unpaid Principal Balance (Net)", "M960", "Unpaid Principal Balance (Net)", "Dynamic", "Mandatory", "Whole Number"),
            (98, "Entity Serviced", "M945", "Entity Serviced", "Static", "Mandatory", "Character(1)"),
            (99, "Total Debt at Time of any Involuntary Termination", "M235", "Total Debt at Time of any Involuntary Termination", "Dynamic", "Mandatory", "Whole Number"),
            (100, "Net Recovery Amount", "M236", "Net Recovery Amount", "Dynamic", "Mandatory", "Whole Number"),
            (101, "Sales Price of Property", "M948", "Sales Price of Property", "Dynamic", "Mandatory", "Whole Number"),
            (102, "Commercial Loan Flag", "M951", "Commercial Loan Flag", "Static", "Mandatory", "Character(1)"),
            (103, "Probability of Default – PD", "M114", "Probability of Default (PD)", "Dynamic", "Optional", "Numeric, up to 5 decimals"),
            (104, "Loss Given Default – LGD", "M115", "Loss Given Default (LGD)", "Dynamic", "Optional", "Numeric, up to 5 decimals"),
            (105, "Expected Loss Given Default – ELGD", "M116", "Expected Loss Given Default (ELGD)", "Dynamic", "Optional", "Numeric, up to 5 decimals"),
            (106, "Exposure at Default – EAD", "M117", "Exposure at Default (EAD)", "Dynamic", "Optional", "Whole Number"),
            (107, "Entity Type", "M952", "Entity Type", "Dynamic", "Mandatory", "Whole number"),
            (108, "HFI FVO/HFS Flag", "M953", "Portfolio HFI FVO / HFS", "Dynamic", "Mandatory", "Character(1)"),
            (109, "Origination Credit Bureau Score Vendor", "R036", "Credit Bureau Score Vendor", "Static", "Mandatory", "Character(1)"),
            (110, "Origination Credit Bureau Score Version", "R037", "Credit Bureau Score Version", "Static", "Mandatory", "Character(30)"),
            (111, "Current Credit Bureau Score Vendor", "R038", "Credit Bureau Score Vendor", "Dynamic", "Optional", "Character(1)"),
            (112, "Current Credit Bureau Score Version", "R039", "Credit Bureau Score Version", "Dynamic", "Optional", "Character(30)"),
            (113, "Current Credit Bureau Score Date", "S382", "Credit Bureau Score Date", "Dynamic", "Optional", "YYYYMMDD"),
            (114, "Serviced by Others (SBO) Flag", "R622", "Serviced by Others Flag", "Dynamic", "Mandatory", "Character(1)"),
            (115, "Reporting As of Month Date", "R623", "Reporting As of Month Date", "Dynamic", "Mandatory", "YYYYMM"),
            (116, "Payment Type at the end of draw period", "R624", "Payment Type at the end of draw period", "Dynamic", "Mandatory", "Character(1)"),
            (117, "National Bank RSSD ID", "JA26", "National Bank RSSD ID", "Dynamic", "Mandatory", "Whole Number"),
            (118, "Charge-off Amount", "LE95", "Charge-off Amount", "Dynamic", "Mandatory", "Whole Number"),
            (119, "Charge-off Date", "LE96", "Charge-off Date", "Dynamic", "Mandatory", "YYYYMMDD"),
            (120, "Workout Type Started", "PG60", "Workout Type Started", "Dynamic", "Mandatory", "Numeric")
        ]
        
        # Schedule B.2 - Portfolio Level Table
        schedule_b2_elements = [
            (1, "Portfolio Segment ID", "M240", "Portfolio Segment ID", "Dynamic", "Mandatory", "Character(1)"),
            (2, "Unpaid Principal Balance", "M201", "Unpaid Principal Balance", "Dynamic", "Mandatory", "Whole Number"),
            (3, "Loss / Write-down Amount", "M241", "Loss / Write-down Amount", "Dynamic", "Mandatory", "Whole Number")
        ]
        
        # Process B.1 elements
        for item in schedule_b1_elements:
            element = {
                'Report Name': 'FR Y-14M',
                'Schedule Name': 'Schedule B.1 - Domestic Home Equity Loan and Home Equity Line (Loan/Line Level)',
                'Line Item #': item[0],
                'Line Item Name': item[1],
                'Technical Line Item Name': item[1],
                'MDRM': item[2],
                'Description': item[3],
                'Static or Dynamic': item[4],
                'Mandatory or Optional': item[5],
                'Format': item[6],
                '# of reports or schedules used in': 1,
                'Other Schedule Reference': ''
            }
            elements.append(element)
            
        # Process B.2 elements
        for item in schedule_b2_elements:
            element = {
                'Report Name': 'FR Y-14M',
                'Schedule Name': 'Schedule B.2 - Domestic Home Equity Loan and Home Equity Line (Portfolio Level)',
                'Line Item #': item[0],
                'Line Item Name': item[1],
                'Technical Line Item Name': item[1],
                'MDRM': item[2],
                'Description': item[3],
                'Static or Dynamic': item[4],
                'Mandatory or Optional': item[5],
                'Format': item[6],
                '# of reports or schedules used in': 1,
                'Other Schedule Reference': ''
            }
            elements.append(element)
            
        return elements
    
    def parse_schedule_c(self, content: str) -> List[Dict]:
        """Parse Schedule C - Address Matching data elements"""
        elements = []
        
        schedule_c_elements = [
            (1, "Loan Number", "M142", "Loan Number", "Static", "Mandatory", "Character(32)"),
            (2, "Property Street Address", "9028", "Property Street Address", "Dynamic", "Mandatory", "Text(100)"),
            (3, "Property City", "9130", "Property City", "Dynamic", "Mandatory", "Text(50)"),
            (4, "Property State", "9200", "Property State", "Dynamic", "Mandatory", "Character(2)"),
            (5, "Property ZIP Code", "9220", "Property ZIP Code", "Dynamic", "Mandatory", "Character(9)"),
            (6, "Mailing Street Address", "9110", "Mailing Street Address", "Dynamic", "Mandatory", "Text(100)"),
            (7, "Mailing City", "F206", "Mailing City", "Dynamic", "Mandatory", "Text(50)"),
            (8, "Mailing State", "F207", "Mailing State", "Dynamic", "Mandatory", "Character(2)"),
            (9, "Mailing ZIP Code", "F208", "Mailing ZIP Code", "Dynamic", "Mandatory", "Character(9)"),
            (10, "Liquidation Status", "M252", "Liquidation Status", "Dynamic", "Mandatory", "Character(1)"),
            (11, "Lien Position at Origination", "M158", "Lien Position at Origination", "Static", "Mandatory", "Character(1)"),
            (12, "Census Tract", "M275", "Census Tract", "Dynamic", "Mandatory", "Character(10)"),
            (13, "Data File Reference", "M946", "Data File Reference", "Dynamic", "Mandatory", "Character(1)")
        ]
        
        for item in schedule_c_elements:
            element = {
                'Report Name': 'FR Y-14M',
                'Schedule Name': 'Schedule C.1 - Address Matching (Loan Level)',
                'Line Item #': item[0],
                'Line Item Name': item[1],
                'Technical Line Item Name': item[1],
                'MDRM': item[2],
                'Description': item[3],
                'Static or Dynamic': item[4],
                'Mandatory or Optional': item[5],
                'Format': item[6],
                '# of reports or schedules used in': 1,
                'Other Schedule Reference': ''
            }
            elements.append(element)
            
        return elements
    
    def parse_schedule_d(self, content: str) -> List[Dict]:
        """Parse Schedule D - Credit Card data elements"""
        elements = []
        
        # Schedule D.1 - Loan Level Table
        schedule_d1_elements = [
            (1, "Reference Number", "M046", "ReferenceNumber", "Static", "Mandatory", "C18"),
            (2, "Customer ID", "M047", "CustomerId", "Static", "Mandatory", "C18"),
            (3, "Bank ID", "9001", "BankId", "Static", "Mandatory", "N10"),
            (4, "Period ID", "9999", "PeriodId", "Dynamic", "Mandatory", "Date YYYYMMDD"),
            (5, "State", "M048", "AccountState", "Dynamic", "Mandatory", "C2"),
            (6, "Zip Code", "M049", "AccountZipCode", "Dynamic", "Mandatory", "C9"),
            (7, "Credit Card Type", "M050", "CreditCardType", "Dynamic", "Mandatory", "N1"),
            (8, "Product Type", "M051", "ProductType", "Dynamic", "Mandatory", "N1"),
            (9, "Lending Type", "M052", "LendingType", "Dynamic", "Mandatory", "N1"),
            (10, "Revolve Feature", "M053", "RevolveFlag", "Dynamic", "Mandatory", "N1"),
            (11, "Network ID", "M054", "NetworkId", "Dynamic", "Mandatory", "N1"),
            (12, "Secured Credit Type", "M055", "CreditCardSecuredFlag", "Dynamic", "Mandatory", "N1"),
            (13, "Loan Source/Channel", "M056", "LoanChannel", "Static", "Mandatory", "N1"),
            (14, "Purchased Credit Deteriorated Status", "M234", "PCDFlag", "Dynamic", "Mandatory", "N1"),
            (15, "Cycle Ending Balance", "M058", "CycleEndingBalance", "Dynamic", "Mandatory", "N12.2"),
            (17, "Accounts Under Promotion", "M060", "PromotionFlag", "Dynamic", "Mandatory", "N1"),
            (18, "Cycle Ending Balances Mix - Promotional", "M061", "CycleEndingBalancePromotional", "Dynamic", "Mandatory", "N12.2"),
            (19, "Cycle Ending Balances Mix - Cash", "M062", "CycleEndingBalanceCash", "Dynamic", "Mandatory", "N12.2"),
            (20, "Cycle Ending Balances Mix - Penalty", "M063", "CycleEndingBalancePenalty", "Dynamic", "Mandatory", "N12.2"),
            (21, "Cycle Ending Balances Mix - Other", "M064", "CycleEndingBalanceOther", "Dynamic", "Mandatory", "N12.2"),
            (22, "Average Daily Balance (ADB)", "M065", "AverageDailyBalance", "Dynamic", "Mandatory", "N12.2"),
            (23, "Total Reward Cash", "M066", "TotalRewardCash", "Dynamic", "Mandatory", "N12.2"),
            (24, "Reward Type", "M067", "RewardType", "Dynamic", "Mandatory", "N1"),
            (25, "Account Cycle Date", "M068", "AccountCycleEndDate", "Dynamic", "Mandatory", "Date YYYYMMDD"),
            (26, "Account Origination Date", "M069", "AccountOriginationDate", "Static", "Mandatory", "Date YYYYMMDD"),
            (27, "Acquisition Date", "M070", "AcqDate", "Static", "Mandatory", "Date YYYYMMDD"),
            (28, "Multiple Banking Relationships", "M071", "MultipleBankingRelationshipFlag", "Dynamic", "Mandatory", "N1"),
            (29, "Multiple Credit Card Relationships", "M072", "MultipleCardRelationshipFlag", "Dynamic", "Mandatory", "N1"),
            (30, "Joint Account", "M073", "JointAccount", "Dynamic", "Mandatory", "N1"),
            (31, "Authorized Users", "M074", "AuthorizedUsers", "Dynamic", "Mandatory", "N5"),
            (32, "Flagged as Securitized", "M075", "SecuritizedFlag", "Dynamic", "Mandatory", "N1"),
            (33, "Borrower's Income at Origination", "M076", "BorrowerIncome", "Static", "Mandatory", "N12"),
            (34, "Income Source at Origination", "M077", "BorrowerIncomeType", "Static", "Mandatory", "N1"),
            (38, "Origination Credit Bureau Score for the primary account holder", "M081", "OriginalCreditScorePrimaryBorrower", "Static", "Mandatory", "N3"),
            (39, "Origination Credit Bureau Score for the co-borrower (if any)", "M082", "OriginalCreditScoreCoborrower", "Static", "Mandatory", "N3"),
            (40, "Refreshed Credit Bureau Score", "M083", "RefreshedCreditScorePrimaryBorrower", "Dynamic", "Mandatory", "N3"),
            (41, "Credit Bureau Score Refresh Date", "M084", "CreditScoreRefreshDate", "Dynamic", "Mandatory", "Date YYYYMMDD"),
            (42, "Behavioral Score", "M085", "BehavioralScore", "Dynamic", "Optional", "N10.6"),
            (43, "Original Credit Limit", "M086", "OriginalCreditLimit", "Static", "Mandatory", "N12.2"),
            (44, "Current Credit limit", "M087", "CurrentCreditLimit", "Dynamic", "Mandatory", "N12.2"),
            (45, "Current Cash Advance Limit", "M088", "CurrentCashAdvanceLimit", "Dynamic", "Mandatory", "N12.2"),
            (46, "Line Frozen in the current month", "M089", "LineFrozenFlag", "Dynamic", "Mandatory", "N1"),
            (47, "Line Increase or Decrease in the current month", "M090", "LineIncreaseDecreaseFlag", "Dynamic", "Mandatory", "N1"),
            (48, "Minimum Payment Due", "M091", "MinimumPaymentDue", "Dynamic", "Mandatory", "N12.2"),
            (49, "Total Payment Due", "M092", "TotalPaymentDue", "Dynamic", "Mandatory", "N12.2"),
            (50, "Next Payment Due Date", "M093", "NextPaymentDueDate", "Dynamic", "Mandatory", "Date YYYYMMDD"),
            (51, "Actual Payment Amount", "M094", "ActualPaymentAmount", "Dynamic", "Mandatory", "N12.2"),
            (52, "Total Past Due", "M095", "TotalPastDue", "Dynamic", "Mandatory", "N12.2"),
            (53, "Days Past Due", "M096", "DaysPastDue", "Dynamic", "Mandatory", "N3"),
            (54, "Account 60 Plus DPD Last Three Years Flag", "M097", "Account60PlusDPDLastThreeYearsFlag", "Dynamic", "Mandatory", "N1"),
            (56, "APR at Cycle End", "M099", "CycleEndingRetailAPR", "Dynamic", "Mandatory", "N6.3"),
            (57, "Fee Type", "M100", "FeeTypeFlag", "Dynamic", "Mandatory", "N1"),
            (58, "Month-end Account Status - Active", "M101", "MonthEndActiveFlag", "Dynamic", "Mandatory", "N1"),
            (59, "Month-end Account Status - Closed", "M102", "MonthEndClosedRevokedFlag", "Dynamic", "Mandatory", "N1"),
            (60, "Collection Re-age Date", "M103", "CollectionReageDate", "Dynamic", "Mandatory", "Date YYYYMMDD"),
            (61, "Charge-off Reason", "M104", "ChargeOffReasonCode", "Dynamic", "Mandatory", "N1"),
            (62, "Gross Charge-off Amount – Current Month", "M105", "GrossChargeOffInCurrentMonthAmount", "Dynamic", "Mandatory", "N12.2"),
            (63, "Recovery Amount – Current Month", "M106", "RecoveryAmount", "Dynamic", "Mandatory", "N12.2"),
            (64, "Purchase Amount", "M107", "PurchaseVolume", "Dynamic", "Mandatory", "N12.2"),
            (65, "Cash Advance Amount", "M108", "CashAdvanceVolume", "Dynamic", "Mandatory", "N12.2"),
            (66, "Balance Transfer Amount", "M109", "BalanceTransferVolume", "Dynamic", "Mandatory", "N12.2"),
            (67, "Convenience Check amount", "M110", "ConvenienceCheckAmount", "Dynamic", "Mandatory", "N12.2"),
            (68, "Account Sold Flag", "M111", "AccountSoldFlag", "Dynamic", "Mandatory", "N1"),
            (69, "Bankruptcy Flag", "M112", "BankruptcyFlag", "Dynamic", "Mandatory", "N1"),
            (70, "Loss sharing", "M113", "LossShare", "Dynamic", "Mandatory", "N1"),
            (71, "Probability of Default - PD", "M114", "Basel2PD", "Dynamic", "Optional", "N6.5"),
            (72, "Loss Given Default - LGD", "M115", "Basel2LGD", "Dynamic", "Optional", "N6.5"),
            (73, "Expected Loss Given Default - ELGD", "M116", "Basel2ELGD", "Dynamic", "Optional", "N6.5"),
            (74, "Exposure at Default - EAD", "M117", "Basel2EAD", "Dynamic", "Optional", "N12.2"),
            (75, "EAD id segment", "M118", "Basel2EADid", "Dynamic", "Optional", "N7"),
            (76, "Corporate ID", "N031", "CorporateID", "Static", "Mandatory", "C18"),
            (77, "Variable Rate Index", "N032", "InterestRateIndex", "Dynamic", "Mandatory", "N2"),
            (78, "Variable Rate Margin", "6271", "InterestRateMargin", "Dynamic", "Mandatory", "N6.3"),
            (79, "Maximum APR", "N033", "MaxAPR", "Dynamic", "Mandatory", "N6.3"),
            (80, "Rate Reset Frequency", "N034", "RateResetFreq", "Dynamic", "Mandatory", "N1"),
            (81, "Promotional APR", "N035", "PromotionalAPR", "Dynamic", "Mandatory", "N6.3"),
            (82, "Cash APR", "N036", "CashAPR", "Dynamic", "Mandatory", "N6.3"),
            (83, "Loss Share ID", "N037", "LossShareId", "Dynamic", "Mandatory", "C7"),
            (84, "Loss Share Rate", "N038", "LossShareRate", "Dynamic", "Mandatory", "N7.5"),
            (85, "Other Credits", "N039", "OtherCredits", "Dynamic", "Mandatory", "N12.2"),
            (86, "Cycles Past Due at Cycle Date", "N129", "AccountCycleEndDelinquency", "Dynamic", "Mandatory", "N2"),
            (87, "Cycles Past Due at Month-End", "N130", "AccountMonthEndDelinquency", "Dynamic", "Mandatory", "N2"),
            (88, "Finance Charge", "N131", "FinanceCharge", "Dynamic", "Mandatory", "N12.2"),
            (89, "Fees Incurred - Late", "N132", "FeeNetLateAmount", "Dynamic", "Mandatory", "N12.2"),
            (90, "Fees Incurred - Over Limit", "N133", "FeeNetOverLimitAmount", "Dynamic", "Mandatory", "N12.2"),
            (91, "Fees Incurred - NSF", "N134", "FeeNetNSFAmount", "Dynamic", "Mandatory", "N12.2"),
            (92, "Fees Incurred - Cash Advance", "N135", "FeeNetCashAdvanceAmount", "Dynamic", "Mandatory", "N12.2"),
            (93, "Fees Incurred – Monthly/Annual", "N136", "FeeNetMonthlyAnnualAmount", "Dynamic", "Mandatory", "N12.2"),
            (94, "Fees Incurred - Debt Suspension", "N137", "FeeNetDebtSuspensionAmount", "Dynamic", "Mandatory", "N12.2"),
            (95, "Fees Incurred – Balance Transfer", "N138", "FeeNetBalanceTransferAmount", "Dynamic", "Mandatory", "N12.2"),
            (96, "Fees Incurred - Other", "N139", "FeeNetOtherAmount", "Dynamic", "Mandatory", "N12.2"),
            (97, "Debt Suspension/Cancellation Program Enrollment", "N140", "DebtWaiverProgramEnrolFlag", "Dynamic", "Mandatory", "N1"),
            (98, "Debt Suspension/Cancellation Program Active", "N141", "DebtWaiverProgramActiveFlag", "Dynamic", "Mandatory", "N1"),
            (99, "Cycle-end Account Status - Active", "N142", "CycleEndActiveFlag", "Dynamic", "Mandatory", "N1"),
            (100, "Cycle-end Account Status - Closed", "N143", "CycleEndClosedRevokedFlag", "Dynamic", "Mandatory", "N1"),
            (101, "Skip-a-payment", "N144", "SkipaPaymentFlag", "Dynamic", "Mandatory", "N1"),
            (102, "Credit Card Workout Program", "N145", "WorkoutProgramFlag", "Dynamic", "Mandatory", "N1"),
            (103, "Workout Program Type", "N146", "WorkoutProgramType", "Dynamic", "Mandatory", "N1"),
            (104, "Workout Program Performance Status", "N147", "WorkOutProgramPerformanceStatus", "Dynamic", "Mandatory", "N1"),
            (105, "Settlement Portion Forgiven", "N148", "SettlementPortionForgivenAmount", "Dynamic", "Mandatory", "N12.2"),
            (106, "Customer Service Re-age Date", "N149", "CustomerServiceReageDate", "Dynamic", "Mandatory", "Date YYYYMMDD"),
            (107, "Principal Charge-off Amount – Current Month", "N150", "PrincipalChargeOffInCurrentMonthAmount", "Dynamic", "Mandatory", "N12.2"),
            (108, "Fraud in the current month", "N151", "FraudFlag", "Dynamic", "Mandatory", "N1"),
            (109, "Original Credit Bureau Score Name", "N152", "OriginalCreditScoreName", "Dynamic", "Mandatory", "N2"),
            (110, "Refreshed Credit Bureau Score Name", "N153", "RefreshedCreditScoreName", "Dynamic", "Mandatory", "N2"),
            (111, "Behavioral Score Name/Version", "N154", "BehavioralScoreNameVersion", "Static", "Optional", "C30"),
            (112, "Credit Limit Type", "N155", "CreditLimitType", "Dynamic", "Mandatory", "N1"),
            (113, "Credit Line Change Type", "N156", "CreditLineChangeType", "Dynamic", "Mandatory", "N1"),
            (114, "Date Co-Borrower Was Added", "N157", "CoBorrowerAddDate", "Dynamic", "Optional", "Date YYYYMMDD"),
            (115, "Entity Type", "M952", "EntityType", "Dynamic", "Mandatory", "N1"),
            (116, "Origination Credit Bureau Score Version", "R037", "OriginalCreditScoreVersion", "Dynamic", "Mandatory", "C30"),
            (117, "Refreshed Credit Bureau Score Version", "R039", "RefreshedCreditScoreVersion", "Dynamic", "Mandatory", "C30"),
            (118, "Internal Origination Credit Score Flag", "R040", "InternalOrigScoreFlag", "Dynamic", "Mandatory", "N1"),
            (119, "Internal Origination Credit Score Value", "R041", "InternalOrigScoreValue", "Dynamic", "Mandatory", "N6.3"),
            (120, "Internal Refreshed Credit Score Flag", "R042", "InternalRefrScoreFlag", "Dynamic", "Mandatory", "N1"),
            (121, "Internal Refreshed Credit Score Value", "R043", "InternalRefrScoreValue", "Dynamic", "Mandatory", "N6.3"),
            (122, "Month-Ending Balance", "JA25", "MonthEndingBalance", "Dynamic", "Mandatory", "N12.2"),
            (123, "National Bank RSSD ID", "JA26", "NationalBankRSSDID", "Dynamic", "Mandatory", "N10")
        ]
        
        # Schedule D.2 - Portfolio Level Table
        schedule_d2_elements = [
            (1, "Bank Id", "9001", "BankId", "Static", "Mandatory", "C18"),
            (2, "Period Id", "9999", "PeriodId", "Dynamic", "Mandatory", "Date YYYYMMDD"),
            (3, "Credit Card Type", "M050", "CreditCardType", "Dynamic", "Mandatory", "N1"),
            (4, "Lending Type", "M052", "LendingType", "Dynamic", "Mandatory", "N1"),
            (5, "End of Month Managed Receivables", "M119", "MonthEndManagedReceivables", "Dynamic", "Mandatory", "N12.4"),
            (6, "End of Month Book Receivables", "M120", "MonthEndBookReceivables", "Dynamic", "Mandatory", "N12.4"),
            (7, "Number of Accounts", "M121", "NumberAccount", "Dynamic", "Mandatory", "N12.4"),
            (8, "Total Number of New Accounts", "M122", "NumberNewAccounts", "Dynamic", "Mandatory", "N12.4"),
            (9, "ACL Managed Balance", "M123", "ACLManagedBalance", "Dynamic", "Mandatory", "N12.4"),
            (10, "ACL Booked Balance", "M124", "ACLBookedBalance", "Dynamic", "Mandatory", "N12.4"),
            (11, "Projected Managed Losses", "M125", "ProjectedManagedLosses", "Dynamic", "Mandatory", "N12.4"),
            (12, "Projected Booked Losses", "M126", "ProjectedBankownedLosses", "Dynamic", "Mandatory", "N12.4"),
            (13, "Managed Gross Charge-offs for the current month", "M127", "ManagedGrossChargeOffs", "Dynamic", "Mandatory", "N12.4"),
            (14, "Booked Gross Charge-offs for the current month", "M128", "OnBalanceSheetGrossChargeOffs", "Dynamic", "Mandatory", "N12.4"),
            (15, "Managed Bankruptcy Charge-off Amount for Current Month", "M129", "ManagedBankruptcyChargeOffAmount", "Dynamic", "Mandatory", "N12.4"),
            (16, "Booked Bankruptcy Charge-off Amount for Current Month", "M130", "OnBookBankruptcyChargeOffAmount", "Dynamic", "Mandatory", "N12.4"),
            (17, "Managed Recoveries", "M131", "ManagedRecoveries", "Dynamic", "Mandatory", "N12.4"),
            (18, "Booked Recoveries", "M132", "BookedRecoveries", "Dynamic", "Mandatory", "N12.4"),
            (19, "Managed Principal Recovery Amount", "M133", "ManagedPrincipalRecoveryAmount", "Dynamic", "Mandatory", "N12.4"),
            (20, "Managed Interest and Fees Recovery Amount", "M134", "ManagedInterestRecoveryAmount", "Dynamic", "Mandatory", "N12.4"),
            (21, "Booked Principal Recovery Amount", "M135", "BookedPrincipalRecoveryAmount", "Dynamic", "Mandatory", "N12.4"),
            (22, "Booked Interest and Fees Recovery Amount", "M136", "BookedInterestRecoveryAmount", "Dynamic", "Mandatory", "N12.4"),
            (23, "Interest and Fees Charge-off/Reversal Amount", "M137", "InterestAndFeeChargeOffAmount", "Dynamic", "Mandatory", "N12.4"),
            (24, "Loan Loss Provision Expense", "M138", "LoanLossProvisionExpense", "Dynamic", "Mandatory", "N12.4"),
            (25, "Loan Loss Provision Taken", "M139", "ProvisionExpenseTaken", "Dynamic", "Mandatory", "N12.4"),
            (26, "Loan Loss Provision Build", "M140", "ProvisionExpenseBuild", "Dynamic", "Mandatory", "N12.4"),
            (27, "Extraordinary Items", "M141", "ExtraOrdinaryItems", "Dynamic", "Mandatory", "N12.4"),
            (28, "Interest Expense", "N158", "InterestExpense", "Dynamic", "Mandatory", "N12.4"),
            (29, "Total Non-Interest Expense", "N159", "TotalNonInterestExpense", "Dynamic", "Mandatory", "N12.4"),
            (30, "Total Non-Interest Expense - Interchange Expense", "N160", "InterchangeExpense", "Dynamic", "Mandatory", "N12.4"),
            (31, "Total Non-Interest Expense - Rewards/Rebates Expense", "N161", "RewardsExpense", "Dynamic", "Mandatory", "N12.4"),
            (32, "Total Non-Interest Expense - Collections Expense", "N162", "CollectionsExpense", "Dynamic", "Mandatory", "N12.4"),
            (33, "Total Non-Interest Expense - Fraud Expense", "N163", "FraudExpense", "Dynamic", "Mandatory", "N12.4"),
            (34, "Total Non-Interest Expense - All Other Expenses", "N164", "OtherNonInterestExpense", "Dynamic", "Mandatory", "N12.4"),
            (35, "Interest Income", "N165", "InterestIncome", "Dynamic", "Mandatory", "N12.4"),
            (36, "Fee Income", "N166", "TotalFeeIncome", "Dynamic", "Mandatory", "N12.4"),
            (37, "Fee Income - Late Fee Income", "N167", "LateFeeIncome", "Dynamic", "Mandatory", "N12.4"),
            (38, "Fee Income - Over Limit Fee Income", "N168", "OverLimitFeeIncome", "Dynamic", "Mandatory", "N12.4"),
            (39, "Fee Income - Balance Transfer Fee", "N169", "BalanceTransferFeeIncome", "Dynamic", "Mandatory", "N12.4"),
            (40, "Fee Income - Convenience Check Fee", "N170", "ConvenienceCheckFeeIncome", "Dynamic", "Mandatory", "N12.4"),
            (41, "Fee Income - Cash Advance Fee", "N171", "CashAdvanceFeeIncome", "Dynamic", "Mandatory", "N12.4"),
            (42, "Fee Income - NSF Fee", "N172", "NSFFeeIncome", "Dynamic", "Mandatory", "N12.4"),
            (43, "Fee Income - Other Fee Income", "N173", "OtherFeeIncome", "Dynamic", "Mandatory", "N12.4"),
            (44, "Interchange Income", "N174", "InterchangeIncome", "Dynamic", "Mandatory", "N12.4"),
            (45, "All Other Non-Interest Income", "N175", "OtherNonInterestIncome", "Dynamic", "Mandatory", "N12.4"),
            (46, "Taxes", "N176", "Taxes", "Dynamic", "Mandatory", "N12.4")
        ]
        
        # Process D.1 elements
        for item in schedule_d1_elements:
            element = {
                'Report Name': 'FR Y-14M',
                'Schedule Name': 'Schedule D.1 - Domestic Credit Card (Loan Level)',
                'Line Item #': item[0],
                'Line Item Name': item[1],
                'Technical Line Item Name': item[3],
                'MDRM': item[2],
                'Description': item[3],
                'Static or Dynamic': item[4],
                'Mandatory or Optional': item[5],
                'Format': item[6],
                '# of reports or schedules used in': 1,
                'Other Schedule Reference': ''
            }
            elements.append(element)
            
        # Process D.2 elements
        for item in schedule_d2_elements:
            element = {
                'Report Name': 'FR Y-14M',
                'Schedule Name': 'Schedule D.2 - Domestic Credit Card (Portfolio Level)',
                'Line Item #': item[0],
                'Line Item Name': item[1],
                'Technical Line Item Name': item[3],
                'MDRM': item[2],
                'Description': item[3],
                'Static or Dynamic': item[4],
                'Mandatory or Optional': item[5],
                'Format': item[6],
                '# of reports or schedules used in': 1,
                'Other Schedule Reference': ''
            }
            elements.append(element)
            
        return elements
    
    def create_master_dictionary(self) -> List[Dict]:
        """Create the complete master data dictionary"""
        all_elements = []
        
        # Parse all schedules
        all_elements.extend(self.parse_schedule_a(""))
        all_elements.extend(self.parse_schedule_b(""))
        all_elements.extend(self.parse_schedule_c(""))
        all_elements.extend(self.parse_schedule_d(""))
        
        return all_elements
    
    def export_to_csv(self, filename: str = "FR_Y14M_Master_Data_Dictionary.csv"):
        """Export the master dictionary to CSV"""
        all_elements = self.create_master_dictionary()
        
        if all_elements:
            fieldnames = all_elements[0].keys()
            
            with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(all_elements)
            
            print(f"Exported {len(all_elements)} data elements to {filename}")
        else:
            print("No data elements to export")
    
    def get_summary_stats(self) -> Dict:
        """Get summary statistics of the data dictionary"""
        all_elements = self.create_master_dictionary()
        
        schedule_counts = defaultdict(int)
        total_count = len(all_elements)
        
        for element in all_elements:
            schedule_counts[element['Schedule Name']] += 1
        
        return {
            'total_elements': total_count,
            'schedule_breakdown': dict(schedule_counts)
        }


if __name__ == "__main__":
    # Create extractor and generate master dictionary
    extractor = FRY14MDictionaryExtractor()
    
    # Get summary statistics
    stats = extractor.get_summary_stats()
    print("FR Y-14M Data Dictionary Summary:")
    print(f"Total Elements: {stats['total_elements']}")
    print("\nSchedule Breakdown:")
    for schedule, count in stats['schedule_breakdown'].items():
        print(f"  {schedule}: {count} elements")
    
    # Export to CSV
    extractor.export_to_csv()
    
    # Show first few elements as sample
    all_elements = extractor.create_master_dictionary()
    print(f"\nFirst 5 elements:")
    for i, element in enumerate(all_elements[:5]):
        print(f"{i+1}. {element['Schedule Name']} - {element['Line Item Name']} ({element['MDRM']})")