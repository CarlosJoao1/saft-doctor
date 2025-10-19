import io
from typing import List, Dict, Any, Tuple, Optional
from defusedxml import ElementTree as ET


def _local(tag: str) -> str:
    """Return the local part of an XML tag (strip namespace)."""
    if '}' in tag:
        return tag.split('}', 1)[1]
    return tag


def parse_xml(data: bytes) -> ET.Element:
    """Parse XML bytes safely and return root element.

    Raises:
        ET.ParseError: If XML is not well-formed
    """
    return ET.parse(io.BytesIO(data)).getroot()


def extract_text(parent: ET.Element, name: str) -> Optional[str]:
    """Find child by local-name and return its text, or None."""
    for child in parent:
        if _local(child.tag) == name:
            return (child.text or '').strip() or None
    return None


def validate_saft(root: ET.Element) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    """Validate a SAFT XML root element.

    Returns:
        issues: list of findings (dicts with level, code, message, path)
        summary: dict with extracted header fields (when available)
    """
    issues: List[Dict[str, Any]] = []
    summary: Dict[str, Any] = {}

    # Root
    if _local(root.tag) != 'AuditFile':
        issues.append({
            'level': 'error',
            'code': 'ROOT_TAG',
            'message': f"Root element should be 'AuditFile', got '{_local(root.tag)}'",
            'path': '/'
        })
        return issues, summary

    # Find Header
    header = None
    for child in root:
        if _local(child.tag) == 'Header':
            header = child
            break
    if header is None:
        issues.append({'level': 'error', 'code': 'HEADER_MISSING', 'message': 'Missing Header element', 'path': '/AuditFile'})
        return issues, summary

    # Extract common header fields
    fields = ['AuditFileVersion', 'CompanyName', 'TaxRegistrationNumber', 'FiscalYear', 'StartDate', 'EndDate', 'CurrencyCode']
    for f in fields:
        summary[f] = extract_text(header, f)

    # Basic required field checks
    for f in ['AuditFileVersion', 'CompanyName', 'TaxRegistrationNumber']:
        if not summary.get(f):
            issues.append({'level': 'error', 'code': f'{f}_MISSING', 'message': f'Missing {f} in Header', 'path': '/AuditFile/Header'})

    # Dates
    if not summary.get('StartDate') or not summary.get('EndDate'):
        issues.append({'level': 'warning', 'code': 'PERIOD_MISSING', 'message': 'StartDate/EndDate missing in Header', 'path': '/AuditFile/Header'})

    # Presence of content sections
    has_gle = any(_local(c.tag) == 'GeneralLedgerEntries' for c in root)
    has_sd = any(_local(c.tag) == 'SourceDocuments' for c in root)
    if not (has_gle or has_sd):
        issues.append({'level': 'warning', 'code': 'NO_TRANSACTIONS', 'message': 'No GeneralLedgerEntries or SourceDocuments section found', 'path': '/AuditFile'})

    return issues, summary
