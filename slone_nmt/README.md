# SLONE-NMT

SLONE-NMT is a toolkit for low-resource neural machine translation.

It has been developed as a follow-up work after creating the first
neural translation system for the Erzya language, in order to reuse its codebase
for the subsequent projects.

Currently, it contains the following modules:
- `document_alignment`: monotonic alignment of sentences from documents, 
similar to [vecalign](https://github.com/thompsonb/vecalign) 
and [lingtrain-aligner](https://github.com/averkij/lingtrain-aligner)\
- `myv_translit`: lookup tables for transliteration between Cyrillic and Latin
forms of Erzya. Copied from https://github.com/slone-nlp/myv-translit.
