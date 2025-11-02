import logging
from pathlib import Path
from typing import Optional, List
import os
import torch
from transformers import AutoTokenizer, AutoModel
from app.core import settings

logger = logging.getLogger(__name__)

os.environ['FLASH_ATTENTION_SKIP_TORCH_CHECK'] = '1'


class OCRService:
    def __init__(self):
        self.device = settings.DEVICE if torch.cuda.is_available() else "cpu"
        self.tokenizer = None
        self.model = None
        self._model_loaded = False
        self._load_attempted = False

    def _load_model(self):
        if self._load_attempted:
            return
        self._load_attempted = True
        logger.info(f"Loading DeepSeek-OCR model on device: {self.device}")
        try:
            self.tokenizer = AutoTokenizer.from_pretrained(
                settings.OCR_MODEL,
                cache_dir=str(settings.MODELS_CACHE_DIR),
                trust_remote_code=True
            )
            try:
                self.model = AutoModel.from_pretrained(
                    settings.OCR_MODEL,
                    cache_dir=str(settings.MODELS_CACHE_DIR),
                    torch_dtype=torch.bfloat16,
                    device_map=self.device,
                    trust_remote_code=True,
                    _attn_implementation='flash_attention_2'
                )
                logger.info("DeepSeek-OCR model loaded with flash_attention_2")
            except (ImportError, ValueError) as flash_err:
                logger.warning(f"Flash-attention not available: {flash_err}. Falling back to eager attention.")
                self.model = AutoModel.from_pretrained(
                    settings.OCR_MODEL,
                    cache_dir=str(settings.MODELS_CACHE_DIR),
                    torch_dtype=torch.bfloat16,
                    device_map=self.device,
                    trust_remote_code=True,
                    attn_implementation='eager'
                )
                logger.info("DeepSeek-OCR model loaded with eager attention")

            self.model = self.model.eval()
            self._model_loaded = True
            logger.info("DeepSeek-OCR model loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load DeepSeek-OCR model: {e}", exc_info=True)
            self._model_loaded = False

    def extract_text_from_image(self, image_path: str) -> str:
        try:
            if not self._model_loaded:
                self._load_model()

            if not self._model_loaded:
                raise RuntimeError("DeepSeek-OCR model failed to load. OCR functionality is unavailable.")

            if not torch.cuda.is_available():
                raise RuntimeError(
                    "DeepSeek-OCR requires CUDA/GPU to run. CPU inference is not supported. "
                    "Please run the application on a machine with NVIDIA GPU support."
                )

            prompt = "<image>\nFree OCR."

            result = self.model.infer(
                self.tokenizer,
                prompt=prompt,
                image_file=image_path,
                output_path=None,
                base_size=1024,
                image_size=640,
                crop_mode=True,
                save_results=False
            )

            text = result if isinstance(result, str) else str(result)
            text = text.strip()

            logger.info(f"Extracted text from {image_path}: {len(text)} characters")
            return text
        except Exception as e:
            logger.error(f"Failed to extract text from image {image_path}: {e}", exc_info=True)
            raise

    def extract_text_from_pdf(self, pdf_path: str) -> str:
        try:
            import pdf2image
            pages = pdf2image.convert_from_path(pdf_path)

            all_text = []
            for page_num, page in enumerate(pages):
                temp_image_path = f"/tmp/page_{page_num}.png"
                page.save(temp_image_path, "PNG")
                text = self.extract_text_from_image(temp_image_path)
                all_text.append(text)
                Path(temp_image_path).unlink()

            combined_text = "\n".join(all_text)
            logger.info(f"Extracted text from PDF {pdf_path}: {len(combined_text)} characters")
            return combined_text
        except ImportError:
            logger.error("pdf2image not installed. Install with: pip install pdf2image poppler-utils")
            raise
        except Exception as e:
            logger.error(f"Failed to extract text from PDF {pdf_path}: {e}")
            raise

    def extract_text(self, file_path: str, original_filename: str = None) -> str:
        if original_filename:
            file_ext = Path(original_filename).suffix.lower()
        else:
            file_ext = Path(file_path).suffix.lower()

        if file_ext in [".png", ".jpg", ".jpeg", ".bmp", ".gif"]:
            return self.extract_text_from_image(file_path)
        elif file_ext == ".pdf":
            return self.extract_text_from_pdf(file_path)
        else:
            raise ValueError(f"Unsupported file format: {file_ext}")

    def process_document(self, file_path: str, original_filename: str = None) -> dict:
        try:
            text = self.extract_text(file_path, original_filename)
            return {
                "success": True,
                "text": text,
                "file_path": file_path,
                "num_characters": len(text)
            }
        except Exception as e:
            logger.error(f"Failed to process document {file_path}: {e}")
            return {
                "success": False,
                "error": str(e),
                "file_path": file_path
            }


ocr_service = OCRService()
