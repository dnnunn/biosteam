#!/usr/bin/env python3
"""
Comprehensive Excel Parameter Extraction Script
Systematically extracts ALL parameters from Excel model for BioSTEAM migration
"""

import pandas as pd
import numpy as np
import json
import os
from collections import defaultdict, OrderedDict
import warnings
warnings.filterwarnings('ignore')

class ComprehensiveExcelExtractor:
    def __init__(self, excel_path):
        self.excel_path = excel_path
        self.workbook = pd.ExcelFile(excel_path)
        self.parameter_database = []
        self.cost_breakdown = {}
        self.module_mapping = defaultdict(list)
        self.critical_costs = []
        self.questions = []

    def extract_all_parameters(self):
        """Extract parameters from all worksheets systematically"""
        print("=" * 80)
        print("COMPREHENSIVE EXCEL PARAMETER EXTRACTION")
        print("=" * 80)
        print(f"Excel file: {self.excel_path}")
        print(f"Available worksheets: {self.workbook.sheet_names}")
        print()

        # Process each worksheet
        for sheet_name in self.workbook.sheet_names:
            print(f"Processing worksheet: {sheet_name}")
            try:
                self.extract_sheet_parameters(sheet_name)
            except Exception as e:
                print(f"Error processing {sheet_name}: {str(e)}")
                self.questions.append({
                    'worksheet': sheet_name,
                    'issue': f'Error reading worksheet: {str(e)}',
                    'action_needed': 'Manual inspection required'
                })
            print()

    def extract_sheet_parameters(self, sheet_name):
        """Extract all parameters from a specific worksheet"""
        try:
            # Read with various options to handle different sheet formats
            df = pd.read_excel(self.excel_path, sheet_name=sheet_name, header=None)

            print(f"  Sheet dimensions: {df.shape[0]} rows x {df.shape[1]} columns")

            # Extract all non-empty cells
            for row_idx in range(df.shape[0]):
                for col_idx in range(df.shape[1]):
                    cell_value = df.iloc[row_idx, col_idx]

                    if pd.notna(cell_value) and str(cell_value).strip():
                        self.process_cell(sheet_name, row_idx, col_idx, cell_value, df)

            # Look for specific cost-related patterns
            self.extract_cost_patterns(sheet_name, df)

            # Look for module identifiers
            self.extract_module_patterns(sheet_name, df)

        except Exception as e:
            print(f"    Error reading sheet {sheet_name}: {str(e)}")
            raise

    def process_cell(self, sheet_name, row_idx, col_idx, cell_value, df):
        """Process individual cell and extract parameter information"""
        cell_str = str(cell_value).strip()

        # Skip if cell is empty or just whitespace
        if not cell_str:
            return

        # Try to get adjacent cells for context
        description = self.get_cell_description(df, row_idx, col_idx)
        units = self.get_cell_units(df, row_idx, col_idx)

        # Determine if this is a parameter
        is_parameter = self.is_parameter_cell(cell_str, description)

        if is_parameter:
            parameter_info = {
                'worksheet': sheet_name,
                'row': row_idx + 1,  # Excel row numbering
                'column': self.get_excel_column(col_idx),
                'cell_reference': f"{self.get_excel_column(col_idx)}{row_idx + 1}",
                'parameter_name': self.extract_parameter_name(cell_str, description),
                'value': cell_value,
                'raw_value': cell_str,
                'description': description,
                'units': units,
                'data_type': self.classify_data_type(cell_value),
                'is_formula': str(cell_value).startswith('=') if isinstance(cell_value, str) else False,
                'context': self.get_cell_context(df, row_idx, col_idx),
                'module': self.identify_module(sheet_name, description, cell_str),
                'cost_category': self.identify_cost_category(description, cell_str)
            }

            self.parameter_database.append(parameter_info)

    def get_cell_description(self, df, row_idx, col_idx):
        """Get description from adjacent cells"""
        descriptions = []

        # Check left cell (common for parameter descriptions)
        if col_idx > 0:
            left_cell = df.iloc[row_idx, col_idx - 1]
            if pd.notna(left_cell):
                descriptions.append(f"Left: {str(left_cell).strip()}")

        # Check above cell
        if row_idx > 0:
            above_cell = df.iloc[row_idx - 1, col_idx]
            if pd.notna(above_cell):
                descriptions.append(f"Above: {str(above_cell).strip()}")

        # Check right cell
        if col_idx < df.shape[1] - 1:
            right_cell = df.iloc[row_idx, col_idx + 1]
            if pd.notna(right_cell):
                descriptions.append(f"Right: {str(right_cell).strip()}")

        return " | ".join(descriptions) if descriptions else ""

    def get_cell_units(self, df, row_idx, col_idx):
        """Extract units from adjacent cells or cell content"""
        # Common unit patterns
        unit_patterns = ['kg', 'L', 'g', 'm3', 'hr', 'min', 'days', '$', '$/kg', '$/L',
                        '$/hr', '$/batch', '%', 'mg/L', 'g/L', 'cycles', 'CV']

        # Check cell content for units
        cell_str = str(df.iloc[row_idx, col_idx]).strip()
        for pattern in unit_patterns:
            if pattern in cell_str:
                return pattern

        # Check adjacent cells
        for r_offset in [-1, 0, 1]:
            for c_offset in [-1, 1]:
                try:
                    adj_row = row_idx + r_offset
                    adj_col = col_idx + c_offset
                    if 0 <= adj_row < df.shape[0] and 0 <= adj_col < df.shape[1]:
                        adj_cell = str(df.iloc[adj_row, adj_col]).strip()
                        for pattern in unit_patterns:
                            if pattern in adj_cell:
                                return pattern
                except:
                    continue

        return ""

    def is_parameter_cell(self, cell_str, description):
        """Determine if a cell contains a parameter value"""
        # Numeric values are likely parameters
        try:
            float(cell_str.replace('$', '').replace(',', '').replace('%', ''))
            return True
        except:
            pass

        # Formulas are parameters
        if cell_str.startswith('='):
            return True

        # Text that looks like parameter names
        parameter_keywords = ['cost', 'price', 'rate', 'efficiency', 'yield', 'titer',
                             'concentration', 'volume', 'time', 'cycles', 'resin', 'buffer']

        cell_lower = cell_str.lower()
        desc_lower = description.lower()

        for keyword in parameter_keywords:
            if keyword in cell_lower or keyword in desc_lower:
                return True

        return False

    def extract_parameter_name(self, cell_str, description):
        """Extract meaningful parameter name"""
        # If description contains parameter name, use it
        if description and any(keyword in description.lower() for keyword in
                              ['cost', 'price', 'rate', 'efficiency', 'yield']):
            return description.split(':')[0].split('|')[0].strip()

        # Otherwise use cell content if it's text
        try:
            float(cell_str.replace('$', '').replace(',', '').replace('%', ''))
            return f"Numeric_Value_{cell_str}"
        except:
            return cell_str.strip()

    def classify_data_type(self, value):
        """Classify the data type of the parameter"""
        if isinstance(value, (int, float, np.number)):
            return 'numeric'

        str_val = str(value).strip()

        # Try to parse as number
        try:
            float(str_val.replace('$', '').replace(',', '').replace('%', ''))
            return 'numeric'
        except:
            pass

        if str_val.startswith('='):
            return 'formula'

        if str_val.lower() in ['yes', 'no', 'true', 'false']:
            return 'boolean'

        return 'text'

    def get_cell_context(self, df, row_idx, col_idx):
        """Get broader context around the cell"""
        context = {}

        # Get row header (leftmost non-empty cell in row)
        for c in range(col_idx):
            cell = df.iloc[row_idx, c]
            if pd.notna(cell) and str(cell).strip():
                context['row_header'] = str(cell).strip()
                break

        # Get column header (topmost non-empty cell in column)
        for r in range(row_idx):
            cell = df.iloc[r, col_idx]
            if pd.notna(cell) and str(cell).strip():
                context['column_header'] = str(cell).strip()
                break

        return context

    def identify_module(self, sheet_name, description, cell_str):
        """Identify which process module this parameter belongs to"""
        module_keywords = {
            'USP01': ['fermentation', 'upstream', 'bioreactor', 'seed', 'inoculum'],
            'DSP02': ['downstream', 'purification', 'chromatography', 'resin', 'buffer'],
            'DSP03': ['concentration', 'ultrafiltration', 'diafiltration', 'membrane'],
            'DSP04': ['formulation', 'final', 'packaging', 'storage'],
            'CMO': ['cmo', 'campaign', 'reservation', 'validation', 'facility'],
            'UTILITIES': ['utility', 'steam', 'cooling', 'electricity', 'water'],
            'CAPEX': ['equipment', 'installation', 'capital', 'depreciation'],
            'OPEX': ['operating', 'labor', 'maintenance', 'consumable']
        }

        text_to_check = f"{sheet_name} {description} {cell_str}".lower()

        for module, keywords in module_keywords.items():
            if any(keyword in text_to_check for keyword in keywords):
                return module

        return 'UNKNOWN'

    def identify_cost_category(self, description, cell_str):
        """Identify the cost category for this parameter"""
        cost_categories = {
            'RAW_MATERIALS': ['media', 'substrate', 'glucose', 'buffer', 'salt'],
            'CONSUMABLES': ['resin', 'membrane', 'filter', 'consumable'],
            'UTILITIES': ['steam', 'cooling', 'electricity', 'water', 'utility'],
            'LABOR': ['labor', 'operator', 'technician', 'staff'],
            'FACILITY': ['facility', 'rental', 'cmo', 'reservation'],
            'EQUIPMENT': ['equipment', 'depreciation', 'amortization'],
            'OTHER': ['other', 'miscellaneous', 'overhead']
        }

        text_to_check = f"{description} {cell_str}".lower()

        for category, keywords in cost_categories.items():
            if any(keyword in text_to_check for keyword in keywords):
                return category

        return 'UNCLASSIFIED'

    def extract_cost_patterns(self, sheet_name, df):
        """Look for specific cost calculation patterns"""
        # Look for total cost calculations
        for row_idx in range(df.shape[0]):
            for col_idx in range(df.shape[1]):
                cell_value = df.iloc[row_idx, col_idx]
                if pd.notna(cell_value):
                    cell_str = str(cell_value).lower()
                    if 'total' in cell_str and ('cost' in cell_str or '$' in str(cell_value)):
                        self.extract_cost_breakdown(df, row_idx, col_idx, sheet_name)

    def extract_cost_breakdown(self, df, row_idx, col_idx, sheet_name):
        """Extract cost breakdown from around a total cost cell"""
        cost_info = {
            'worksheet': sheet_name,
            'location': f"Row {row_idx + 1}, Col {self.get_excel_column(col_idx)}",
            'components': []
        }

        # Look for cost components in surrounding area
        for r_offset in range(-10, 11):
            for c_offset in range(-3, 4):
                try:
                    r = row_idx + r_offset
                    c = col_idx + c_offset
                    if 0 <= r < df.shape[0] and 0 <= c < df.shape[1]:
                        cell = df.iloc[r, c]
                        if pd.notna(cell) and ('$' in str(cell) or
                                             isinstance(cell, (int, float, np.number))):
                            cost_info['components'].append({
                                'value': cell,
                                'location': f"{self.get_excel_column(c)}{r + 1}",
                                'context': self.get_cell_description(df, r, c)
                            })
                except:
                    continue

        self.cost_breakdown[f"{sheet_name}_{row_idx}_{col_idx}"] = cost_info

    def extract_module_patterns(self, sheet_name, df):
        """Look for module identifiers and technology selections"""
        module_patterns = ['USP01', 'DSP02', 'DSP03', 'DSP04', 'AEX', 'CEX', 'HIC']

        for row_idx in range(df.shape[0]):
            for col_idx in range(df.shape[1]):
                cell_value = df.iloc[row_idx, col_idx]
                if pd.notna(cell_value):
                    cell_str = str(cell_value).strip()
                    for pattern in module_patterns:
                        if pattern in cell_str:
                            self.module_mapping[pattern].append({
                                'worksheet': sheet_name,
                                'location': f"{self.get_excel_column(col_idx)}{row_idx + 1}",
                                'context': self.get_cell_description(df, row_idx, col_idx),
                                'full_content': cell_str
                            })

    def get_excel_column(self, col_idx):
        """Convert column index to Excel column letter"""
        result = ""
        while col_idx >= 0:
            result = chr(65 + (col_idx % 26)) + result
            col_idx = col_idx // 26 - 1
        return result

    def analyze_critical_costs(self):
        """Identify critical cost drivers"""
        print("ANALYZING CRITICAL COST DRIVERS")
        print("=" * 50)

        # Group parameters by cost impact
        cost_parameters = [p for p in self.parameter_database
                          if p['data_type'] == 'numeric' and
                          ('cost' in p['description'].lower() or
                           '$' in str(p['value']))]

        # Sort by magnitude
        numeric_costs = []
        for param in cost_parameters:
            try:
                value = float(str(param['value']).replace('$', '').replace(',', ''))
                numeric_costs.append((abs(value), param))
            except:
                continue

        numeric_costs.sort(key=lambda x: x[0], reverse=True)
        self.critical_costs = [param for _, param in numeric_costs[:20]]

        print(f"Found {len(cost_parameters)} cost-related parameters")
        print(f"Top 20 by magnitude identified")

    def validate_cost_structure(self):
        """Validate that parameters sum to expected total cost"""
        print("VALIDATING COST STRUCTURE")
        print("=" * 50)

        target_cost = 1264.34  # $/kg as stated

        # Look for total cost cells
        total_costs = []
        for param in self.parameter_database:
            if 'total' in param['description'].lower() and 'cost' in param['description'].lower():
                try:
                    value = float(str(param['value']).replace('$', '').replace(',', ''))
                    total_costs.append((value, param))
                except:
                    continue

        print(f"Found {len(total_costs)} total cost entries")
        for value, param in total_costs:
            print(f"  {value:.2f} at {param['worksheet']}!{param['cell_reference']}")
            if abs(value - target_cost) < 10:  # Within $10/kg
                print(f"    *** MATCHES TARGET: {target_cost} $/kg ***")

    def generate_report(self):
        """Generate comprehensive analysis report"""
        print("\n" + "=" * 80)
        print("COMPREHENSIVE PARAMETER EXTRACTION REPORT")
        print("=" * 80)

        # Summary statistics
        print(f"\nSUMMARY STATISTICS:")
        print(f"Total parameters extracted: {len(self.parameter_database)}")
        print(f"Worksheets processed: {len(self.workbook.sheet_names)}")
        print(f"Cost breakdown sections found: {len(self.cost_breakdown)}")
        print(f"Module mappings identified: {len(self.module_mapping)}")
        print(f"Questions/issues raised: {len(self.questions)}")

        # Parameter distribution by worksheet
        worksheet_counts = defaultdict(int)
        for param in self.parameter_database:
            worksheet_counts[param['worksheet']] += 1

        print(f"\nPARAMETERS BY WORKSHEET:")
        for worksheet, count in sorted(worksheet_counts.items()):
            print(f"  {worksheet}: {count} parameters")

        # Module distribution
        module_counts = defaultdict(int)
        for param in self.parameter_database:
            module_counts[param['module']] += 1

        print(f"\nPARAMETERS BY MODULE:")
        for module, count in sorted(module_counts.items()):
            print(f"  {module}: {count} parameters")

        # Cost category distribution
        cost_counts = defaultdict(int)
        for param in self.parameter_database:
            cost_counts[param['cost_category']] += 1

        print(f"\nPARAMETERS BY COST CATEGORY:")
        for category, count in sorted(cost_counts.items()):
            print(f"  {category}: {count} parameters")

    def export_results(self, output_dir):
        """Export all results to files"""
        os.makedirs(output_dir, exist_ok=True)

        # Export parameter database
        database_file = os.path.join(output_dir, 'complete_parameter_database.json')
        with open(database_file, 'w') as f:
            json.dump(self.parameter_database, f, indent=2, default=str)

        # Export cost breakdown
        cost_file = os.path.join(output_dir, 'cost_breakdown_analysis.json')
        with open(cost_file, 'w') as f:
            json.dump(self.cost_breakdown, f, indent=2, default=str)

        # Export module mapping
        module_file = os.path.join(output_dir, 'module_parameter_mapping.json')
        with open(module_file, 'w') as f:
            json.dump(dict(self.module_mapping), f, indent=2, default=str)

        # Export critical costs
        critical_file = os.path.join(output_dir, 'critical_cost_drivers.json')
        with open(critical_file, 'w') as f:
            json.dump(self.critical_costs, f, indent=2, default=str)

        # Export questions
        questions_file = os.path.join(output_dir, 'extraction_questions.json')
        with open(questions_file, 'w') as f:
            json.dump(self.questions, f, indent=2, default=str)

        # Export summary report
        summary_file = os.path.join(output_dir, 'extraction_summary_report.txt')
        with open(summary_file, 'w') as f:
            # Redirect print output to file
            import sys
            original_stdout = sys.stdout
            sys.stdout = f
            self.generate_report()
            sys.stdout = original_stdout

        print(f"\nResults exported to: {output_dir}")
        print(f"Files created:")
        print(f"  - complete_parameter_database.json")
        print(f"  - cost_breakdown_analysis.json")
        print(f"  - module_parameter_mapping.json")
        print(f"  - critical_cost_drivers.json")
        print(f"  - extraction_questions.json")
        print(f"  - extraction_summary_report.txt")

def main():
    excel_path = "/Users/davidnunn/Desktop/Apps/BetterDairy/TEAM/Revised Model_15052025v44.xlsx"
    output_dir = "/Users/davidnunn/Desktop/Apps/BetterDairy/Biosteam/excel_extraction_results"

    print("Starting comprehensive Excel parameter extraction...")

    extractor = ComprehensiveExcelExtractor(excel_path)

    # Main extraction process
    extractor.extract_all_parameters()

    # Analysis
    extractor.analyze_critical_costs()
    extractor.validate_cost_structure()

    # Generate report
    extractor.generate_report()

    # Export results
    extractor.export_results(output_dir)

    print("\nExtraction complete!")

if __name__ == "__main__":
    main()