"""Table parser for OHAS assessment data from clipboard"""

import re
from typing import List, Dict, Optional
from ..models import (
    Assessment,
    AssessmentCategory,
    FeatureType,
    Coordinate,
    EarthquakeAssessment,
    VolcanoAssessment,
)


class TableParseError(Exception):
    """Exception raised when table parsing fails"""
    pass


class TableParser:
    """
    Parse OHAS assessment tables from various text formats.

    Supports:
    - Markdown tables (from Obsidian webclipper)
    - TSV (tab-separated, copy-paste from browser)
    - Simple field-based format (like HAM filename tools)
    """

    # Field name mappings (handle variations)
    FIELD_MAPPINGS = {
        'assessment': ['assessment', 'assessment no', 'id', 'assessment_id'],
        'category': ['category'],
        'feature_type': ['feature type', 'feature_type', 'type'],
        'location': ['location', 'coordinates', 'coordinate'],
        'active_fault': ['active fault', 'active_fault', 'ground rupture'],
        'liquefaction': ['liquefaction', 'liq'],
        'landslide': ['landslide', 'earthquake-induced landslide', 'eil'],
        'tsunami': ['tsunami', 'tsu'],
        'fissure': ['fissure'],
        'nearest_active_volcano': ['nearest active volcano', 'nearest_active_volcano',
                                   'nearest volcano', 'active volcano'],
        'nearest_pav': ['nearest potentially active volcano', 'nearest_potentially_active_volcano',
                       'nearest pav', 'pav'],
        'lahar': ['lahar'],
        'pyroclastic_flow': ['pyroclastic flow', 'pyroclastic_flow', 'pdc',
                            'pyroclastic density current'],
        'base_surge': ['base surge', 'base_surge'],
        'lava_flow': ['lava flow', 'lava_flow'],
        'ballistic_projectile': ['ballistic projectile', 'ballistic_projectile',
                                'ballistic projectiles'],
        'volcanic_tsunami': ['volcanic tsunami', 'volcanic_tsunami'],
    }

    @staticmethod
    def parse_from_clipboard() -> List[Assessment]:
        """
        Parse assessment data from clipboard.

        Auto-detects format:
        - Markdown table
        - TSV (tab-separated)
        - Field-based format

        Returns:
            List of Assessment objects

        Raises:
            TableParseError: If clipboard is empty or parsing fails
        """
        try:
            import pyperclip
            text = pyperclip.paste()
        except ImportError:
            raise TableParseError(
                "pyperclip not installed. Install with: pip install pyperclip"
            )

        if not text or not text.strip():
            raise TableParseError("Clipboard is empty")

        return TableParser.parse_from_text(text)

    @staticmethod
    def parse_from_text(text: str) -> List[Assessment]:
        """
        Parse assessment data from text (auto-detect format).

        Args:
            text: Raw text (markdown table, TSV, or field-based)

        Returns:
            List of Assessment objects
        """
        text = text.strip()

        # Detect format
        if 'Hazard Assessment' in text or 'Displaying' in text:
            # OHAS native format (messy copy-paste from browser)
            return TableParser._parse_ohas_native(text)
        elif '|' in text and '\n' in text:
            # Markdown table format
            return TableParser._parse_markdown_table(text)
        elif '\t' in text:
            # Tab-separated format
            return TableParser._parse_tsv(text)
        else:
            # Field-based format (like HAM filename tools)
            return [TableParser._parse_field_based(text)]

    @staticmethod
    def _parse_ohas_native(text: str) -> List[Assessment]:
        """
        Parse OHAS native copy-paste format (messy).

        Format:
        ```
        Hazard Assessment
        Displaying 1-1 of 1 result.
        Assessment
        Category
        Feature Type
        Location
        Active Fault
        ...
        24916    Earthquake    Polygon    121.073821,14.600733    Safe; ...    --    --
        No Files Attached
        ```

        Strategy:
        1. Skip header lines ("Hazard Assessment", "Displaying...")
        2. Collect individual column header lines
        3. Find data rows (lines with numeric assessment ID)
        4. Stop at footer ("No Files Attached", etc.)
        """
        lines = [line.strip() for line in text.split('\n') if line.strip()]

        # Find where headers start and end
        header_start_idx = None
        data_start_idx = None

        # Common header keywords that indicate start of column headers
        header_keywords = ['assessment', 'category', 'feature type', 'location']

        # Find header start
        for i, line in enumerate(lines):
            line_lower = line.lower()
            if line_lower in header_keywords:
                header_start_idx = i
                break

        if header_start_idx is None:
            raise TableParseError("Could not find column headers in OHAS format")

        # Collect headers (one per line until we hit a data row)
        headers = []
        for i in range(header_start_idx, len(lines)):
            line = lines[i]

            # Check if this line is a data row (starts with digits)
            if re.match(r'^\d+\s+', line):
                data_start_idx = i
                break

            # This is a header line
            headers.append(line.lower().strip())

        if data_start_idx is None:
            raise TableParseError("Could not find data rows in OHAS format")

        # Parse data rows
        assessments = []
        for i in range(data_start_idx, len(lines)):
            line = lines[i]

            # Stop at footer
            if 'no files' in line.lower() or 'attached' in line.lower():
                break

            # Skip empty or non-data lines
            if not re.match(r'^\d+', line):
                continue

            # Split by multiple spaces or tabs (OHAS uses multiple spaces as separators)
            # This is tricky - need to handle "Safe; Approximately 35 meters..." as one field
            values = re.split(r'\s{2,}|\t', line)

            # Build row data
            if len(values) >= len(headers):
                row_data = dict(zip(headers, values))
            else:
                # Try to match what we can
                row_data = dict(zip(headers, values + ['--'] * (len(headers) - len(values))))

            assessment = TableParser._parse_row_data(row_data)
            if assessment:
                assessments.append(assessment)

        if not assessments:
            raise TableParseError("No valid assessment data found in OHAS format")

        return assessments

    @staticmethod
    def _parse_markdown_table(text: str) -> List[Assessment]:
        """
        Parse markdown table format.

        Example:
        | Assessment | Category | Feature Type | Location | Active Fault | ... |
        |------------|----------|--------------|----------|--------------|-----|
        | 24918      | Earthquake | Polygon    | 120.989669,14.537869 | Safe | ... |
        """
        lines = [line.strip() for line in text.split('\n') if line.strip()]

        # Find header row (first row with |)
        header_line = None
        data_start_idx = 0

        for i, line in enumerate(lines):
            if line.startswith('|') and line.endswith('|'):
                # Skip separator rows (|----|----| etc)
                if re.match(r'^\|\s*[-:]+\s*(\|\s*[-:]+\s*)*\|$', line):
                    continue
                if header_line is None:
                    header_line = line
                    data_start_idx = i + 1
                    break

        if not header_line:
            raise TableParseError("Could not find table header row")

        # Parse header
        headers = [h.strip() for h in header_line.split('|')[1:-1]]  # Skip first/last empty
        headers = TableParser._clean_headers(headers)

        # Parse data rows
        assessments = []
        for line in lines[data_start_idx:]:
            if not line.startswith('|'):
                continue
            # Skip separator rows
            if re.match(r'^\|\s*[-:]+\s*(\|\s*[-:]+\s*)*\|$', line):
                continue

            values = [v.strip() for v in line.split('|')[1:-1]]

            if len(values) != len(headers):
                # Try to handle by matching as many as possible
                pass

            row_data = dict(zip(headers, values))
            assessment = TableParser._parse_row_data(row_data)
            if assessment:
                assessments.append(assessment)

        if not assessments:
            raise TableParseError("No valid assessment data found in table")

        return assessments

    @staticmethod
    def _parse_tsv(text: str) -> List[Assessment]:
        """Parse tab-separated values format."""
        lines = [line.strip() for line in text.split('\n') if line.strip()]

        # First line is headers
        headers = lines[0].split('\t')
        headers = TableParser._clean_headers(headers)

        # Parse data rows
        assessments = []
        for line in lines[1:]:
            values = line.split('\t')
            row_data = dict(zip(headers, values))
            assessment = TableParser._parse_row_data(row_data)
            if assessment:
                assessments.append(assessment)

        return assessments

    @staticmethod
    def _parse_field_based(text: str) -> Assessment:
        """
        Parse field-based format (like HAM filename tools).

        Example:
        Request: 24918
        Category: Earthquake
        Feature Type: Polygon
        Location: 120.989669,14.537869
        Active Fault: Safe; Approximately 7.1 km west...
        """
        def extract_field(label, text):
            """Extract field value using regex (like HAM tools)"""
            pattern = rf"{re.escape(label)}\s*:?\s*(.+)"
            match = re.search(pattern, text, re.IGNORECASE)
            return match.group(1).strip() if match else ""

        # Build row data from fields
        row_data = {}

        # Try common field names
        for canonical, variations in TableParser.FIELD_MAPPINGS.items():
            for variant in variations:
                value = extract_field(variant, text)
                if value:
                    row_data[canonical] = value
                    break

        return TableParser._parse_row_data(row_data)

    @staticmethod
    def _clean_headers(headers: List[str]) -> List[str]:
        """
        Clean and normalize header names.

        Removes markdown links, extra whitespace, normalizes to lowercase.
        """
        cleaned = []
        for header in headers:
            # Remove markdown links: [Text](url) → Text
            header = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', header)
            # Remove extra whitespace
            header = ' '.join(header.split())
            # Lowercase
            header = header.lower().strip()
            cleaned.append(header)

        return cleaned

    @staticmethod
    def _normalize_field_name(field: str) -> Optional[str]:
        """
        Normalize field name to canonical form.

        Args:
            field: Raw field name from table

        Returns:
            Canonical field name or None if unknown
        """
        field_lower = field.lower().strip()

        for canonical, variations in TableParser.FIELD_MAPPINGS.items():
            if field_lower in variations or field_lower == canonical:
                return canonical

        return None

    @staticmethod
    def _parse_row_data(row_data: Dict[str, str]) -> Optional[Assessment]:
        """
        Parse row data dictionary into Assessment object.

        Args:
            row_data: Dictionary of field name → value

        Returns:
            Assessment object or None if invalid
        """
        # Normalize field names
        normalized = {}
        for field, value in row_data.items():
            canonical = TableParser._normalize_field_name(field)
            if canonical:
                normalized[canonical] = value

        # Extract required fields
        assessment_id = normalized.get('assessment')
        if not assessment_id:
            return None

        # Try to parse as integer
        try:
            assessment_id = int(assessment_id)
        except (ValueError, TypeError):
            # If it's not a number, it might be in a different column
            return None

        category_str = normalized.get('category', '')
        if not category_str:
            return None

        # Determine category
        category_lower = category_str.lower()
        if 'earthquake' in category_lower:
            category = AssessmentCategory.EARTHQUAKE
        elif 'volcano' in category_lower:
            category = AssessmentCategory.VOLCANO
        else:
            return None

        # Parse feature type
        feature_str = normalized.get('feature_type', 'Polygon')
        feature_lower = feature_str.lower()
        if 'polygon' in feature_lower:
            feature_type = FeatureType.POLYGON
        elif 'point' in feature_lower:
            feature_type = FeatureType.POINT
        elif 'line' in feature_lower:
            feature_type = FeatureType.LINE
        else:
            feature_type = FeatureType.POLYGON  # Default

        # Parse location
        location_str = normalized.get('location', '')
        if not location_str or location_str == '--':
            # No location provided
            return None

        try:
            location = Coordinate.from_string(location_str)
        except (ValueError, AttributeError):
            return None

        # Parse earthquake fields
        earthquake = None
        if category == AssessmentCategory.EARTHQUAKE:
            earthquake = EarthquakeAssessment(
                active_fault=normalized.get('active_fault'),
                liquefaction=normalized.get('liquefaction'),
                landslide=normalized.get('landslide'),
                tsunami=normalized.get('tsunami'),
                fissure=normalized.get('fissure')
            )

        # Parse volcano fields
        volcano = None
        if category == AssessmentCategory.VOLCANO:
            volcano = VolcanoAssessment(
                nearest_active_volcano=normalized.get('nearest_active_volcano'),
                nearest_pav=normalized.get('nearest_pav'),
                fissure=normalized.get('fissure'),
                lahar=normalized.get('lahar'),
                pyroclastic_flow=normalized.get('pyroclastic_flow'),
                base_surge=normalized.get('base_surge'),
                lava_flow=normalized.get('lava_flow'),
                ballistic_projectile=normalized.get('ballistic_projectile'),
                volcanic_tsunami=normalized.get('volcanic_tsunami')
            )

        return Assessment(
            id=assessment_id,
            category=category,
            feature_type=feature_type,
            location=location,
            earthquake=earthquake,
            volcano=volcano,
            vicinity_map_provided=True  # Assume true if parsing from OHAS
        )
