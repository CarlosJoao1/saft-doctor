"""
SAFT Accounting Parser
Extrai lançamentos contabilísticos de ficheiros SAFT-PT de contabilidade
"""
import xml.etree.ElementTree as ET
from typing import List, Dict, Any, Optional
from pathlib import Path


def parse_accounting_saft(xml_path: str) -> Dict[str, Any]:
    """
    Parse SAFT accounting file and extract general ledger entries.

    Args:
        xml_path: Path to the SAFT XML file

    Returns:
        Dictionary with parsed accounting data including:
        - header: Company and period information
        - accounts: Chart of accounts
        - entries: List of accounting entries (flattened from transactions)
        - summary: Statistics about the file
    """
    # Read and clean the XML file to handle invalid characters
    import re
    with open(xml_path, 'r', encoding='utf-8', errors='replace') as f:
        content = f.read()

    # Remove invalid XML characters
    content = re.sub(r'&#x([0-9a-fA-F]+);', lambda m: chr(int(m.group(1), 16)) if int(m.group(1), 16) >= 32 else '', content)

    # Parse cleaned content
    root = ET.fromstring(content)

    # Namespace
    ns = {'saft': 'urn:OECD:StandardAuditFile-Tax:PT_1.04_01'}

    # Parse Header
    header = parse_header(root, ns)

    # Parse Chart of Accounts
    accounts = parse_accounts(root, ns)

    # Parse General Ledger Entries
    entries = parse_general_ledger_entries(root, ns)

    # Calculate summary statistics
    summary = calculate_summary(entries, accounts)

    return {
        'ok': True,
        'header': header,
        'accounts': accounts,
        'entries': entries,
        'summary': summary
    }


def parse_header(root: ET.Element, ns: dict) -> Dict[str, Any]:
    """Extract header information"""
    header_elem = root.find('saft:Header', ns)
    if header_elem is None:
        return {}

    return {
        'CompanyName': get_text(header_elem, 'saft:CompanyName', ns),
        'TaxRegistrationNumber': get_text(header_elem, 'saft:TaxRegistrationNumber', ns),
        'FiscalYear': get_text(header_elem, 'saft:FiscalYear', ns),
        'StartDate': get_text(header_elem, 'saft:StartDate', ns),
        'EndDate': get_text(header_elem, 'saft:EndDate', ns),
        'CurrencyCode': get_text(header_elem, 'saft:CurrencyCode', ns),
        'DateCreated': get_text(header_elem, 'saft:DateCreated', ns),
    }


def parse_accounts(root: ET.Element, ns: dict) -> List[Dict[str, Any]]:
    """Extract chart of accounts"""
    accounts = []
    accounts_elem = root.find('.//saft:GeneralLedgerAccounts', ns)

    if accounts_elem is None:
        return accounts

    for account in accounts_elem.findall('saft:Account', ns):
        accounts.append({
            'AccountID': get_text(account, 'saft:AccountID', ns),
            'AccountDescription': get_text(account, 'saft:AccountDescription', ns),
            'OpeningDebitBalance': get_float(account, 'saft:OpeningDebitBalance', ns),
            'OpeningCreditBalance': get_float(account, 'saft:OpeningCreditBalance', ns),
            'ClosingDebitBalance': get_float(account, 'saft:ClosingDebitBalance', ns),
            'ClosingCreditBalance': get_float(account, 'saft:ClosingCreditBalance', ns),
            'GroupingCategory': get_text(account, 'saft:GroupingCategory', ns),
            'GroupingCode': get_text(account, 'saft:GroupingCode', ns),
            'TaxonomyCode': get_text(account, 'saft:TaxonomyCode', ns),
        })

    return accounts


def parse_general_ledger_entries(root: ET.Element, ns: dict) -> List[Dict[str, Any]]:
    """
    Extract all general ledger entries.
    Flattens transactions into individual lines (debit/credit) for table display.
    """
    entries = []
    gl_entries = root.find('.//saft:GeneralLedgerEntries', ns)

    if gl_entries is None:
        return entries

    entry_id = 0

    for journal in gl_entries.findall('saft:Journal', ns):
        journal_id = get_text(journal, 'saft:JournalID', ns)
        journal_desc = get_text(journal, 'saft:Description', ns)

        for transaction in journal.findall('saft:Transaction', ns):
            trans_id = get_text(transaction, 'saft:TransactionID', ns)
            trans_date = get_text(transaction, 'saft:TransactionDate', ns)
            period = get_text(transaction, 'saft:Period', ns)
            source_id = get_text(transaction, 'saft:SourceID', ns)
            trans_desc = get_text(transaction, 'saft:Description', ns)
            doc_arch_number = get_text(transaction, 'saft:DocArchivalNumber', ns)
            trans_type = get_text(transaction, 'saft:TransactionType', ns)
            gl_posting_date = get_text(transaction, 'saft:GLPostingDate', ns)

            lines_elem = transaction.find('saft:Lines', ns)
            if lines_elem is None:
                continue

            # Process Debit Lines
            for debit_line in lines_elem.findall('saft:DebitLine', ns):
                entry_id += 1
                entries.append({
                    'EntryID': entry_id,
                    'JournalID': journal_id,
                    'JournalDescription': journal_desc,
                    'TransactionID': trans_id,
                    'TransactionDate': trans_date,
                    'Period': period,
                    'SourceID': source_id,
                    'Description': get_text(debit_line, 'saft:Description', ns) or trans_desc,
                    'DocArchivalNumber': doc_arch_number,
                    'TransactionType': trans_type,
                    'GLPostingDate': gl_posting_date,
                    'RecordID': get_text(debit_line, 'saft:RecordID', ns),
                    'AccountID': get_text(debit_line, 'saft:AccountID', ns),
                    'SystemEntryDate': get_text(debit_line, 'saft:SystemEntryDate', ns),
                    'LineType': 'Debit',
                    'DebitAmount': get_float(debit_line, 'saft:DebitAmount', ns),
                    'CreditAmount': 0.0,
                })

            # Process Credit Lines
            for credit_line in lines_elem.findall('saft:CreditLine', ns):
                entry_id += 1
                entries.append({
                    'EntryID': entry_id,
                    'JournalID': journal_id,
                    'JournalDescription': journal_desc,
                    'TransactionID': trans_id,
                    'TransactionDate': trans_date,
                    'Period': period,
                    'SourceID': source_id,
                    'Description': get_text(credit_line, 'saft:Description', ns) or trans_desc,
                    'DocArchivalNumber': doc_arch_number,
                    'TransactionType': trans_type,
                    'GLPostingDate': gl_posting_date,
                    'RecordID': get_text(credit_line, 'saft:RecordID', ns),
                    'AccountID': get_text(credit_line, 'saft:AccountID', ns),
                    'SystemEntryDate': get_text(credit_line, 'saft:SystemEntryDate', ns),
                    'LineType': 'Credit',
                    'DebitAmount': 0.0,
                    'CreditAmount': get_float(credit_line, 'saft:CreditAmount', ns),
                })

    return entries


def calculate_summary(entries: List[Dict[str, Any]], accounts: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Calculate summary statistics"""
    total_debit = sum(e['DebitAmount'] for e in entries)
    total_credit = sum(e['CreditAmount'] for e in entries)

    journals = set(e['JournalID'] for e in entries)
    accounts_used = set(e['AccountID'] for e in entries)

    # Count by period
    by_period = {}
    for entry in entries:
        period = entry.get('Period', '0')
        by_period[period] = by_period.get(period, 0) + 1

    return {
        'TotalEntries': len(entries),
        'TotalDebit': total_debit,
        'TotalCredit': total_credit,
        'TotalJournals': len(journals),
        'TotalAccounts': len(accounts),
        'AccountsUsed': len(accounts_used),
        'EntriesByPeriod': by_period,
    }


def get_text(element: ET.Element, path: str, ns: dict) -> str:
    """Helper to get text from element"""
    child = element.find(path, ns)
    return child.text if child is not None and child.text else ''


def get_float(element: ET.Element, path: str, ns: dict) -> float:
    """Helper to get float from element"""
    child = element.find(path, ns)
    if child is not None and child.text:
        try:
            return float(child.text)
        except ValueError:
            return 0.0
    return 0.0
