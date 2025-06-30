#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
EML文件解析工具
用于解析邮件客户端导出的.eml格式文件
"""

import os
import json
import email
import base64
import quopri
import mimetypes
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from email.message import EmailMessage
from email.header import decode_header
from email.utils import parsedate_to_datetime, parseaddr
from datetime import datetime
import argparse
import logging

class EMLParser:
    """EML文件解析器"""
    
    def __init__(self, output_dir: str = "eml_output"):
        """
        初始化EML解析器
        
        Args:
            output_dir: 输出目录
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
        # 设置日志
        self._setup_logging()
        
        # 统计信息
        self.stats = {
            'total_files': 0,
            'parsed_successfully': 0,
            'parse_errors': 0,
            'attachments_extracted': 0
        }
    
    def _setup_logging(self):
        """设置日志"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('eml_parser.log', encoding='utf-8'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    def _decode_header(self, header_value: str) -> str:
        """
        解码邮件头信息
        
        Args:
            header_value: 头信息值
            
        Returns:
            解码后的字符串
        """
        if not header_value:
            return ""
        
        try:
            decoded_parts = decode_header(header_value)
            decoded_string = ""
            
            for part, encoding in decoded_parts:
                if isinstance(part, bytes):
                    if encoding:
                        decoded_string += part.decode(encoding)
                    else:
                        # 尝试常见编码
                        for enc in ['utf-8', 'gb2312', 'gbk', 'big5']:
                            try:
                                decoded_string += part.decode(enc)
                                break
                            except UnicodeDecodeError:
                                continue
                        else:
                            decoded_string += part.decode('utf-8', errors='ignore')
                else:
                    decoded_string += str(part)
            
            return decoded_string.strip()
        except Exception as e:
            self.logger.warning(f"解码头信息失败: {e}")
            return str(header_value)
    
    def _parse_address(self, address_str: str) -> Dict[str, str]:
        """
        解析邮件地址
        
        Args:
            address_str: 地址字符串
            
        Returns:
            包含姓名和邮箱的字典
        """
        if not address_str:
            return {"name": "", "email": ""}
        
        try:
            decoded_addr = self._decode_header(address_str)
            name, email_addr = parseaddr(decoded_addr)
            return {
                "name": name.strip(),
                "email": email_addr.strip()
            }
        except Exception as e:
            self.logger.warning(f"解析地址失败: {e}")
            return {"name": "", "email": address_str}
    
    def _parse_addresses(self, address_str: str) -> List[Dict[str, str]]:
        """
        解析多个邮件地址
        
        Args:
            address_str: 地址字符串（可能包含多个地址）
            
        Returns:
            地址列表
        """
        if not address_str:
            return []
        
        addresses = []
        # 简单分割，实际情况可能更复杂
        for addr in address_str.split(','):
            addr = addr.strip()
            if addr:
                addresses.append(self._parse_address(addr))
        
        return addresses
    
    def _extract_headers(self, message: EmailMessage) -> Dict[str, Any]:
        """
        提取邮件头信息
        
        Args:
            message: 邮件消息对象
            
        Returns:
            头信息字典
        """
        headers = {}
        
        # 基本头信息
        basic_headers = [
            'Message-ID', 'Date', 'From', 'To', 'Cc', 'Bcc', 'Subject',
            'Reply-To', 'Return-Path', 'In-Reply-To', 'References',
            'Content-Type', 'Content-Transfer-Encoding', 'MIME-Version'
        ]
        
        for header in basic_headers:
            value = message.get(header)
            if value:
                headers[header.lower().replace('-', '_')] = self._decode_header(value)
        
        # 解析特殊头信息
        if headers.get('from'):
            headers['from_parsed'] = self._parse_address(headers['from'])
        
        if headers.get('to'):
            headers['to_parsed'] = self._parse_addresses(headers['to'])
        
        if headers.get('cc'):
            headers['cc_parsed'] = self._parse_addresses(headers['cc'])
        
        if headers.get('bcc'):
            headers['bcc_parsed'] = self._parse_addresses(headers['bcc'])
        
        # 解析日期
        if headers.get('date'):
            try:
                date_obj = parsedate_to_datetime(headers['date'])
                headers['date_parsed'] = date_obj.isoformat()
                headers['date_timestamp'] = date_obj.timestamp()
            except Exception as e:
                self.logger.warning(f"解析日期失败: {e}")
        
        # 添加所有其他头信息
        headers['all_headers'] = {}
        for key, value in message.items():
            decoded_key = key.lower()
            decoded_value = self._decode_header(value)
            headers['all_headers'][decoded_key] = decoded_value
        
        return headers
    
    def _decode_content(self, content: bytes, encoding: str = None) -> str:
        """
        解码邮件内容
        
        Args:
            content: 内容字节
            encoding: 编码方式
            
        Returns:
            解码后的文本
        """
        if not content:
            return ""
        
        # 如果已经是字符串，直接返回
        if isinstance(content, str):
            return content
        
        # 尝试指定编码
        if encoding:
            try:
                return content.decode(encoding)
            except Exception as e:
                self.logger.warning(f"使用编码 {encoding} 解码失败: {e}")
        
        # 尝试常见编码
        encodings = ['utf-8', 'gb2312', 'gbk', 'big5', 'iso-8859-1', 'windows-1252']
        for enc in encodings:
            try:
                return content.decode(enc)
            except UnicodeDecodeError:
                continue
        
        # 最后使用utf-8并忽略错误
        return content.decode('utf-8', errors='ignore')
    
    def _extract_body(self, message: EmailMessage) -> Dict[str, str]:
        """
        提取邮件正文
        
        Args:
            message: 邮件消息对象
            
        Returns:
            包含文本和HTML内容的字典
        """
        body = {
            'text': '',
            'html': '',
            'parts': []
        }
        
        def extract_part(part):
            content_type = part.get_content_type()
            content_disposition = part.get('Content-Disposition', '')
            
            # 跳过附件
            if 'attachment' in content_disposition:
                return
            
            if content_type == 'text/plain':
                content = part.get_payload(decode=True)
                if content:
                    charset = part.get_content_charset() or 'utf-8'
                    decoded_content = self._decode_content(content, charset)
                    body['text'] += decoded_content + '\n'
                    body['parts'].append({
                        'type': 'text',
                        'content': decoded_content,
                        'charset': charset
                    })
            
            elif content_type == 'text/html':
                content = part.get_payload(decode=True)
                if content:
                    charset = part.get_content_charset() or 'utf-8'
                    decoded_content = self._decode_content(content, charset)
                    body['html'] += decoded_content + '\n'
                    body['parts'].append({
                        'type': 'html',
                        'content': decoded_content,
                        'charset': charset
                    })
        
        if message.is_multipart():
            for part in message.walk():
                extract_part(part)
        else:
            extract_part(message)
        
        # 清理内容
        body['text'] = body['text'].strip()
        body['html'] = body['html'].strip()
        
        return body
    
    def _extract_attachments(self, message: EmailMessage, eml_filename: str) -> List[Dict[str, Any]]:
        """
        提取附件
        
        Args:
            message: 邮件消息对象
            eml_filename: EML文件名（用于创建附件目录）
            
        Returns:
            附件信息列表
        """
        attachments = []
        
        # 创建附件目录
        attachment_dir = self.output_dir / "attachments" / Path(eml_filename).stem
        attachment_dir.mkdir(parents=True, exist_ok=True)
        
        for part in message.walk():
            content_disposition = part.get('Content-Disposition', '')
            content_type = part.get_content_type()
            
            # 检查是否为附件
            if 'attachment' in content_disposition or part.get_filename():
                filename = part.get_filename()
                if filename:
                    filename = self._decode_header(filename)
                else:
                    # 生成默认文件名
                    ext = mimetypes.guess_extension(content_type) or '.bin'
                    filename = f"attachment_{len(attachments) + 1}{ext}"
                
                # 获取附件内容
                content = part.get_payload(decode=True)
                if content:
                    # 保存附件
                    attachment_path = attachment_dir / filename
                    try:
                        with open(attachment_path, 'wb') as f:
                            f.write(content)
                        
                        attachment_info = {
                            'filename': filename,
                            'content_type': content_type,
                            'size': len(content),
                            'saved_path': str(attachment_path),
                            'content_disposition': content_disposition
                        }
                        
                        attachments.append(attachment_info)
                        self.stats['attachments_extracted'] += 1
                        self.logger.info(f"提取附件: {filename} ({len(content)} bytes)")
                        
                    except Exception as e:
                        self.logger.error(f"保存附件失败 {filename}: {e}")
        
        return attachments
    
    def parse_eml_file(self, eml_path: str) -> Optional[Dict[str, Any]]:
        """
        解析单个EML文件
        
        Args:
            eml_path: EML文件路径
            
        Returns:
            解析结果字典，失败时返回None
        """
        try:
            self.logger.info(f"开始解析: {eml_path}")
            
            with open(eml_path, 'rb') as f:
                message = email.message_from_bytes(f.read())
            
            eml_filename = Path(eml_path).name
            
            # 提取各部分信息
            parsed_data = {
                'file_info': {
                    'filename': eml_filename,
                    'file_path': str(eml_path),
                    'file_size': os.path.getsize(eml_path),
                    'parse_time': datetime.now().isoformat()
                },
                'headers': self._extract_headers(message),
                'body': self._extract_body(message),
                'attachments': self._extract_attachments(message, eml_filename)
            }
            
            self.stats['parsed_successfully'] += 1
            self.logger.info(f"解析成功: {eml_filename}")
            
            return parsed_data
            
        except Exception as e:
            self.stats['parse_errors'] += 1
            self.logger.error(f"解析文件失败 {eml_path}: {e}")
            return None
    
    def parse_directory(self, directory_path: str) -> List[Dict[str, Any]]:
        """
        批量解析目录中的所有EML文件
        
        Args:
            directory_path: 目录路径
            
        Returns:
            解析结果列表
        """
        directory = Path(directory_path)
        if not directory.exists():
            self.logger.error(f"目录不存在: {directory_path}")
            return []
        
        eml_files = list(directory.glob("*.eml"))
        if not eml_files:
            self.logger.warning(f"目录中没有找到EML文件: {directory_path}")
            return []
        
        self.logger.info(f"找到 {len(eml_files)} 个EML文件")
        self.stats['total_files'] = len(eml_files)
        
        results = []
        for eml_file in eml_files:
            result = self.parse_eml_file(str(eml_file))
            if result:
                results.append(result)
        
        return results
    
    def export_results(self, results: List[Dict[str, Any]], format_type: str = 'json'):
        """
        导出解析结果
        
        Args:
            results: 解析结果列表
            format_type: 导出格式 (json, csv)
        """
        if not results:
            self.logger.warning("没有结果可导出")
            return
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        if format_type.lower() == 'json':
            output_file = self.output_dir / f"eml_parse_results_{timestamp}.json"
            try:
                with open(output_file, 'w', encoding='utf-8') as f:
                    json.dump(results, f, ensure_ascii=False, indent=2)
                self.logger.info(f"结果已导出到: {output_file}")
            except Exception as e:
                self.logger.error(f"导出JSON失败: {e}")
        
        elif format_type.lower() == 'csv':
            import csv
            output_file = self.output_dir / f"eml_parse_results_{timestamp}.csv"
            try:
                with open(output_file, 'w', newline='', encoding='utf-8') as f:
                    if results:
                        # 创建CSV表头
                        fieldnames = [
                            'filename', 'subject', 'from_email', 'from_name',
                            'to_emails', 'date', 'text_length', 'html_length',
                            'attachment_count', 'file_size'
                        ]
                        
                        writer = csv.DictWriter(f, fieldnames=fieldnames)
                        writer.writeheader()
                        
                        for result in results:
                            headers = result.get('headers', {})
                            body = result.get('body', {})
                            file_info = result.get('file_info', {})
                            attachments = result.get('attachments', [])
                            
                            # 处理收件人列表
                            to_parsed = headers.get('to_parsed', [])
                            to_emails = '; '.join([addr.get('email', '') for addr in to_parsed])
                            
                            from_parsed = headers.get('from_parsed', {})
                            
                            row = {
                                'filename': file_info.get('filename', ''),
                                'subject': headers.get('subject', ''),
                                'from_email': from_parsed.get('email', ''),
                                'from_name': from_parsed.get('name', ''),
                                'to_emails': to_emails,
                                'date': headers.get('date_parsed', ''),
                                'text_length': len(body.get('text', '')),
                                'html_length': len(body.get('html', '')),
                                'attachment_count': len(attachments),
                                'file_size': file_info.get('file_size', 0)
                            }
                            writer.writerow(row)
                
                self.logger.info(f"结果已导出到: {output_file}")
            except Exception as e:
                self.logger.error(f"导出CSV失败: {e}")
    
    def print_summary(self, results: List[Dict[str, Any]]):
        """
        打印解析摘要
        
        Args:
            results: 解析结果列表
        """
        print("\n" + "="*60)
        print("EML文件解析摘要")
        print("="*60)
        
        print(f"总文件数: {self.stats['total_files']}")
        print(f"成功解析: {self.stats['parsed_successfully']}")
        print(f"解析失败: {self.stats['parse_errors']}")
        print(f"提取附件: {self.stats['attachments_extracted']}")
        
        if results:
            print(f"\n成功率: {self.stats['parsed_successfully']/self.stats['total_files']*100:.1f}%")
            
            # 统计信息
            total_text_length = sum(len(r.get('body', {}).get('text', '')) for r in results)
            total_html_length = sum(len(r.get('body', {}).get('html', '')) for r in results)
            total_attachments = sum(len(r.get('attachments', [])) for r in results)
            
            print(f"文本内容总长度: {total_text_length:,} 字符")
            print(f"HTML内容总长度: {total_html_length:,} 字符")
            print(f"附件总数: {total_attachments}")
            
            # 显示前几个邮件的基本信息
            print(f"\n前 {min(5, len(results))} 个邮件:")
            for i, result in enumerate(results[:5], 1):
                headers = result.get('headers', {})
                file_info = result.get('file_info', {})
                
                print(f"\n{i}. {file_info.get('filename', '未知')}")
                print(f"   主题: {headers.get('subject', '无主题')}")
                
                from_parsed = headers.get('from_parsed', {})
                from_display = from_parsed.get('name') or from_parsed.get('email', '未知')
                print(f"   发件人: {from_display}")
                
                print(f"   日期: {headers.get('date_parsed', '未知')}")
                print(f"   附件数: {len(result.get('attachments', []))}")


def main():
    """主函数，处理命令行参数"""
    parser = argparse.ArgumentParser(description='EML文件解析工具')
    parser.add_argument('input', help='输入文件或目录路径')
    parser.add_argument('-o', '--output', default='eml_output', help='输出目录 (默认: eml_output)')
    parser.add_argument('-f', '--format', choices=['json', 'csv'], default='json', help='导出格式 (默认: json)')
    parser.add_argument('--no-attachments', action='store_true', help='不提取附件')
    parser.add_argument('-v', '--verbose', action='store_true', help='详细输出')
    
    args = parser.parse_args()
    
    # 设置日志级别
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # 创建解析器
    parser_instance = EMLParser(args.output)
    
    # 解析文件或目录
    input_path = Path(args.input)
    
    if input_path.is_file() and input_path.suffix.lower() == '.eml':
        # 单个文件
        result = parser_instance.parse_eml_file(str(input_path))
        results = [result] if result else []
    elif input_path.is_dir():
        # 目录
        results = parser_instance.parse_directory(str(input_path))
    else:
        print(f"错误: 输入路径无效或不是EML文件/目录: {args.input}")
        return
    
    # 导出结果
    if results:
        parser_instance.export_results(results, args.format)
        parser_instance.print_summary(results)
    else:
        print("没有成功解析任何文件")


if __name__ == "__main__":
    main() 