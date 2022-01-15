import argparse
import pickle
from collections import Counter
import nltk
import re
import statistics
import time
import datetime
import concurrent.futures
from urllib.request import Request, urlopen
import validators
from sqlalchemy import create_engine, MetaData, Table, Column, Integer, String, PickleType

class Timer:
    """
    Starts and stops timer automatically
    """
    def __init__(self):
        self.elapsed = 0

    def __enter__(self):
        self.start = time.perf_counter()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.end = time.perf_counter()
        self.elapsed = self.end - self.start

class Analyzer:
    """
    generates detailed report about input text
    """
    def __init__(self, file):
        self.file = file

    def analyze(self):
        self.time_of_report = datetime.datetime.now()
        if validators.url(self.file):
            self.type_of_resource = 'resource'
        else:
            self.type_of_resource = 'file'

        try:
            if self.type_of_resource == 'resource':
                req = Request(self.file, headers={'User-Agent': 'Mozilla/5.0'})
                self.text = urlopen(req).read().decode('utf-8')
            elif self.type_of_resource == 'file':
                with open(self.file, 'r') as r:
                    self.text = r.read()
                    self.type_of_resource = 'file'
            nltk.download('punkt')
            self.report = dict()
            self.report["sentences"] = self.count_sentences(self.text)
            self.report["words"] = self.count_words(self.report["sentences"])
            self.report["number_of_characters"] = self.count_number_of_characters(self.text)
            self.report["number_of_words"] =  self.report["words"]
            self.report["number_of_sentences"] = len(self.report["sentences"])
            self.report["frequency_of_chars"] = Counter(self.text)
            # self.report["distr_of_chars"] = {char: dist/(self.report["number_of_characters"]*100 for char, dist in self.report["frequency_of_chars"].items()}
            self.report["avrg_word_length"] = statistics.mean([len(word) for word in self.report["words"]])
            self.report["avrg_words_in_sentence"] = statistics.mean([len(sentence.split()) for sentence in self.report["sentences"]])
            self.report["top10_words"] = Counter([word.lower() for word in self.report["words"]]).most_common(10)
            self.report["top10_long_words"] = list(sorted(set(self.report["words"]), key=len, reverse=True))[:10]
            self.report["top10_short_words"] = list(sorted(set(self.report["words"]), key=len))[:10]
            self.report["top10_long_sentences"] = list(sorted(self.report["sentences"], key=len, reverse=True))[:10]
            self.report["top10_short_sentences"] = list(sorted(self.report["sentences"], key=len))[:10]
            self.report["palindromes"] = set([word for word in self.report["words"] if word==word[::-1]])
            self.report["number_of_palindromes"] = len(self.palindromes)
            self.report["top10_long_palindromes"] = list(sorted(self.palindromes, key=len, reverse=True))[:10]
            self.report["text_is_palindrome"] = re.sub(r'\W+', '', self.text) == re.sub(r'\W+', '', self.text)[::-1]
            self.report["reversed_text"] = self.text[::-1]
            self.report["reversed_text_char_order"] = ' '.join(self.text.split()[::-1])

        except Exception as e:
            self.result = f"{self.time_of_report}|{self.type_of_resource}|{self.file}|CRITICAL"
        else:
            self.result = f"{self.time_of_report}|{self.type_of_resource}|{self.file}|INFO"
            print(f"Report for file {self.file}:date and time: {self.time_of_report}")

    @staticmethod
    def count_sentences(text):
        return nltk.tokenize.sent_tokenize(text)

    @staticmethod
    def count_words(sentences):
        return [re.sub(r'\W+', '', word) for sentence in [words.split() for words in sentences] for word in
                  sentence]

    @staticmethod
    def count_number_of_characters(text):
        return len([char for char in text if not char.isspace()])



def analyze_file(file):
    print(f'working with file {file}')
    report = Analyzer(file)
    with Timer() as timer:
        report.analyze()
    print(f"time to generate report for file {file}: {int(timer.elapsed * 1000)} ms")
    return report

if __name__ == '__main__':
    report = analyze_file('https://filesamples.com/samples/document/txt/sample3.txt')

    engine = create_engine('sqlite:///mytextanalyzer.db', echo=True)
    meta = MetaData()

    results = Table(
        'mytextanalyzer', meta,
        Column('id', Integer, primary_key=True),
        Column('result', String),
        Column('report', PickleType)
    )
    meta.create_all(engine)

    ins = results.insert().values(result=report.result, report=report.report)
    conn = engine.connect()
    result = conn.execute(ins)



    print('finished')


###################################################