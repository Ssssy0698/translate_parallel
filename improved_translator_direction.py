#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
改进版藏语翻译器 - 支持双向翻译
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
    def __init__(self, headless=True, translation_direction="tibetan_to_chinese"):
        """
        初始化翻译器
        
        Args:
            headless: 是否使用无头模式
            translation_direction: 翻译方向
                "tibetan_to_chinese": 藏语到汉语 (默认)
                "chinese_to_tibetan": 汉语到藏语
        """
        self.url = "http://222.19.82.141:5002/index-Final.html"
        self.headless = headless
        self.driver = None
        self.wait = None
        self.is_initialized = False
        self.translation_direction = translation_direction
        self.translation_stats = {"success": 0, "failed": 0, "retries": 0}
        
        print(f"初始化翻译器 - 方向: {self.translation_direction}")
    
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
            
            # 添加用户代理和更多选项
            options.add_argument('--disable-gpu')
            options.add_argument('--disable-software-rasterizer')
            options.add_argument('--disable-extensions')
            options.add_argument('--disable-popup-blocking')
            options.add_argument('--ignore-certificate-errors')
            options.add_argument('--ignore-ssl-errors')
            
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=options)
            
            self.driver.implicitly_wait(20)  # 增加隐式等待时间
            self.wait = WebDriverWait(self.driver, 40)  # 增加显式等待时间
            
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
            
            # 等待页面完全加载
            self.wait.until(
                EC.presence_of_element_located((By.ID, "inputText"))
            )
            
            # 额外等待确保页面完全加载
            time.sleep(2)
            
            print("翻译页面加载成功")
            self.is_initialized = True
            return True
        except Exception as e:
            print(f"初始化页面时出错: {e}")
            return False
    
    def calculate_wait_time(self, text):
        """根据文本长度计算等待时间 - 更保守的策略"""
        text_length = len(text)
        
        # 更保守的等待时间
        if text_length <= 20:
            base_wait = 2.0
        elif text_length <= 50:
            base_wait = 3.0
        elif text_length <= 100:
            base_wait = 4.5
        elif text_length <= 200:
            base_wait = 6.0
        elif text_length <= 300:
            base_wait = 8.0
        else:
            base_wait = 10.0
        
        # 对于长文本，额外增加等待时间
        if text_length > 300:
            extra = (text_length - 300) / 100 * 0.8
            base_wait += min(extra, 8.0)
        
        # 汉语到藏语可能需要更多时间
        if self.translation_direction == "chinese_to_tibetan":
            base_wait *= 1.3
        
        return base_wait
    
    def wait_for_translation_complete(self, base_wait_time, original_text):
        """
        等待翻译完成 - 改进的等待逻辑
        
        关键改进：即使超时也返回结果，但会标记为可能不完整
        """
        print(f"等待翻译: {base_wait_time:.1f}秒")
        time.sleep(base_wait_time)
        
        max_additional_wait = 15  # 增加最大额外等待时间
        check_interval = 0.5
        total_additional = 0
        
        last_result = ""
        result_changed_count = 0
        stable_count_required = 3
        
        # 藏语标点列表
        tibetan_punctuation = ['།', '༎', '༏', '༐', '༑', '༔']
        
        # 如果是汉语到藏语，不需要检查藏语标点
        check_tibetan_chars = (self.translation_direction == "tibetan_to_chinese")
        
        while total_additional < max_additional_wait:
            try:
                result_div = self.driver.find_element(By.ID, "result")
                current_result = result_div.text
                
                if not current_result:
                    time.sleep(check_interval)
                    total_additional += check_interval
                    continue
                
                # 检查结果是否稳定
                if current_result == last_result:
                    result_changed_count += 1
                    
                    # 根据翻译方向决定稳定条件
                    if self.translation_direction == "chinese_to_tibetan":
                        # 汉语到藏语：只要稳定就认为完成
                        if result_changed_count >= stable_count_required:
                            print(f"翻译结果稳定，总等待时间: {base_wait_time + total_additional:.1f}秒")
                            return True
                    else:
                        # 藏语到汉语：需要稳定且不包含藏语字符
                        has_tibetan_char = any(char in current_result for char in tibetan_punctuation)
                        if result_changed_count >= stable_count_required and not has_tibetan_char:
                            print(f"翻译结果稳定，总等待时间: {base_wait_time + total_additional:.1f}秒")
                            return True
                else:
                    result_changed_count = 0
                
                # 如果结果变化，打印信息
                if current_result != last_result:
                    print(f"翻译结果变化中... (已等待{total_additional:.1f}秒)")
                
                last_result = current_result
                
            except Exception as e:
                print(f"检测翻译状态时出错: {e}")
            
            time.sleep(check_interval)
            total_additional += check_interval
        
        print(f"达到最大额外等待时间 ({max_additional_wait}秒)，返回当前结果")
        return True  # 即使超时也返回True，继续获取结果
    
    def input_text_safely(self, text):
        """安全输入文本 - 改进版本"""
        try:
            input_box = self.wait.until(
                EC.presence_of_element_located((By.ID, "inputText"))
            )
            
            # 清空输入框
            input_box.clear()
            time.sleep(0.3)  # 增加清空后的等待时间
            
            # 分段输入文本，避免过快
            chunk_size = 30  # 减少分块大小
            for i in range(0, len(text), chunk_size):
                chunk = text[i:i+chunk_size]
                input_box.send_keys(chunk)
                time.sleep(0.1)  # 增加分块输入间隔
            
            # 输入后短暂等待
            time.sleep(0.5)
            
            print(f"文本输入完成 (长度: {len(text)} 字符)")
            return True
        except Exception as e:
            print(f"输入文本时出错: {e}")
            return False
    
    def translate_single(self, text, max_retries=5):  # 增加最大重试次数
        """翻译单个句子 - 改进的重试机制"""
        for attempt in range(max_retries):
            try:
                print(f"\n翻译尝试 {attempt + 1}/{max_retries}")
                print(f"原文长度: {len(text)} 字符")
                
                # 显示原文预览（不显示太长的内容）
                if len(text) > 100:
                    print(f"原文预览: {text[:80]}...")
                else:
                    print(f"原文: {text}")
                
                if not self.is_initialized:
                    print("初始化翻译器...")
                    if not self.initialize():
                        print("初始化失败，等待后重试...")
                        time.sleep(5)
                        continue
                
                base_wait = self.calculate_wait_time(text)
                print(f"基础等待时间: {base_wait:.1f}秒")
                
                print("1. 输入文本...")
                if not self.input_text_safely(text):
                    print("输入失败，重试...")
                    self.translation_stats["retries"] += 1
                    time.sleep(3)
                    continue
                
                print("2. 点击翻译按钮...")
                try:
                    # 确保按钮可点击
                    time.sleep(0.5)
                    translate_button = self.wait.until(
                        EC.element_to_be_clickable((By.ID, "translateBtn"))
                    )
                    translate_button.click()
                    print("点击成功")
                except Exception as e:
                    print(f"点击翻译按钮失败: {e}")
                    self.translation_stats["retries"] += 1
                    time.sleep(3)
                    continue
                
                print("3. 等待翻译...")
                self.wait_for_translation_complete(base_wait, text)
                
                print("4. 获取翻译结果...")
                try:
                    # 等待结果出现
                    time.sleep(0.5)
                    result_div = self.driver.find_element(By.ID, "result")
                    result = result_div.text
                    
                    if not result or result.isspace():
                        print("翻译结果为空")
                        self.translation_stats["retries"] += 1
                        
                        # 如果是最后一次尝试，尝试刷新页面
                        if attempt == max_retries - 1:
                            print("最后一次尝试，刷新页面...")
                            self.driver.refresh()
                            time.sleep(3)
                            self.is_initialized = False
                        
                        time.sleep(2)
                        continue
                    
                    # 验证翻译结果
                    validation_result = self.validate_translation(text, result)
                    
                    if validation_result["valid"]:
                        print(f"翻译成功 (长度: {len(result)} 字符)")
                        if len(result) > 100:
                            print(f"结果预览: {result[:80]}...")
                        else:
                            print(f"结果: {result}")
                        
                        self.translation_stats["success"] += 1
                        return result
                    else:
                        print(f"翻译结果验证失败: {validation_result['reason']}")
                        print(f"当前结果: {result[:100]}...")
                        
                        self.translation_stats["retries"] += 1
                        
                        if attempt < max_retries - 1:
                            print("将重试...")
                            self.clear_input_box()
                            time.sleep(2)
                            continue
                        else:
                            print("达到最大重试次数，返回空结果")
                            self.translation_stats["failed"] += 1
                            return ""
                            
                except Exception as e:
                    print(f"获取结果时出错: {e}")
                    self.translation_stats["retries"] += 1
                    time.sleep(2)
                    continue
                    
            except Exception as e:
                print(f"翻译过程中出错: {e}")
                self.translation_stats["retries"] += 1
                
                if attempt < max_retries - 1:
                    print("将重试...")
                    time.sleep(3)
                continue
        
        print("所有尝试均失败")
        self.translation_stats["failed"] += 1
        return ""
    
    def clear_input_box(self):
        """清空输入框"""
        try:
            input_box = self.driver.find_element(By.ID, "inputText")
            input_box.clear()
            time.sleep(1)  # 增加清空后的等待时间
        except:
            pass
    
    def validate_translation(self, original, translation):
        """验证翻译结果 - 更宽松的验证逻辑"""
        result = {"valid": True, "reason": ""}
        
        if not translation or translation.isspace():
            result["valid"] = False
            result["reason"] = "结果为空"
            return result
        
        # 对于藏语到汉语，检查是否包含藏语标点
        if self.translation_direction == "tibetan_to_chinese":
            tibetan_punctuation = ['།', '༎', '༏', '༐', '༑', '༔']
            if any(char in translation for char in tibetan_punctuation):
                result["valid"] = False
                result["reason"] = "包含藏语标点（可能未翻译完）"
                return result
        
        original_len = len(original)
        translation_len = len(translation)
        
        # 根据翻译方向调整验证逻辑
        if self.translation_direction == "tibetan_to_chinese":
            # 藏语到汉语：通常藏语较长，汉语较短
            # 放宽验证条件
            if original_len > 20 and translation_len < 2:
                result["valid"] = False
                result["reason"] = f"结果过短 ({translation_len}字符 vs 原文{original_len}字符)"
                return result
        else:
            # 汉语到藏语：汉语较短，藏语可能较长
            # 更宽松的验证
            if original_len > 5 and translation_len < 1:
                result["valid"] = False
                result["reason"] = f"结果过短 ({translation_len}字符 vs 原文{original_len}字符)"
                return result
        
        # 检查常见的问题模式
        problematic_patterns = [
            "翻译失败", "错误", "无法翻译", "timeout", "error"
        ]
        
        for pattern in problematic_patterns:
            if pattern.lower() in translation.lower():
                result["valid"] = False
                result["reason"] = f"包含问题模式: {pattern}"
                return result
        
        # 检查是否以省略号结尾（可能被截断）
        if translation.endswith('...') or translation.endswith('……'):
            # 如果是短文本，这可能是个问题
            if translation_len < 10:
                result["valid"] = False
                result["reason"] = "结果以省略号结尾且过短（可能被截断）"
                return result
        
        return result
    
    def get_stats(self):
        """获取翻译统计信息"""
        return self.translation_stats
    
    def reset_stats(self):
        """重置统计信息"""
        self.translation_stats = {"success": 0, "failed": 0, "retries": 0}
    
    def close(self):
        if self.driver:
            self.driver.quit()
            print("浏览器已关闭")
            print(f"翻译统计: 成功={self.translation_stats['success']}, "
                  f"失败={self.translation_stats['failed']}, "
                  f"重试={self.translation_stats['retries']}")
    
    def __enter__(self):
        if self.setup_driver():
            return self
        else:
            raise Exception("无法初始化WebDriver")
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()