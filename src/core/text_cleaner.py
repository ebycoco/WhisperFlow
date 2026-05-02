"""
WhisperFlow — Text Cleaner
Post-processes transcribed text: removes fillers, fixes punctuation, capitalizes.
"""

import re
from src.utils.logger import get_logger

logger = get_logger("TextCleaner")

# Filler words to remove (multi-language)
FILLER_WORDS = {
    # English
    "uh", "um", "uhm", "erm", "er", "ah", "like",
    # French
    "euh", "heu", "hum", "ben", "bah", "beh",
    "genre", "en fait", "du coup", "voilà",
    # Spanish
    "eh", "este", "pues", "bueno",
}

# Patterns for filler detection (word boundaries)
FILLER_PATTERN = re.compile(
    r'\b(' + '|'.join(re.escape(f) for f in FILLER_WORDS) + r')\b[,.]?\s*',
    re.IGNORECASE,
)

# Multiple spaces/punctuation cleanup
MULTI_SPACE = re.compile(r'\s{2,}')
MULTI_PERIOD = re.compile(r'\.{2,}')
SPACE_BEFORE_PUNCT = re.compile(r'\s+([.,!?;:])')


class TextCleaner:
    """Post-processes transcribed text for natural output."""

    def __init__(
        self,
        remove_fillers: bool = True,
        auto_punctuation: bool = True,
        auto_capitalize: bool = True,
    ):
        self.remove_fillers = remove_fillers
        self.auto_punctuation = auto_punctuation
        self.auto_capitalize = auto_capitalize

    def clean(self, text: str) -> str:
        """
        Apply all cleaning operations to the transcribed text.

        Args:
            text: Raw transcription output

        Returns:
            Cleaned, formatted text
        """
        if not text:
            return ""

        original = text
        result = text.strip()

        # Step 1: Remove filler words
        if self.remove_fillers:
            result = self._remove_fillers(result)

        # Step 2: Clean up spacing and punctuation
        result = self._clean_spacing(result)

        # Step 3: Auto-capitalize
        if self.auto_capitalize:
            result = self._capitalize(result)

        # Step 4: Ensure ending punctuation
        if self.auto_punctuation:
            result = self._ensure_ending_punctuation(result)

        if result != original:
            logger.debug(f"Cleaned: '{original[:50]}' → '{result[:50]}'")

        return result

    def _remove_fillers(self, text: str) -> str:
        """Remove filler words from text."""
        return FILLER_PATTERN.sub(' ', text)

    def _clean_spacing(self, text: str) -> str:
        """Fix spacing issues."""
        text = MULTI_SPACE.sub(' ', text)
        text = MULTI_PERIOD.sub('.', text)
        text = SPACE_BEFORE_PUNCT.sub(r'\1', text)
        return text.strip()

    def _capitalize(self, text: str) -> str:
        """Capitalize first letter and after sentence-ending punctuation."""
        if not text:
            return text

        # Capitalize first character
        text = text[0].upper() + text[1:] if len(text) > 1 else text.upper()

        # Capitalize after . ! ?
        result = re.sub(
            r'([.!?]\s+)([a-zà-ÿ])',
            lambda m: m.group(1) + m.group(2).upper(),
            text,
        )
        return result

    def _ensure_ending_punctuation(self, text: str) -> str:
        """Add a period at the end if no ending punctuation exists."""
        if text and text[-1] not in '.!?':
            text += '.'
        return text
