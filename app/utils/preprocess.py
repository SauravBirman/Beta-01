import re
import numpy as np
import pandas as pd
from typing import Dict, Any, List, Tuple, Union
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.impute import SimpleImputer
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from sentence_transformers import SentenceTransformer
import torch
import logging

from app.utils.logger import get_logger
from PIL import Image
import cv2
from torchvision import transforms

from app.utils.image_preprocess import ImagePreprocessor  # ✅ NEW

logger = get_logger(__name__)


class TextPreprocessor:
    """
    Handles preprocessing for text-based data such as:
    - Doctor notes
    - Symptoms
    - Prescriptions
    Converts text to embeddings using a pretrained model.
    """

    def __init__(self, model_name: str = "sentence-transformers/all-MiniLM-L6-v2"):
        logger.info(f"Initializing TextPreprocessor with model: {model_name}")
        self.model = SentenceTransformer(model_name)
        self.stop_words = set(stopwords.words("english"))

    def clean_text(self, text: str) -> str:
        """
        Perform text normalization, removing punctuation, stopwords, and unnecessary symbols.
        """
        if not isinstance(text, str):
            logger.warning("Expected string input for text, got %s", type(text))
            return ""
        text = text.lower()
        text = re.sub(r"[^a-zA-Z0-9\s]", "", text)
        tokens = word_tokenize(text)
        filtered_tokens = [t for t in tokens if t not in self.stop_words]
        return " ".join(filtered_tokens)

    def encode_text(self, text: str) -> np.ndarray:
        """
        Convert cleaned text to embedding vector.
        """
        cleaned = self.clean_text(text)
        embedding = self.model.encode(cleaned)
        return np.array(embedding)

    def batch_encode(self, texts: List[str]) -> np.ndarray:
        """
        Encode a list of text entries.
        """
        cleaned_texts = [self.clean_text(t) for t in texts]
        embeddings = self.model.encode(cleaned_texts)
        return np.array(embeddings)


class NumericalPreprocessor:
    """
    Handles lab data, vitals, and other numerical input preprocessing.
    Includes missing value imputation and normalization.
    """

    def __init__(self):
        self.imputer = SimpleImputer(strategy="mean")
        self.scaler = StandardScaler()

    def fit_transform(self, data: pd.DataFrame) -> np.ndarray:
        """
        Fit and transform numerical data.
        """
        logger.info("Fitting numerical imputer and scaler")
        data_imputed = self.imputer.fit_transform(data)
        data_scaled = self.scaler.fit_transform(data_imputed)
        return data_scaled

    def transform(self, data: pd.DataFrame) -> np.ndarray:
        """
        Transform numerical data using existing fit.
        """
        data_imputed = self.imputer.transform(data)
        data_scaled = self.scaler.transform(data_imputed)
        return data_scaled


class CategoricalPreprocessor:
    """
    Handles categorical & lifestyle data preprocessing.
    """

    def __init__(self):
        self.encoder = OneHotEncoder(sparse_output=False, handle_unknown="ignore")

    def fit_transform(self, data: pd.DataFrame) -> np.ndarray:
        logger.info("Fitting categorical encoder")
        return self.encoder.fit_transform(data)

    def transform(self, data: pd.DataFrame) -> np.ndarray:
        return self.encoder.transform(data)


class TimeSeriesPreprocessor:
    """
    Handles preprocessing for time-series data (e.g., vitals over time).
    Windowing, normalization, and tensor conversion for LSTM/GRU models.
    """

    def __init__(self, window_size: int = 5):
        self.window_size = window_size
        self.scaler = StandardScaler()

    def create_windows(self, series: Union[List[float], np.ndarray]) -> np.ndarray:
        """
        Convert a single time-series into overlapping windows.
        """
        X = []
        for i in range(len(series) - self.window_size + 1):
            window = series[i:i + self.window_size]
            X.append(window)
        return np.array(X)

    def preprocess(self, series: Union[List[float], np.ndarray]) -> torch.Tensor:
        """
        Full pipeline: scale → window → convert to tensor.
        """
        series = np.array(series).reshape(-1, 1)
        scaled = self.scaler.fit_transform(series).flatten()
        windows = self.create_windows(scaled)
        return torch.tensor(windows, dtype=torch.float32)

class HistoryContextPreprocessor:
    """
    Summarizes patient history, previous reports, and treatments into a contextual embedding.
    This helps models leverage longitudinal patient data for better prediction.
    """

    def __init__(self, model_name: str = "sentence-transformers/all-MiniLM-L6-v2"):
        logger.info("Initializing HistoryContextPreprocessor")
        self.model = SentenceTransformer(model_name)
        self.text_cleaner = TextPreprocessor(model_name)

    def summarize_history(self, records: List[str]) -> np.ndarray:
        """
        Combines multiple past entries (e.g., past diagnoses, prescriptions)
        into a single contextual embedding.
        """
        if not records:
            logger.warning("Empty patient history received.")
            return np.zeros(384)

        cleaned = [self.text_cleaner.clean_text(r) for r in records]
        embeddings = self.model.encode(cleaned)
        mean_embedding = np.mean(embeddings, axis=0)
        logger.info("Generated history context embedding of shape %s", mean_embedding.shape)
        return mean_embedding

class DataPreprocessor:
    """
    Unified preprocessor combining multiple preprocessing pipelines
    for multi-modal patient data.
    """

    def __init__(self):
        self.text_processor = TextPreprocessor()
        self.num_processor = NumericalPreprocessor()
        self.cat_processor = CategoricalPreprocessor()
        self.ts_processor = TimeSeriesPreprocessor()
        self.image_processor = ImagePreprocessor()            # ✅ NEW
        self.history_processor = HistoryContextPreprocessor()  # ✅ NEW


    def preprocess_patient_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Expects a dictionary with possible keys:
            {
                "symptoms": str,
                "doctor_notes": str,
                "lab_results": pd.DataFrame,
                "vitals": pd.DataFrame,
                "lifestyle": pd.DataFrame,
                "time_series": list or np.ndarray
            }
        Returns preprocessed dictionary with embeddings, normalized arrays, etc.
        """
        logger.info("Starting multi-modal preprocessing pipeline")
        processed = {}

        if "symptoms" in data:
            processed["symptoms_emb"] = self.text_processor.encode_text(data["symptoms"])

        if "doctor_notes" in data:
            processed["notes_emb"] = self.text_processor.encode_text(data["doctor_notes"])

        if "lab_results" in data:
            processed["lab_features"] = self.num_processor.fit_transform(data["lab_results"])

        if "vitals" in data:
            processed["vitals_features"] = self.num_processor.fit_transform(data["vitals"])

        if "lifestyle" in data:
            processed["lifestyle_features"] = self.cat_processor.fit_transform(data["lifestyle"])

        if "time_series" in data:
            processed["time_series_tensor"] = self.ts_processor.preprocess(data["time_series"])

        # ✅ NEW: Handle medical images
        if "images" in data and data["images"]:
            processed["image_features"] = self.image_processor.process_images(data["images"])

        # ✅ NEW: Handle patient history
        if "patient_history" in data and data["patient_history"]:
            processed["history_context"] = self.history_processor.summarize_history(data["patient_history"])

        logger.info("Preprocessing completed successfully with multimodal data")
        return processed
