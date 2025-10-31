"""
Summary Model Service

Provides AI functionality for summarizing medical reports:
- Loads pretrained HuggingFace/BioBERT model
- Generates summaries with max token limits
- Supports batch summarization
- Integrates logging and exception handling
"""

from typing import List, Optional
import torch
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
from app.utils.logger import log_info, log_debug, log_error, log_exceptions
from app.config import settings

# --------------------------
# SummaryModelService Class
# --------------------------
class SummaryModelService:
    def __init__(self, model_name: str = None, device: str = None, max_tokens: int = None):
        self.model_name = model_name or str(settings.summary_model_path)
        self.device = device or settings.device
        self.max_tokens = max_tokens or settings.summary_max_tokens

        self.tokenizer = None
        self.model = None
        self._load_model()

    @log_exceptions
    def _load_model(self):
        """Load pretrained summarization model and tokenizer"""
        try:
            self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
            self.model = AutoModelForSeq2SeqLM.from_pretrained(self.model_name).to(self.device)
            log_info("Summary model loaded successfully", model_name=self.model_name, device=self.device)
        except Exception as e:
            log_error("Failed to load summary model", exc=e)
            raise RuntimeError(f"Could not load summary model from {self.model_name}") from e

    @log_exceptions
    def summarize(self, report_text: str) -> str:
        """
        Generate a summary for a single report.

        Args:
            report_text (str): Raw report text

        Returns:
            str: Generated summary
        """
        if not report_text:
            return ""

        # Tokenize input
        inputs = self.tokenizer(report_text, return_tensors="pt", truncation=True, padding=True, max_length=2048).to(self.device)
        log_debug("Report tokenized", input_ids_shape=inputs["input_ids"].shape)

        # Generate summary
        with torch.no_grad():
            summary_ids = self.model.generate(
                inputs["input_ids"],
                max_length=self.max_tokens,
                num_beams=4,
                early_stopping=True
            )
        summary_text = self.tokenizer.decode(summary_ids[0], skip_special_tokens=True)
        log_info("Report summarized", summary=summary_text[:100]+"..." if len(summary_text)>100 else summary_text)
        return summary_text
# --------------------------
# Batch summarization
# --------------------------
from app.utils.postprocess import format_summary_output

class SummaryModelService(SummaryModelService):  # Extending the previous class
    @log_exceptions
    def summarize_batch(
        self,
        report_texts: List[str],
        max_tokens: Optional[int] = None
    ) -> List[str]:
        """
        Generate summaries for a batch of reports.

        Args:
            report_texts (List[str]): List of raw report texts
            max_tokens (Optional[int]): Maximum tokens per summary

        Returns:
            List[str]: List of generated summaries
        """
        summaries = []
        for report in report_texts:
            summary = self.summarize(report)
            # Format and truncate if needed
            summary = format_summary_output(summary, max_length=max_tokens or self.max_tokens)
            summaries.append(summary)
            log_debug("Batch report summarized", report_preview=report[:50], summary_preview=summary[:50])
        log_info("Batch summarization completed", batch_size=len(report_texts))
        return summaries

# --------------------------
# Factory function
# --------------------------
def get_summary_service(model_name: str = None, device: str = None, max_tokens: int = None) -> SummaryModelService:
    """
    Returns a ready-to-use SummaryModelService instance.
    """
    return SummaryModelService(model_name=model_name, device=device, max_tokens=max_tokens)
