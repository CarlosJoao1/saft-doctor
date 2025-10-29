"""
SAFT Accounting Mock Data
Dados de exemplo para desenvolvimento do frontend enquanto resolvemos problemas de encoding
"""
from typing import Dict, Any


def get_mock_accounting_data() -> Dict[str, Any]:
    """Retorna dados contabilísticos de exemplo baseados na estrutura real"""

    return {
        'ok': True,
        'header': {
            'CompanyName': 'AQUINOS, S.A.',
            'TaxRegistrationNumber': '501789227',
            'FiscalYear': '2025',
            'StartDate': '2025-01-01',
            'EndDate': '2025-12-31',
            'CurrencyCode': 'EUR',
        },
        'accounts': [
            {
                'AccountID': '121',
                'Description': 'DEPÓSITOS À ORDEM',
                'TotalDebit': 15234567.89,
                'TotalCredit': 16432040.76,
                'Balance': -1197472.87,
                'MovementCount': 8234,
                'TotalMovement': 31666608.65,
                'Periods': [
                    {'Period': '1', 'Debit': 1234567.00, 'Credit': 1456789.00, 'Balance': -222222.00, 'Count': 687},
                    {'Period': '2', 'Debit': 1345678.00, 'Credit': 1567890.00, 'Balance': -222212.00, 'Count': 712},
                    {'Period': '3', 'Debit': 1456789.00, 'Credit': 1678901.00, 'Balance': -222112.00, 'Count': 745},
                    {'Period': '4', 'Debit': 1234560.00, 'Credit': 1456780.00, 'Balance': -222220.00, 'Count': 698},
                    {'Period': '5', 'Debit': 1345670.00, 'Credit': 1567800.00, 'Balance': -222130.00, 'Count': 702},
                    {'Period': '6', 'Debit': 1456780.00, 'Credit': 1678910.00, 'Balance': -222130.00, 'Count': 738},
                    {'Period': '7', 'Debit': 1234567.00, 'Credit': 1456789.00, 'Balance': -222222.00, 'Count': 681},
                    {'Period': '8', 'Debit': 1345678.00, 'Credit': 1567890.00, 'Balance': -222212.00, 'Count': 697},
                    {'Period': '9', 'Debit': 1456789.00, 'Credit': 1678901.00, 'Balance': -222112.00, 'Count': 704},
                    {'Period': '10', 'Debit': 1234560.00, 'Credit': 1456780.00, 'Balance': -222220.00, 'Count': 689},
                    {'Period': '11', 'Debit': 1345670.00, 'Credit': 1567800.00, 'Balance': -222130.00, 'Count': 695},
                    {'Period': '12', 'Debit': 1543459.89, 'Credit': 1596010.76, 'Balance': -52550.87, 'Count': 686},
                ]
            },
            {
                'AccountID': '361',
                'Description': 'MERCADORIAS',
                'TotalDebit': 12567890.45,
                'TotalCredit': 11234567.23,
                'Balance': 1333323.22,
                'MovementCount': 6789,
                'TotalMovement': 23802457.68,
                'Periods': [
                    {'Period': '1', 'Debit': 1045678.00, 'Credit': 934567.00, 'Balance': 111111.00, 'Count': 567},
                    {'Period': '2', 'Debit': 1056789.00, 'Credit': 945678.00, 'Balance': 111111.00, 'Count': 574},
                    {'Period': '3', 'Debit': 1067890.00, 'Credit': 956789.00, 'Balance': 111101.00, 'Count': 581},
                    {'Period': '4', 'Debit': 1045670.00, 'Credit': 934560.00, 'Balance': 111110.00, 'Count': 568},
                    {'Period': '5', 'Debit': 1056780.00, 'Credit': 945670.00, 'Balance': 111110.00, 'Count': 575},
                    {'Period': '6', 'Debit': 1067800.00, 'Credit': 956780.00, 'Balance': 111020.00, 'Count': 582},
                    {'Period': '7', 'Debit': 1045678.00, 'Credit': 934567.00, 'Balance': 111111.00, 'Count': 569},
                    {'Period': '8', 'Debit': 1056789.00, 'Credit': 945678.00, 'Balance': 111111.00, 'Count': 576},
                    {'Period': '9', 'Debit': 1067890.00, 'Credit': 956789.00, 'Balance': 111101.00, 'Count': 583},
                    {'Period': '10', 'Debit': 1045670.00, 'Credit': 934560.00, 'Balance': 111110.00, 'Count': 570},
                    {'Period': '11', 'Debit': 1056780.00, 'Credit': 945670.00, 'Balance': 111110.00, 'Count': 577},
                    {'Period': '12', 'Debit': 954476.45, 'Credit': 900089.23, 'Balance': 54387.22, 'Count': 567},
                ]
            },
            {
                'AccountID': '383',
                'Description': 'PRODUTOS ACABADOS E INTERMÉDIOS',
                'TotalDebit': 8765432.10,
                'TotalCredit': 9012345.67,
                'Balance': -246913.57,
                'MovementCount': 5234,
                'TotalMovement': 17777777.77,
                'Periods': [
                    {'Period': '1', 'Debit': 730453.00, 'Credit': 751029.00, 'Balance': -20576.00, 'Count': 436},
                    {'Period': '2', 'Debit': 730450.00, 'Credit': 751020.00, 'Balance': -20570.00, 'Count': 437},
                    {'Period': '3', 'Debit': 730460.00, 'Credit': 751030.00, 'Balance': -20570.00, 'Count': 438},
                    {'Period': '4', 'Debit': 730440.00, 'Credit': 751010.00, 'Balance': -20570.00, 'Count': 435},
                    {'Period': '5', 'Debit': 730450.00, 'Credit': 751020.00, 'Balance': -20570.00, 'Count': 436},
                    {'Period': '6', 'Debit': 730460.00, 'Credit': 751030.00, 'Balance': -20570.00, 'Count': 437},
                    {'Period': '7', 'Debit': 730453.00, 'Credit': 751029.00, 'Balance': -20576.00, 'Count': 436},
                    {'Period': '8', 'Debit': 730450.00, 'Credit': 751020.00, 'Balance': -20570.00, 'Count': 436},
                    {'Period': '9', 'Debit': 730460.00, 'Credit': 751030.00, 'Balance': -20570.00, 'Count': 437},
                    {'Period': '10', 'Debit': 730440.00, 'Credit': 751010.00, 'Balance': -20570.00, 'Count': 435},
                    {'Period': '11', 'Debit': 730450.00, 'Credit': 751020.00, 'Balance': -20570.00, 'Count': 436},
                    {'Period': '12', 'Debit': 729416.10, 'Credit': 750097.67, 'Balance': -20681.57, 'Count': 435},
                ]
            },
            {
                'AccountID': '2111',
                'Description': 'FORNECEDORES C/C',
                'TotalDebit': 7654321.98,
                'TotalCredit': 8765432.10,
                'Balance': -1111110.12,
                'MovementCount': 4567,
                'TotalMovement': 16419754.08,
                'Periods': [
                    {'Period': '1', 'Debit': 637860.16, 'Credit': 730536.00, 'Balance': -92675.84, 'Count': 381},
                    {'Period': '2', 'Debit': 637860.00, 'Credit': 730530.00, 'Balance': -92670.00, 'Count': 382},
                    {'Period': '3', 'Debit': 637865.00, 'Credit': 730540.00, 'Balance': -92675.00, 'Count': 383},
                    {'Period': '4', 'Debit': 637855.00, 'Credit': 730520.00, 'Balance': -92665.00, 'Count': 380},
                    {'Period': '5', 'Debit': 637860.00, 'Credit': 730530.00, 'Balance': -92670.00, 'Count': 381},
                    {'Period': '6', 'Debit': 637865.00, 'Credit': 730540.00, 'Balance': -92675.00, 'Count': 382},
                    {'Period': '7', 'Debit': 637860.16, 'Credit': 730536.00, 'Balance': -92675.84, 'Count': 381},
                    {'Period': '8', 'Debit': 637860.00, 'Credit': 730530.00, 'Balance': -92670.00, 'Count': 381},
                    {'Period': '9', 'Debit': 637865.00, 'Credit': 730540.00, 'Balance': -92675.00, 'Count': 382},
                    {'Period': '10', 'Debit': 637855.00, 'Credit': 730520.00, 'Balance': -92665.00, 'Count': 380},
                    {'Period': '11', 'Debit': 637860.00, 'Credit': 730530.00, 'Balance': -92670.00, 'Count': 381},
                    {'Period': '12', 'Debit': 636676.66, 'Credit': 729080.10, 'Balance': -92403.44, 'Count': 383},
                ]
            },
            {
                'AccountID': '2421',
                'Description': 'ESTADO - IMPOSTO S/ RENDIMENTO',
                'TotalDebit': 3456789.01,
                'TotalCredit': 4567890.12,
                'Balance': -1111101.11,
                'MovementCount': 3456,
                'TotalMovement': 8024679.13,
                'Periods': [
                    {'Period': '1', 'Debit': 288065.75, 'Credit': 380657.50, 'Balance': -92591.75, 'Count': 288},
                    {'Period': '2', 'Debit': 288065.00, 'Credit': 380650.00, 'Balance': -92585.00, 'Count': 289},
                    {'Period': '3', 'Debit': 288070.00, 'Credit': 380660.00, 'Balance': -92590.00, 'Count': 290},
                    {'Period': '4', 'Debit': 288060.00, 'Credit': 380640.00, 'Balance': -92580.00, 'Count': 287},
                    {'Period': '5', 'Debit': 288065.00, 'Credit': 380650.00, 'Balance': -92585.00, 'Count': 288},
                    {'Period': '6', 'Debit': 288070.00, 'Credit': 380660.00, 'Balance': -92590.00, 'Count': 289},
                    {'Period': '7', 'Debit': 288065.75, 'Credit': 380657.50, 'Balance': -92591.75, 'Count': 288},
                    {'Period': '8', 'Debit': 288065.00, 'Credit': 380650.00, 'Balance': -92585.00, 'Count': 288},
                    {'Period': '9', 'Debit': 288070.00, 'Credit': 380660.00, 'Balance': -92590.00, 'Count': 289},
                    {'Period': '10', 'Debit': 288060.00, 'Credit': 380640.00, 'Balance': -92580.00, 'Count': 287},
                    {'Period': '11', 'Debit': 288065.00, 'Credit': 380650.00, 'Balance': -92585.00, 'Count': 288},
                    {'Period': '12', 'Debit': 287102.51, 'Credit': 379815.12, 'Balance': -92712.61, 'Count': 285},
                ]
            },
        ],
        'journals': [
            {'JournalID': 'AJUEXIST', 'Description': 'Registar Variação Inventário', 'TotalDebit': 8765432.10, 'TotalCredit': 8765432.10, 'Count': 2456},
            {'JournalID': 'COMPRAS', 'Description': 'Diário de Compras', 'TotalDebit': 12345678.90, 'TotalCredit': 12345678.90, 'Count': 5678},
            {'JournalID': 'VENDAS', 'Description': 'Diário de Vendas', 'TotalDebit': 15678901.23, 'TotalCredit': 15678901.23, 'Count': 6789},
            {'JournalID': 'CAIXA', 'Description': 'Diário de Caixa', 'TotalDebit': 4567890.12, 'TotalCredit': 4567890.12, 'Count': 3456},
            {'JournalID': 'BANCOS', 'Description': 'Diário de Bancos', 'TotalDebit': 23456789.01, 'TotalCredit': 23456789.01, 'Count': 7890},
            {'JournalID': 'OPERGER', 'Description': 'Operações Gerais', 'TotalDebit': 9876543.21, 'TotalCredit': 9876543.21, 'Count': 4321},
        ],
        'periods': [
            {'Period': '1', 'Debit': 94224908.67, 'Credit': 94224908.67, 'Count': 4277},
            {'Period': '2', 'Debit': 94225000.00, 'Credit': 94225000.00, 'Count': 4278},
            {'Period': '3', 'Debit': 94225100.00, 'Credit': 94225100.00, 'Count': 4279},
            {'Period': '4', 'Debit': 94224800.00, 'Credit': 94224800.00, 'Count': 4276},
            {'Period': '5', 'Debit': 94225000.00, 'Credit': 94225000.00, 'Count': 4277},
            {'Period': '6', 'Debit': 94225100.00, 'Credit': 94225100.00, 'Count': 4278},
            {'Period': '7', 'Debit': 94224908.67, 'Credit': 94224908.67, 'Count': 4277},
            {'Period': '8', 'Debit': 94225000.00, 'Credit': 94225000.00, 'Count': 4277},
            {'Period': '9', 'Debit': 94225100.00, 'Credit': 94225100.00, 'Count': 4278},
            {'Period': '10', 'Debit': 94224800.00, 'Credit': 94224800.00, 'Count': 4276},
            {'Period': '11', 'Debit': 94225000.00, 'Credit': 94225000.00, 'Count': 4277},
            {'Period': '12', 'Debit': 93923697.41, 'Credit': 93923697.41, 'Count': 4274},
        ],
        'summary': {
            'TotalAccounts': 5,
            'TotalJournals': 6,
            'TotalTransactions': 28945,
            'TotalEntries': 51293,
            'TotalDebit': 1129599515.42,
            'TotalCredit': 1129599515.42
        }
    }
