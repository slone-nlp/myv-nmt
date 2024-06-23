import json
import os
import shutil
from collections import Counter
from pathlib import Path
from typing import List, Tuple

import sentencepiece
from sentencepiece import sentencepiece_model_pb2 as sp_pb2_model
from transformers import NllbTokenizer
from transformers.models.nllb.tokenization_nllb import FAIRSEQ_LANGUAGE_CODES

from slone_nmt.nllb_preprocessing import replace_nonprint


def train_spm(
    texts: List[str], workdir: str, size: int = 2**14, min_char_count=3
) -> Tuple[Path, sentencepiece.SentencePieceProcessor]:
    print("Counting characters...")
    chars_cnt = Counter(c for text in texts for c in replace_nonprint(text))
    required_chars = "".join(
        [k for k, v in chars_cnt.most_common() if v >= min_char_count and k not in " "]
    )
    print(f"Total characters: {len(chars_cnt)}, required: {len(required_chars)}")

    workdir = Path(workdir)
    workdir.mkdir(parents=True, exist_ok=True)
    all_texts_file = workdir / "all_texts_plain.txt"
    spm_prefix = "spm"
    spm_file = workdir / f"{spm_prefix}.model"

    with open(all_texts_file, "w") as f:
        for text in texts:
            print(text, file=f)
    print(f"training on {len(texts)} texts")

    sentencepiece.SentencePieceTrainer.train(
        input=all_texts_file,
        model_prefix=f"{workdir}/{spm_prefix}",
        vocab_size=size,  # 16K
        character_coverage=1,
        num_threads=16,
        train_extremely_large_corpus=False,
        add_dummy_prefix=False,
        max_sentencepiece_length=128,
        max_sentence_length=4192 * 4,
        pad_id=0,
        eos_id=1,
        unk_id=2,
        bos_id=-1,
        required_chars=required_chars,
    )
    print("training done!")

    sp_trained = sentencepiece.SentencePieceProcessor(model_file=str(spm_file))
    return spm_file, sp_trained


def get_spm_vocab(model_path: str) -> List[Tuple[str, float]]:
    """Read a sentencepiece model and extract its tokens (except the special ones) and their scores"""
    sp_trained = spm.SentencePieceProcessor(model_file=model_path)
    added_spm = sp_pb2_model.ModelProto()
    added_spm.ParseFromString(sp_trained.serialized_model_proto())
    # not including counting the special tokens!
    new_pieces = [(p.piece, p.score) for p in added_spm.pieces if p.type == 1]
    return new_pieces


def create_enlarged_spm(
    sp_model: sentencepiece.SentencePieceProcessor,
    new_pieces_and_scores: List[Tuple[str, float]],
) -> Tuple[sentencepiece.SentencePieceProcessor, List[str]]:
    spmodel = sp_pb2_model.ModelProto()
    spmodel.ParseFromString(sp_model.serialized_model_proto())

    old_tokens_set = {p.piece for p in spmodel.pieces}
    print("old size:", len(old_tokens_set))

    prev_min_score = spmodel.pieces[-1].score
    n_added = 0
    added_tokens = []
    for new_piece, orig_score in new_pieces_and_scores:
        if new_piece not in old_tokens_set:
            n_added += 1
            new_p = sp_pb2_model.ModelProto().SentencePiece()
            new_p.piece = new_piece
            new_p.score = orig_score + prev_min_score
            spmodel.pieces.append(new_p)
            added_tokens.append(new_piece)
    print("new tokens:", n_added)
    return spmodel, added_tokens


def update_nllb_tokenizer(
    old_tokenizer: NllbTokenizer,
    new_spm_path: str,
    new_lang_codes: List[str],
) -> NllbTokenizer:
    """
    Create a new tokenizer for NLLB, with an updated sentencepiece model and some new language codes.
    In order to get rid of the old (and wrong) added token encoders/decoders, we save the tokenizer to disk and remove those files.
    :param old_tokenizer: the original tokenizer
    :param new_spm_path: path to the file with the sentncepiece model
    :param new_lang_codes: list of the new codes to add to the tokenizer
    :return: the new NllbTokenizer
    """
    TKN_DIR = "old_tokenizer"  # todo: make it a temp dir
    old_tokenizer.save_pretrained(TKN_DIR)

    with open(f"{TKN_DIR}/tokenizer_config.json", "r") as f:
        cfg = json.load(f)
    cfg["added_tokens_decoder"] = {
        k: v
        for k, v in cfg["added_tokens_decoder"].items()
        if k in ["0", "1", "2", "3"]
    }
    cfg["additional_special_tokens"] = []
    with open(f"{TKN_DIR}/tokenizer_config.json", "w") as f:
        json.dump(cfg, f, indent=2)
    # os.remove(f"{TKN_DIR}/tokenizer.json") # this one does not exist
    # this contains added tokens: language codes and mask
    os.remove(f"{TKN_DIR}/added_tokens.json")
    os.remove(f"{TKN_DIR}/special_tokens_map.json")
    os.remove(f"{TKN_DIR}/sentencepiece.bpe.model")
    shutil.copy(new_spm_path, f"{TKN_DIR}/sentencepiece.bpe.model")

    new_tokenizer = NllbTokenizer.from_pretrained(
        TKN_DIR,
        additional_special_tokens=sorted(FAIRSEQ_LANGUAGE_CODES + new_lang_codes),
    )
    return new_tokenizer
