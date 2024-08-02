CONSTANT_INFER_PARAMS = {
    "sampling_framework": "arekit",
    "bert_framework": "opennre",
    "ner_framework": "deeppavlov",
    "collection_name": None,
    "backend": "d3js_graphs",
    "log_file": "arelight.log",
    "torch_num_workers": 0,
    "output_template": "output",
    "synonyms_filepath": None
}

CONSTANT_INFER_IGNORE_PARAMS = {"from_files", "d3js_label_names", "labels_fmt", "csv_sep", "csv_column"}

UI_INFER_PRESETS = {
    "russian": {
        "ner_model_name": "ner_ontonotes_bert_mult",
        "sentence_parser": "nltk:russian",
        "pretrained_bert": "DeepPavlov/rubert-base-cased",
        "bert_torch_checkpoint": "ra4-rsr1_DeepPavlov-rubert-base-cased_cls.pth.tar",
        "translate_framework": "googletrans",
        "translate_text": "auto:ru"
    }
}