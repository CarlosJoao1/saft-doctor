"""
SAFT Accounting Aggregator
Processa ficheiros SAFT de contabilidade e cria visões agregadas para análise eficiente
"""
import xml.etree.ElementTree as ET
from typing import Dict, Any, List
from collections import defaultdict
from decimal import Decimal
import re


def aggregate_accounting_data(xml_path: str) -> Dict[str, Any]:
    """
    Parse SAFT accounting file and create aggregated views.

    Returns aggregated data by:
    - Account (with monthly breakdown)
    - Journal
    - Period

    This avoids loading 50k+ individual entries in memory/frontend.
    """

    # Clean XML file first (remove invalid characters)
    import tempfile
    import shutil
    import os

    cleaned_file = None
    try:
        # Create a temporary cleaned file
        with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', delete=False, suffix='.xml') as temp_file:
            cleaned_file = temp_file.name
            with open(xml_path, 'r', encoding='windows-1252', errors='replace') as source:
                for line in source:
                    # Remove control characters except newline/tab/carriage return
                    cleaned_line = ''.join(char for char in line if ord(char) >= 32 or char in '\n\r\t')
                    temp_file.write(cleaned_line)

        # Use iterparse for memory-efficient processing of large files
        context = ET.iterparse(cleaned_file, events=('start', 'end'))
        context = iter(context)

        # Get root and namespace
        event, root = next(context)
        ns = {'saft': 'urn:OECD:StandardAuditFile-Tax:PT_1.04_01'}

    # Data structures for aggregation
    accounts_map = {}  # AccountID -> {description, opening, closing}
    account_movements = defaultdict(lambda: {
        'total_debit': Decimal('0'),
        'total_credit': Decimal('0'),
        'count': 0,
        'by_period': defaultdict(lambda: {
            'debit': Decimal('0'),
            'credit': Decimal('0'),
            'count': 0,
            'transactions': []  # List of transaction IDs for drill-down
        }),
        'by_journal': defaultdict(lambda: {
            'debit': Decimal('0'),
            'credit': Decimal('0'),
            'count': 0
        })
    })

    journal_summary = defaultdict(lambda: {
        'description': '',
        'total_debit': Decimal('0'),
        'total_credit': Decimal('0'),
        'count': 0
    })

    period_summary = defaultdict(lambda: {
        'debit': Decimal('0'),
        'credit': Decimal('0'),
        'count': 0
    })

    header_data = {}
    total_transactions = 0
    total_entries = 0

    # Process XML incrementally
    try:
        for event, elem in context:
            if event != 'end':
                continue

            # Parse Header
            if elem.tag.endswith('Header') and not header_data:
                header_data = parse_header_elem(elem, ns)
                elem.clear()

            # Parse Accounts
            elif elem.tag.endswith('Account'):
                acc_id = get_text_elem(elem, 'saft:AccountID', ns)
                if acc_id:
                    accounts_map[acc_id] = {
                        'AccountID': acc_id,
                        'Description': get_text_elem(elem, 'saft:AccountDescription', ns),
                        'OpeningDebitBalance': get_decimal_elem(elem, 'saft:OpeningDebitBalance', ns),
                        'OpeningCreditBalance': get_decimal_elem(elem, 'saft:OpeningCreditBalance', ns),
                        'ClosingDebitBalance': get_decimal_elem(elem, 'saft:ClosingDebitBalance', ns),
                        'ClosingCreditBalance': get_decimal_elem(elem, 'saft:ClosingCreditBalance', ns),
                    }
                elem.clear()

            # Parse Journal
            elif elem.tag.endswith('Journal'):
                journal_id = get_text_elem(elem, 'saft:JournalID', ns)
                journal_desc = get_text_elem(elem, 'saft:Description', ns)

                if journal_id:
                    journal_summary[journal_id]['description'] = journal_desc

                # Process transactions within this journal
                for transaction in elem.findall('.//saft:Transaction', ns):
                    total_transactions += 1
                    trans_id = get_text_elem(transaction, 'saft:TransactionID', ns)
                    trans_date = get_text_elem(transaction, 'saft:TransactionDate', ns)
                    period = get_text_elem(transaction, 'saft:Period', ns) or '0'

                    lines = transaction.find('saft:Lines', ns)
                    if lines is None:
                        continue

                    # Process Debit Lines
                    for debit_line in lines.findall('saft:DebitLine', ns):
                        total_entries += 1
                        account_id = get_text_elem(debit_line, 'saft:AccountID', ns)
                        amount = get_decimal_elem(debit_line, 'saft:DebitAmount', ns)

                        if account_id and amount:
                            # Aggregate by account
                            account_movements[account_id]['total_debit'] += amount
                            account_movements[account_id]['count'] += 1

                            # Aggregate by period
                            account_movements[account_id]['by_period'][period]['debit'] += amount
                            account_movements[account_id]['by_period'][period]['count'] += 1
                            account_movements[account_id]['by_period'][period]['transactions'].append({
                                'TransactionID': trans_id,
                                'Date': trans_date,
                                'Type': 'Debit',
                                'Amount': float(amount)
                            })

                            # Aggregate by journal
                            account_movements[account_id]['by_journal'][journal_id]['debit'] += amount
                            account_movements[account_id]['by_journal'][journal_id]['count'] += 1

                            # Journal totals
                            journal_summary[journal_id]['total_debit'] += amount
                            journal_summary[journal_id]['count'] += 1

                            # Period totals
                            period_summary[period]['debit'] += amount
                            period_summary[period]['count'] += 1

                    # Process Credit Lines
                    for credit_line in lines.findall('saft:CreditLine', ns):
                        total_entries += 1
                        account_id = get_text_elem(credit_line, 'saft:AccountID', ns)
                        amount = get_decimal_elem(credit_line, 'saft:CreditAmount', ns)

                        if account_id and amount:
                            # Aggregate by account
                            account_movements[account_id]['total_credit'] += amount
                            account_movements[account_id]['count'] += 1

                            # Aggregate by period
                            account_movements[account_id]['by_period'][period]['credit'] += amount
                            account_movements[account_id]['by_period'][period]['count'] += 1
                            account_movements[account_id]['by_period'][period]['transactions'].append({
                                'TransactionID': trans_id,
                                'Date': trans_date,
                                'Type': 'Credit',
                                'Amount': float(amount)
                            })

                            # Aggregate by journal
                            account_movements[account_id]['by_journal'][journal_id]['credit'] += amount
                            account_movements[account_id]['by_journal'][journal_id]['count'] += 1

                            # Journal totals
                            journal_summary[journal_id]['total_credit'] += amount
                            journal_summary[journal_id]['count'] += 1

                            # Period totals
                            period_summary[period]['credit'] += amount
                            period_summary[period]['count'] += 1

                elem.clear()

    except ET.ParseError as e:
        return {
            'ok': False,
            'error': f'XML Parse Error: {str(e)}'
        }
    finally:
        # Clean up temporary file
        if cleaned_file:
            try:
                import os
                os.unlink(cleaned_file)
            except:
                pass

    # Convert aggregated data to JSON-serializable format
    accounts_list = []
    for acc_id, movement in account_movements.items():
        acc_info = accounts_map.get(acc_id, {})

        balance = (
            (movement['total_debit'] - movement['total_credit']) +
            (acc_info.get('OpeningDebitBalance', Decimal('0')) - acc_info.get('OpeningCreditBalance', Decimal('0')))
        )

        # Convert by_period dict to list
        periods = []
        for period, period_data in sorted(movement['by_period'].items()):
            period_balance = period_data['debit'] - period_data['credit']
            periods.append({
                'Period': period,
                'Debit': float(period_data['debit']),
                'Credit': float(period_data['credit']),
                'Balance': float(period_balance),
                'Count': period_data['count'],
                'Transactions': period_data['transactions'][:100]  # Limit to 100 per period
            })

        # Convert by_journal dict to list
        journals = []
        for j_id, j_data in movement['by_journal'].items():
            journals.append({
                'JournalID': j_id,
                'Debit': float(j_data['debit']),
                'Credit': float(j_data['credit']),
                'Count': j_data['count']
            })

        accounts_list.append({
            'AccountID': acc_id,
            'Description': acc_info.get('Description', ''),
            'TotalDebit': float(movement['total_debit']),
            'TotalCredit': float(movement['total_credit']),
            'Balance': float(balance),
            'MovementCount': movement['count'],
            'OpeningDebitBalance': float(acc_info.get('OpeningDebitBalance', Decimal('0'))),
            'OpeningCreditBalance': float(acc_info.get('OpeningCreditBalance', Decimal('0'))),
            'ClosingDebitBalance': float(acc_info.get('ClosingDebitBalance', Decimal('0'))),
            'ClosingCreditBalance': float(acc_info.get('ClosingCreditBalance', Decimal('0'))),
            'Periods': periods,
            'Journals': journals
        })

    # Sort accounts by total movement (debit + credit)
    accounts_list.sort(key=lambda x: x['TotalDebit'] + x['TotalCredit'], reverse=True)

    # Convert journal summary
    journals_list = [
        {
            'JournalID': j_id,
            'Description': data['description'],
            'TotalDebit': float(data['total_debit']),
            'TotalCredit': float(data['total_credit']),
            'Count': data['count']
        }
        for j_id, data in journal_summary.items()
    ]

    # Convert period summary
    periods_list = [
        {
            'Period': period,
            'Debit': float(data['debit']),
            'Credit': float(data['credit']),
            'Count': data['count']
        }
        for period, data in sorted(period_summary.items())
    ]

    return {
        'ok': True,
        'header': header_data,
        'accounts': accounts_list,
        'journals': journals_list,
        'periods': periods_list,
        'summary': {
            'TotalAccounts': len(accounts_list),
            'TotalJournals': len(journals_list),
            'TotalTransactions': total_transactions,
            'TotalEntries': total_entries,
            'TotalDebit': float(sum(d['debit'] for d in period_summary.values())),
            'TotalCredit': float(sum(d['credit'] for d in period_summary.values()))
        }
    }


def parse_header_elem(elem: ET.Element, ns: dict) -> Dict[str, str]:
    """Parse header element"""
    return {
        'CompanyName': get_text_elem(elem, 'saft:CompanyName', ns),
        'TaxRegistrationNumber': get_text_elem(elem, 'saft:TaxRegistrationNumber', ns),
        'FiscalYear': get_text_elem(elem, 'saft:FiscalYear', ns),
        'StartDate': get_text_elem(elem, 'saft:StartDate', ns),
        'EndDate': get_text_elem(elem, 'saft:EndDate', ns),
        'CurrencyCode': get_text_elem(elem, 'saft:CurrencyCode', ns),
    }


def get_text_elem(elem: ET.Element, path: str, ns: dict) -> str:
    """Get text from sub-element"""
    child = elem.find(path, ns)
    return child.text.strip() if child is not None and child.text else ''


def get_decimal_elem(elem: ET.Element, path: str, ns: dict) -> Decimal:
    """Get decimal from sub-element"""
    text = get_text_elem(elem, path, ns)
    if text:
        try:
            return Decimal(text)
        except:
            return Decimal('0')
    return Decimal('0')
