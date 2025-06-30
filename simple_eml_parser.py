#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
简化版EML文件解析工具
只包含一个函数：parse_eml(file_path, save_attachments=True, attachment_dir="attachments") -> dict
"""

import email
import base64
from email.header import decode_header
from email.utils import parsedate_to_datetime, parseaddr
from datetime import datetime
import os
from pathlib import Path


def parse_eml(file_path: str, save_attachments: bool = True, attachment_dir: str = "attachments") -> dict:
    """
    解析EML文件并返回JSON格式数据
    
    Args:
        file_path: EML文件路径
        save_attachments: 是否保存附件到文件夹
        attachment_dir: 附件保存目录
        
    Returns:
        解析结果字典，包含邮件的所有信息
    """
    
    def _decode_header(header_value):
        """解码邮件头"""
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
        except:
            return str(header_value)
    
    def _parse_address(address_str):
        """解析邮件地址"""
        if not address_str:
            return {"name": "", "email": ""}
        
        try:
            decoded_addr = _decode_header(address_str)
            name, email_addr = parseaddr(decoded_addr)
            return {"name": name.strip(), "email": email_addr.strip()}
        except:
            return {"name": "", "email": address_str}
    
    def _parse_addresses(address_str):
        """解析多个邮件地址"""
        if not address_str:
            return []
        
        addresses = []
        for addr in address_str.split(','):
            addr = addr.strip()
            if addr:
                addresses.append(_parse_address(addr))
        return addresses
    
    def _decode_content(content, encoding=None):
        """解码邮件内容"""
        if not content:
            return ""
        
        if isinstance(content, str):
            return content
        
        if encoding:
            try:
                return content.decode(encoding)
            except:
                pass
        
        # 尝试常见编码
        for enc in ['utf-8', 'gb2312', 'gbk', 'big5', 'iso-8859-1']:
            try:
                return content.decode(enc)
            except UnicodeDecodeError:
                continue
        
        return content.decode('utf-8', errors='ignore')
    
    def _extract_body(message):
        """提取邮件正文"""
        body = {'text': '', 'html': ''}
        
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
                    decoded = _decode_content(content, charset)
                    body['text'] += decoded + '\n'
            
            elif content_type == 'text/html':
                content = part.get_payload(decode=True)
                if content:
                    charset = part.get_content_charset() or 'utf-8'
                    decoded = _decode_content(content, charset)
                    body['html'] += decoded + '\n'
        
        if message.is_multipart():
            for part in message.walk():
                extract_part(part)
        else:
            extract_part(message)
        
        body['text'] = body['text'].strip()
        body['html'] = body['html'].strip()
        return body
    
    def _extract_attachments(message, eml_filename):
        """提取附件信息"""
        attachments = []
        
        if save_attachments:
            # 创建附件目录：attachments/邮件名称/
            eml_name = Path(eml_filename).stem
            attachment_folder = Path(attachment_dir) / eml_name
            attachment_folder.mkdir(parents=True, exist_ok=True)
        
        for part in message.walk():
            content_disposition = part.get('Content-Disposition', '')
            
            if 'attachment' in content_disposition or part.get_filename():
                filename = part.get_filename()
                if filename:
                    filename = _decode_header(filename)
                else:
                    # 根据内容类型生成文件名
                    import mimetypes
                    ext = mimetypes.guess_extension(part.get_content_type()) or '.bin'
                    filename = f"attachment_{len(attachments) + 1}{ext}"
                
                # 确保文件名安全（移除可能的路径分隔符）
                filename = filename.replace('/', '_').replace('\\', '_')
                
                content = part.get_payload(decode=True)
                if content:
                    attachment_info = {
                        'filename': filename,
                        'content_type': part.get_content_type(),
                        'size': len(content)
                    }
                    
                    if save_attachments:
                        # 保存附件到文件
                        save_path = attachment_folder / filename
                        try:
                            with open(save_path, 'wb') as f:
                                f.write(content)
                            attachment_info['saved_path'] = str(save_path)
                            attachment_info['saved'] = True
                            print(f"✅ 附件已保存: {save_path}")
                        except Exception as e:
                            attachment_info['save_error'] = str(e)
                            attachment_info['saved'] = False
                            print(f"❌ 附件保存失败 {filename}: {e}")
                    else:
                        # 不保存文件，只返回Base64内容
                        attachment_info['content'] = base64.b64encode(content).decode('utf-8')
                        attachment_info['saved'] = False
                    
                    attachments.append(attachment_info)
        
        return attachments
    
    # 开始解析
    try:
        with open(file_path, 'rb') as f:
            message = email.message_from_bytes(f.read())
        
        # 提取基本头信息
        headers = {}
        basic_headers = ['Date', 'From', 'To', 'Cc', 'Bcc', 'Subject', 'Message-ID']
        
        for header in basic_headers:
            value = message.get(header)
            if value:
                headers[header.lower()] = _decode_header(value)
        
        # 解析地址信息
        if headers.get('from'):
            headers['from_parsed'] = _parse_address(headers['from'])
        if headers.get('to'):
            headers['to_parsed'] = _parse_addresses(headers['to'])
        if headers.get('cc'):
            headers['cc_parsed'] = _parse_addresses(headers['cc'])
        
        # 解析日期
        if headers.get('date'):
            try:
                date_obj = parsedate_to_datetime(headers['date'])
                headers['date_parsed'] = date_obj.isoformat()
                headers['date_timestamp'] = date_obj.timestamp()
            except:
                pass
        
        # 提取邮件正文
        body = _extract_body(message)
        
        # 提取附件
        attachments = _extract_attachments(message, os.path.basename(file_path))
        
        # 简化附件信息（只保留LLM需要的核心数据）
        simplified_attachments = []
        for att in attachments:
            simplified_att = {
                'filename': att['filename'],
                'type': att['content_type'],
                'size_kb': round(att['size'] / 1024, 2)  # 转换为KB并保留2位小数
            }
            
            # 添加保存路径（如果已保存）
            if att.get('saved_path'):
                simplified_att['saved_path'] = att['saved_path']
            
            simplified_attachments.append(simplified_att)
        
        # 返回简化的结果（专为LLM优化）
        return {
            'subject': headers.get('subject', ''),
            'from': {
                'name': headers.get('from_parsed', {}).get('name', ''),
                'email': headers.get('from_parsed', {}).get('email', '')
            },
            'to': headers.get('to_parsed', []),
            'cc': headers.get('cc_parsed', []),
            'date': headers.get('date_parsed', ''),
            'content': {
                'text': body['text'],
                'html': body['html']
            },
            'attachments': simplified_attachments
        }
        
    except Exception as e:
        return {
            'error': str(e),
            'subject': '',
            'from': {'name': '', 'email': ''},
            'to': [],
            'cc': [],
            'date': '',
            'content': {'text': '', 'html': ''},
            'attachments': []
        }


# 使用示例
if __name__ == "__main__":
    # 测试函数
    eml_file = "/Users/gushizhi/Projects/creatoros/KYC.eml"
    
    if os.path.exists(eml_file):
        print("🔍 开始解析EML文件...")
        
        # 解析并保存附件
        result = parse_eml(eml_file, save_attachments=True, attachment_dir="attachments")
        
        if not result.get('error'):
            print("\n✅ 解析成功!")
            print(f"📧 主题: {result['subject']}")
            print(f"👤 发件人: {result['from']['name']} <{result['from']['email']}>")
            print(f"📅 日期: {result['date']}")
            print(f"📝 文本长度: {len(result['content']['text'])} 字符")
            print(f"🌐 HTML长度: {len(result['content']['html'])} 字符")
            print(f"📎 附件数量: {len(result['attachments'])}")
            
            # 显示附件详情
            if result['attachments']:
                print("\n📎 附件列表:")
                for i, att in enumerate(result['attachments'], 1):
                    print(f"  {i}. {att['filename']} ({att['size_kb']} KB, {att['type']})")
            
            # 显示正文预览
            if result['content']['text']:
                print(f"\n📄 正文预览:")
                preview = result['content']['text'][:200]
                print(f"   {preview}...")
                
        else:
            print(f"❌ 解析失败: {result['error']}")

        print(result)
    else:
        print(f"⚠️  文件不存在: {eml_file}")
        print("请确保EML文件路径正确") 