import re
from .utils.helper import score_from_sentences, clean_words
from .BaseExtractor import BaseExtractor
from .utils.defaults import TITLE_GUESS_XPATH


class TitleExtractor(BaseExtractor):

    def __init__(self, element, guess_xpath, xpath, pattern, guess_from_title):
        self.element = element
        self.guess_xpath = guess_xpath
        self.xpath = xpath
        self.pattern = pattern
        self.guess_from_title = guess_from_title

    @classmethod
    def from_fields(cls, parser, element, guess_from_title=None):
        guess_xpath = TITLE_GUESS_XPATH
        pattern = parser.get("title", "PATTERN")
        xpath = parser.get("title", "XPATH")
        return cls(
            element=element,
            guess_xpath=guess_xpath,
            guess_from_title=guess_from_title,
            xpath=eval(xpath),
            pattern=eval(pattern)
        )

    def extract_by_xpath(self, xpath):
        title_list = self.element.xpath(xpath)
        if title_list:
            return title_list[0]
        return ''

    def extract_by_title(self):
        title_list = self.element.xpath('//title/text()')
        if not title_list:
            return ''
        title = re.split(self.pattern, title_list[0])
        return "".join(title[0])

    def extract_by_guess_xpath(self):
        title_list = self.element.xpath(self.guess_xpath)
        if not title_list:
            return ''
        return title_list

    def extract_by_samilarity(self, c=0.8):
        from_title = self.extract_by_title()
        from_guess_xpath_titles = self.extract_by_guess_xpath()
        if not from_title:
            return ''

        if from_guess_xpath_titles:
            # filter
            from_guess_xpath_titles = [
                title.strip() for title in from_guess_xpath_titles if title.strip()]
            score_array = score_from_sentences(
                clean_words(from_title),
                *[clean_words(title) for title in from_guess_xpath_titles]
            )
            if score_array.max() >= c:
                index = score_array.argmax()
                return {
                    "xpath": self.guess_xpath.split("|")[index],
                    "value": self._format_title(from_guess_xpath_titles[index]),
                    "regex": ""
                }

        return {
            "xpath": "//title/text()",
            "value": self._format_title(from_title),
            "regex": ""
        }

    @staticmethod
    def _format_title(title):
        if not title:
            return ''
        return title.split("\n")[0]

    def extract(self):
        if self.xpath:
            if isinstance(self.xpath, str):
                value = self.extract_by_xpath(self.xpath)
                if bool(value):
                    return {
                        "xpath": self.xpath,
                        "value": self._format_title(value),
                        "regex": ""
                    }
            elif isinstance(self.xpath, list):
                for xpath in self.xpath:
                    value = self.extract_by_xpath(xpath)
                    if xpath and value:
                        return {
                            "xpath": xpath,
                            "value": self._format_title(value),
                            "regex": ""
                        }
        if self.guess_from_title.get("value"):
            return {
                "xpath": f'string({self.guess_from_title.get("xpath")})',
                "value": self._format_title(self.guess_from_title.get("value")),
                "regex": ""
            }
        return self.extract_by_samilarity()
