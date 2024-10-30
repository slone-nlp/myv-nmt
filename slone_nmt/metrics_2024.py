from typing import List, Tuple

import editdistance
import numpy as np
import pandas as pd
import torch
from tqdm.auto import tqdm, trange
from transformers import AutoModel, AutoModelForSeq2SeqLM, AutoTokenizer, NllbTokenizer
from transformers.models.m2m_100.modeling_m2m_100 import shift_tokens_right

from slone_nmt.dictionary_tools.explainer import Explainer, MultiLemmer
from slone_nmt.document_alignment import embed
from slone_nmt.nllb_preprocessing import preproc


def len_ratio(x: str, y: str) -> float:
    """Compute shortest-to-longest ratio of two strings"""
    return min(len(x), len(y)) / max(len(x), len(y), 1)


def rel_sim(text1: str, text2: str) -> float:
    """Compute superficial similarity of two strings as their edit distance divided by length and subtracted from 1."""
    return 1 - editdistance.eval(text1, text2) / max(len(text1), len(text2), 1)


class LabseScorer:
    """A scorer that computes LaBSE cosine similarity between sentence pairs."""

    def __init__(self, model_name_or_path="slone/LaBSE-en-ru-myv-v2"):
        self.tokenizer = AutoTokenizer.from_pretrained(model_name_or_path)
        self.model = AutoModel.from_pretrained(model_name_or_path)
        if torch.cuda.is_available():
            self.model.cuda()

    def score_pairs(self, src_sents: List[str], tgt_sents: List[str]) -> np.ndarray:
        src_embs = embed(
            src_sents, self.model, self.tokenizer, batch_size=16, progress=True
        )
        tgt_embs = embed(
            tgt_sents, self.model, self.tokenizer, batch_size=16, progress=True
        )
        sims = (src_embs * tgt_embs).sum(-1)
        return sims


class NllbScorer:
    def __init__(self, model_name_or_path="slone/nllb-with-myv-v2024"):
        self.tokenizer = NllbTokenizer.from_pretrained(model_name_or_path)
        self.model = AutoModelForSeq2SeqLM.from_pretrained(model_name_or_path)
        if torch.cuda.is_available():
            self.model.cuda()

    def score_pairs(
        self, src_sents: List[str], tgt_sents: List[str], src_lang: str, tgt_lang: str
    ) -> pd.DataFrame:
        src_embs_nllb, tgt_losses, tgt_tokens, tgt_cross_attentions_all = (
            self.apply_model(src_sents, tgt_sents, src_lang, tgt_lang)
        )
        tgt_embs_nllb, src_losses, src_tokens, src_cross_attentions_all = (
            self.apply_model(tgt_sents, src_sents, tgt_lang, src_lang)
        )

        df = pd.DataFrame(
            dict(
                src_loss=[x[1:].mean() for x in src_losses],
                tgt_loss=[x[1:].mean() for x in tgt_losses],
                nllb_enc_sim=(
                    np.concatenate(tgt_embs_nllb) * np.concatenate(src_embs_nllb)
                ).sum(-1),
                t2s_att_sum_mean=[
                    x.mean(0).mean(0)[:, 1:-1].sum(0).mean()
                    for x in src_cross_attentions_all
                ],
                s2t_att_sum_mean=[
                    x.mean(0).mean(0)[:, 1:-1].sum(0).mean()
                    for x in tgt_cross_attentions_all
                ],
            )
        )
        return df

    def apply_model(
        self, src_sents: List[str], tgt_sents: List[str], src_lang: str, tgt_lang: str
    ):
        src_embs_nllb = []
        tgt_losses = []
        tgt_tokens = []
        tgt_cross_attentions_all = []
        loss_fct = torch.nn.CrossEntropyLoss(reduction="none")
        for i in trange(len(src_sents)):
            src = preproc(src_sents[i])
            tgt = preproc(tgt_sents[i])
            self.tokenizer.src_lang = src_lang
            sbatch = self.tokenizer(src, return_tensors="pt").to(self.model.device)
            self.tokenizer.src_lang = tgt_lang
            tbatch = self.tokenizer(tgt, return_tensors="pt").to(self.model.device)
            with torch.inference_mode():
                dii = shift_tokens_right(
                    tbatch.input_ids,
                    self.model.config.pad_token_id,
                    self.model.config.decoder_start_token_id,
                )
                out = self.model(
                    **sbatch, decoder_input_ids=dii, output_attentions=True
                )
                labels = tbatch.input_ids

                lm_loss = (
                    loss_fct(
                        out.logits.view(-1, self.model.config.vocab_size),
                        labels.view(-1),
                    )
                    .cpu()
                    .numpy()
                )
                tgt_losses.append(lm_loss)
                tgt_tokens.append(self.tokenizer.convert_ids_to_tokens(labels[0]))
                tgt_cross_attentions_all.append(
                    torch.concat(out.cross_attentions).cpu().numpy()
                )
                src_embs_nllb.append(
                    torch.nn.functional.normalize(out.encoder_last_hidden_state.sum(1))
                    .cpu()
                    .numpy()
                )
        return src_embs_nllb, tgt_losses, tgt_tokens, tgt_cross_attentions_all


def _get_word_recall(srce, tgte, verbose=False):
    src2cand = {}
    for tok in srce:
        src2cand[tok.text] = tok.text
        src2cand[tok.text.lower()] = tok.text
        for lemma in tok.lemmas:
            src2cand[lemma["lemma"]] = tok.text
            for tr in lemma["translations"]:
                src2cand[tr] = tok.text
    src_bag = set(src2cand.keys())
    results = []
    for tok in tgte:
        candidates = {lemma["lemma"] for lemma in tok.lemmas}.union(
            {tok.text, tok.text.lower()}
        )
        found = candidates.intersection(src_bag)
        if verbose:
            print(tok.text, {src2cand[w] for w in found})
        results.append(int(bool(found)))
    return np.mean(results)


class WordExplainerScorer:
    def __init__(self, src_explainer_path: str, tgt_explainer_path: str):
        self.lemmer = MultiLemmer()
        self.src_explainer = Explainer.load_from_json(
            src_explainer_path, lemmer=self.lemmer
        )
        self.tgt_explainer = Explainer.load_from_json(
            tgt_explainer_path, lemmer=self.lemmer
        )

    def score_pairs(self, src_sents: List[str], tgt_sents: List[str]) -> pd.DataFrame:
        src_word_rec = []
        tgt_word_rec = []
        for src, tgt in tqdm(zip(src_sents, tgt_sents), total=len(src_sents)):
            src_exp = self.src_explainer.explain_text(src, include_empty=True)
            tgt_exp = self.tgt_explainer.explain_text(tgt, include_empty=True)
            src_word_rec.append(_get_word_recall(tgt_exp, src_exp, verbose=False))
            tgt_word_rec.append(_get_word_recall(src_exp, tgt_exp, verbose=False))
        df = pd.DataFrame(
            dict(
                src_word_rec=src_word_rec,
                tgt_word_rec=tgt_word_rec,
            )
        )
        return df
