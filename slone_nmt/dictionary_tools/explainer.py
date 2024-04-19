import json
import re
from collections import Counter, defaultdict
from dataclasses import dataclass
from functools import lru_cache
from typing import Callable, Dict, List, Optional, Set, Tuple

import pymorphy2
from razdel import tokenize as razdel_tokenize
from tqdm.auto import tqdm
from uralicNLP import uralicApi

Lemma = Tuple[str, List[str]]


@dataclass
class ExplainedToken:
    text: str
    start: int
    stop: int
    lemmas: List[Lemma]
    # TODO: maybe, add some morphological info


def clean_word(word):
    # TODO: support the alphabets with extra characters
    return re.sub("[^а-яёa-z]", "", word.lower())


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


class Explainer:
    def __init__(
        self,
        src_lang: str,
        tgt_lang: str,
        dictionary: Dict[str, List[str]],
        tgt_freqs: Dict[str, float],
        lemmer: Optional[Callable] = None,
    ):
        self.src_lang = src_lang
        self.tgt_lang = tgt_lang
        self.dictionary = dictionary
        self.tgt_freqs = tgt_freqs
        if lemmer is None:
            lemmer = MultiLemmer()
        self.lemmer = lemmer

    def suggest_word_translations(
        self, word: str, max_n: int = 5, include_empty: bool = True
    ) -> List[Lemma]:
        results = []
        for lemma in sorted(set(self.lemmer(word, self.src_lang)).union({word})):
            tr_pairs = sorted(
                [
                    (self.tgt_freqs.get(tr, 0), tr)
                    for tr in self.dictionary.get(lemma, [])
                ],
                reverse=True,
            )
            total_freq = sum(n for n, w in tr_pairs)
            top_translations = [w for n, w in tr_pairs[:max_n]]
            results.append((total_freq, lemma, top_translations))
        return [
            (lemma, translations)
            for n, lemma, translations in sorted(results, reverse=True)
            if include_empty or len(translations) > 0
        ]

    def explain_text(
        self, text: str, include_empty: bool = False
    ) -> List[ExplainedToken]:
        results = [
            ExplainedToken(
                text=token.text,
                start=token.start,
                stop=token.stop,
                lemmas=self.suggest_word_translations(
                    token.text, include_empty=include_empty
                ),
            )
            for token in razdel_tokenize(text)
        ]
        return results

    def serialize(self) -> Dict:
        return {
            "src_lang": self.src_lang,
            "tgt_lang": self.tgt_lang,
            "dictionary": self.dictionary,
            "tgt_freqs": self.tgt_freqs,
        }

    def save_to_json(self, filename: str):
        data = self.serialize()
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=1)

    @classmethod
    def load_from_json(cls, filename: str, lemmer=None):
        with open(filename, "r") as f:
            data = json.load(f)
        return cls(
            src_lang=data["src_lang"],
            tgt_lang=data["tgt_lang"],
            dictionary=data["dictionary"],
            tgt_freqs=data["tgt_freqs"],
            lemmer=lemmer,
        )

    @classmethod
    def build_from_corpus(
        cls,
        src_lang: str,
        tgt_lang: str,
        word_pairs: List[Tuple[str, str]],
        target_corpus: List[str],
        lemmer=None,
    ):
        if lemmer is None:
            lemmer = MultiLemmer()
        # Step 1: build the dictionary
        target_set = set()
        raw_dictionary = defaultdict(set)
        for src_word, tgt_word in word_pairs:
            src_word, tgt_word = clean_word(src_word), clean_word(tgt_word)
            if src_word and tgt_word:
                target_set.add(tgt_word)
                raw_dictionary[src_word].add(tgt_word)

        # Step 2: build word frequency of target words in the corpus
        target_freqs = Counter()
        for text in tqdm(target_corpus):
            for token in razdel_tokenize(text):
                word = token.text
                lemmas = (
                    set(lemmer(word, tgt_lang)).union({word}).intersection(target_set)
                )
                for lemma in lemmas:
                    target_freqs[lemma] += 1 / len(lemmas)

        return cls(
            src_lang=src_lang,
            tgt_lang=tgt_lang,
            dictionary={w: sorted(tr) for w, tr in raw_dictionary.items()},
            tgt_freqs={k: v for k, v in target_freqs.most_common()},
            lemmer=lemmer,
        )
