#!/usr/bin/env python3
"""Test aggregated accounting parser"""

from core.saft_accounting_aggregator_v2 import aggregate_accounting_data
import json

if __name__ == '__main__':
    xml_file = r'tests\saft_contabilidae_01012024_31122024.xml'

    print(f"Aggregating {xml_file}...")
    print("(This may take a minute for large files...)\n")

    result = aggregate_accounting_data(xml_file)

    if not result.get('ok'):
        print(f"ERROR: {result.get('error')}")
        exit(1)

    print(f"Aggregation complete!\n")
    print(f"Summary:")
    print(f"  - Company: {result['header'].get('CompanyName')}")
    print(f"  - Fiscal Year: {result['header'].get('FiscalYear')}")
    print(f"  - Total Accounts with movement: {result['summary']['TotalAccounts']}")
    print(f"  - Total Journals: {result['summary']['TotalJournals']}")
    print(f"  - Total Transactions: {result['summary']['TotalTransactions']:,}")
    print(f"  - Total Entries (lines): {result['summary']['TotalEntries']:,}")
    print(f"  - Total Debit: € {result['summary']['TotalDebit']:,.2f}")
    print(f"  - Total Credit: € {result['summary']['TotalCredit']:,.2f}")

    print(f"\nTop 10 Accounts by Movement:")
    for i, acc in enumerate(result['accounts'][:10], 1):
        total_movement = acc['TotalDebit'] + acc['TotalCredit']
        print(f"  {i}. {acc['AccountID']} - {acc['Description'][:40]}")
        print(f"     Debito: EUR {acc['TotalDebit']:,.2f} | Credito: EUR {acc['TotalCredit']:,.2f}")
        print(f"     Total Movement: EUR {total_movement:,.2f} | Entries: {acc['MovementCount']}")
        print()

    print(f"\nJournals:")
    for j in result['journals'][:5]:
        print(f"  - {j['JournalID']}: {j['Description']}")
        print(f"    Debito: EUR {j['TotalDebit']:,.2f} | Credito: EUR {j['TotalCredit']:,.2f} | Entries: {j['Count']}")

    print(f"\nPeriods:")
    for p in result['periods']:
        print(f"  - Period {p['Period']}: {p['Count']} entries | D: EUR {p['Debit']:,.2f} | C: EUR {p['Credit']:,.2f}")

    # Show drill-down example
    if result['accounts']:
        first_acc = result['accounts'][0]
        print(f"\nDrill-down example for account {first_acc['AccountID']}:")
        print(f"  Has {len(first_acc['Periods'])} periods with movement")
        if first_acc['Periods']:
            print(f"  Period {first_acc['Periods'][0]['Period']}: {first_acc['Periods'][0]['Count']} entries")
