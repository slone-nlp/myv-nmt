from functools import lru_cache
from typing import List, Set

import pymorphy2
from uralicNLP import uralicApi


class MultiLemmer:
    def __init__(self):
        self.pymorphy_analyzer = pymorphy2.MorphAnalyzer()

    @lru_cache(maxsize=100_000)
    def __call__(self, text: str, lang: str) -> List[str]:
        if lang == "rus":
            result = []
            for hyp in self.pymorphy_analyzer.parse(text):
                result.append(hyp.normal_form)
            return result
        return uralicApi.lemmatize(text, lang)
