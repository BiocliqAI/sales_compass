import re
from typing import Optional

# Common replacements to normalise regional language tokens.
_DEVANAGARI_REPLACEMENTS = {
    "महाराष्ट्र": "Maharashtra",
    "भारत": "India",
    "कर्नाटक": "Karnataka",
    "कोल्हापूर": "Kolhapur",
    "जत": "Jath",
    "जथ": "Jath",
}

# State and country keywords that usually follow the city in the address.
_STATE_KEYWORDS = (
    "maharashtra",
    "karnataka",
    "goa",
    "india",
    "telangana",
    "andhra pradesh",
    "gujarat",
    "madhya pradesh",
)

# Words that typically indicate the token is not a city.
_GENERIC_PREFIXES = (
    "near",
    "opp",
    "opposite",
    "beside",
    "behind",
    "shop",
    "station",
    "plot",
    "floor",
    "gat no",
    "sr no",
    "survey no",
    "tal",
    "tal:",
    "taluka",
    "at post",
    "post",
    "dist",
    "district",
    "tehsil",
    "teh",
    "block",
    "sector",
    "suite",
    "flat",
    "q",
)

_GENERIC_SUBSTRINGS = (
    " road",
    " rd",
    " lane",
    " chowk",
    " bazar",
    " market",
    " hospital",
    " temple",
    " society",
    " colony",
    " complex",
    " apartment",
    " heights",
    " garden",
    " corner",
    " stop",
    " stand",
    " nagar",
    " wadi",
    " peth",
    " highway",
    " hwy",
)

_ADDRESS_STOPWORDS = {
    "india",
    "maharashtra",
    "mah",
    "mh",
    "maha",
    "maharastra",
    "country",
    "state",
    "district",
    "dist",
    "taluka",
    "taluk",
    "tal",
    "post",
    "atpost",
    "tehsil",
    "teh",
    "po",
    "p.o",
    "ps",
    "police",
    "station",
    "opp",
    "opposite",
    "near",
    "nearby",
    "beside",
    "besides",
    "besids",
    "behind",
    "besides",
    "above",
    "below",
    "next",
    "to",
}

_ADDRESS_TOKEN_REPLACEMENTS = {
    "rd": "road",
    "road": "road",
    "marg": "road",
    "hwy": "highway",
    "hwy.": "highway",
    "highway": "highway",
    "st.": "saint",
    "st": "saint",
    "s.t": "state",
    "tal-": "tal",
    "dist-": "dist",
}

_NAME_STOPWORDS = {
    "the",
    "and",
    "&",
    "of",
    "llp",
    "ltd",
    "pvt",
    "private",
    "limited",
    "llp",
    "clinic",
    "centre",
    "center",
    "centers",
    "centres",
    "hospital",
    "hospitals",
    "diagnostics",
    "diagnostic",
    "diagnost",
    "diagnostics.",
    "labs",
    "lab",
    "imaging",
    "imaging.",
    "radiology",
    "services",
    "service",
}

_NAME_TOKEN_REPLACEMENTS = {
    "diagnostics": "diagnostic",
    "diagnostic": "diagnostic",
    "centre": "center",
    "centres": "center",
    "centers": "center",
    "labs": "lab",
    "scans": "scan",
    "ctscan": "ctscan",
    "ct-scan": "ctscan",
    "ct": "ct",
    "pvt": "private",
    "ltd": "limited",
    "llp": "llp",
    "imaging": "imaging",
}

_PINCODE_PATTERN = re.compile(r"\b\d{6}\b")

BASE_CITY_NAMES = [
    'Ahilyanagar', 'Ahmednagar', 'Airoli', 'Ajara', 'Akkalkot', 'Akluj', 'Akola', 'Akole',
    'Alephata', 'Alibag', 'Amalner', 'Ambajogai', 'Ambarnath', 'Ambegaon', 'Ambernath', 'Amravati',
    'Andheri', 'Apte Colony', 'Arvi', 'Ashti', 'Atpadi', 'Aundh', 'Aundh Road', 'Aurangabad',
    'Babhulgaon', 'Badlapur', 'Balewadi', 'Bandra', 'Baner', 'Baramati', 'Barshi', 'Beed',
    'Belapur', 'Belapur CBD', 'Bhadgaon', 'Bhadravati', 'Bhandara', 'Bhaskar Market Rd', 'Bhira', 'Bhor',
    'Bhusawal', 'Boat Club Road', 'Bodwad', 'Boripardhi', 'Borivali', 'Buldhana', 'Bund Garden Road', 'Butibori',
    'Camp', 'Chakan', 'Chalisgaon', 'Chandrapur', 'Charholi', 'Chhatrapati Sambhajinagar', 'Chinchwad', 'Chiplun',
    'Chopda', 'Dadar', 'Dahanu', 'Dahegaon', 'Dahisar', 'Dapoli', 'Darwha', 'Daund',
    'Deccan Gymkhana', 'Deglur', 'Dehu Road', 'Deogad', 'Deoli', 'Devidas Colony', 'Dharangaon', 'Dhole Patil Road',
    'Digras', 'Dindori', 'Divya Shakti Township', 'Dombivli', 'Dombivli East', 'Dopatta', 'E Ward', 'Erandol',
    'Erandwane', 'FC Road', 'Gadhinglaj', 'Gandhinagar', 'Ganesh Nagar', 'Ganeshkhind', 'Ghansoli', 'Ghatanji',
    'Ghodegaon', 'Ghoti', 'Ghoti Budruk', 'Gondia', 'Goregaon', 'Guhagar', 'Hadapsar', 'Hatkanangale',
    'Hatkanangle', 'Hinganghat', 'Hingna', 'Hingoli', 'Hinjewadi', 'Ichalkaranji', 'Indapur', 'Islampur',
    'JM Road', 'Jalgaon', 'Jalna', 'Jamkhed', 'Jamner', 'Jat', 'Jath', 'Jawhar',
    'Jaysingpur', 'Jejuri', 'Juhu', 'Juinagar', 'Junnar', 'K K Zenith Building', 'Kadamwadi', 'Kadamwadi - Jadhavwadi Rd',
    'Kadegaon', 'Kagal', 'Kalamb', 'Kalamboli', 'Kalamnuri', 'Kalmana', 'Kalmeshwar', 'Kalwa',
    'Kalyan', 'Kamothe', 'Kamptee', 'Kandivali', 'Kankavli', 'Karad', 'Karjat', 'Karmala',
    'Katol', 'Katraj', 'Kavath', 'Kavlapur', 'Kawala Naka', 'Kelapur', 'Khadkale', 'Khadkoli',
    'Khandala', 'Kharghar', 'Khatav', 'Khed', 'Khopoli', 'Kolhapur', 'Kopar', 'Kopar Khairane',
    'Kopargaon', 'Koradi', 'Koregaon', 'Kothrud', 'Kudal', 'Kuhi', 'Kusgaon Budruk', 'Lakshmi Rd',
    'Lanja', 'Latur', 'Law College Road', 'Laxmi Nagar', 'Laxminarayan Nagar', 'Lonavala', 'MG Road', 'Madangad',
    'Madha', 'Mahabaleshwar', 'Mahad', 'Mahagaon', 'Mahalaxminagar', 'Malad', 'Malegaon', 'Malkapur',
    'Malshiras', 'Malwan', 'Man', 'Manchar', 'Mandangad', 'Mangaon', 'Mangrulpir', 'Maregaon',
    'Mauda', 'Maval', 'Mhasla', 'Mhaswad', 'Mira Bhayandar', 'Mira Bhayander', 'Miraj', 'Model Colony',
    'Mohol', 'Mokhada', 'Moschi', 'Muktainagar', 'Mumbai', 'Mumbai - Pune Hwy', 'Mumbra', 'Murud',
    'Nagar', 'Nagothane', 'Nagpur', 'Nallasopara', 'Nanded', 'Narayangaon', 'Nashik', 'Navi Mumbai',
    'Neral', 'Nerul', 'Nevasa', 'New Usmanpura', 'Newasa', 'Nigdi', 'Niphad', 'Osmanabad',
    'Ozar', 'Pachora', 'Palghar', 'Pali', 'Palus', 'Pandharpur', 'Panvel', 'Parbhani',
    'Parli', 'Parner', 'Parseoni', 'Pathardi', 'Pathri', 'Patil Mala', 'Pen', 'Phaltan',
    'Pimpri-Chinchwad', 'Poladpur', 'Poorvarang', 'Pratap Nagar', 'Pulgaon', 'Pune', 'Purandhar', 'Pusad',
    'Rabale', 'Rahuri', 'Raigad', 'Rajapur', 'Rajarampuri', 'Ramtek', 'Ranchos Nagar', 'Ratnagiri',
    'Raver', 'Rewas', 'Risod', 'S T Stand', 'Sangameshwar', 'Sangamner', 'Sangli', 'Sangli-Miraj-Kupwad',
    'Sangole', 'Sankeshwar', 'Saoner', 'Satara', 'Sawantwadi', 'Scheme No.4', 'Seawoods', 'Seloo',
    'Shahapur', 'Shahu Mill Rd', 'Shahupuri', 'Shevgaon', 'Shikrapur', 'Shilphata', 'Shirala', 'Shirdi',
    'Shirgaon', 'Shirol', 'Shirol wadi road', 'Shirpur', 'Shirur', 'Shivaji Nagar', 'Shrigonda', 'Shrirampur',
    'Shrivardhan', 'Sillod', 'Sindhudurg', 'Sinnar', 'Sion', 'Solapur', 'Somatne', 'Somatne Phata',
    'Sonbhadra', 'South Solapur', 'Suyog Society', 'Tala', 'Talasari', 'Talegaon Dabhade', 'Taloja', 'Tarapur',
    'Tasgaon', 'Thane', 'Turbhe', 'Ujalaiwadi', 'Ulhasnagar', 'Ulwe', 'Umred', 'University Road',
    'Uran', 'Vadgaon', 'Vadodara', 'Vaibhavwadi', 'Vaijapur', 'Varunji', 'Vasai', 'Vasai-Virar',
    'Vashi', 'Velhe', 'Vengurla', 'Versova', 'Vikramgad', 'Viman Nagar', 'Virar', 'Vita',
    'Vitthalwadi', 'Wada', 'Wai', 'Wakad', 'Walchandnagar', 'Waluj', 'Walwa', 'Wanadongri',
    'Wani', 'Wardha', 'Warje', 'Warora', 'Washim', 'Yaval', 'Yavatmal', 'Yawal',
    'Yerwada', 'Zari',
]

CITY_ALIASES = {
    "mira bhayander": "Mira Bhayandar",
    "mumbai - pune hwy": "Mumbai",
    "k k zenith building": "K K Zenith Building",
    "kadambwadi": "Kadamwadi",
    "shirol wadi road": "Shirol wadi road",
}

CITY_KEYWORDS = {name.lower(): name for name in BASE_CITY_NAMES}
CITY_KEYWORDS.update({alias: canonical for alias, canonical in CITY_ALIASES.items()})


def _normalise_address(address: str) -> str:
    normalised = address
    for native, latin in _DEVANAGARI_REPLACEMENTS.items():
        normalised = normalised.replace(native, latin)
    return normalised


def _contains_state_keyword(fragment: str) -> bool:
    fragment_lower = fragment.lower()
    return any(keyword in fragment_lower for keyword in _STATE_KEYWORDS)


def _cleanup_candidate(section: str) -> str:
    cleaned = section.strip().strip(".")
    if not cleaned:
        return ""
    cleaned = cleaned.replace("|", " ")
    cleaned = cleaned.replace("/", " ")
    cleaned = cleaned.replace("&", " ")
    cleaned = re.sub(r"[()]", " ", cleaned)
    cleaned = re.sub(r"\\s+", " ", cleaned).strip()
    lowered = cleaned.lower()
    for prefix in ("taluka ", "tal ", "dist ", "district ", "tehsil ", "teh "):
        if lowered.startswith(prefix):
            cleaned = cleaned[len(prefix):].strip()
            lowered = cleaned.lower()
    cleaned = re.sub(r"[^A-Za-z\s-]", "", cleaned)
    cleaned = re.sub(r"\\s+", " ", cleaned).strip()
    return cleaned


def _is_generic_token(token: str) -> bool:
    if not token:
        return True
    lowered = token.lower()
    if any(lowered.startswith(prefix) for prefix in _GENERIC_PREFIXES):
        return True
    if any(substr in lowered for substr in _GENERIC_SUBSTRINGS):
        return True
    if re.fullmatch(r"[a-z]", lowered):
        return True
    return False


def _extract_from_state_parts(address: str) -> Optional[str]:
    parts = [part.strip() for part in address.split(",")]
    for index, part in enumerate(parts):
        if not _contains_state_keyword(part):
            continue
        for cursor in range(index - 1, -1, -1):
            candidate = _cleanup_candidate(parts[cursor])
            if not candidate:
                continue
            if _is_generic_token(candidate):
                continue
            lowered = candidate.lower()
            canonical = CITY_KEYWORDS.get(lowered) or CITY_ALIASES.get(lowered)
            if canonical:
                return canonical
            tokens = candidate.split()
            for idx in range(len(tokens) - 1, -1, -1):
                token = tokens[idx]
                token_lower = token.lower()
                if token_lower in {"tal", "taluka", "dist", "district"} or token_lower.startswith(("tal-", "dist-")):
                    continue
                prev_lower = tokens[idx - 1].lower() if idx > 0 else ""
                if (
                    prev_lower in {"tal", "taluka", "dist", "district"}
                    or prev_lower.startswith(("tal-", "dist-"))
                ):
                    continue
                canonical = CITY_KEYWORDS.get(token_lower) or CITY_ALIASES.get(token_lower)
                if canonical:
                    return canonical
    return None


def extract_city_from_address(address: str) -> str:
    if not address:
        return "Unknown"

    normalised = _normalise_address(address)
    candidate = _extract_from_state_parts(normalised)
    if candidate:
        return candidate

    address_lower = normalised.lower()
    for keyword, canonical in CITY_KEYWORDS.items():
        if keyword and keyword in address_lower:
            return canonical

    return "Unknown"


def normalize_address_for_dedup(address: str) -> str:
    if not address:
        return ""

    normalised = _normalise_address(address)
    lowered = _PINCODE_PATTERN.sub(" ", normalised.lower())
    lowered = re.sub(r"[^a-z0-9\s-]", " ", lowered)
    lowered = lowered.replace("-", " ")

    tokens = []
    for raw_token in lowered.split():
        token = _ADDRESS_TOKEN_REPLACEMENTS.get(raw_token, raw_token)
        token = token.strip()
        if not token:
            continue
        if token in _ADDRESS_STOPWORDS:
            continue
        if len(token) == 1 and not token.isdigit():
            continue
        tokens.append(token)

    if not tokens:
        return ""

    # Preserve order while dropping duplicates
    deduped_tokens = list(dict.fromkeys(tokens))
    return " ".join(deduped_tokens)


def normalize_center_name_for_dedup(name: str) -> str:
    if not name:
        return ""

    normalised = _normalise_address(name)
    lowered = re.sub(r"[^a-z0-9\s-]", " ", normalised.lower()).replace("-", " ")

    tokens = []
    for raw_token in lowered.split():
        token = _NAME_TOKEN_REPLACEMENTS.get(raw_token, raw_token)
        if not token:
            continue
        if token in _NAME_STOPWORDS:
            continue
        tokens.append(token)

    if not tokens:
        return ""

    deduped_tokens = list(dict.fromkeys(tokens))
    return " ".join(deduped_tokens)
