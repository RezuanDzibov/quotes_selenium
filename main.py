import csv
from abc import ABC, abstractmethod

from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.by import By


URL = 'https://quotes.toscrape.com/'


class BaseParseQuotes(ABC):
    field_names = None

    def __init__(self, csv_file_name):
        self.csvfile = open(f'{csv_file_name}.csv', 'w', newline='', encoding='utf-8')
        self.writer = csv.DictWriter(self.csvfile, fieldnames=self.field_names)
        self.writer.writeheader()

    @abstractmethod
    def parse(self):
        pass

    def write_to_csv(self, data):
        self.writer.writerow(data)

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.csvfile.close()


class ParseQuotes(BaseParseQuotes):
    csv_file_name = 'quotes'
    field_names = ['Text', 'Author', 'Tags']

    def __init__(self, csv_file_name):
        self.driver = webdriver.Chrome()
        super().__init__(csv_file_name=csv_file_name)

    def parse(self):
        self.driver.get(URL)
        while True:
            self.parse_quotes()
            try:
                next_page = self.driver.find_element(By.CLASS_NAME, 'next')
                next_page = next_page.find_element(By.TAG_NAME, 'a')
                next_page.click()
                continue
            except NoSuchElementException:
                break

    def parse_quotes(self):

        quotes = self.driver.find_elements(By.CLASS_NAME, 'quote')
        for quote in quotes:
            quote_data = [
                quote.find_element(By.CLASS_NAME, 'text').text.strip(),
                quote.find_element(By.CLASS_NAME, 'author').text.strip(),
                ', '.join([tag.text for tag in quote.find_elements(By.CLASS_NAME, 'tag')]).strip()
            ]
            quote_data = dict({k: v for k, v in zip(self.field_names, quote_data)})
            self.write_to_csv(quote_data)

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.driver.close()
        super().__exit__(exc_type, exc_val, exc_tb)


class ParseAuthors(BaseParseQuotes):
    field_names = ['Fullname', 'Born Date', 'Born Location', 'Description']

    def __init__(self, csv_file_name):
        self.driver = webdriver.Chrome()
        self.authors = set()
        super().__init__(csv_file_name=csv_file_name)

    def parse(self):
        self.driver.get(URL)
        while True:
            self.parse_authors_links()
            try:
                next_page = self.driver.find_element(By.CLASS_NAME, 'next')
                next_page = next_page.find_element(By.TAG_NAME, 'a')
                next_page.click()
                continue
            except NoSuchElementException:
                break

    def parse_authors_links(self):
        url = self.driver.current_url
        authors_names = self.driver.find_elements(By.CLASS_NAME, 'author')
        authors = [author.find_element(By.XPATH, 'following-sibling::*').get_attribute('href') for author in authors_names]
        for author in authors:
            if author not in self.authors:
                self.driver.get(f'{author}')
                self.parse_author_page()
                self.authors.add(author)
            else:
                continue
        self.driver.get(url)

    def parse_author_page(self):
        author_data = [
            self.driver.find_element(By.CLASS_NAME, 'author-title').text.strip(),
            self.driver.find_element(By.CLASS_NAME, 'author-born-date').text.strip(),
            self.driver.find_element(By.CLASS_NAME, 'author-born-location').text.strip().split('in ')[1],
            self.driver.find_element(By.CLASS_NAME, 'author-description').text.strip()

        ]
        author_data_dict = dict({k: v for k, v in zip(self.field_names, author_data)})
        self.write_to_csv(author_data_dict)