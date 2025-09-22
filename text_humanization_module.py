# text_humanization_module.py

import logging
import torch
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
import os

# --- Logger Setup ---
# Create logs directory in current working directory for cross-platform compatibility
LOGS_DIR = os.path.join(os.getcwd(), "logs")
os.makedirs(LOGS_DIR, exist_ok=True)
LOG_FILE_TH = os.path.join(LOGS_DIR, "bot_text_humanization.log")

def setup_logger_th(name, log_file, level=logging.INFO):
    formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(module)s - %(funcName)s - %(message)s")
    file_handler = logging.FileHandler(log_file)
    file_handler.setFormatter(formatter)
    logger = logging.getLogger(name)
    logger.setLevel(level)
    if not logger.handlers:
        logger.addHandler(file_handler)
    return logger

th_logger = setup_logger_th("TextHumanizationLogger", LOG_FILE_TH)

class TextHumanizer:
    def __init__(self, model_name="Ateeqq/Text-Rewriter-Paraphraser"):
        self.logger = th_logger
        self.model_name = model_name
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.logger.info(f"Using device: {self.device}")
        self.tokenizer = None
        self.model = None
        try:
            self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
            self.model = AutoModelForSeq2SeqLM.from_pretrained(self.model_name).to(self.device)
            self.logger.info(f"TextHumanizer initialized with model: {self.model_name}")
        except Exception as e:
            self.logger.error(f"Failed to load model or tokenizer {self.model_name}: {e}", exc_info=True)
            # Allow initialization to complete, but humanize_text will fail gracefully
            raise # Re-raise to signal failure to initialize properly

    def humanize_text(self, text: str, num_beams: int = 4, num_beam_groups: int = 4, num_return_sequences: int = 1, repetition_penalty: float = 10.0, diversity_penalty: float = 3.0, no_repeat_ngram_size: int = 2, temperature: float = 0.8, max_length: int = 128):
        """
        Paraphrases the input text to make it sound more human-like.
        Args:
            text (str): The text to humanize.
            num_beams (int): Number of beams for beam search.
            num_beam_groups (int): Number of groups for diverse beam search.
            num_return_sequences (int): Number of paraphrased sequences to return.
            repetition_penalty (float): Penalty for repetition.
            diversity_penalty (float): Penalty for diversity.
            no_repeat_ngram_size (int): Size of n-grams that cannot be repeated.
            temperature (float): Sampling temperature.
            max_length (int): Maximum length of the generated sequence.
        Returns:
            list[str]: A list of humanized text variations, or an error message string in a list.
        """
        if not self.model or not self.tokenizer:
            self.logger.error("TextHumanizer model/tokenizer not loaded.")
            return ["Error: TextHumanizer model not available."]

        self.logger.info(f"Humanizing text (first 100 chars): {text[:100]!r} with params: num_beams={num_beams}, temp={temperature}, max_len={max_length}")
        try:
            prefix = "paraphraser: " # As per model card
            input_text = f"{prefix}{text}"
            
            input_ids = self.tokenizer(
                input_text, 
                return_tensors="pt", 
                padding="longest", 
                truncation=True, 
                max_length=max_length # Max input length, model card uses 64, but let's make it configurable
            ).input_ids.to(self.device)
            
            outputs = self.model.generate(
                input_ids,
                num_beams=num_beams,
                num_beam_groups=num_beam_groups,
                num_return_sequences=num_return_sequences,
                repetition_penalty=repetition_penalty,
                diversity_penalty=diversity_penalty,
                no_repeat_ngram_size=no_repeat_ngram_size,
                temperature=temperature,
                max_length=max_length # Max output length
            )
            
            decoded_outputs = self.tokenizer.batch_decode(outputs, skip_special_tokens=True)
            self.logger.info(f"Generated {len(decoded_outputs)} humanized versions.")
            return decoded_outputs
        except Exception as e:
            self.logger.exception(f"Error during text humanization: {e}")
            return [f"Error during text humanization: {e}"]

# --- Example Usage (for testing this module directly) ---
if __name__ == "__main__":
    print("Initializing TextHumanizer for testing...")
    try:
        humanizer = TextHumanizer()
        print("TextHumanizer initialized.")

        sample_text_1 = "By leveraging prior model training through transfer learning, fine-tuning can reduce the amount of expensive computing power and labeled data needed to obtain large models tailored to niche use cases and business needs."
        sample_text_2 = "The cat sat on the mat. It was a fluffy cat. The mat was blue."
        
        texts_to_humanize = [
            ("Technical Sentence", sample_text_1),
            ("Simple Sentence", sample_text_2)
        ]

        for description, text in texts_to_humanize:
            print(f"\n--- Humanizing: {description} ---")
            print(f"Original Text: {text}")
            # Using fewer return sequences for brevity in test output
            humanized_versions = humanizer.humanize_text(text, num_return_sequences=2, max_length=128) 
            if humanized_versions and humanized_versions[0].startswith("Error:"):
                print(f"Humanization failed: {humanized_versions[0]}")
            else:
                for i, h_text in enumerate(humanized_versions):
                    print(f"Humanized Version {i+1}: {h_text}")
    
    except Exception as e:
        print(f"Error during TextHumanizer example: {e}")
        th_logger.error(f"Error in TextHumanizer __main__: {e}", exc_info=True)

    print(f"\nLog file for Text Humanization: {LOG_FILE_TH}")
    print("Test finished.")

