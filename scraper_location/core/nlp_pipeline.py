from transformers import pipeline, AutoModelForTokenClassification, AutoTokenizer

class NLPPipeline:
    def __init__(self):
        self.ner_pipeline = self._create_ner_pipeline()
        self.pos_pipeline = self._create_pos_pipeline()

    def _create_ner_pipeline(self):
        model_name = "apwic/nerugm-base-4"
        return pipeline(
            "ner",
            model=AutoModelForTokenClassification.from_pretrained(model_name),
            tokenizer=AutoTokenizer.from_pretrained(model_name),
            aggregation_strategy="simple",
            device=-1
        )

    def _create_pos_pipeline(self):
        model_name = "wietsedv/xlm-roberta-base-ft-udpos28-id"
        return pipeline(
            "ner",
            model=AutoModelForTokenClassification.from_pretrained(model_name),
            tokenizer=AutoTokenizer.from_pretrained(model_name),
            aggregation_strategy="simple",
            device=-1
        )

    def extract_ner(self, text: str):
        """Return grouped NER entities."""
        entities = self.ner_pipeline(text)
        grouped = []
        current = None
        for ent in entities:
            word = ent["word"].lstrip("▁")
            if current and ent["entity_group"] == current["entity"]:
                current["text"] += word
            else:
                if current:
                    grouped.append(current)
                current = {"entity": ent["entity_group"], "text": word}
        if current:
            grouped.append(current)
        return grouped

    def extract_pos(self, text: str):
        """Return raw POS tagging results."""
        return [
            {"word": r["word"], "tag": r["entity_group"]}
            for r in self.pos_pipeline(text)
        ]
