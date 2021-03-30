from bs4 import BeautifulSoup
from typing import List
import MeCab
import collections
import markdown
import re
import regex
import sys

hiragana = regex.compile(r'\p{Script=Hiragana}+')


class KwdGenerator:
    mecab = MeCab.Tagger()
    score_map = collections.Counter()

    def scoring(self, text: str):
        noun = ""
        score = 0
        general = False
        node = self.mecab.parseToNode(text)

        while node:
            parts = node.feature.split(",")

            word = node.surface
            if word.isascii() and (word.islower() or word == "The"):
                pass
            elif hiragana.search(word):
                pass
            elif parts[0] == "名詞":
                # print(node.surface, parts)
                general = parts[1] == "普通名詞" and parts[2] != "一般"
                if noun and (not word.isascii() and noun.isascii()):
                    if not general:
                        self.score_map[noun] += score
                    noun = ""
                    score = 0
                noun += word
                score += 1
                if parts[1] == "固有名詞" and parts[2] == "一般":
                    score += 2
                if noun.isascii():
                    score += 1
                node = node.next
                continue

            if noun:
                if not general and noun[-1] != "感" and not noun.isdecimal(
                ) and not noun.startswith("The"):
                    self.score_map[noun] += score
                noun = ""
                score = 0

            node = node.next

    def generate(self, limits=15) -> List[str]:
        sorted_kwds = sorted(self.score_map.items(),
                             key=lambda item: item[1],
                             reverse=True)
        kwds = []
        while sorted_kwds and len(kwds) < limits:
            cur = sorted_kwds.pop(0)[0]
            if len(cur) > 1:
                kwds.append(cur)
        return kwds


def get_path(args: List[str]) -> str:
    if len(args) != 2:
        raise ValueError("<path/to/post> is a required argument")
    return args[1]


def hugoMd2txt(md: str) -> str:
    md = re.sub(r'`[^`]+`', "", md)
    md = re.sub(r'\{#[^}]*\}', "", md)
    html = markdown.markdown(md)
    soup = BeautifulSoup(html, features='html.parser')
    return soup.get_text()


def main():
    filepath = get_path(sys.argv)
    kwdgen = KwdGenerator()

    sep_cnt = 0
    code_block = False

    with open(filepath, 'r') as f:
        for line in f:
            line = line.strip()
            if line.startswith("```"):
                code_block = not code_block
            elif code_block:  # skip code block
                continue
            elif sep_cnt >= 2:  # skip meta block
                line = hugoMd2txt(line)
                kwdgen.scoring(line)
            elif line == "---":
                sep_cnt += 1

    print(' '.join(kwdgen.generate()), end='')


main()
