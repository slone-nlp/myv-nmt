import logging
import pandas as pd
import typing as tp
import numpy as np

import torch
import razdel
from transformers import AutoTokenizer, AutoModel


logger = logging.getLogger(__name__)

def center_norm(v):
    v = v - v.mean(0)
    return v /  (v**2).sum(1, keepdims=True) ** 0.5


def center_dot(x, y):
    m = (x.sum(0) + y.sum(0)) / (x.shape[0] + y.shape[0])
    x = x - m
    y = y - m
    x =  x /  (x**2).sum(1, keepdims=True) ** 0.5
    y =  y /  (y**2).sum(1, keepdims=True) ** 0.5
    return np.dot(x, y.T)


def get_top_mean_by_row(x, k=5):
    m, n = x.shape
    k = min(k, n)
    topk_indices = np.argpartition(x, -k, axis=1)[:, -k:]
    rows, _ = np.indices((m, k))
    return x[rows, topk_indices].mean(1)


def embed(texts, model, tokenizer, max_length=512, batch_size=16) -> np.ndarray:
    """LaBSE-like sentence embeding"""
    if isinstance(texts, str):
        single = True
        texts = [texts]
    else:
        single = False
    result = []
    for i in range(0, len(texts), batch_size):
        batch = texts[i:i+batch_size]
        encoded_input = tokenizer(batch, padding=True, truncation=True, max_length=max_length, return_tensors='pt')
        with torch.inference_mode():
            model_output = model(**encoded_input.to(model.device))
            result.append(torch.nn.functional.normalize(model_output.pooler_output).cpu().numpy())
    embeddings = np.concatenate(result)
    if single:
        return embeddings[0]
    return embeddings


def align3(sims: np.ndarray) -> tp.List[tp.Tuple[int, int]]:
    """
    Given an array of similarity values, compute a strictly monotonic path (possibly with skips)
    with the maximal sum of similarities along the path.
    Skipping happens if the similaritie are negative, so they would otherwise decrease the total.
    """
    nrows, ncols = sims.shape

    rewards = np.zeros_like(sims)
    choices = np.zeros_like(sims).astype(int)  # 1: choose this pair, 2: decrease i, 3: decrease j

    for i in range(nrows):
        for j in range(ncols):
            # Option 1: align i to j
            score_add = sims[i, j]
            if i > 0 and j > 0:
                score_add += rewards[i - 1, j - 1]
                choices[i, j] = 1
            best = score_add
            # Option 2: skip i, align j to the best alignment before
            if i > 0 and rewards[i - 1, j] > best:
                best = rewards[i - 1, j]
                choices[i, j] = 2
            # Option 3: skip j, align i to the best alignment before
            if j > 0 and rewards[i, j - 1] > best:
                best = rewards[i, j - 1]
                choices[i, j] = 3
            rewards[i, j] = best

    # backtracking the optimal alignment
    alignment = []
    i = nrows - 1
    j = ncols - 1
    while i >= 0 and j >= 0:
        if choices[i, j] in {0, 1}:  # 0 occurs only in the pair of first sentences, if we are at it
            alignment.append((i, j))
            i -= 1
            j -= 1
        elif choices[i, j] == 2:
            i -= 1
        else:
            j -= 1
    return alignment[::-1]


def get_penalized_sims(
    src_sents, tgt_sents, src_embs, tgt_embs,
    rel_penalty=0.2,
    abs_penalty=0.2,
    cosine_power=1,
) -> tp.Tuple[np.ndarray, np.ndarray]:
    len_sims = np.array([[min(len(x), len(y)) / max(len(x), len(y)) for x in tgt_sents] for y in src_sents])
    sims = np.maximum(0, np.dot(src_embs, tgt_embs.T)) ** cosine_power * len_sims
    sims_rel = (sims.T - get_top_mean_by_row(sims) * rel_penalty).T - get_top_mean_by_row(sims.T) * rel_penalty - abs_penalty
    return sims, sims_rel


def align_docs(
    src_sents: tp.List[str],
    tgt_sents: tp.List[str],
    pair_ids: tp.List[tp.Tuple[int, int]],
    sims: np.ndarray,
    sims_rel: np.ndarray,
) -> pd.DataFrame:
    """ Align two documents into a single parallel document, possibly with gaps """
    doc_sents = []
    prev_i, prev_j = 0, 0
    for pair_i, pair_j in pair_ids + [(len(src_sents), len(tgt_sents))]:
        for i in range(prev_i, pair_i):
            doc_sents.append({'src_sent_id': i, 'src_sent': src_sents[i]})
        for j in range(prev_j, pair_j):
            doc_sents.append({'tgt_sent_id': j, 'tgt_sent': tgt_sents[j]})
        if pair_i >= len(src_sents):
            break
        doc_sents.append({
            'src_sent_id': pair_i, 'src_sent': src_sents[pair_i],
            'tgt_sent_id': pair_j, 'tgt_sent': tgt_sents[pair_j],
            'sim': sims[pair_i, pair_j],
            'sim_pnlz': sims_rel[pair_i, pair_j],
        })
        prev_i, prev_j = pair_i + 1, pair_j + 1

    doc_df = pd.DataFrame(doc_sents)
    return doc_df


class AlignmentPipeline:
    """ A class that exemplifies the usage of sentence alignment tools"""
    def __init__(self, model_name_or_path="slone/LaBSE-en-ru-myv-v2"):
        self.tokenizer = AutoTokenizer.from_pretrained(model_name_or_path)
        self.model = AutoModel.from_pretrained(model_name_or_path)
        if torch.cuda.is_available():
            self.model.cuda()
        else:
            logger.warning("CUDA is not available; sentence embedding is going to be slow")

    def sentenenize(self, text):
        return [s.text for s in razdel.sentenize(text)]

    def align_docs(self, src_text: str, tgt_text: str, rel_penalty=0.2, abs_penalty=0.2) -> pd.DataFrame:
        src_sents = self.sentenenize(src_text)
        src_embs = embed(src_sents, self.model, self.tokenizer)
        tgt_sents = self.sentenenize(tgt_text)
        tgt_embs = embed(tgt_sents, self.model, self.tokenizer)

        sims, sims_rel = get_penalized_sims(src_sents, tgt_sents, src_embs, tgt_embs, rel_penalty=rel_penalty, abs_penalty=abs_penalty)
        pair_ids = align3(sims_rel)

        doc_df = align_docs(src_sents, tgt_sents, pair_ids, sims, sims_rel)
        doc_df['docs_sim'] = doc_df.sim.fillna(0).mean()
        return doc_df
