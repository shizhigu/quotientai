#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Gmail邮件拉取工具配置文件
"""

import os

# Gmail API配置
GMAIL_API_CONFIG = {
    # API权限范围
    'SCOPES': [
        'https://www.googleapis.com/auth/gmail.readonly',
        # 如果需要修改邮件，可以使用更广泛的权限
        # 'https://www.googleapis.com/auth/gmail.modify',
        # 'https://www.googleapis.com/auth/gmail.compose',
    ],
    
    # 凭证文件路径
    'CREDENTIALS_FILE': 'credentials.json',
    
    # Token文件路径
    'TOKEN_FILE': 'token.pickle',
    
    # API服务名称和版本
    'SERVICE_NAME': 'gmail',
    'API_VERSION': 'v1',
}

# 默认查询参数
DEFAULT_QUERY_PARAMS = {
    # 默认最大返回数量
    'max_results': 10,
    
    # 默认查询格式
    'format': 'full',
    
    # 默认用户ID
    'user_id': 'me',
}

# 邮件搜索预设
SEARCH_PRESETS = {
    'unread': 'is:unread',
    'starred': 'is:starred',
    'important': 'label:important',
    'social': 'category:social',
    'promotions': 'category:promotions',
    'updates': 'category:updates',
    'forums': 'category:forums',
    'with_attachments': 'has:attachment',
    'recent_week': 'newer_than:7d',
    'recent_month': 'newer_than:1m',
    'large_emails': 'size:10m',
}

# 导出设置
EXPORT_CONFIG = {
    # 默认导出目录
    'export_dir': 'exports',
    
    # 导出文件格式
    'formats': ['json', 'csv'],
    
    # JSON导出设置
    'json_settings': {
        'ensure_ascii': False,
        'indent': 2,
        'sort_keys': True,
    },
    
    # 文件名时间戳格式
    'timestamp_format': '%Y%m%d_%H%M%S',
}

# 日志配置
LOGGING_CONFIG = {
    'level': 'INFO',  # DEBUG, INFO, WARNING, ERROR, CRITICAL
    'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    'file': 'gmail_client.log',
}

# 错误重试配置
RETRY_CONFIG = {
    'max_retries': 3,
    'retry_delay': 1,  # 秒
    'backoff_factor': 2,
}

# 批处理配置
BATCH_CONFIG = {
    'batch_size': 100,  # 批处理大小
    'request_delay': 0.1,  # 请求之间的延迟（秒）
}

# 邮件内容解析配置
PARSING_CONFIG = {
    # 是否解析HTML内容
    'parse_html': True,
    
    # 是否解析纯文本内容
    'parse_text': True,
    
    # 是否提取附件信息
    'extract_attachments': True,
    
    # 文本内容最大长度
    'max_text_length': 10000,
    
    # HTML内容最大长度
    'max_html_length': 50000,
}

# 缓存配置
CACHE_CONFIG = {
    # 是否启用缓存
    'enabled': True,
    
    # 缓存目录
    'cache_dir': '.cache',
    
    # 缓存过期时间（秒）
    'expiry_time': 3600,  # 1小时
}

def get_config(section: str = None):
    """
    获取配置信息
    
    Args:
        section: 配置段名称，如果为None则返回所有配置
        
    Returns:
        配置字典
    """
    all_configs = {
        'gmail_api': GMAIL_API_CONFIG,
        'default_query': DEFAULT_QUERY_PARAMS,
        'search_presets': SEARCH_PRESETS,
        'export': EXPORT_CONFIG,
        'logging': LOGGING_CONFIG,
        'retry': RETRY_CONFIG,
        'batch': BATCH_CONFIG,
        'parsing': PARSING_CONFIG,
        'cache': CACHE_CONFIG,
    }
    
    if section:
        return all_configs.get(section, {})
    return all_configs

def create_directories():
    """创建必要的目录"""
    directories = [
        EXPORT_CONFIG['export_dir'],
        CACHE_CONFIG['cache_dir'],
    ]
    
    for directory in directories:
        if not os.path.exists(directory):
            os.makedirs(directory)
            print(f"创建目录: {directory}")

def validate_config():
    """验证配置文件"""
    errors = []
    
    # 检查凭证文件
    if not os.path.exists(GMAIL_API_CONFIG['CREDENTIALS_FILE']):
        errors.append(f"凭证文件不存在: {GMAIL_API_CONFIG['CREDENTIALS_FILE']}")
    
    # 检查导出目录权限
    export_dir = EXPORT_CONFIG['export_dir']
    if not os.path.exists(export_dir):
        try:
            os.makedirs(export_dir)
        except Exception as e:
            errors.append(f"无法创建导出目录 {export_dir}: {e}")
    
    if errors:
        print("配置验证失败:")
        for error in errors:
            print(f"  - {error}")
        return False
    
    print("配置验证通过！")
    return True

if __name__ == "__main__":
    # 测试配置
    print("Gmail邮件拉取工具 - 配置信息")
    print("=" * 40)
    
    # 显示所有配置
    configs = get_config()
    for section, config in configs.items():
        print(f"\n[{section.upper()}]")
        for key, value in config.items():
            print(f"  {key}: {value}")
    
    # 创建必要目录
    print("\n" + "=" * 40)
    create_directories()
    
    # 验证配置
    print("\n" + "=" * 40)
    validate_config() 