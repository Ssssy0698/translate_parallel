#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
改进版藏语翻译器
"""

import time
import random
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service

class ImprovedTibetanTranslator:
    def __init__(self, headless=True):
        self.url = "http://222.19.82.141:5002/index-Final.html"
        self.headless = headless
        self.driver = None
        self.wait = None
        self.is_initialized = False
        
    def setup_driver(self):
        try:
            options = webdriver.ChromeOptions()
            if self.headless:
                options.add_argument('--headless')
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-dev-shm-usage')
            options.add_argument('--window-size=1920,1080')
            options.add_argument('--disable-blink-features=AutomationControlled')
            options.add_experimental_option("excludeSwitches", ["enable-automation"])
            options.add_experimental_option('useAutomationExtension', False)
            
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=options)
            
            self.driver.implicitly_wait(15)
            self.wait = WebDriverWait(self.driver, 30)
            
            print("WebDriver初始化成功")
            return True
        except Exception as e:
            print(f"WebDriver初始化失败: {e}")
            return False
    
    def initialize(self):
        if self.is_initialized:
            return True
            
        try:
            print(f"正在访问: {self.url}")
            self.driver.get(self.url)
            
            self.wait.until(
                EC.presence_of_element_located((By.ID, "inputText"))
            )
            
            print("翻译页面加载成功")
            self.is_initialized = True
            return True
        except Exception as e:
            print(f"初始化页面时出错: {e}")
            return False
    
    def calculate_wait_time(self, tibetan_text):
        text_length = len(tibetan_text)
        
        if text_length <= 30:
            base_wait = 1.5
        elif text_length <= 80:
            base_wait = 2.5
        elif text_length <= 150:
            base_wait = 4.0
        elif text_length <= 300:
            base_wait = 6.0
        else:
            base_wait = 8.0
        
        if text_length > 300:
            extra = (text_length - 300) / 100 * 0.5
            base_wait += min(extra, 5.0)
        
        return base_wait
    
    def wait_for_translation_complete(self, base_wait_time):
        print(f"等待翻译: {base_wait_time:.1f}秒")
        time.sleep(base_wait_time)
        
        max_additional_wait = 10
        check_interval = 0.5
        total_additional = 0
        
        last_result = ""
        result_changed_count = 0
        
        while total_additional < max_additional_wait:
            try:
                result_div = self.driver.find_element(By.ID, "result")
                current_result = result_div.text
                
                if not current_result:
                    time.sleep(check_interval)
                    total_additional += check_interval
                    continue
                
                tibetan_punctuation = ['།', '༎', '༏', '༐', '༑', '༔']
                has_tibetan_char = any(char in current_result for char in tibetan_punctuation)
                
                if current_result == last_result:
                    result_changed_count += 1
                    if result_changed_count >= 3 and not has_tibetan_char:
                        print(f"翻译结果稳定，总等待时间: {base_wait_time + total_additional:.1f}秒")
                        return True
                else:
                    result_changed_count = 0
                
                if has_tibetan_char:
                    print(f"检测到藏语字符，继续等待... (已等待{total_additional:.1f}秒)")
                elif current_result != last_result:
                    print(f"翻译结果仍在变化，继续等待... (已等待{total_additional:.1f}秒)")
                
                last_result = current_result
                
            except Exception as e:
                print(f"检测翻译状态时出错: {e}")
            
            time.sleep(check_interval)
            total_additional += check_interval
        
        print(f"达到最大额外等待时间 ({max_additional_wait}秒)")
        return True
    
    def input_text_safely(self, text):
        try:
            input_box = self.wait.until(
                EC.presence_of_element_located((By.ID, "inputText"))
            )
            
            input_box.clear()
            time.sleep(0.1)
            
            chunk_size = 50
            for i in range(0, len(text), chunk_size):
                chunk = text[i:i+chunk_size]
                input_box.send_keys(chunk)
                time.sleep(0.05)
            
            print(f"文本输入完成 (长度: {len(text)} 字符)")
            return True
        except Exception as e:
            print(f"输入文本时出错: {e}")
            return False
    
    def translate_single(self, tibetan_text, max_retries=3):
        for attempt in range(max_retries):
            try:
                print(f"\n翻译尝试 {attempt + 1}/{max_retries}")
                print(f"原文长度: {len(tibetan_text)} 字符")
                print(f"原文预览: {tibetan_text[:80]}..." if len(tibetan_text) > 80 else f"原文: {tibetan_text}")
                
                if not self.is_initialized:
                    if not self.initialize():
                        continue
                
                base_wait = self.calculate_wait_time(tibetan_text)
                print(f"基础等待时间: {base_wait:.1f}秒")
                
                print("1. 输入文本...")
                if not self.input_text_safely(tibetan_text):
                    print("输入失败")
                    continue
                
                print("2. 点击翻译按钮...")
                try:
                    translate_button = self.wait.until(
                        EC.element_to_be_clickable((By.ID, "translateBtn"))
                    )
                    translate_button.click()
                    print("点击成功")
                except Exception as e:
                    print(f"点击失败: {e}")
                    continue
                
                print("3. 等待翻译...")
                self.wait_for_translation_complete(base_wait)
                
                print("4. 获取翻译结果...")
                try:
                    result_div = self.wait.until(
                        EC.presence_of_element_located((By.ID, "result"))
                    )
                    result = result_div.text
                    
                    if not result or result.isspace():
                        print("翻译结果为空")
                        continue
                    
                    validation_result = self.validate_translation(tibetan_text, result)
                    
                    if validation_result["valid"]:
                        print(f"翻译成功 (长度: {len(result)} 字符)")
                        print(f"结果预览: {result[:100]}..." if len(result) > 100 else f"结果: {result}")
                        return result
                    else:
                        print(f"翻译结果验证失败: {validation_result['reason']}")
                        print(f"当前结果: {result[:100]}...")
                        
                        if attempt < max_retries - 1:
                            print("将重试...")
                            self.clear_input_box()
                            continue
                        else:
                            print("达到最大重试次数")
                            return ""
                            
                except Exception as e:
                    print(f"获取结果时出错: {e}")
                    continue
                    
            except Exception as e:
                print(f"翻译过程中出错: {e}")
                if attempt < max_retries - 1:
                    print("将重试...")
                continue
        
        print("所有尝试均失败")
        return ""
    
    def clear_input_box(self):
        try:
            input_box = self.driver.find_element(By.ID, "inputText")
            input_box.clear()
            time.sleep(0.5)
        except:
            pass
    
    def validate_translation(self, original, translation):
        result = {"valid": True, "reason": ""}
        
        if not translation or translation.isspace():
            result["valid"] = False
            result["reason"] = "结果为空"
            return result
        
        tibetan_punctuation = ['།', '༎', '༏', '༐', '༑', '༔']
        if any(char in translation for char in tibetan_punctuation):
            result["valid"] = False
            result["reason"] = "包含藏语标点（可能未翻译完）"
            return result
        
        original_len = len(original)
        translation_len = len(translation)
        
        if original_len > 100 and translation_len < original_len * 0.2:
            result["valid"] = False
            result["reason"] = f"结果过短 ({translation_len}字符 vs 原文{original_len}字符)"
            return result
        
        if translation.endswith('...') or translation.endswith('……'):
            result["valid"] = False
            result["reason"] = "结果以省略号结尾（可能被截断）"
            return result
        
        if translation_len < 10 and original_len > 30:
            incomplete_patterns = ['的', '是', '在', '有', '了', '着', '过']
            if any(pattern in translation for pattern in incomplete_patterns) and translation_len < 5:
                result["valid"] = False
                result["reason"] = "结果过短且可能不完整"
                return result
        
        return result
    
    def close(self):
        if self.driver:
            self.driver.quit()
            print("浏览器已关闭")
    
    def __enter__(self):
        if self.setup_driver():
            return self
        else:
            raise Exception("无法初始化WebDriver")
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()