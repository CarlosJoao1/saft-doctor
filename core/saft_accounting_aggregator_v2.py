"""
SAFT Accounting Aggregator V2
Versão corrigida e otimizada para processar ficheiros SAFT de contabilidade
"""
import xml.etree.ElementTree as ET
from typing import Dict, Any, List
from collections import defaultdict
from decimal import Decimal
import tempfile
import os


def aggregate_accounting_data(xml_path: str) -> Dict[str, Any]:
    """
    Parse SAFT accounting file and create aggregated views.
    Processa ficheiros grandes de forma eficiente com agregação hierárquica.
    """

    # Limpar XML primeiro (remover caracteres inválidos)
    cleaned_file = clean_xml_file(xml_path)

    try:
        return process_accounting_xml(cleaned_file)
    finally:
        # Limpar ficheiro temporário
        if cleaned_file and os.path.exists(cleaned_file):
            try:
                os.unlink(cleaned_file)
            except:
                pass


def clean_xml_file(xml_path: str) -> str:
    """Cria ficheiro temporário limpo sem caracteres inválidos"""
    import re
    import codecs

    with tempfile.NamedTemporaryFile(mode='wb', delete=False, suffix='.xml') as temp_file:
        temp_path = temp_file.name

        # Tentar vários encodings
        encodings_to_try = ['windows-1252', 'latin-1', 'iso-8859-1', 'utf-8']

        content = None
        for enc in encodings_to_try:
            try:
                with open(xml_path, 'r', encoding=enc, errors='ignore') as source:
                    content = source.read()
                    break
            except:
                continue

        if content is None:
            # Fallback: ler como bytes e decodificar
            with open(xml_path, 'rb') as source:
                content = source.read().decode('windows-1252', errors='ignore')

        # Remover caracteres de controlo inválidos em XML
        # Permitir apenas: tab (0x09), LF (0x0A), CR (0x0D), e >= 0x20
        content = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F]', '', content)

        # Remover entidades de caracteres inválidas
        content = re.sub(r'&#x([0-8BCEF]|1[0-9A-F]);', '', content, flags=re.IGNORECASE)

        # Escapar caracteres problemáticos em descrições
        # Substituir & não seguido de amp;, lt;, gt;, quot;, apos; por &amp;
        content = re.sub(r'&(?!(amp|lt|gt|quot|apos|#\d+|#x[\da-fA-F]+);)', '&amp;', content)

        temp_file.write(content.encode('utf-8'))

    return temp_path


def process_accounting_xml(xml_path: str) -> Dict[str, Any]:
    """Processa XML limpo e agrega dados"""

    # Namespace SAFT-PT
    ns = {'saft': 'urn:OECD:StandardAuditFile-Tax:PT_1.04_01'}

    # Estruturas para agregação
    accounts_map = {}
    account_movements = defaultdict(lambda: {
        'total_debit': Decimal('0'),
        'total_credit': Decimal('0'),
        'count': 0,
        'by_period': defaultdict(lambda: {
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

    # Processar XML com iterparse (eficiente para ficheiros grandes)
    try:
        for event, elem in ET.iterparse(xml_path, events=('end',)):

            # Header
            if elem.tag.endswith('Header') and not header_data:
                header_data = {
                    'CompanyName': get_text(elem, 'saft:CompanyName', ns),
                    'TaxRegistrationNumber': get_text(elem, 'saft:TaxRegistrationNumber', ns),
                    'FiscalYear': get_text(elem, 'saft:FiscalYear', ns),
                    'StartDate': get_text(elem, 'saft:StartDate', ns),
                    'EndDate': get_text(elem, 'saft:EndDate', ns),
                    'CurrencyCode': get_text(elem, 'saft:CurrencyCode', ns),
                }
                elem.clear()

            # Account
            elif elem.tag.endswith('Account'):
                acc_id = get_text(elem, 'saft:AccountID', ns)
                if acc_id:
                    accounts_map[acc_id] = {
                        'AccountID': acc_id,
                        'Description': get_text(elem, 'saft:AccountDescription', ns),
                        'OpeningDebitBalance': get_decimal(elem, 'saft:OpeningDebitBalance', ns),
                        'OpeningCreditBalance': get_decimal(elem, 'saft:OpeningCreditBalance', ns),
                        'ClosingDebitBalance': get_decimal(elem, 'saft:ClosingDebitBalance', ns),
                        'ClosingCreditBalance': get_decimal(elem, 'saft:ClosingCreditBalance', ns),
                    }
                elem.clear()

            # Journal (contém transações)
            elif elem.tag.endswith('Journal'):
                journal_id = get_text(elem, 'saft:JournalID', ns)
                journal_desc = get_text(elem, 'saft:Description', ns)

                if journal_id:
                    journal_summary[journal_id]['description'] = journal_desc

                # Processar todas as transações deste diário
                for transaction in elem.findall('.//saft:Transaction', ns):
                    total_transactions += 1
                    period = get_text(transaction, 'saft:Period', ns) or '0'

                    lines = transaction.find('saft:Lines', ns)
                    if lines is None:
                        continue

                    # Débitos
                    for debit in lines.findall('saft:DebitLine', ns):
                        total_entries += 1
                        acc_id = get_text(debit, 'saft:AccountID', ns)
                        amount = get_decimal(debit, 'saft:DebitAmount', ns)

                        if acc_id and amount > 0:
                            account_movements[acc_id]['total_debit'] += amount
                            account_movements[acc_id]['count'] += 1
                            account_movements[acc_id]['by_period'][period]['debit'] += amount
                            account_movements[acc_id]['by_period'][period]['count'] += 1

                            journal_summary[journal_id]['total_debit'] += amount
                            journal_summary[journal_id]['count'] += 1

                            period_summary[period]['debit'] += amount
                            period_summary[period]['count'] += 1

                    # Créditos
                    for credit in lines.findall('saft:CreditLine', ns):
                        total_entries += 1
                        acc_id = get_text(credit, 'saft:AccountID', ns)
                        amount = get_decimal(credit, 'saft:CreditAmount', ns)

                        if acc_id and amount > 0:
                            account_movements[acc_id]['total_credit'] += amount
                            account_movements[acc_id]['count'] += 1
                            account_movements[acc_id]['by_period'][period]['credit'] += amount
                            account_movements[acc_id]['by_period'][period]['count'] += 1

                            journal_summary[journal_id]['total_credit'] += amount
                            journal_summary[journal_id]['count'] += 1

                            period_summary[period]['credit'] += amount
                            period_summary[period]['count'] += 1

                elem.clear()

    except ET.ParseError as e:
        return {'ok': False, 'error': f'XML Parse Error: {str(e)}'}

    # Converter para JSON-serializable
    accounts_list = []
    for acc_id, movement in account_movements.items():
        acc_info = accounts_map.get(acc_id, {})

        # Calcular saldo
        balance = movement['total_debit'] - movement['total_credit']

        # Converter períodos
        periods = []
        for period, p_data in sorted(movement['by_period'].items()):
            periods.append({
                'Period': period,
                'Debit': float(p_data['debit']),
                'Credit': float(p_data['credit']),
                'Balance': float(p_data['debit'] - p_data['credit']),
                'Count': p_data['count']
            })

        accounts_list.append({
            'AccountID': acc_id,
            'Description': acc_info.get('Description', ''),
            'TotalDebit': float(movement['total_debit']),
            'TotalCredit': float(movement['total_credit']),
            'Balance': float(balance),
            'MovementCount': movement['count'],
            'TotalMovement': float(movement['total_debit'] + movement['total_credit']),
            'Periods': periods
        })

    # Ordenar por movimento total (maior atividade primeiro)
    accounts_list.sort(key=lambda x: x['TotalMovement'], reverse=True)

    # Converter diários
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

    # Converter períodos
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


def get_text(elem: ET.Element, path: str, ns: dict) -> str:
    """Helper para extrair texto"""
    child = elem.find(path, ns)
    return child.text.strip() if child is not None and child.text else ''


def get_decimal(elem: ET.Element, path: str, ns: dict) -> Decimal:
    """Helper para extrair decimal"""
    text = get_text(elem, path, ns)
    if text:
        try:
            return Decimal(text)
        except:
            return Decimal('0')
    return Decimal('0')
