This repository contains the supplementary materials to the paper on neural machine translation for the Erzya language. 

В этом репозитории содержатся материалы к статье по нейросетевому машинному переводу для эрзянского языка.

# Deliverables
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


# License
<a rel="license" href="http://creativecommons.org/licenses/by-sa/4.0/"><img alt="Creative Commons License" style="border-width:0" src="https://i.creativecommons.org/l/by-sa/4.0/88x31.png" /></a><br />This work is licensed under a <a rel="license" href="http://creativecommons.org/licenses/by-sa/4.0/">Creative Commons Attribution-ShareAlike 4.0 International License</a>.
