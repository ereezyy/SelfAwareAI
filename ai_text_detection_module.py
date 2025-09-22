# ai_text_detection_module.py

import logging
from transformers import AutoModelForSequenceClassification, AutoTokenizer, pipeline
import torch
import os

# --- Logger Setup ---
# Create logs directory in current working directory for cross-platform compatibility
LOGS_DIR = os.path.join(os.getcwd(), "logs")
os.makedirs(LOGS_DIR, exist_ok=True)
LOG_FILE_AID = os.path.join(LOGS_DIR, "bot_ai_detection.log")

def setup_logger_aid(name, log_file, level=logging.INFO):
    formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(module)s - %(funcName)s - %(message)s")
    file_handler = logging.FileHandler(log_file)
    file_handler.setFormatter(formatter)
    logger = logging.getLogger(name)
    logger.setLevel(level)
    if not logger.handlers:
        logger.addHandler(file_handler)
    return logger

aid_logger = setup_logger_aid("AITextDetectionLogger", LOG_FILE_AID)

class AITextDetector:
    def __init__(self, model_name="AICodexLab/answerdotai-ModernBERT-base-ai-detector"):
        self.logger = aid_logger
        self.device = 0 if torch.cuda.is_available() else -1 # pipeline expects device as int (GPU index or -1 for CPU)
        self.logger.info(f"Using device: {"GPU" if self.device == 0 else "CPU"}")
        self.model_name = model_name
        self.classifier = None
        try:
            # Load model and tokenizer using pipeline for simplicity
            self.classifier = pipeline("text-classification", model=self.model_name, tokenizer=self.model_name, device=self.device)
            self.logger.info(f"AITextDetector initialized with model: {self.model_name}")
        except Exception as e:
            self.logger.error(f"Failed to load AI text detection model or tokenizer {self.model_name}: {e}")
            # self.classifier will remain None, handled in detect_text
            raise

    def detect_text(self, text):
        """
        Detects if the input text is AI-generated or human-written.
        Args:
            text (str): The text to analyze.
        Returns:
            dict: A dictionary containing the classification label and score, or an error message string.
                  Example: {"label": "AI", "score": 0.98}
                           {"label": "Human", "score": 0.75}
        """
        if not self.classifier:
            self.logger.error("AI text detection classifier not initialized.")
            return {"error": "AI text detection model not available."}

        self.logger.info(f"Detecting AI text (first 100 chars): {text[:100]!r}...")
        try:
            result = self.classifier(text)
            # The model returns a list of dictionaries, e.g., [{"label": "HUMAN", "score": 0.8}]
            if result and len(result) > 0:
                prediction = result[0]
                label = prediction.get("label", "Unknown")
                score = prediction.get("score", 0.0)
                
                # Normalize labels and create response
                if label.upper() == "HUMAN":
                    return {
                        "Human": score,
                        "AI": 1.0 - score,
                        "warning": "Note: This AI detection model may exhibit a tendency to classify human-written text as AI-generated. Interpret results with caution."
                    }
                else:  # Assume AI/Generated
                    return {
                        "Human": 1.0 - score,
                        "AI": score,
                        "warning": "Note: This AI detection model may exhibit a tendency to classify human-written text as AI-generated. Interpret results with caution."
                    }
            else:
                return {"error": "No prediction returned from model"}
                
        except Exception as e:
            self.logger.error(f"Error during AI text detection: {e}")
            return {"error": f"Error during AI text detection: {e}"}

    def detect_ai_text(self, text):
        """Legacy method name for compatibility"""
        return self.detect_text(text)

# --- Example Usage (for testing this module directly) ---
if __name__ == "__main__":
    print("Initializing AITextDetector for testing...")
    try:
        detector = AITextDetector()
        print("AITextDetector initialized.")

        human_text_example = "I went to the park yesterday and saw a dog playing fetch. It was a sunny day."
        ai_text_example = "The fine-tuning can reduce the amount of expensive computing power and labeled data required to obtain large models adapted for niche use cases and business needs by using prior model training through transfer learning."
        short_human_text = "This is a test."

        texts_to_detect = [
            ("Known Human Text", human_text_example),
            ("Known AI-Paraphrased Text", ai_text_example),
            ("Short Human Text (potential misclassification)", short_human_text)
        ]

        for description, text in texts_to_detect:
            print(f"\n--- Detecting: {description} ---")
            print(f"Original Text: {text}")
            detection_result = detector.detect_ai_text(text)
            print(f"Detection Result: {detection_result}")
    
    except Exception as e:
        print(f"Error during AITextDetector example: {e}")
        aid_logger.error(f"Error in AITextDetector __main__: {e}", exc_info=True)

    print(f"\nLog file for AI Text Detection: {LOG_FILE_AID}")
    print("Test finished.")