import re
from typing import Optional, Dict, List
from pydantic import BaseModel, Field

# ── ANGOAL BANK REGISTRY ──────────────────────────────────────
# Standardized mapping of bank codes to names and identities
BANKS = {
    "0003": {"name": "BNA",  "full": "Banco Nacional de Angola",         "color": "#003087"},
    "0005": {"name": "BCI",  "full": "Banco de Comércio e Indústria",    "color": "#c8102e"},
    "0006": {"name": "BFA",  "full": "Banco de Fomento Angola",          "color": "#009b3a"},
    "0009": {"name": "BIC",  "full": "Banco BIC",                        "color": "#ff6600"},
    "0020": {"name": "BMA",  "full": "Banco Millennium Angola",          "color": "#002855"},
    "0040": {"name": "BAI",  "full": "Banco Angolano de Investimentos",  "color": "#003087"},
    "0045": {"name": "SOL",  "full": "Banco Sol",                        "color": "#f5a623"},
    "0050": {"name": "CGTA", "full": "Caixa Geral Totta Angola",         "color": "#008000"},
    "0055": {"name": "ATL",  "full": "Banco Millennium Atlântico",       "color": "#0072ce"},
    "0060": {"name": "KEVE", "full": "Banco Keve",                       "color": "#6a0dad"},
}

class BankInfo(BaseModel):
    code: str
    name: str
    full_name: str
    color: str

class ValidationResult(BaseModel):
    is_valid: bool
    error: Optional[str] = None
    bank: Optional[BankInfo] = None
    iban_formatted: Optional[str] = None

# ── IBAN VALIDATION (MOD-97) ──────────────────────────────────
def validate_angola_iban(raw_iban: str) -> ValidationResult:
    """
    Validates an Angolan IBAN using the standard ISO 13616 / MOD-97 algorithm.
    Angolan IBANs are exactly 25 characters starting with 'AO06'.
    """
    # 1. Basic format check
    clean = re.sub(r'[\s.]', '', raw_iban).upper()
    
    if len(clean) != 25:
        return ValidationResult(is_valid=False, error="INVALID_LENGTH")
    
    if not clean.startswith('AO06'):
        return ValidationResult(is_valid=False, error="INVALID_PREFIX")
    
    # 2. MOD-97 Checksum
    # Rearrange: move first 4 chars to end
    rearranged = clean[4:] + clean[:4]
    
    # Convert characters to digits (A=10, O=24)
    numeric_iban = ""
    for char in rearranged:
        if char.isdigit():
            numeric_iban += char
        else:
            numeric_iban += str(ord(char) - 55)
            
    if int(numeric_iban) % 97 != 1:
        return ValidationResult(is_valid=False, error="CHECKSUM_FAILED")
        
    # 3. Bank Identification
    bank_code = clean[4:8]
    bank_data = BANKS.get(bank_code)
    
    if not bank_data:
        return ValidationResult(is_valid=False, error="UNKNOWN_BANK_CODE")
        
    bank_info = BankInfo(
        code=bank_code,
        name=bank_data["name"],
        full_name=bank_data["full"],
        color=bank_data["color"]
    )
    
    # Format for display: AO06 0040 0000 7247 8459 1014 6
    parts = [clean[i:i+4] for i in range(0, 24, 4)]
    parts.append(clean[24:])
    
    return ValidationResult(
        is_valid=True, 
        bank=bank_info, 
        iban_formatted=" ".join(parts)
    )

# ── AMOUNT PARSER (BUG FIX PORT) ──────────────────────────────
def parse_angolan_amount(raw_text: str) -> float:
    """
    Robustly parses Angolan currency amounts.
    Supports dots for thousands and commas for decimals, or spaces for thousands.
    Example: '35.000,00' -> 35000.0, '35 000' -> 35000.0
    """
    if not raw_text:
        return 0.0
        
    # Remove currency symbols and spaces
    clean = re.sub(r'[Kz|AOA|\s]', '', raw_text, flags=re.IGNORECASE)
    
    if ',' in clean:
        # European format: 35.000,00
        clean = clean.replace('.', '').replace(',', '.')
    else:
        # Check if dots are thousands separators
        # If there's a dot and then 3 digits at the end, it's likely a delimiter not a decimal
        if '.' in clean:
            parts = clean.split('.')
            if len(parts[-1]) == 3:
                clean = clean.replace('.', '')
                
    try:
        return float(clean)
    except ValueError:
        return 0.0

def extract_amount_from_ocr(ocr_lines: List[str]) -> Dict:
    """
    Logic ported from the senior JS implementation.
    Prioritizes labels like MONTANTE or TOTAL.
    """
    amount_patterns = [
        r'(?:MONTANTE|VALOR|TOTAL|QUANTIA)[:\s]+([\d.\s]+(?:,[\d]{2})?)',
    ]
    
    # 1. Search for keyword-prefixed amounts
    for line in ocr_lines:
        for pattern in amount_patterns:
            match = re.search(pattern, line, re.IGNORECASE)
            if match:
                raw_val = match.group(1)
                amount = parse_angolan_amount(raw_val)
                if amount > 0:
                    return {"amount": amount, "raw": raw_val, "found_by": "label"}
                    
    # 2. Fallback: Search for any standalone Angolan-formatted currency amount and take the largest
    standalone_pattern = r'([\d]{1,3}(?:[.\s][\d]{3})+(?:,[\d]{2})?)'
    found_amounts = []
    
    for line in ocr_lines:
        matches = re.findall(standalone_pattern, line)
        for val in matches:
            amount = parse_angolan_amount(val)
            if amount > 0:
                found_amounts.append(amount)
                
    if found_amounts:
        return {"amount": max(found_amounts), "raw": "extracted", "found_by": "standalone"}
        
    return {"amount": 0.0, "raw": "N/D", "found_by": "none"}
