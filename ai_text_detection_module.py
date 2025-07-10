# ai_text_detection_module.py

import logging
import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification
import torch.nn.functional as F # For softmax

# --- Logger Setup ---
LOG_FILE_AD = "/home/ubuntu/bot_ai_detection.log"

def setup_logger_ad(name, log_file, level=logging.INFO):
    formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(module)s - %(funcName)s - %(message)s")
    file_handler = logging.FileHandler(log_file)
    file_handler.setFormatter(formatter)
    logger = logging.getLogger(name)
    logger.setLevel(level)
    if not logger.handlers:
        logger.addHandler(file_handler)
    return logger

ad_logger = setup_logger_ad("AITextDetectionLogger", LOG_FILE_AD)

class AITextDetector:
    def __init__(self, model_name="AICodexLab/answerdotai-ModernBERT-base-ai-detector"):
        self.logger = ad_logger
        self.model_name = model_name
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.logger.info(f"Using device: {self.device}")
        self.tokenizer = None
        self.model = None
        try:
            self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
            self.model = AutoModelForSequenceClassification.from_pretrained(self.model_name).to(self.device)
            self.model.eval() # Set model to evaluation mode
            self.logger.info(f"AITextDetector initialized with model: {self.model_name}")
        except Exception as e:
            self.logger.error(f"Failed to load model or tokenizer {self.model_name}: {e}", exc_info=True)
            # Allow initialization to complete, but detect_ai_text will fail gracefully
            raise # Re-raise to signal failure to initialize properly

    def detect_ai_text(self, text: str):
        """
        Detects if the input text is AI-generated or human-written.
        Args:
            text (str): The text to analyze.
        Returns:
            dict: A dictionary containing probabilities for 'Human' and 'AI' labels,
                  and a warning message if applicable. Example:
                  {"Human": 0.1, "AI": 0.9, "warning": "Model may misclassify..."}
                  Returns an error dictionary if detection fails.
        """
        if not self.model or not self.tokenizer:
            self.logger.error("AITextDetector model/tokenizer not loaded.")
            return {"error": "AITextDetector model not available."}

        self.logger.info(f"Detecting AI text (first 100 chars): {text[:100]!r}")
        warning_message = ("Note: This AI detection model (AICodexLab/answerdotai-ModernBERT-base-ai-detector) "
                           "may exhibit a tendency to classify human-written text, especially shorter or less formal text, "
                           "as AI-generated with high confidence. Interpret results with caution.")
        try:
            inputs = self.tokenizer(text, return_tensors="pt", truncation=True, padding=True, max_length=512).to(self.device)
            
            with torch.no_grad(): # Disable gradient calculations for inference
                logits = self.model(**inputs).logits
            
            probabilities = F.softmax(logits, dim=-1).squeeze().tolist() # Get probabilities
            
            # Assuming the model has labels in the order: Human, AI (or similar)
            # This needs to be confirmed from the model card or by inspecting model.config.id2label
            # For AICodexLab/answerdotai-ModernBERT-base-ai-detector, label 0 is Human, label 1 is AI.
            # model.config.id2label = {0: "Human", 1: "AI"}
            
            results = {
                "Human": probabilities[0],
                "AI": probabilities[1],
                "warning": warning_message
            }
            self.logger.info(f"Detection results: {results}")
            return results
        except Exception as e:
            self.logger.exception(f"Error during AI text detection: {e}")
            return {"error": f"Error during AI text detection: {e}", "warning": warning_message}

# --- Example Usage (for testing this module directly) ---
if __name__ == "__main__":
    print("Initializing AITextDetector for testing...")
    try:
        detector = AITextDetector()
        print("AITextDetector initialized.")

        human_text_example = "I went to the park yesterday and saw a dog playing fetch. It was a sunny day."
        # This text is from the humanizer output, which the detector might flag as AI
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
        ad_logger.error(f"Error in AITextDetector __main__: {e}", exc_info=True)

    print(f"\nLog file for AI Text Detection: {LOG_FILE_AD}")
    print("Test finished.")