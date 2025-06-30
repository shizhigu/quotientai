import os
import pickle
import base64
import email
import json
from datetime import datetime
from typing import List, Dict, Optional, Any
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials

class GmailClient:
    """Gmail API客户端，用于拉取邮件和thread"""
    
    # Gmail API权限范围
    SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']
    
    def __init__(self, credentials_file: str = 'credentials.json'):
        """
        初始化Gmail客户端
        
        Args:
            credentials_file: Google API凭证文件路径
        """
        self.credentials_file = credentials_file
        self.token_file = 'token.pickle'
        self.service = None
        self._authenticate()
    
    def _authenticate(self):
        """Gmail API认证"""
        creds = None
        
        # 检查是否已有保存的token
        if os.path.exists(self.token_file):
            with open(self.token_file, 'rb') as token:
                creds = pickle.load(token)
        
        # 如果没有有效凭证，进行OAuth认证
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                if not os.path.exists(self.credentials_file):
                    raise FileNotFoundError(
                        f"请先下载Google API凭证文件并保存为 {self.credentials_file}\n"
                        "获取步骤：https://console.developers.google.com/"
                    )
                
                flow = InstalledAppFlow.from_client_secrets_file(
                    self.credentials_file, self.SCOPES
                )
                creds = flow.run_local_server(port=0)
            
            # 保存凭证以供下次使用
            with open(self.token_file, 'wb') as token:
                pickle.dump(creds, token)
        
        # 构建Gmail API服务
        self.service = build('gmail', 'v1', credentials=creds)
        print("Gmail API认证成功！")
    
    def get_messages(self, query: str = '', max_results: int = 10) -> List[Dict]:
        """
        获取邮件列表
        
        Args:
            query: 搜索查询（Gmail搜索语法）
            max_results: 最大返回数量
            
        Returns:
            邮件列表
        """
        try:
            results = self.service.users().messages().list(
                userId='me',
                q=query,
                maxResults=max_results
            ).execute()
            
            messages = results.get('messages', [])
            
            if not messages:
                print("没有找到邮件")
                return []
            
            print(f"找到 {len(messages)} 封邮件")
            return messages
            
        except Exception as error:
            print(f"获取邮件列表时出错: {error}")
            return []
    
    def get_message_detail(self, message_id: str) -> Optional[Dict]:
        """
        获取邮件详细信息
        
        Args:
            message_id: 邮件ID
            
        Returns:
            邮件详细信息
        """
        try:
            message = self.service.users().messages().get(
                userId='me',
                id=message_id,
                format='full'
            ).execute()
            
            return self._parse_message(message)
            
        except Exception as error:
            print(f"获取邮件详情时出错: {error}")
            return None
    
    def _parse_message(self, message: Dict) -> Dict:
        """解析邮件内容"""
        headers = message['payload'].get('headers', [])
        
        # 提取邮件头信息
        email_data = {
            'id': message['id'],
            'thread_id': message['threadId'],
            'label_ids': message.get('labelIds', []),
            'snippet': message.get('snippet', ''),
            'internal_date': message.get('internalDate', ''),
            'size_estimate': message.get('sizeEstimate', 0)
        }
        
        # 解析头部信息
        for header in headers:
            name = header['name'].lower()
            if name == 'from':
                email_data['from'] = header['value']
            elif name == 'to':
                email_data['to'] = header['value']
            elif name == 'subject':
                email_data['subject'] = header['value']
            elif name == 'date':
                email_data['date'] = header['value']
            elif name == 'cc':
                email_data['cc'] = header['value']
            elif name == 'bcc':
                email_data['bcc'] = header['value']
        
        # 解析邮件正文
        email_data['body'] = self._extract_body(message['payload'])
        
        return email_data
    
    def _extract_body(self, payload: Dict) -> Dict:
        """提取邮件正文"""
        body = {'text': '', 'html': ''}
        
        if 'parts' in payload:
            # 多部分邮件
            for part in payload['parts']:
                if part['mimeType'] == 'text/plain':
                    data = part['body'].get('data', '')
                    if data:
                        body['text'] = base64.urlsafe_b64decode(data).decode('utf-8')
                elif part['mimeType'] == 'text/html':
                    data = part['body'].get('data', '')
                    if data:
                        body['html'] = base64.urlsafe_b64decode(data).decode('utf-8')
                elif part['mimeType'] == 'multipart/alternative':
                    # 递归处理嵌套的多部分内容
                    nested_body = self._extract_body(part)
                    if nested_body['text']:
                        body['text'] = nested_body['text']
                    if nested_body['html']:
                        body['html'] = nested_body['html']
        else:
            # 单部分邮件
            if payload['mimeType'] == 'text/plain':
                data = payload['body'].get('data', '')
                if data:
                    body['text'] = base64.urlsafe_b64decode(data).decode('utf-8')
            elif payload['mimeType'] == 'text/html':
                data = payload['body'].get('data', '')
                if data:
                    body['html'] = base64.urlsafe_b64decode(data).decode('utf-8')
        
        return body
    
    def get_threads(self, query: str = '', max_results: int = 10) -> List[Dict]:
        """
        获取邮件线程列表
        
        Args:
            query: 搜索查询
            max_results: 最大返回数量
            
        Returns:
            线程列表
        """
        try:
            results = self.service.users().threads().list(
                userId='me',
                q=query,
                maxResults=max_results
            ).execute()
            
            threads = results.get('threads', [])
            
            if not threads:
                print("没有找到线程")
                return []
            
            print(f"找到 {len(threads)} 个线程")
            return threads
            
        except Exception as error:
            print(f"获取线程列表时出错: {error}")
            return []
    
    def get_thread_detail(self, thread_id: str) -> Optional[Dict]:
        """
        获取线程详细信息
        
        Args:
            thread_id: 线程ID
            
        Returns:
            线程详细信息，包含所有邮件
        """
        try:
            thread = self.service.users().threads().get(
                userId='me',
                id=thread_id,
                format='full'
            ).execute()
            
            # 解析线程中的所有邮件
            messages = []
            for message in thread.get('messages', []):
                parsed_message = self._parse_message(message)
                messages.append(parsed_message)
            
            return {
                'id': thread['id'],
                'snippet': thread.get('snippet', ''),
                'history_id': thread.get('historyId', ''),
                'message_count': len(messages),
                'messages': messages
            }
            
        except Exception as error:
            print(f"获取线程详情时出错: {error}")
            return None
    
    def search_messages(self, 
                       sender: str = None,
                       subject: str = None,
                       after_date: str = None,
                       before_date: str = None,
                       has_attachment: bool = None,
                       is_unread: bool = None,
                       max_results: int = 10) -> List[Dict]:
        """
        高级邮件搜索
        
        Args:
            sender: 发件人
            subject: 主题关键词
            after_date: 开始日期 (YYYY/MM/DD格式)
            before_date: 结束日期 (YYYY/MM/DD格式)
            has_attachment: 是否包含附件
            is_unread: 是否未读
            max_results: 最大返回数量
            
        Returns:
            搜索到的邮件列表
        """
        query_parts = []
        
        if sender:
            query_parts.append(f"from:{sender}")
        if subject:
            query_parts.append(f"subject:{subject}")
        if after_date:
            query_parts.append(f"after:{after_date}")
        if before_date:
            query_parts.append(f"before:{before_date}")
        if has_attachment:
            query_parts.append("has:attachment")
        if is_unread:
            query_parts.append("is:unread")
        
        query = " ".join(query_parts)
        print(f"搜索查询: {query}")
        
        messages = self.get_messages(query, max_results)
        detailed_messages = []
        
        for msg in messages:
            detail = self.get_message_detail(msg['id'])
            if detail:
                detailed_messages.append(detail)
        
        return detailed_messages
    
    def export_to_json(self, data: Any, filename: str):
        """导出数据到JSON文件"""
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            print(f"数据已导出到: {filename}")
        except Exception as error:
            print(f"导出数据时出错: {error}")


def main():
    """示例使用"""
    try:
        # 创建Gmail客户端
        gmail = GmailClient()
        
        print("\n=== Gmail邮件拉取示例 ===")
        
        # 1. 获取最新的10封邮件
        print("\n1. 获取最新邮件...")
        messages = gmail.get_messages(max_results=5)
        
        if messages:
            # 获取第一封邮件的详细信息
            first_message = gmail.get_message_detail(messages[0]['id'])
            if first_message:
                print(f"邮件主题: {first_message.get('subject', '无主题')}")
                print(f"发件人: {first_message.get('from', '未知')}")
                print(f"日期: {first_message.get('date', '未知')}")
                print(f"摘要: {first_message.get('snippet', '无摘要')}")
        
        # 2. 获取邮件线程
        print("\n2. 获取邮件线程...")
        threads = gmail.get_threads(max_results=3)
        
        if threads:
            # 获取第一个线程的详细信息
            first_thread = gmail.get_thread_detail(threads[0]['id'])
            if first_thread:
                print(f"线程ID: {first_thread['id']}")
                print(f"邮件数量: {first_thread['message_count']}")
                print(f"线程摘要: {first_thread['snippet']}")
        
        # 3. 搜索特定邮件
        print("\n3. 搜索未读邮件...")
        unread_messages = gmail.search_messages(is_unread=True, max_results=3)
        
        print(f"找到 {len(unread_messages)} 封未读邮件")
        for msg in unread_messages:
            print(f"- {msg.get('subject', '无主题')} (来自: {msg.get('from', '未知')})")
        
        # 4. 导出数据
        if messages:
            gmail.export_to_json(messages, 'messages.json')
        if threads:
            gmail.export_to_json(threads, 'threads.json')
            
    except Exception as error:
        print(f"程序运行出错: {error}")


if __name__ == "__main__":
    main() 