#!/usr/bin/env python3
"""
Union Build Automation Script
Автоматизирует подключение кошельков и выполнение транзакций на Union Build
"""

import time
import random
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import json
import os

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import TimeoutException, NoSuchElementException

class UnionBuildAutomation:
    """Класс для автоматизации работы с Union Build"""
    
    def __init__(self, config_file: str = "config.json"):
        """Инициализация автоматизации"""
        self.config = self._load_config(config_file)
        self.driver = None
        self.wait = None
        self.setup_logging()
        
        # Поддерживаемые сети
        self.networks = {
            'ethereum': {'name': 'Ethereum', 'type': 'evm'},
            'arbitrum': {'name': 'Arbitrum', 'type': 'evm'},
            'polygon': {'name': 'Polygon', 'type': 'evm'},
            'bsc': {'name': 'BSC', 'type': 'evm'},
            'cosmos': {'name': 'Cosmos Hub', 'type': 'cosmos'},
            'osmosis': {'name': 'Osmosis', 'type': 'cosmos'},
            'juno': {'name': 'Juno', 'type': 'cosmos'},
        }
        
    def _load_config(self, config_file: str) -> Dict:
        """Загрузка конфигурации"""
        default_config = {
            "min_delay": 30,
            "max_delay": 300,
            "transaction_amount_min": 0.01,
            "transaction_amount_max": 0.1,
            "headless": False,
            "implicit_wait": 10,
            "page_load_timeout": 30,
            "networks_to_use": ["ethereum", "arbitrum", "cosmos", "osmosis"],
            "max_transactions_per_session": 5,
            "wallet_passwords": {
                "metamask": "",
                "keplr": ""
            }
        }
        
        if os.path.exists(config_file):
            try:
                with open(config_file, 'r', encoding='utf-8') as f:
                    user_config = json.load(f)
                default_config.update(user_config)
            except Exception as e:
                logging.warning(f"Ошибка загрузки конфига: {e}, используется конфиг по умолчанию")
        
        return default_config
    
    def setup_logging(self):
        """Настройка логирования"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('union_build_automation.log', encoding='utf-8'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    def setup_browser(self):
        """Настройка браузера Chrome"""
        chrome_options = Options()
        
        if self.config.get("headless", False):
            chrome_options.add_argument("--headless")
        
        # Настройки для расширений кошельков
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        chrome_options.add_argument("--disable-web-security")
        chrome_options.add_argument("--allow-running-insecure-content")
        chrome_options.add_argument("--disable-extensions-file-access-check")
        chrome_options.add_argument("--disable-extensions-http-throttling")
        
        # Увеличиваем размер окна
        chrome_options.add_argument("--window-size=1920,1080")
        
        try:
            self.driver = webdriver.Chrome(options=chrome_options)
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            self.driver.implicitly_wait(self.config.get("implicit_wait", 10))
            self.driver.set_page_load_timeout(self.config.get("page_load_timeout", 30))
            self.wait = WebDriverWait(self.driver, 15)
            
            self.logger.info("Браузер успешно инициализирован")
            return True
            
        except Exception as e:
            self.logger.error(f"Ошибка инициализации браузера: {e}")
            return False
    
    def navigate_to_union_build(self):
        """Переход на сайт Union Build"""
        try:
            self.logger.info("Переход на https://app.union.build/")
            self.driver.get("https://app.union.build/")
            
            # Ждем загрузки страницы
            self.wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
            
            self.logger.info("Страница Union Build загружена")
            time.sleep(3)
            return True
            
        except Exception as e:
            self.logger.error(f"Ошибка перехода на Union Build: {e}")
            return False
    
    def connect_evm_wallet(self):
        """Подключение EVM кошелька (MetaMask)"""
        try:
            self.logger.info("Попытка подключения EVM кошелька...")
            
            # Ищем кнопку подключения кошелька
            connect_selectors = [
                "button[data-testid='connect-wallet']",
                "button:contains('Connect Wallet')",
                "button:contains('Connect')",
                ".connect-wallet",
                "[data-cy='connect-wallet']"
            ]
            
            wallet_button = None
            for selector in connect_selectors:
                try:
                    if ":contains" in selector:
                        # Для текстового поиска используем XPath
                        xpath = f"//button[contains(text(), '{selector.split(':contains(')[1].replace(')', '').replace(\"'\", '')}')]"
                        wallet_button = self.driver.find_element(By.XPATH, xpath)
                    else:
                        wallet_button = self.driver.find_element(By.CSS_SELECTOR, selector)
                    break
                except NoSuchElementException:
                    continue
            
            if not wallet_button:
                # Пробуем найти любую кнопку с текстом, связанным с подключением
                buttons = self.driver.find_elements(By.TAG_NAME, "button")
                for button in buttons:
                    text = button.text.lower()
                    if any(word in text for word in ["connect", "подключ", "wallet", "кошел"]):
                        wallet_button = button
                        break
            
            if wallet_button:
                self.driver.execute_script("arguments[0].click();", wallet_button)
                self.logger.info("Кнопка подключения кошелька нажата")
                time.sleep(2)
                
                # Ищем MetaMask в списке кошельков
                metamask_selectors = [
                    "button:contains('MetaMask')",
                    "[data-testid='metamask']",
                    ".metamask",
                    "img[alt*='MetaMask']"
                ]
                
                for selector in metamask_selectors:
                    try:
                        if ":contains" in selector:
                            xpath = "//button[contains(text(), 'MetaMask')] | //div[contains(text(), 'MetaMask')]//parent::button"
                            metamask_option = self.driver.find_element(By.XPATH, xpath)
                        else:
                            metamask_option = self.driver.find_element(By.CSS_SELECTOR, selector)
                        
                        self.driver.execute_script("arguments[0].click();", metamask_option)
                        self.logger.info("MetaMask выбран")
                        break
                    except NoSuchElementException:
                        continue
                
                # Ждем появления popup MetaMask и обрабатываем его
                time.sleep(3)
                self._handle_metamask_popup()
                return True
            else:
                self.logger.warning("Кнопка подключения кошелька не найдена")
                return False
                
        except Exception as e:
            self.logger.error(f"Ошибка подключения EVM кошелька: {e}")
            return False
    
    def connect_cosmos_wallet(self):
        """Подключение Cosmos кошелька (Keplr)"""
        try:
            self.logger.info("Попытка подключения Cosmos кошелька...")
            
            # Ищем кнопку для Cosmos/Keplr
            keplr_selectors = [
                "button:contains('Keplr')",
                "button:contains('Cosmos')",
                "[data-testid='keplr']",
                ".keplr",
                "img[alt*='Keplr']"
            ]
            
            for selector in keplr_selectors:
                try:
                    if ":contains" in selector:
                        text = selector.split(':contains(')[1].replace(')', '').replace("'", '')
                        xpath = f"//button[contains(text(), '{text}')] | //div[contains(text(), '{text}')]//parent::button"
                        keplr_option = self.driver.find_element(By.XPATH, xpath)
                    else:
                        keplr_option = self.driver.find_element(By.CSS_SELECTOR, selector)
                    
                    self.driver.execute_script("arguments[0].click();", keplr_option)
                    self.logger.info("Keplr выбран")
                    time.sleep(3)
                    self._handle_keplr_popup()
                    return True
                except NoSuchElementException:
                    continue
            
            self.logger.warning("Кнопка Keplr не найдена")
            return False
            
        except Exception as e:
            self.logger.error(f"Ошибка подключения Cosmos кошелька: {e}")
            return False
    
    def _handle_metamask_popup(self):
        """Обработка popup MetaMask"""
        try:
            # Переключаемся на popup окно MetaMask
            current_window = self.driver.current_window_handle
            all_windows = self.driver.window_handles
            
            for window in all_windows:
                if window != current_window:
                    self.driver.switch_to.window(window)
                    if "metamask" in self.driver.current_url.lower() or "extension" in self.driver.current_url:
                        self.logger.info("Переключились на окно MetaMask")
                        
                        # Ищем кнопки подтверждения
                        time.sleep(2)
                        confirm_buttons = [
                            "button:contains('Connect')",
                            "button:contains('Confirm')",
                            "button:contains('Accept')",
                            "[data-testid='page-container-footer-next']"
                        ]
                        
                        for selector in confirm_buttons:
                            try:
                                if ":contains" in selector:
                                    text = selector.split(':contains(')[1].replace(')', '').replace("'", '')
                                    button = self.driver.find_element(By.XPATH, f"//button[contains(text(), '{text}')]")
                                else:
                                    button = self.driver.find_element(By.CSS_SELECTOR, selector)
                                
                                button.click()
                                self.logger.info("Подтверждение в MetaMask выполнено")
                                break
                            except NoSuchElementException:
                                continue
                        
                        time.sleep(2)
                        break
            
            # Возвращаемся на основное окно
            self.driver.switch_to.window(current_window)
            
        except Exception as e:
            self.logger.error(f"Ошибка обработки MetaMask popup: {e}")
    
    def _handle_keplr_popup(self):
        """Обработка popup Keplr"""
        try:
            # Аналогично MetaMask
            current_window = self.driver.current_window_handle
            all_windows = self.driver.window_handles
            
            for window in all_windows:
                if window != current_window:
                    self.driver.switch_to.window(window)
                    if "keplr" in self.driver.current_url.lower() or "extension" in self.driver.current_url:
                        self.logger.info("Переключились на окно Keplr")
                        
                        time.sleep(2)
                        confirm_buttons = [
                            "button:contains('Approve')",
                            "button:contains('Connect')",
                            "button:contains('Confirm')"
                        ]
                        
                        for selector in confirm_buttons:
                            try:
                                text = selector.split(':contains(')[1].replace(')', '').replace("'", '')
                                button = self.driver.find_element(By.XPATH, f"//button[contains(text(), '{text}')]")
                                button.click()
                                self.logger.info("Подтверждение в Keplr выполнено")
                                break
                            except NoSuchElementException:
                                continue
                        
                        time.sleep(2)
                        break
            
            self.driver.switch_to.window(current_window)
            
        except Exception as e:
            self.logger.error(f"Ошибка обработки Keplr popup: {e}")
    
    def perform_random_transaction(self):
        """Выполнение случайной транзакции"""
        try:
            # Выбираем случайные сети из настроенных
            available_networks = [net for net in self.config.get("networks_to_use", list(self.networks.keys())) 
                                if net in self.networks]
            
            if len(available_networks) < 2:
                self.logger.error("Недостаточно сетей для выполнения транзакции")
                return False
            
            from_network = random.choice(available_networks)
            to_network = random.choice([net for net in available_networks if net != from_network])
            
            amount = round(random.uniform(
                self.config.get("transaction_amount_min", 0.01),
                self.config.get("transaction_amount_max", 0.1)
            ), 4)
            
            self.logger.info(f"Выполняется транзакция: {from_network} -> {to_network}, сумма: {amount}")
            
            # Здесь должна быть логика поиска и заполнения формы транзакции
            success = self._execute_bridge_transaction(from_network, to_network, amount)
            
            if success:
                self.logger.info("Транзакция успешно инициирована")
                return True
            else:
                self.logger.error("Ошибка выполнения транзакции")
                return False
                
        except Exception as e:
            self.logger.error(f"Ошибка выполнения случайной транзакции: {e}")
            return False
    
    def _execute_bridge_transaction(self, from_network: str, to_network: str, amount: float):
        """Выполнение bridge транзакции"""
        try:
            # Ищем элементы формы транзакции
            # Это зависит от конкретного интерфейса Union Build
            
            # Поиск селектора исходной сети
            from_network_selector = self._find_network_selector("from")
            if from_network_selector:
                self._select_network(from_network_selector, from_network)
            
            # Поиск селектора целевой сети
            to_network_selector = self._find_network_selector("to")
            if to_network_selector:
                self._select_network(to_network_selector, to_network)
            
            # Ввод суммы
            amount_input = self._find_amount_input()
            if amount_input:
                amount_input.clear()
                amount_input.send_keys(str(amount))
            
            # Поиск и нажатие кнопки отправки
            submit_button = self._find_submit_button()
            if submit_button:
                submit_button.click()
                time.sleep(2)
                
                # Обработка подтверждения в кошельке
                self._handle_transaction_confirmation()
                return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"Ошибка выполнения bridge транзакции: {e}")
            return False
    
    def _find_network_selector(self, selector_type: str):
        """Поиск селектора сети"""
        selectors = [
            f"select[data-testid='{selector_type}-network']",
            f".{selector_type}-network-selector",
            f"[data-cy='{selector_type}-network']",
            f".network-select.{selector_type}"
        ]
        
        for selector in selectors:
            try:
                element = self.driver.find_element(By.CSS_SELECTOR, selector)
                return element
            except NoSuchElementException:
                continue
        
        return None
    
    def _select_network(self, selector_element, network: str):
        """Выбор сети в селекторе"""
        try:
            selector_element.click()
            time.sleep(1)
            
            network_option = self.driver.find_element(By.XPATH, 
                f"//option[contains(text(), '{self.networks[network]['name']}')]")
            network_option.click()
            
        except Exception as e:
            self.logger.error(f"Ошибка выбора сети {network}: {e}")
    
    def _find_amount_input(self):
        """Поиск поля ввода суммы"""
        selectors = [
            "input[data-testid='amount']",
            "input[placeholder*='amount']",
            "input[type='number']",
            ".amount-input input"
        ]
        
        for selector in selectors:
            try:
                element = self.driver.find_element(By.CSS_SELECTOR, selector)
                return element
            except NoSuchElementException:
                continue
        
        return None
    
    def _find_submit_button(self):
        """Поиск кнопки отправки транзакции"""
        selectors = [
            "button[data-testid='submit-transaction']",
            "button:contains('Bridge')",
            "button:contains('Transfer')",
            "button:contains('Send')",
            ".submit-button",
            ".bridge-button"
        ]
        
        for selector in selectors:
            try:
                if ":contains" in selector:
                    text = selector.split(':contains(')[1].replace(')', '').replace("'", '')
                    element = self.driver.find_element(By.XPATH, f"//button[contains(text(), '{text}')]")
                else:
                    element = self.driver.find_element(By.CSS_SELECTOR, selector)
                return element
            except NoSuchElementException:
                continue
        
        return None
    
    def _handle_transaction_confirmation(self):
        """Обработка подтверждения транзакции в кошельке"""
        try:
            time.sleep(3)  # Ждем появления popup
            
            current_window = self.driver.current_window_handle
            all_windows = self.driver.window_handles
            
            for window in all_windows:
                if window != current_window:
                    self.driver.switch_to.window(window)
                    
                    # Ищем кнопки подтверждения
                    confirm_buttons = [
                        "button:contains('Confirm')",
                        "button:contains('Send')",
                        "button:contains('Sign')",
                        "[data-testid='page-container-footer-next']"
                    ]
                    
                    for selector in confirm_buttons:
                        try:
                            if ":contains" in selector:
                                text = selector.split(':contains(')[1].replace(')', '').replace("'", '')
                                button = self.driver.find_element(By.XPATH, f"//button[contains(text(), '{text}')]")
                            else:
                                button = self.driver.find_element(By.CSS_SELECTOR, selector)
                            
                            button.click()
                            self.logger.info("Транзакция подтверждена в кошельке")
                            time.sleep(2)
                            break
                        except NoSuchElementException:
                            continue
                    
                    break
            
            self.driver.switch_to.window(current_window)
            
        except Exception as e:
            self.logger.error(f"Ошибка подтверждения транзакции: {e}")
    
    def random_delay(self):
        """Случайная задержка между действиями"""
        delay = random.randint(
            self.config.get("min_delay", 30),
            self.config.get("max_delay", 300)
        )
        self.logger.info(f"Ожидание {delay} секунд до следующего действия")
        time.sleep(delay)
    
    def run_automation(self):
        """Запуск основного цикла автоматизации"""
        if not self.setup_browser():
            return False
        
        try:
            if not self.navigate_to_union_build():
                return False
            
            # Подключение кошельков
            self.logger.info("Подключение кошельков...")
            evm_connected = self.connect_evm_wallet()
            time.sleep(3)
            cosmos_connected = self.connect_cosmos_wallet()
            
            if not (evm_connected or cosmos_connected):
                self.logger.error("Не удалось подключить ни одного кошелька")
                return False
            
            # Основной цикл транзакций
            max_transactions = self.config.get("max_transactions_per_session", 5)
            successful_transactions = 0
            
            for i in range(max_transactions):
                self.logger.info(f"Выполнение транзакции {i+1}/{max_transactions}")
                
                if self.perform_random_transaction():
                    successful_transactions += 1
                
                if i < max_transactions - 1:  # Не ждем после последней транзакции
                    self.random_delay()
            
            self.logger.info(f"Сессия завершена. Успешных транзакций: {successful_transactions}/{max_transactions}")
            return True
            
        except Exception as e:
            self.logger.error(f"Ошибка в процессе автоматизации: {e}")
            return False
        
        finally:
            if self.driver:
                self.driver.quit()
                self.logger.info("Браузер закрыт")

def main():
    """Главная функция"""
    automation = UnionBuildAutomation()
    success = automation.run_automation()
    
    if success:
        print("Автоматизация завершена успешно")
    else:
        print("Автоматизация завершена с ошибками")

if __name__ == "__main__":
    main()