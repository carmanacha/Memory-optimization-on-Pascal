#!/usr/bin/env python3
"""
Расширенная автоматизация Union Build
Включает улучшенные алгоритмы для обхода защиты от ботов и более стабильную работу
"""

import asyncio
import aiohttp
import undetected_chrome as uc
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import Select
import pyautogui
from PIL import Image
import cv2
import numpy as np
import base64
from datetime import datetime
import pickle
import threading
import queue
from dataclasses import dataclass
from typing import Union, Callable
import subprocess
import psutil

from union_build_automation import UnionBuildAutomation

@dataclass
class NetworkConfig:
    """Конфигурация сети"""
    name: str
    chain_id: str
    rpc_url: str
    currency_symbol: str
    explorer_url: str
    bridge_fee: float = 0.001

class AdvancedUnionBuildAutomation(UnionBuildAutomation):
    """Расширенная версия автоматизации с дополнительными возможностями"""
    
    def __init__(self, config_file: str = "config.json"):
        super().__init__(config_file)
        
        # Расширенная конфигурация сетей
        self.network_configs = {
            'ethereum': NetworkConfig(
                name='Ethereum Mainnet',
                chain_id='0x1',
                rpc_url='https://mainnet.infura.io/v3/',
                currency_symbol='ETH',
                explorer_url='https://etherscan.io/',
                bridge_fee=0.005
            ),
            'arbitrum': NetworkConfig(
                name='Arbitrum One',
                chain_id='0xa4b1',
                rpc_url='https://arb1.arbitrum.io/rpc',
                currency_symbol='ETH',
                explorer_url='https://arbiscan.io/',
                bridge_fee=0.001
            ),
            'polygon': NetworkConfig(
                name='Polygon Mainnet',
                chain_id='0x89',
                rpc_url='https://polygon-rpc.com/',
                currency_symbol='MATIC',
                explorer_url='https://polygonscan.com/',
                bridge_fee=0.01
            ),
            'cosmos': NetworkConfig(
                name='Cosmos Hub',
                chain_id='cosmoshub-4',
                rpc_url='https://cosmos-rpc.polkachu.com',
                currency_symbol='ATOM',
                explorer_url='https://www.mintscan.io/cosmos/',
                bridge_fee=0.001
            ),
            'osmosis': NetworkConfig(
                name='Osmosis',
                chain_id='osmosis-1',
                rpc_url='https://osmosis-rpc.polkachu.com',
                currency_symbol='OSMO',
                explorer_url='https://www.mintscan.io/osmosis/',
                bridge_fee=0.001
            )
        }
        
        self.transaction_queue = queue.Queue()
        self.session_stats = {
            'total_transactions': 0,
            'successful_transactions': 0,
            'failed_transactions': 0,
            'total_volume': 0.0,
            'start_time': None,
            'errors': []
        }
    
    def setup_browser(self):
        """Настройка undetected-chrome для обхода защиты"""
        try:
            options = uc.ChromeOptions()
            
            # Основные настройки
            if self.config.get("headless", False):
                options.add_argument("--headless=new")
            
            # Настройки для обхода детекции
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")
            options.add_argument("--disable-blink-features=AutomationControlled")
            options.add_argument("--disable-extensions")
            options.add_argument("--no-first-run")
            options.add_argument("--disable-default-apps")
            options.add_argument("--disable-infobars")
            options.add_argument("--window-size=1920,1080")
            
            # Пользовательский агент
            if self.config.get("user_agent"):
                options.add_argument(f"--user-agent={self.config['user_agent']}")
            
            # Прокси если настроен
            if self.config.get("proxy", {}).get("enabled"):
                proxy_config = self.config["proxy"]
                proxy_str = f"{proxy_config['host']}:{proxy_config['port']}"
                options.add_argument(f"--proxy-server={proxy_str}")
            
            # Профиль Chrome
            if self.config.get("chrome_profile_path"):
                options.add_argument(f"--user-data-dir={self.config['chrome_profile_path']}")
            
            self.driver = uc.Chrome(options=options, version_main=None)
            
            # Дополнительные настройки JavaScript
            self.driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {
                'source': '''
                    Object.defineProperty(navigator, 'webdriver', {
                        get: () => undefined,
                    });
                    Object.defineProperty(navigator, 'plugins', {
                        get: () => [1, 2, 3, 4, 5],
                    });
                    Object.defineProperty(navigator, 'languages', {
                        get: () => ['en-US', 'en'],
                    });
                    window.chrome = { runtime: {} };
                '''
            })
            
            self.driver.implicitly_wait(self.config.get("implicit_wait", 15))
            self.driver.set_page_load_timeout(self.config.get("page_load_timeout", 45))
            self.wait = WebDriverWait(self.driver, 20)
            
            self.logger.info("Undetected Chrome браузер успешно инициализирован")
            return True
            
        except Exception as e:
            self.logger.error(f"Ошибка инициализации undetected Chrome: {e}")
            return False
    
    def wait_and_find_element(self, by, value, timeout=20, clickable=False):
        """Улучшенный поиск элементов с ожиданием"""
        try:
            if clickable:
                element = WebDriverWait(self.driver, timeout).until(
                    EC.element_to_be_clickable((by, value))
                )
            else:
                element = WebDriverWait(self.driver, timeout).until(
                    EC.presence_of_element_located((by, value))
                )
            return element
        except TimeoutException:
            self.logger.warning(f"Элемент {value} не найден за {timeout} секунд")
            return None
    
    def human_like_click(self, element):
        """Клик, имитирующий человеческое поведение"""
        try:
            # Наводим курсор на элемент
            ActionChains(self.driver).move_to_element(element).perform()
            time.sleep(random.uniform(0.1, 0.3))
            
            # Случайная задержка перед кликом
            time.sleep(random.uniform(0.05, 0.15))
            
            # Выполняем клик
            ActionChains(self.driver).click(element).perform()
            
        except Exception as e:
            # Fallback на JavaScript клик
            self.driver.execute_script("arguments[0].click();", element)
    
    def human_like_type(self, element, text, clear_first=True):
        """Печать текста, имитирующая человеческое поведение"""
        try:
            if clear_first:
                element.clear()
                time.sleep(random.uniform(0.1, 0.2))
            
            for char in text:
                element.send_keys(char)
                time.sleep(random.uniform(0.05, 0.15))
                
        except Exception as e:
            # Fallback на обычную отправку
            if clear_first:
                element.clear()
            element.send_keys(text)
    
    def take_screenshot_on_error(self, error_msg: str):
        """Создание скриншота при ошибке"""
        if self.config.get("screenshot_on_error", True):
            try:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"error_{timestamp}.png"
                self.driver.save_screenshot(filename)
                self.logger.info(f"Скриншот ошибки сохранен: {filename}")
            except Exception as e:
                self.logger.error(f"Не удалось создать скриншот: {e}")
    
    def detect_captcha(self):
        """Обнаружение капчи на странице"""
        captcha_indicators = [
            "//iframe[contains(@src, 'recaptcha')]",
            "//div[contains(@class, 'captcha')]",
            "//div[contains(@class, 'hcaptcha')]",
            "//*[contains(text(), 'verify') and contains(text(), 'human')]"
        ]
        
        for indicator in captcha_indicators:
            try:
                element = self.driver.find_element(By.XPATH, indicator)
                if element and element.is_displayed():
                    return True
            except NoSuchElementException:
                continue
        
        return False
    
    def handle_captcha(self):
        """Обработка капчи (базовая реализация)"""
        self.logger.warning("Обнаружена капча. Требуется ручное вмешательство.")
        input("Пожалуйста, решите капчу вручную и нажмите Enter для продолжения...")
    
    async def check_network_status(self, network: str):
        """Асинхронная проверка статуса сети"""
        try:
            config = self.network_configs.get(network)
            if not config:
                return False
            
            async with aiohttp.ClientSession() as session:
                async with session.get(config.rpc_url, timeout=10) as response:
                    return response.status == 200
        except:
            return False
    
    def smart_network_selection(self):
        """Умный выбор сетей на основе их статуса"""
        available_networks = self.config.get("networks_to_use", list(self.networks.keys()))
        
        # Фильтруем сети, которые доступны в конфигурации
        valid_networks = [net for net in available_networks if net in self.network_configs]
        
        if len(valid_networks) < 2:
            self.logger.error("Недостаточно валидных сетей для транзакций")
            return None, None
        
        # Выбираем случайные сети
        from_network = random.choice(valid_networks)
        to_network = random.choice([net for net in valid_networks if net != from_network])
        
        return from_network, to_network
    
    def calculate_optimal_amount(self, from_network: str, to_network: str):
        """Расчет оптимальной суммы с учетом комиссий"""
        base_amount = random.uniform(
            self.config.get("transaction_amount_min", 0.001),
            self.config.get("transaction_amount_max", 0.01)
        )
        
        # Учитываем комиссии сети
        from_config = self.network_configs.get(from_network)
        to_config = self.network_configs.get(to_network)
        
        if from_config and to_config:
            # Добавляем небольшой буфер для комиссий
            total_fee_estimate = from_config.bridge_fee + to_config.bridge_fee
            amount = base_amount + total_fee_estimate * 1.1
        else:
            amount = base_amount
        
        return round(amount, 6)
    
    def enhanced_connect_evm_wallet(self):
        """Улучшенное подключение EVM кошелька"""
        try:
            self.logger.info("Попытка подключения EVM кошелька (улучшенная версия)...")
            
            # Более широкий поиск кнопки подключения
            connect_selectors = [
                "//button[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'connect')]",
                "//button[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'wallet')]",
                "//div[contains(@class, 'connect') or contains(@class, 'wallet')]//button",
                "//*[@data-testid='connect-wallet' or @data-cy='connect-wallet']",
                "//button[contains(@class, 'connect') or contains(@class, 'wallet')]"
            ]
            
            wallet_button = None
            for selector in connect_selectors:
                try:
                    elements = self.driver.find_elements(By.XPATH, selector)
                    for element in elements:
                        if element.is_displayed() and element.is_enabled():
                            wallet_button = element
                            break
                    if wallet_button:
                        break
                except Exception:
                    continue
            
            if wallet_button:
                self.human_like_click(wallet_button)
                self.logger.info("Кнопка подключения кошелька нажата")
                time.sleep(random.uniform(2, 4))
                
                # Поиск MetaMask с улучшенной логикой
                metamask_found = self._find_and_click_metamask()
                
                if metamask_found:
                    time.sleep(random.uniform(2, 4))
                    return self._handle_metamask_popup_advanced()
                
            return False
            
        except Exception as e:
            self.logger.error(f"Ошибка подключения EVM кошелька: {e}")
            self.take_screenshot_on_error("evm_wallet_connection_error")
            return False
    
    def _find_and_click_metamask(self):
        """Улучшенный поиск и клик по MetaMask"""
        metamask_selectors = [
            "//button[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'metamask')]",
            "//div[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'metamask')]//parent::button",
            "//img[contains(@alt, 'MetaMask') or contains(@src, 'metamask')]//ancestor::button[1]",
            "//*[contains(@data-testid, 'metamask') or contains(@data-cy, 'metamask')]"
        ]
        
        for selector in metamask_selectors:
            try:
                elements = self.driver.find_elements(By.XPATH, selector)
                for element in elements:
                    if element.is_displayed() and element.is_enabled():
                        self.human_like_click(element)
                        self.logger.info("MetaMask опция выбрана")
                        return True
            except Exception:
                continue
        
        self.logger.warning("MetaMask опция не найдена")
        return False
    
    def _handle_metamask_popup_advanced(self):
        """Улучшенная обработка popup MetaMask"""
        try:
            current_window = self.driver.current_window_handle
            
            # Ждем появления нового окна
            for _ in range(10):
                windows = self.driver.window_handles
                if len(windows) > 1:
                    break
                time.sleep(1)
            
            for window in self.driver.window_handles:
                if window != current_window:
                    self.driver.switch_to.window(window)
                    
                    if "metamask" in self.driver.current_url.lower() or "extension" in self.driver.current_url:
                        self.logger.info("Переключились на окно MetaMask")
                        
                        # Ждем загрузки страницы MetaMask
                        time.sleep(random.uniform(2, 4))
                        
                        # Множественные попытки найти кнопки подтверждения
                        success = self._click_metamask_confirm_buttons()
                        
                        # Возвращаемся на основное окно
                        self.driver.switch_to.window(current_window)
                        return success
            
            self.driver.switch_to.window(current_window)
            return False
            
        except Exception as e:
            self.logger.error(f"Ошибка обработки MetaMask popup: {e}")
            return False
    
    def _click_metamask_confirm_buttons(self):
        """Клик по кнопкам подтверждения в MetaMask"""
        confirm_selectors = [
            "//button[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'connect')]",
            "//button[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'confirm')]",
            "//button[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'accept')]",
            "//button[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'approve')]",
            "//*[@data-testid='page-container-footer-next' or @data-testid='confirm-footer-button']"
        ]
        
        for attempt in range(3):
            for selector in confirm_selectors:
                try:
                    elements = self.driver.find_elements(By.XPATH, selector)
                    for element in elements:
                        if element.is_displayed() and element.is_enabled():
                            self.human_like_click(element)
                            self.logger.info("Кнопка подтверждения в MetaMask нажата")
                            time.sleep(random.uniform(1, 2))
                            return True
                except Exception:
                    continue
            
            time.sleep(2)  # Ждем перед следующей попыткой
        
        return False
    
    def run_automation_with_recovery(self):
        """Запуск автоматизации с возможностью восстановления"""
        self.session_stats['start_time'] = datetime.now()
        max_retries = self.config.get("retry_attempts", 3)
        
        for attempt in range(max_retries):
            try:
                self.logger.info(f"Попытка {attempt + 1}/{max_retries}")
                
                if self.setup_browser() and self.navigate_to_union_build():
                    # Проверяем наличие капчи
                    if self.detect_captcha():
                        self.handle_captcha()
                    
                    # Подключение кошельков
                    evm_success = self.enhanced_connect_evm_wallet()
                    time.sleep(random.uniform(3, 5))
                    
                    # Основной цикл транзакций
                    if evm_success:
                        return self._execute_transaction_cycle()
                
            except Exception as e:
                self.logger.error(f"Ошибка в попытке {attempt + 1}: {e}")
                self.session_stats['errors'].append(str(e))
                self.take_screenshot_on_error(f"attempt_{attempt + 1}_error")
                
                if self.driver:
                    self.driver.quit()
                
                if attempt < max_retries - 1:
                    delay = random.uniform(10, 30)
                    self.logger.info(f"Ждем {delay} секунд перед следующей попыткой")
                    time.sleep(delay)
        
        self.logger.error("Все попытки исчерпаны")
        return False
    
    def _execute_transaction_cycle(self):
        """Выполнение цикла транзакций"""
        max_transactions = self.config.get("max_transactions_per_session", 3)
        
        for i in range(max_transactions):
            try:
                self.logger.info(f"Транзакция {i+1}/{max_transactions}")
                
                from_network, to_network = self.smart_network_selection()
                if not from_network or not to_network:
                    continue
                
                amount = self.calculate_optimal_amount(from_network, to_network)
                
                success = self._execute_bridge_transaction_advanced(from_network, to_network, amount)
                
                self.session_stats['total_transactions'] += 1
                if success:
                    self.session_stats['successful_transactions'] += 1
                    self.session_stats['total_volume'] += amount
                else:
                    self.session_stats['failed_transactions'] += 1
                
                if i < max_transactions - 1:
                    self.random_delay()
                
            except Exception as e:
                self.logger.error(f"Ошибка в транзакции {i+1}: {e}")
                self.session_stats['failed_transactions'] += 1
        
        self._log_session_stats()
        return True
    
    def _execute_bridge_transaction_advanced(self, from_network: str, to_network: str, amount: float):
        """Улучшенное выполнение bridge транзакции"""
        try:
            self.logger.info(f"Выполнение транзакции: {from_network} -> {to_network}, сумма: {amount}")
            
            # Поиск и заполнение формы с улучшенной логикой
            form_filled = self._fill_transaction_form_advanced(from_network, to_network, amount)
            
            if form_filled:
                submit_success = self._submit_transaction_advanced()
                if submit_success:
                    return self._handle_transaction_confirmation_advanced()
            
            return False
            
        except Exception as e:
            self.logger.error(f"Ошибка выполнения транзакции: {e}")
            self.take_screenshot_on_error("transaction_error")
            return False
    
    def _fill_transaction_form_advanced(self, from_network: str, to_network: str, amount: float):
        """Улучшенное заполнение формы транзакции"""
        try:
            # Поиск полей формы с множественными селекторами
            amount_input = self._find_element_advanced([
                "//input[@placeholder and contains(translate(@placeholder, 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'amount')]",
                "//input[@type='number']",
                "//input[contains(@class, 'amount')]",
                "//*[@data-testid='amount-input' or @data-cy='amount-input']"
            ])
            
            if amount_input:
                self.human_like_type(amount_input, str(amount))
                self.logger.info(f"Сумма {amount} введена")
                time.sleep(random.uniform(1, 2))
            
            # Выбор сетей (если необходимо)
            self._select_networks_if_needed(from_network, to_network)
            
            return True
            
        except Exception as e:
            self.logger.error(f"Ошибка заполнения формы: {e}")
            return False
    
    def _find_element_advanced(self, selectors: list, timeout=10):
        """Улучшенный поиск элемента по множественным селекторам"""
        for selector in selectors:
            try:
                element = WebDriverWait(self.driver, timeout).until(
                    EC.presence_of_element_located((By.XPATH, selector))
                )
                if element.is_displayed() and element.is_enabled():
                    return element
            except TimeoutException:
                continue
        return None
    
    def _select_networks_if_needed(self, from_network: str, to_network: str):
        """Выбор сетей если есть селекторы"""
        # Логика выбора сетей (зависит от интерфейса Union Build)
        pass
    
    def _submit_transaction_advanced(self):
        """Улучшенная отправка транзакции"""
        submit_selectors = [
            "//button[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'bridge')]",
            "//button[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'transfer')]",
            "//button[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'send')]",
            "//button[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'submit')]",
            "//*[@data-testid='submit-button' or @data-cy='submit-button']"
        ]
        
        submit_button = self._find_element_advanced(submit_selectors)
        if submit_button:
            self.human_like_click(submit_button)
            self.logger.info("Кнопка отправки транзакции нажата")
            time.sleep(random.uniform(2, 4))
            return True
        
        self.logger.warning("Кнопка отправки не найдена")
        return False
    
    def _handle_transaction_confirmation_advanced(self):
        """Улучшенная обработка подтверждения транзакции"""
        try:
            # Ждем появления popup кошелька
            time.sleep(random.uniform(3, 5))
            
            current_window = self.driver.current_window_handle
            
            for window in self.driver.window_handles:
                if window != current_window:
                    self.driver.switch_to.window(window)
                    
                    if any(keyword in self.driver.current_url.lower() 
                           for keyword in ['metamask', 'extension', 'keplr']):
                        
                        success = self._confirm_transaction_in_wallet()
                        self.driver.switch_to.window(current_window)
                        return success
            
            self.driver.switch_to.window(current_window)
            return False
            
        except Exception as e:
            self.logger.error(f"Ошибка подтверждения транзакции: {e}")
            return False
    
    def _confirm_transaction_in_wallet(self):
        """Подтверждение транзакции в кошельке"""
        confirm_selectors = [
            "//button[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'confirm')]",
            "//button[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'send')]",
            "//button[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'sign')]",
            "//button[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'approve')]"
        ]
        
        for attempt in range(5):
            confirm_button = self._find_element_advanced(confirm_selectors, timeout=5)
            if confirm_button:
                self.human_like_click(confirm_button)
                self.logger.info("Транзакция подтверждена в кошельке")
                time.sleep(random.uniform(2, 4))
                return True
            time.sleep(2)
        
        return False
    
    def _log_session_stats(self):
        """Логирование статистики сессии"""
        duration = datetime.now() - self.session_stats['start_time']
        
        self.logger.info("=== СТАТИСТИКА СЕССИИ ===")
        self.logger.info(f"Продолжительность: {duration}")
        self.logger.info(f"Всего транзакций: {self.session_stats['total_transactions']}")
        self.logger.info(f"Успешных: {self.session_stats['successful_transactions']}")
        self.logger.info(f"Неудачных: {self.session_stats['failed_transactions']}")
        self.logger.info(f"Общий объем: {self.session_stats['total_volume']}")
        self.logger.info(f"Количество ошибок: {len(self.session_stats['errors'])}")

def main():
    """Главная функция для расширенной автоматизации"""
    automation = AdvancedUnionBuildAutomation()
    success = automation.run_automation_with_recovery()
    
    if success:
        print("Расширенная автоматизация завершена успешно")
    else:
        print("Расширенная автоматизация завершена с ошибками")

if __name__ == "__main__":
    main()