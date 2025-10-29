#!/usr/bin/env python3
"""Test script for accounting SAFT parser"""

from core.saft_accounting_parser import parse_accounting_saft
import json

if __name__ == '__main__':
    xml_file = r'tests\saft_contabilidae_01012024_31122024.xml'

    print(f"Parsing {xml_file}...")
    result = parse_accounting_saft(xml_file)

    print(f"\n✅ Parsed successfully!")
    print(f"\n📊 Summary:")
    print(f"  - Company: {result['header'].get('CompanyName')}")
    print(f"  - Fiscal Year: {result['header'].get('FiscalYear')}")
    print(f"  - Period: {result['header'].get('StartDate')} to {result['header'].get('EndDate')}")
    print(f"  - Total Accounts: {result['summary']['TotalAccounts']}")
    print(f"  - Total Entries: {result['summary']['TotalEntries']}")
    print(f"  - Total Debit: € {result['summary']['TotalDebit']:,.2f}")
    print(f"  - Total Credit: € {result['summary']['TotalCredit']:,.2f}")
    print(f"  - Journals: {result['summary']['TotalJournals']}")

    print(f"\n📝 First 3 entries:")
    for i, entry in enumerate(result['entries'][:3], 1):
        print(f"  {i}. {entry['TransactionDate']} | {entry['JournalID']} | {entry['AccountID']} | {entry['LineType']}: € {entry['DebitAmount'] + entry['CreditAmount']:.2f}")

    print(f"\n💾 Accounts sample (first 5):")
    for i, acc in enumerate(result['accounts'][:5], 1):
        print(f"  {i}. {acc['AccountID']} - {acc['AccountDescription']}")
