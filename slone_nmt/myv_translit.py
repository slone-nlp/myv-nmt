# this code is based on Mikhail Potapov's algorithm:
# https://github.com/potapoff271083/automatic_translation_latin_to_cyrillic
# http://valks.erzja.info/2020/04/30/эрзянский-алфавит/
import re
from collections import Counter


CYR_CHARS = 'абвгдеёжзийклмнопрстуфхцчшщъыьэюя'
BASIC_LAT_CHARS = 'abcdefghijklmnopqrtuvwxyz'
ACCENT_LAT_CHARS = 'ěäüöśźćńŕťďĺ'
LAT_CHARS = BASIC_LAT_CHARS + ACCENT_LAT_CHARS

CYR_CONSONANTS_LOWER_HARD = 'бвгдзклмнпрстфх'
CYR_CONSONANTS_UPPER_HARD = 'БВГДЗКЛМНПРСТФХ'
CYR_CONSONANTS_HARD = CYR_CONSONANTS_LOWER_HARD + CYR_CONSONANTS_UPPER_HARD


_cyr2lat = [
    {'find_what': 'ъё', 'replacer': 'jo', 're': False},
    {'find_what': 'ъю', 'replacer': 'ju', 're': False},
    {'find_what': 'ъя', 'replacer': 'ja', 're': False},
    {'find_what': 'ъе', 'replacer': 'je', 're': False},
    {'find_what': 'ЪЁ', 'replacer': 'JO', 're': False},
    {'find_what': 'ЪЮ', 'replacer': 'JU', 're': False},
    {'find_what': 'ЪЯ', 'replacer': 'JA', 're': False},
    {'find_what': 'ЪЕ', 'replacer': 'JE', 're': False},

    {'find_what': 'А', 'replacer': 'A', 're': False},
    {'find_what': 'а', 'replacer': 'a', 're': False},
    {'find_what': 'О', 'replacer': 'O', 're': False},
    {'find_what': 'о', 'replacer': 'o', 're': False},
    {'find_what': 'У', 'replacer': 'U', 're': False},
    {'find_what': 'у', 'replacer': 'u', 're': False},
    {'find_what': 'Ы', 'replacer': 'Y', 're': False},
    {'find_what': 'ы', 'replacer': 'y', 're': False},
    {'find_what': 'И', 'replacer': 'I', 're': False},
    {'find_what': 'и', 'replacer': 'i', 're': False},
    {'find_what': 'Е', 'replacer': 'E', 're': False},
    {'find_what': 'е', 'replacer': 'e', 're': False},
    {'find_what': 'Б', 'replacer': 'B', 're': False},
    {'find_what': 'б', 'replacer': 'b', 're': False},
    {'find_what': 'В', 'replacer': 'V', 're': False},
    {'find_what': 'в', 'replacer': 'v', 're': False},
    {'find_what': 'Г', 'replacer': 'G', 're': False},
    {'find_what': 'г', 'replacer': 'g', 're': False},
    {'find_what': 'Д', 'replacer': 'D', 're': False},
    {'find_what': 'д', 'replacer': 'd', 're': False},
    {'find_what': 'З', 'replacer': 'Z', 're': False},
    {'find_what': 'з', 'replacer': 'z', 're': False},
    {'find_what': 'К', 'replacer': 'K', 're': False},
    {'find_what': 'к', 'replacer': 'k', 're': False},
    {'find_what': 'Л', 'replacer': 'L', 're': False},
    {'find_what': 'л', 'replacer': 'l', 're': False},
    {'find_what': 'М', 'replacer': 'M', 're': False},
    {'find_what': 'м', 'replacer': 'm', 're': False},
    {'find_what': 'Н', 'replacer': 'N', 're': False},
    {'find_what': 'н', 'replacer': 'n', 're': False},
    {'find_what': 'П', 'replacer': 'P', 're': False},
    {'find_what': 'п', 'replacer': 'p', 're': False},
    {'find_what': 'Р', 'replacer': 'R', 're': False},
    {'find_what': 'р', 'replacer': 'r', 're': False},
    {'find_what': 'С', 'replacer': 'S', 're': False},
    {'find_what': 'с', 'replacer': 's', 're': False},
    {'find_what': 'Т', 'replacer': 'T', 're': False},
    {'find_what': 'т', 'replacer': 't', 're': False},
    {'find_what': 'Ф', 'replacer': 'F', 're': False},
    {'find_what': 'ф', 'replacer': 'f', 're': False},
    {'find_what': 'Х', 'replacer': 'H', 're': False},
    {'find_what': 'х', 'replacer': 'h', 're': False},
    {'find_what': 'Ц', 'replacer': 'C', 're': False},
    {'find_what': 'ц', 'replacer': 'c', 're': False},
    {'find_what': 'Ч', 'replacer': 'Č', 're': False},
    {'find_what': 'ч', 'replacer': 'č', 're': False},
    {'find_what': 'Ш', 'replacer': 'Š', 're': False},
    {'find_what': 'ш', 'replacer': 'š', 're': False},
    {'find_what': 'Ж', 'replacer': 'Ž', 're': False},
    {'find_what': 'ж', 'replacer': 'ž', 're': False},
    {'find_what': 'Щ', 'replacer': 'Čš', 're': False},
    {'find_what': 'щ', 'replacer': 'čš', 're': False},
    {'find_what': 'Ь', 'replacer': '́', 're': False},
    {'find_what': 'ь', 'replacer': '́', 're': False},
    {'find_what': 'Й', 'replacer': 'J', 're': False},
    {'find_what': 'й', 'replacer': 'j', 're': False},
    {'find_what': 'Ъ', 'replacer': '', 're': False},
    {'find_what': 'ъ', 'replacer': '', 're': False},
    {'find_what': 'Э', 'replacer': 'Ě', 're': False},
    {'find_what': 'э', 'replacer': 'ě', 're': False},
    {'find_what': 'Я', 'replacer': 'Ä', 're': False},
    {'find_what': 'я', 'replacer': 'ä', 're': False},
    {'find_what': 'Ю', 'replacer': 'Ü', 're': False},
    {'find_what': 'ю', 'replacer': 'ü', 're': False},
    {'find_what': 'Ё', 'replacer': 'Ö', 're': False},
    {'find_what': 'ё', 'replacer': 'ö', 're': False},
    {'find_what': '\\bö\\b', 'replacer': 'jo', 're': True},
    {'find_what': '\\bÖ\\b', 'replacer': 'Jo', 're': True},
    {'find_what': '\\bü\\b', 'replacer': 'ju', 're': True},
    {'find_what': '\\bÜ\\b', 'replacer': 'Ju', 're': True},
    {'find_what': '\\bä\\b', 'replacer': 'ja', 're': True},
    {'find_what': '\\bÄ\\b', 'replacer': 'Ja', 're': True},
    {'find_what': '(\\bö)([a-zöäüšžčě])', 'replacer': 'jo\\2', 're': True},
    {'find_what': '(\\bä)([a-zöäüšžčě])', 'replacer': 'ja\\2', 're': True},
    {'find_what': '(\\bü)([a-zöäüšžčě])', 'replacer': 'ju\\2', 're': True},
    {'find_what': '(\\bÖ)([a-zöäüšžčě])', 'replacer': 'Jo\\2', 're': True},
    {'find_what': '(\\bÄ)([a-zöäüšžčě])', 'replacer': 'Ja\\2', 're': True},
    {'find_what': '(\\bÜ)([a-zöäüšžčě])', 'replacer': 'Ju\\2', 're': True},
    {'find_what': '(\\bö)([A-ZÖÄÜŠŽČĚ])', 'replacer': 'jo\\2', 're': True},
    {'find_what': '(\\bä)([A-ZÖÄÜŠŽČĚ])', 'replacer': 'ja\\2', 're': True},
    {'find_what': '(\\bü)([A-ZÖÄÜŠŽČĚ])', 'replacer': 'ju\\2', 're': True},
    {'find_what': '(\\bÖ)([A-ZÖÄÜŠŽČĚ])', 'replacer': 'JO\\2', 're': True},
    {'find_what': '(\\bÄ)([A-ZÖÄÜŠŽČĚ])', 'replacer': 'JA\\2', 're': True},
    {'find_what': '(\\bÜ)([A-ZÖÄÜŠŽČĚ])', 'replacer': 'JU\\2', 're': True},
    {'find_what': '([aouiěyeöüäAOUIĚYEÖÜÄ])(ä)', 'replacer': '\\1ja', 're': True},
    {'find_what': '([aouiěyeöüäAOUIĚYEÖÜÄ])(Ä)', 'replacer': '\\1JA', 're': True},
    {'find_what': '([aouiěyeöüäAOUIĚYEÖÜÄ])(ö)', 'replacer': '\\1jo', 're': True},
    {'find_what': '([aouiěyeöüäAOUIĚYEÖÜÄ])(Ö)', 'replacer': '\\1JO', 're': True},
    {'find_what': '([aouiěyeöüäAOUIĚYEÖÜÄ])(ü)', 'replacer': '\\1ju', 're': True},
    {'find_what': '([aouiěyeöüäAOUIĚYEÖÜÄ])(Ü)', 'replacer': '\\1JU', 're': True},
]

_cyr2lat_joint_acutes = [
    {'find_what': 'ś', 'replacer': 'ś', 're': False},
    {'find_what': 'ź', 'replacer': 'ź', 're': False},
    {'find_what': 'ć', 'replacer': 'ć', 're': False},
    {'find_what': 'ń', 'replacer': 'ń', 're': False},
    {'find_what': 'ŕ', 'replacer': 'ŕ', 're': False},
    {'find_what': 't́', 'replacer': 'ť', 're': False},
    {'find_what': 'd́', 'replacer': 'ď', 're': False},
    {'find_what': 'ĺ', 'replacer': 'ĺ', 're': False},
    {'find_what': 'Ś', 'replacer': 'Ś', 're': False},
    {'find_what': 'Ź', 'replacer': 'Ź', 're': False},
    {'find_what': 'Ć', 'replacer': 'Ć', 're': False},
    {'find_what': 'Ń', 'replacer': 'Ń', 're': False},
    {'find_what': 'T́', 'replacer': 'Ť', 're': False},
    {'find_what': 'D́', 'replacer': 'Ď', 're': False},
    {'find_what': 'Ĺ', 'replacer': 'Ĺ', 're': False},
    {'find_what': 'Ŕ', 'replacer': 'Ŕ', 're': False},
]

_cyr2lat_first_e = [
    {'find_what': '\\bĚ', 'replacer': 'E', 're': True},
    {'find_what': '\\bě', 'replacer': 'e', 're': True},
]

_lat2cyr_first_e = [
    {'find_what': '\\bE', 'replacer': 'Ě', 're': True},
    {'find_what': '\\be', 'replacer': 'ě', 're': True},
]

_cyr2lat_soft_l_after_vowels = [
    # joint acutes | disjoint acutes
    {'find_what': '([iěeIĚE])(Ĺ|Ĺ)', 'replacer': '\\1L', 're': True},
    {'find_what': '([iěeIĚE])(ĺ|ĺ)', 'replacer': '\\1l', 're': True},
]

_lat2cyr_soft_l_after_vowels = [
    # add the soft sign, but only if the next letter is not softening
    {'find_what': '([иэеИЭЕ])(Л)\\b', 'replacer': '\\1Ль', 're': True},
    {'find_what': '([иэеИЭЕ])(л)\\b', 'replacer': '\\1ль', 're': True},
    {'find_what': '([иэеИЭЕ])(Л)([^ьъиеюяю])', 'replacer': '\\1ЛЬ\\3', 're': True},
    {'find_what': '([иэеИЭЕ])(л)([^ьъиеюяю])', 'replacer': '\\1ль\\3', 're': True},
    # special cases when L is still hard
    # todo: fix all the exclusions from the list in https://t.me/ravo_club/9776
    {'find_what': '([иэеИЭЕ][Лл])([Ьь])(ГАД|ГАВТ|гад|гавт)', 'replacer': '\\1\\3', 're': True},
]

_lat2cyr = [
    {'find_what': 'Ŕ', 'replacer': 'Ŕ', 're': False},
    {'find_what': 'Ĺ', 'replacer': 'Ĺ', 're': False},
    {'find_what': 'Ď', 'replacer': 'D́', 're': False},
    {'find_what': 'Ť', 'replacer': 'T́', 're': False},
    {'find_what': 'Ń', 'replacer': 'Ń', 're': False},
    {'find_what': 'Ć', 'replacer': 'Ć', 're': False},
    {'find_what': 'Ź', 'replacer': 'Ź', 're': False},
    {'find_what': 'Ś', 'replacer': 'Ś', 're': False},
    {'find_what': 'ĺ', 'replacer': 'ĺ', 're': False},
    {'find_what': 'ď', 'replacer': 'd́', 're': False},
    {'find_what': 'ť', 'replacer': 't́', 're': False},
    {'find_what': 'ŕ', 'replacer': 'ŕ', 're': False},
    {'find_what': 'ń', 'replacer': 'ń', 're': False},
    {'find_what': 'ć', 'replacer': 'ć', 're': False},
    {'find_what': 'ź', 'replacer': 'ź', 're': False},
    {'find_what': 'ś', 'replacer': 'ś', 're': False},
    # {'find_what': '\\1JU', 'replacer': '([aouiěyeöüäAOUIĚYEÖÜÄ])(Ü)', 're': True},
    # {'find_what': '\\1ju', 'replacer': '([aouiěyeöüäAOUIĚYEÖÜÄ])(ü)', 're': True},
    # {'find_what': '\\1JO', 'replacer': '([aouiěyeöüäAOUIĚYEÖÜÄ])(Ö)', 're': True},
    # {'find_what': '\\1jo', 'replacer': '([aouiěyeöüäAOUIĚYEÖÜÄ])(ö)', 're': True},
    # {'find_what': '\\1JA', 'replacer': '([aouiěyeöüäAOUIĚYEÖÜÄ])(Ä)', 're': True},
    # {'find_what': '\\1ja', 'replacer': '([aouiěyeöüäAOUIĚYEÖÜÄ])(ä)', 're': True},
    # {'find_what': 'JU\\2', 'replacer': '(\\bÜ)([A-ZÖÄÜŠŽČĚ])', 're': True},
    # {'find_what': 'JA\\2', 'replacer': '(\\bÄ)([A-ZÖÄÜŠŽČĚ])', 're': True},
    # {'find_what': 'JO\\2', 'replacer': '(\\bÖ)([A-ZÖÄÜŠŽČĚ])', 're': True},
    # {'find_what': 'ju\\2', 'replacer': '(\\bü)([A-ZÖÄÜŠŽČĚ])', 're': True},
    # {'find_what': 'ja\\2', 'replacer': '(\\bä)([A-ZÖÄÜŠŽČĚ])', 're': True},
    # {'find_what': 'jo\\2', 'replacer': '(\\bö)([A-ZÖÄÜŠŽČĚ])', 're': True},
    # {'find_what': 'Ju\\2', 'replacer': '(\\bÜ)([a-zöäüšžčě])', 're': True},
    # {'find_what': 'Ja\\2', 'replacer': '(\\bÄ)([a-zöäüšžčě])', 're': True},
    # {'find_what': 'Jo\\2', 'replacer': '(\\bÖ)([a-zöäüšžčě])', 're': True},
    # {'find_what': 'ju\\2', 'replacer': '(\\bü)([a-zöäüšžčě])', 're': True},
    # {'find_what': 'ja\\2', 'replacer': '(\\bä)([a-zöäüšžčě])', 're': True},
    # {'find_what': 'jo\\2', 'replacer': '(\\bö)([a-zöäüšžčě])', 're': True},
    # {'find_what': 'Ja', 'replacer': '\\bÄ\\b', 're': True},
    # {'find_what': 'ja', 'replacer': '\\bä\\b', 're': True},
    # {'find_what': 'Ju', 'replacer': '\\bÜ\\b', 're': True},
    # {'find_what': 'ju', 'replacer': '\\bü\\b', 're': True},
    # {'find_what': 'Jo', 'replacer': '\\bÖ\\b', 're': True},
    # {'find_what': 'jo', 'replacer': '\\bö\\b', 're': True},
    {'find_what': 'ö', 'replacer': 'ё', 're': False},
    {'find_what': 'Ö', 'replacer': 'Ё', 're': False},
    {'find_what': 'ü', 'replacer': 'ю', 're': False},
    {'find_what': 'Ü', 'replacer': 'Ю', 're': False},
    {'find_what': 'ä', 'replacer': 'я', 're': False},
    {'find_what': 'Ä', 'replacer': 'Я', 're': False},
    {'find_what': 'ě', 'replacer': 'э', 're': False},
    {'find_what': 'Ě', 'replacer': 'Э', 're': False},
    # {'find_what': '', 'replacer': 'ъ', 're': False},
    # {'find_what': '', 'replacer': 'Ъ', 're': False},
    {'find_what': 'j', 'replacer': 'й', 're': False},
    {'find_what': 'J', 'replacer': 'Й', 're': False},
    {'find_what': '́', 'replacer': 'ь', 're': False},
    {'find_what': '́', 'replacer': 'Ь', 're': False},
    {'find_what': 'čš', 'replacer': 'щ', 're': False},
    {'find_what': 'Čš', 'replacer': 'Щ', 're': False},
    {'find_what': 'ž', 'replacer': 'ж', 're': False},
    {'find_what': 'Ž', 'replacer': 'Ж', 're': False},
    {'find_what': 'š', 'replacer': 'ш', 're': False},
    {'find_what': 'Š', 'replacer': 'Ш', 're': False},
    {'find_what': 'č', 'replacer': 'ч', 're': False},
    {'find_what': 'Č', 'replacer': 'Ч', 're': False},
    {'find_what': 'c', 'replacer': 'ц', 're': False},
    {'find_what': 'C', 'replacer': 'Ц', 're': False},
    {'find_what': 'h', 'replacer': 'х', 're': False},
    {'find_what': 'H', 'replacer': 'Х', 're': False},
    {'find_what': 'f', 'replacer': 'ф', 're': False},
    {'find_what': 'F', 'replacer': 'Ф', 're': False},
    {'find_what': 't', 'replacer': 'т', 're': False},
    {'find_what': 'T', 'replacer': 'Т', 're': False},
    {'find_what': 's', 'replacer': 'с', 're': False},
    {'find_what': 'S', 'replacer': 'С', 're': False},
    {'find_what': 'r', 'replacer': 'р', 're': False},
    {'find_what': 'R', 'replacer': 'Р', 're': False},
    {'find_what': 'p', 'replacer': 'п', 're': False},
    {'find_what': 'P', 'replacer': 'П', 're': False},
    {'find_what': 'n', 'replacer': 'н', 're': False},
    {'find_what': 'N', 'replacer': 'Н', 're': False},
    {'find_what': 'm', 'replacer': 'м', 're': False},
    {'find_what': 'M', 'replacer': 'М', 're': False},
    {'find_what': 'l', 'replacer': 'л', 're': False},
    {'find_what': 'L', 'replacer': 'Л', 're': False},
    {'find_what': 'k', 'replacer': 'к', 're': False},
    {'find_what': 'K', 'replacer': 'К', 're': False},
    {'find_what': 'z', 'replacer': 'з', 're': False},
    {'find_what': 'Z', 'replacer': 'З', 're': False},
    {'find_what': 'd', 'replacer': 'д', 're': False},
    {'find_what': 'D', 'replacer': 'Д', 're': False},
    {'find_what': 'g', 'replacer': 'г', 're': False},
    {'find_what': 'G', 'replacer': 'Г', 're': False},
    {'find_what': 'v', 'replacer': 'в', 're': False},
    {'find_what': 'V', 'replacer': 'В', 're': False},
    {'find_what': 'b', 'replacer': 'б', 're': False},
    {'find_what': 'B', 'replacer': 'Б', 're': False},
    {'find_what': 'e', 'replacer': 'е', 're': False},
    {'find_what': 'E', 'replacer': 'Е', 're': False},
    {'find_what': 'i', 'replacer': 'и', 're': False},
    {'find_what': 'I', 'replacer': 'И', 're': False},
    {'find_what': 'y', 'replacer': 'ы', 're': False},
    {'find_what': 'Y', 'replacer': 'Ы', 're': False},
    {'find_what': 'u', 'replacer': 'у', 're': False},
    {'find_what': 'U', 'replacer': 'У', 're': False},
    {'find_what': 'o', 'replacer': 'о', 're': False},
    {'find_what': 'O', 'replacer': 'О', 're': False},
    {'find_what': 'a', 'replacer': 'а', 're': False},
    {'find_what': 'A', 'replacer': 'А', 're': False},
    # make the soft sign upper in an uppercase word
    {'find_what': '([А-ЯЁ]{2,})ь', 'replacer': '\\1Ь', 're': True},
    {'find_what': '([А-ЯЁ])ь([А-ЯЁ])', 'replacer': '\\1Ь\\2', 're': True},
    # introduce Ъ when appropriate
    {'find_what': f'([{CYR_CONSONANTS_HARD}])Й[Аа]', 'replacer': '\\1ЪЯ', 're': True},
    {'find_what': f'([{CYR_CONSONANTS_HARD}])й[Аа]', 'replacer': '\\1ъя', 're': True},
    {'find_what': f'([{CYR_CONSONANTS_HARD}])Й[Оо]', 'replacer': '\\1ЪЁ', 're': True},
    {'find_what': f'([{CYR_CONSONANTS_HARD}])й[Оо]', 'replacer': '\\1ъё', 're': True},
    {'find_what': f'([{CYR_CONSONANTS_HARD}])Й[Уу]', 'replacer': '\\1ЪЮ', 're': True},
    {'find_what': f'([{CYR_CONSONANTS_HARD}])й[Уу]', 'replacer': '\\1ъю', 're': True},
    {'find_what': f'([{CYR_CONSONANTS_HARD}])Й[Ee]', 'replacer': '\\1ЪЕ', 're': True},
    {'find_what': f'([{CYR_CONSONANTS_HARD}])й[Ee]', 'replacer': '\\1ъе', 're': True},
    # ya, yo, yu
    {'find_what': 'Й[Аа]', 'replacer': 'Я', 're': True},
    {'find_what': 'й[Аа]', 'replacer': 'я', 're': True},
    {'find_what': 'Й[Оо]', 'replacer': 'Ё', 're': True},
    {'find_what': 'й[Оо]', 'replacer': 'ё', 're': True},
    {'find_what': 'Й[Уу]', 'replacer': 'Ю', 're': True},
    {'find_what': 'й[Уу]', 'replacer': 'ю', 're': True},
]

_lat2cyr_special_cases = [
    {'find_what': 'раён', 'replacer': 'район'},
    {'find_what': 'РАЁН', 'replacer': 'РАЙОН'},
]


def transliterate_with_rules(text, rules):
    for item in rules:
        if item.get('re'):
            text = re.sub(item['find_what'], item['replacer'], text)
        else:
            text = text.replace(item['find_what'], item['replacer'])
    return text


def cyr2lat(text, joint_acute=True, first_e_with_hacek=True, soft_l_after_vowels=True):
    text = transliterate_with_rules(text, _cyr2lat)
    if joint_acute:
        text = transliterate_with_rules(text, _cyr2lat_joint_acutes)
    if not first_e_with_hacek:
        text = transliterate_with_rules(text, _cyr2lat_first_e)
    if not soft_l_after_vowels:
        text = transliterate_with_rules(text, _cyr2lat_soft_l_after_vowels)
    return text


def lat2cyr(text, joint_acute=True, first_e_with_hacek=True, soft_l_after_vowels=True):
    if not first_e_with_hacek:
        text = transliterate_with_rules(text, _lat2cyr_first_e)
    text = transliterate_with_rules(text, _lat2cyr)
    if not soft_l_after_vowels:
        text = transliterate_with_rules(text, _lat2cyr_soft_l_after_vowels)
    text = transliterate_with_rules(text, _lat2cyr_special_cases)
    return text


def detect_script(text: str, min_prevalence: float = 2.0, min_detectable: float = 0.1) -> str:
    """ Detect the script of the text.
    Possible values:
        - cyr - Cyrillic
        - lat - Latin
        - mix - Mixed Cyrillic and Latin script
        - unk - Unknown script (probably neither Latin nor Cyrillic)
    """
    cyr, lat, other = 0, 0, 0
    char_cnt = Counter(text.lower())
    for char, cnt in char_cnt.items():
        if char in CYR_CHARS:
            cyr += cnt
        elif char in LAT_CHARS:
            lat += cnt
        else:
            other += cnt
    total = cyr + lat + other
    if not total:
        return 'unk'
    if (cyr + lat) / total < min_detectable:
        return 'unk'
    if cyr >= lat * min_prevalence:
        return 'cyr'
    if lat >= cyr * min_prevalence:
        return 'lat'
    return 'mix'
