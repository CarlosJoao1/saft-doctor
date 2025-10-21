"""
SAFT File Archiver - Utilities for compressing and storing SAFT files
"""
import os
import zipfile
import re
from datetime import datetime
from typing import Dict, Any, Optional, Tuple
from pathlib import Path


def create_zip_filename(nif: str, year: str, month: str) -> str:
    """
    Generate ZIP filename in format: [NIF]_[YEAR]_[MONTH]_[DDHHMMSS].zip
    
    Args:
        nif: Tax ID
        year: Fiscal year
        month: Fiscal month (01-12)
    
    Returns:
        ZIP filename (e.g., "501789227_2025_09_20192530.zip")
    """
    timestamp = datetime.now().strftime('%d%H%M%S')
    return f"{nif}_{year}_{month}_{timestamp}.zip"


def compress_xml_to_zip(xml_path: str, zip_path: str, original_filename: Optional[str] = None) -> int:
    """
    Compress XML file to ZIP
    
    Args:
        xml_path: Path to source XML file
        zip_path: Destination ZIP file path
        original_filename: Name to use inside ZIP (default: uses xml_path basename)
    
    Returns:
        Size of created ZIP file in bytes
    """
    if not os.path.exists(xml_path):
        raise FileNotFoundError(f"XML file not found: {xml_path}")
    
    # Name inside ZIP (preserve original if provided)
    arcname = original_filename or os.path.basename(xml_path)
    
    # Create ZIP with compression
    with zipfile.ZipFile(zip_path, 'w', compression=zipfile.ZIP_DEFLATED, compresslevel=9) as zf:
        zf.write(xml_path, arcname=arcname)
    
    return os.path.getsize(zip_path)


def generate_storage_key(nif: str, year: str, month: str, filename: str, country: str = 'pt') -> str:
    """
    Generate B2/S3 object key for storing ZIP file
    
    Format: {country}/saft-archives/{nif}/{year}/{month}/{filename}
    Example: pt/saft-archives/501789227/2025/09/501789227_2025_09_20192530.zip
    
    Args:
        nif: Tax ID
        year: Fiscal year
        month: Fiscal month
        filename: ZIP filename
        country: Country code (default: 'pt')
    
    Returns:
        Full S3 object key
    """
    return f"{country}/saft-archives/{nif}/{year}/{month}/{filename}"


def parse_jar_response_xml(output: str) -> Dict[str, Any]:
    """
    Parse FACTEMICLI.jar XML response from stdout
    
    Looks for XML like:
    <?xml version="1.0" encoding="ISO-8859-1"?> 
    <response code="200">
        <totalFaturas>2562</totalFaturas>
        <totalCreditos>8888810.81</totalCreditos>
        <totalDebitos>430700.63</totalDebitos>
        <nomeFicheiro>SAFT-T AQUINOS_092025.xml</nomeFicheiro>
    </response>
    
    Args:
        output: Complete stdout from JAR
    
    Returns:
        Dict with parsed data:
        {
            'response_code': '200',
            'total_faturas': 2562,
            'total_creditos': 8888810.81,
            'total_debitos': 430700.63,
            'nome_ficheiro': 'SAFT-T AQUINOS_092025.xml',
            'raw_xml': '<response code="200">...</response>'
        }
        Returns empty dict if XML not found
    """
    result = {}
    
    # Find response XML (may span multiple lines)
    xml_match = re.search(
        r'<response\s+code="(\d+)">(.*?)</response>',
        output,
        re.DOTALL | re.IGNORECASE
    )
    
    if not xml_match:
        return result
    
    response_code = xml_match.group(1)
    xml_body = xml_match.group(2)
    raw_xml = xml_match.group(0)
    
    result['response_code'] = response_code
    result['raw_xml'] = raw_xml
    
    # Parse individual fields
    def extract_tag(tag: str, text: str, convert_to: type = str):
        match = re.search(f'<{tag}>(.+?)</{tag}>', text, re.DOTALL)
        if match:
            value = match.group(1).strip()
            try:
                if convert_to == int:
                    return int(value)
                elif convert_to == float:
                    return float(value)
                else:
                    return value
            except (ValueError, TypeError):
                return value
        return None
    
    result['total_faturas'] = extract_tag('totalFaturas', xml_body, int)
    result['total_creditos'] = extract_tag('totalCreditos', xml_body, float)
    result['total_debitos'] = extract_tag('totalDebitos', xml_body, float)
    result['nome_ficheiro'] = extract_tag('nomeFicheiro', xml_body, str)
    
    return result


def is_validation_successful(jar_stdout: str, returncode: int) -> bool:
    """
    Determine if validation was successful based on JAR output
    
    Args:
        jar_stdout: Complete stdout from JAR
        returncode: Process return code
    
    Returns:
        True if validation successful, False otherwise
    """
    if returncode != 0:
        return False
    
    # Check for success indicators
    success_patterns = [
        r'validado com sucesso',
        r'<response\s+code="200"',
    ]
    
    for pattern in success_patterns:
        if re.search(pattern, jar_stdout, re.IGNORECASE):
            return True
    
    return False


def extract_validation_summary(jar_stdout: str) -> Dict[str, Any]:
    """
    Extract human-readable validation summary from JAR output
    
    Args:
        jar_stdout: Complete stdout from JAR
    
    Returns:
        Dict with summary info (for display purposes)
    """
    summary = {
        'success': False,
        'message': '',
        'documents_summary': ''
    }
    
    # Check for success message
    success_match = re.search(
        r'O ficheiro foi validado com sucesso,\s*foram selecionados os seguintes documentos.*?:(.+?)(?=\[I\]|\Z)',
        jar_stdout,
        re.DOTALL | re.IGNORECASE
    )
    
    if success_match:
        summary['success'] = True
        summary['message'] = 'Ficheiro validado com sucesso'
        summary['documents_summary'] = success_match.group(1).strip()
    
    return summary
