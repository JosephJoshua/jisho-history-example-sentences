import csv
import requests
import os.path
import urllib.parse
from bs4 import BeautifulSoup
from timeit import default_timer

BASE_URL = 'https://yourei.jp/'
CSV_INPUT_FIELDS = [
    'word',
    'reading',
    'meaning',
]

def get_sentence_from_page(soup):
    sentence = soup.select_one('#sentence-1 > .the-sentence')

    if sentence is None:
        return '-'

    # Remove all the furigana from the text
    for furigana in sentence.find_all('rt'):
        furigana.decompose()

    return sentence.text

def get_example_sentence(word):
    word_escaped = urllib.parse.quote_plus(word.encode('utf-8'))

    page = requests.get(BASE_URL + word_escaped)
    soup = BeautifulSoup(page.content, 'html.parser')

    return get_sentence_from_page(soup)

def read_csv(file_path):
    rows = []
    with open(file_path, mode='r', encoding='utf-8') as file:
        reader = csv.DictReader(file, fieldnames=CSV_INPUT_FIELDS)
        for row in reader:
            rows.append(row)

    return rows

# Returns all words that couldn't be found an example sentence for
def add_example_sentences(file_path, rows):
    with open(file_path, mode='w', encoding='utf-8', newline='') as file:
        output_fields = [
            *CSV_INPUT_FIELDS,
            'example_sentence'
        ]

        writer = csv.DictWriter(file, fieldnames=output_fields, quoting=csv.QUOTE_ALL)
        row_index = 1
        row_count = len(rows)

        failed_words = []

        for row in rows:
            # The word field is empty if the word is only written in Hiragana or Katakana
            if row['word'] == '':
                row['word'] = row['reading']
            
            example_sentence = get_example_sentence(row['word'])
            row['example_sentence'] = example_sentence

            percentage_done_str = f'({row_index}/{row_count})'

            if example_sentence == '-':
                failed_words.append({
                    'word': row['word'],
                    'index': row_index
                })

                print("Couldn't find any example sentences for", row['word'], percentage_done_str)
            else:
                print('Done:', row['word'], percentage_done_str)

            writer.writerow(row)
            row_index += 1

    return failed_words

def ask_file_path(question, must_exist):
    # Just prompt the user until they give an answer
    while True:
        path = input(question)
        if path.strip() != '':
            if (not must_exist) or os.path.exists(path):
                return path

def print_failed_words(failed_words):
    if len(failed_words) > 0:
        print("Words that weren't on yourei.jp (need to manually find example sentences for):")

        for word in failed_words:
            print(word['word'], 'at row', word['index'])

def main():
    print('=================== Jisho Example Sentences ===================')
    print('This script will update the CSV file exported from the Jisho app with example sentences from yourei.jp')

    input_file_path = ask_file_path('Please enter your CSV file path: ', True)
    output_file_path = ask_file_path('Where do you want your new CSV file to be saved? ', False)

    start_time = default_timer()

    rows = read_csv(input_file_path)
    failed_words = add_example_sentences(output_file_path, rows)

    end_time = default_timer()
    time_taken = end_time - start_time

    print(f'========================== DONE (took {time_taken:.5f}s) ===========================')
    print_failed_words(failed_words)
    

if __name__ == '__main__':
    main()