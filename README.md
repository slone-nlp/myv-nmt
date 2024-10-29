# Machine translation for Erzya (and other lower-resourced languages)
This repository contains materials for a couple of papers about Erzya machine translation, and a tool `slone_nmt` for reproducing some of their results.

Этот репозиторий содержит материалы для нескольких статей об эрзянском машинном переводе и инструмент `slone_nmt` для воспроизведения некоторых из их результатов.

Те репозиториесь кирди эрзянь машинной ютавксонь коряс зярыя сёрмадовкстнэнь туртов материалтнэнь ды зярыя результаттнэнь одс тееманть туртов `slone_nmt` инструментэсь.

## The first neural machine translation system for the Erzya language
This section contains the supplementary materials to the paper [The first neural machine translation system for the Erzya language](https://arxiv.org/abs/2209.09368) 
by David Dale (2022). 

> We present the first neural machine translation system for translation between the endangered Erzya language and Russian and the dataset collected by us to train and evaluate it. 
The BLEU scores are 17 and 19 for translation to Erzya and Russian respectively, and more than half of the translations are rated as acceptable by native speakers. 
We also adapt our model to translate between Erzya and 10 other languages, but without additional parallel data, the quality on these directions remains low.
We release the translation models along with the collected text corpus, a new language identification model, and a multilingual sentence encoder adapted for the Erzya language.
These resources will be available at https://github.com/slone-nlp/myv-nmt.",


### Deliverables
These delivarables are released as supplementary materials to the paper:
- Demo translation app: https://huggingface.co/spaces/slone/myv-translation-2022-demo
- Dirty code for the paper: in the folder `dirty-code-2022`.
    - The code is *really dirty*, because it is contained in the notebooks 
        that depend on missing directories 
        and sometimes have non-direct order of execution.
    - It is intended not for full reproducibility, but just for demonstrating 
    the implementation of some ideas mentioned in the paper.   
- More reproducible code: will be added later.
- Test and dev datasets for translation between `myv` and `ru,en,fi`: in the folder `test_data`.
- The collected myv-ru parallel corpus: https://huggingface.co/datasets/slone/myv_ru_2022
- Language identification model (fastText): https://huggingface.co/slone/fastText-LID-323
- Erzya sentence encoder: https://huggingface.co/slone/LaBSE-en-ru-myv-v1
- The model for translation from 11 languages to Erzya: https://huggingface.co/slone/LaBSE-en-ru-myv-v1
- The model for translation from Erzya to 11 languages: https://huggingface.co/slone/mbart-large-51-myv-mul-v1

### Citation
```bib
@inproceedings{dale-2022-first,
    title = "The first neural machine translation system for the {E}rzya language",
    author = "Dale, David",
    editor = "Serikov, Oleg and Voloshina, Ekaterina and Postnikova, Anna and Klyachko, Elena and Neminova, Ekaterina  and Vylomova, Ekaterina  and Shavrina, Tatiana  and Ferrand, Eric Le  and Malykh, Valentin  and Tyers, Francis  and Arkhangelskiy, Timofey  and Mikhailov, Vladislav  and Fenogenova, Alena",
    booktitle = "Proceedings of the first workshop on NLP applications to field linguistics",
    month = oct,
    year = "2022",
    address = "Gyeongju, Republic of Korea",
    publisher = "International Conference on Computational Linguistics",
    url = "https://aclanthology.org/2022.fieldmatters-1.6",
    pages = "45--53",
    abstract = "We present the first neural machine translation system for translation between the endangered Erzya language and Russian and the dataset collected by us to train and evaluate it. The BLEU scores are 17 and 19 for translation to Erzya and Russian respectively, and more than half of the translations are rated as acceptable by native speakers. We also adapt our model to translate between Erzya and 10 other languages, but without additional parallel data, the quality on these directions remains low. We release the translation models along with the collected text corpus, a new language identification model, and a multilingual sentence encoder adapted for the Erzya language. These resources will be available at \url{https://github.com/slone-nlp/myv-nmt}.",
}
```

## FLORES+ Translation and Machine Translation Evaluation for the Erzya Language
This section contains the supplementary materials to the paper [FLORES+ Translation and Machine Translation Evaluation for the Erzya Language](https://www2.statmt.org/wmt24/pdf/2024.wmt-1.49.pdf) 
by Isai Gordeev, Sergey Kuldin and David Dale (2024).

> This paper introduces a translation of the FLORES+ dataset into the endangered Erzya language, 
with the goal of evaluating machine translation  between this language and any of the other 200 languages already included into FLORES+. 
This translation was carried out as a part of the Open Language Data shared task at WMT24. 
We also present a benchmark of existing translation models bases on this dataset 
and a new translation model that achieves the state-of-the-art quality of translation into Erzya from Russian and English.

### Deliverables
- Data:
    - [ ] FLORES+ in Erzya: to appear in https://github.com/openlanguagedata/flores and https://huggingface.co/datasets/openlanguagedata/flores_plus.
    - [ ] Held-out Russian-Erzya dataset, annotated for accuracy and fluency: TBD
- Models:
    - [x] Translation model: [NLLB-with-myv-v2024](https://huggingface.co/slone/nllb-with-myv-v2024) on HF
    - [x] LaBSE with Erzya support: [LaBSE-en-ru-myv-v2](https://huggingface.co/slone/LaBSE-en-ru-myv-v2) on HF.
- Code:
    - [ ] Training code for the translation model: TBD
    - [ ] Training code for the LaBSE model: 
    - [ ] Code for automatic translation quality metrics: TBD

## SLONE-NMT

SLONE-NMT is a Python package with some utilities for Erzya and for low-resource neural machine translation.

### Installation
To install its current version, please clone and install this repo:
```
git clone https://github.com/slone-nlp/myv-nmt
cd myv-nmt
pip install -e .
```
If you don't plan to edit the source code, you can also clone and install with a single command:
```
pip install git+https://github.com/slone-nlp/myv-nmt
```

### Usage

Here is an example of using the Erzya transliteration module:
```python
from slone_nmt.myv_translit import cyr2lat
print(cyr2lat("шумбрачи!"))
# šumbrači!
```

For more info, please read [slone_nmt/README.md](slone_nmt/README.md).


# License for the repository contents
<a rel="license" href="http://creativecommons.org/licenses/by-sa/4.0/"><img alt="Creative Commons License" style="border-width:0" src="https://i.creativecommons.org/l/by-sa/4.0/88x31.png" /></a><br />This work is licensed under a <a rel="license" href="http://creativecommons.org/licenses/by-sa/4.0/">Creative Commons Attribution-ShareAlike 4.0 International License</a>.
