import time
from typing import Optional

import undetected_chromedriver as uc
# from parss.admpars.management.commands._base_parser import Parser
from fake_useragent import FakeUserAgent
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.remote.webdriver import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait


class EmployersDataParser:
    def __init__(self):
        self.main_url = 'https://2gis.ru/volgograd/rubrics'
        self.urls_for_search = []

        options = Options()
        my_useragent = FakeUserAgent(browsers='chrome', min_percentage=1.3, os='linux').random
        options.add_argument("--window-size=1920,1080")
        options.add_argument("--enable-logging")
        options.add_argument("--headless=new")
        options.add_argument("--incognito")
        options.add_argument(f"--user-agent={my_useragent}")

        self.driver = uc.Chrome(use_subprocess=True, options=options, headless=True)
        self.action = ActionChains(self.driver)

    def pause(self, element):
        attempts = 0
        while attempts < 3:
            try:
                WebDriverWait(self.driver, 10).until(EC.presence_of_element_located((By.XPATH, element)))
                return
            except TimeoutException:
                print(f"Попытка {attempts + 1} не удалась. Не могу найти элемент {element}. "
                      f"Повторная попытка через 1 секунду...")
                time.sleep(1)
                attempts += 1
        return Exception("Не найден элемент для отслеживания загрузки. (ಥ﹏ಥ)")

    def get_rubrics_url(self) -> list[str]:
        """
        Первый этап получения итоговых URL адресов.
        Метод позволяет получить URL адреса всех подрубрик, из окна 'rubrics'.
        :return: Список, содержащие URL адреса подрубрик каждой рубрики.
        """

        rubrics_url_lst = []

        self.driver.get(self.main_url)
        # time.sleep(0.7)
        self.pause("//div[@class='_1rkbbi0x']")
        print(f"Всего организаций: {self.driver.find_element(By.CLASS_NAME, '_hc69qa').text}")

        try:
            rubrics = self.driver.find_element(By.XPATH, "//div[@style='padding:16px 8px']")

            for each_rubric in rubrics.find_elements(By.CLASS_NAME, "_mq2eit"):
                time.sleep(0.2)
                rubric_url = each_rubric.find_element(By.TAG_NAME, 'a').get_attribute("href")
                if rubric_url.startswith(self.main_url + "/subrubrics/"):
                    rubrics_url_lst.append(rubric_url)

            print(f"Найдено рубрик: {len(rubrics_url_lst)}")
            return rubrics_url_lst

        except Exception as e:
            print(e)

    def get_subrubrics_url(self, rubrics_url_list: list[str]) -> Optional[list[str]]:
        """
        Метод позволяет получить 2 вида URL ссылок.
        В цикле происходит перебор полученных URL адресов. В случае, если при переходе по очередному адресу,
        будет возвращаться ссылка на дополнительную подрубрику, то такая ссылка будет попадать в
        список 'subrubric_url_lst'.

        В случае, если же при переходе по URL адресу мы будем попадать на поисковую страницу, то такой URL добавляется в
        список 'urls_for_search'.

        :param rubrics_url_list: Список URL адресов, из которого будут извлекаться либо дополнительные адреса подрубрик,
        либо итоговые адреса для поиска информации о компаниях.

        :return: Список URL адресов дополнительных подрубрик для дальнейшей итерации по ним и
        извлечения поисковых страниц.
        """

        subrubric_url_lst = []
        rubric_tag = "//div[@class='_guxkefv']//div[@class='_hc69qa']"

        try:
            for url in rubrics_url_list:
                self.driver.get(url)
                print(f"Текущая рубрика: {self.driver.find_element(By.XPATH, rubric_tag).text}")
                print(f"Текущая страница: {url}")
                self.pause("//div[@class='_guxkefv']")

                subrubric_block = self.driver.find_element(By.CLASS_NAME, "_guxkefv")

                for each_subrubric in subrubric_block.find_elements(By.CLASS_NAME, "_mq2eit"):
                    time.sleep(0.2)
                    subrubric_url = each_subrubric.find_element(By.TAG_NAME, 'a').get_attribute("href")

                    # Проверяем, это URL адрес дополнительной подрубрики или адрес для поиска организаций.
                    if subrubric_url.startswith(self.main_url + "/subrubrics/"):
                        subrubric_url_lst.append(subrubric_url)
                    else:
                        self.urls_for_search.append(subrubric_url)

        except Exception as e:
            print(e)
            return

        print("Собрано итоговых поисковых ссылок: ", len(self.urls_for_search))
        print("Собрано дополнительных адресов для подрубрик: ", len(subrubric_url_lst))
        return subrubric_url_lst

    def collect_searched_urls(self, subrubrics_url_list: list[str]):
        """
        Метод для итогового формирования списка URL адресов для поиска информации об организациях.

        :param subrubrics_url_list: На вход метод принимает все найденные на предыдущем шаге
        URL адреса дополнительных рубрик.
        В процессе итерации по этим адреса, извлекаются итоговые адреса, из которых получаем информацию об организациях.

        :return: None. Дополняется список 'urls_for_search', который уже содержит некоторые итоговые адреса,
        полученные с помощью метода 'get_subrubrics_url()'.
        """

        rubric_tag = "//div[@class='_guxkefv']//div[@class='_hc69qa']"

        for url in subrubrics_url_list:
            self.driver.get(url)
            self.pause("//div[@class='_guxkefv']")
            searhed_block = self.driver.find_element(By.CLASS_NAME, "_guxkefv")

            for search_url in searhed_block.find_elements(By.CLASS_NAME, "_13w22bi"):
                link_for_search = search_url.find_element(By.TAG_NAME, 'a').get_attribute("href")

                print(f"Собираются итоговые поисковые сслыки для категории "
                      f"'{self.driver.find_element(By.XPATH, rubric_tag).text}'")
                print(link_for_search)

                self.urls_for_search.append(link_for_search)

        print("Собрано итоговых поисковых ссылок: ", len(self.urls_for_search))

    def run(self):
        try:
            rubrics_url = self.get_rubrics_url()
            subrubrics_url = self.get_subrubrics_url(rubrics_url)
            self.collect_searched_urls(subrubrics_url)

        except Exception as e:
            print(e)
            return

        finally:
            self.driver.close()
            self.driver.quit()


edp = EmployersDataParser()
edp.run()
