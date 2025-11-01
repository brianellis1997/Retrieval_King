import logging
from pathlib import Path
from typing import Optional, List
import torch
from PIL import Image
from transformers import AutoProcessor, AutoModelForCausalLM
from app.core import settings

logger = logging.getLogger(__name__)


class OCRService:
    def __init__(self):
        self.device = settings.DEVICE if torch.cuda.is_available() else "cpu"
        self.processor = None
        self.model = None
        self._load_model()

    def _load_model(self):
        logger.info(f"Loading DeepSeek-OCR model on device: {self.device}")
        try:
            self.processor = AutoProcessor.from_pretrained(
                settings.OCR_MODEL,
                cache_dir=str(settings.MODELS_CACHE_DIR)
            )
            self.model = AutoModelForCausalLM.from_pretrained(
                settings.OCR_MODEL,
                cache_dir=str(settings.MODELS_CACHE_DIR),
                torch_dtype=torch.bfloat16,
                device_map=self.device,
                trust_remote_code=True
            )
            logger.info("DeepSeek-OCR model loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load DeepSeek-OCR model: {e}")
            raise

    def extract_text_from_image(self, image_path: str) -> str:
        try:
            image = Image.open(image_path).convert("RGB")

            inputs = self.processor(images=image, return_tensors="pt").to(self.device)

            with torch.no_grad():
                outputs = self.model.generate(
                    **inputs,
                    max_new_tokens=4096,
                    temperature=0.1
                )

            text = self.processor.decode(outputs[0], skip_special_tokens=True)
            logger.info(f"Extracted text from {image_path}: {len(text)} characters")
            return text
        except Exception as e:
            logger.error(f"Failed to extract text from image {image_path}: {e}")
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

    def extract_text(self, file_path: str) -> str:
        file_ext = Path(file_path).suffix.lower()

        if file_ext in [".png", ".jpg", ".jpeg", ".bmp", ".gif"]:
            return self.extract_text_from_image(file_path)
        elif file_ext == ".pdf":
            return self.extract_text_from_pdf(file_path)
        else:
            raise ValueError(f"Unsupported file format: {file_ext}")

    def process_document(self, file_path: str) -> dict:
        try:
            text = self.extract_text(file_path)
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
