"""代理模块 - OpenAI API代理"""
import requests
from flask import request, jsonify, Response
from redactor import desensitize_text
from config import Config


def process_messages(messages, replacement=Config.DEFAULT_REPLACEMENT, scope=Config.DEFAULT_SCOPE):
    """
    处理messages数组，对role为user的content进行脱敏
    
    Args:
        messages: 消息数组
        replacement: 替换文本
        scope: 脱敏范围
    
    Returns:
        处理后的messages数组
    """
    if not messages:
        return messages
    
    processed_messages = []
    for msg in messages:
        # 深拷贝消息对象
        processed_msg = dict(msg)
        
        # 只处理role为user的消息
        if processed_msg.get('role') == 'user':
            content = processed_msg.get('content')
            if isinstance(content, str):
                # 简单文本内容
                desensitized_content, _ = desensitize_text(
                    content, 
                    replacement=replacement, 
                    scope=scope, 
                    use_html=False
                )
                processed_msg['content'] = desensitized_content
            elif isinstance(content, list):
                # 复杂内容（如包含图片等），只处理文本部分
                for item in content:
                    if isinstance(item, dict) and item.get('type') == 'text':
                        text = item.get('text', '')
                        desensitized_text_content, _ = desensitize_text(
                            text, 
                            replacement=replacement, 
                            scope=scope, 
                            use_html=False
                        )
                        item['text'] = desensitized_text_content
                processed_msg['content'] = content
        
        processed_messages.append(processed_msg)
    
    return processed_messages


def forward_to_remote_api(endpoint, headers, data, method='POST', timeout=Config.PROXY_TIMEOUT):
    """
    转发请求到远程API
    
    Args:
        endpoint: 远程API端点
        headers: 请求头
        data: 请求数据
        method: HTTP方法（GET/POST/PUT/DELETE等）
        timeout: 超时时间（秒）
    
    Returns:
        Response对象
    """
    try:
        # 构建完整URL
        url = Config.REMOTE_API_ENDPOINT.rstrip('/') + endpoint
        
        # 根据HTTP方法构建请求参数
        request_kwargs = {
            'method': method,
            'url': url,
            'headers': headers,
            'timeout': timeout,
            'stream': True
        }
        
        # GET请求不传递body，其他方法传递JSON数据
        if method.upper() != 'GET':
            request_kwargs['json'] = data
        
        # 转发请求，使用流式响应以支持SSE
        response = requests.request(**request_kwargs)
        
        return response
    except requests.exceptions.Timeout:
        raise Exception("远程API请求超时")
    except requests.exceptions.ConnectionError:
        raise Exception("无法连接到远程API")
    except Exception as e:
        raise Exception(f"转发请求失败: {str(e)}")


def handle_proxy_request():
    """
    处理代理请求的主函数
    
    处理流程：
    1. 判断请求路径是否需要脱敏（chat/completions端点）
    2. 如果需要，对messages中role为user的内容进行脱敏
    3. 转发到远程API
    4. 返回响应
    """
    try:
        # 获取请求数据（GET请求不解析JSON）
        if request.method.upper() == 'GET':
            data = {}
        else:
            data = request.get_json()
            if data is None:
                data = {}
        
        # 判断是否需要脱敏处理（仅对chat/completions端点）
        path = request.path
        needs_desensitization = '/chat/completions' in path
        
        if data and needs_desensitization:
            # 提取messages并进行脱敏处理
            messages = data.get('messages')
            if messages:
                # 从请求中获取脱敏配置（可选）
                replacement = data.pop('desensitize_replacement', Config.DEFAULT_REPLACEMENT)
                scope = data.pop('desensitize_scope', Config.DEFAULT_SCOPE)
                
                # 处理messages
                data['messages'] = process_messages(messages, replacement, scope)
        
        # 构建转发请求头
        headers = {}
        
        # 转发所有请求头到远程API
        # 排除host、content-length等不需要转发的头
        excluded_headers = ['host', 'content-length', 'transfer-encoding', 'connection', 'content-type']
        for name, value in request.headers:
            if name.lower() not in excluded_headers:
                headers[name] = value
        
        # 如果是GET请求，不添加Content-Type；如果是POST等请求，确保有Content-Type
        if request.method.upper() != 'GET' and 'content-type' not in [h.lower() for h in headers.keys()]:
            headers['Content-Type'] = 'application/json'
        
        # 如果环境变量配置了API Key，也添加（作为fallback）
        if Config.REMOTE_API_KEY and 'Authorization' not in headers:
            headers['Authorization'] = f'Bearer {Config.REMOTE_API_KEY}'
        
        # 转发到远程API（保持原始HTTP方法）
        endpoint = request.path
        method = request.method
        remote_response = forward_to_remote_api(endpoint, headers, data, method)
        
        # 处理流式响应
        def generate():
            try:
                # 设置合理的chunk大小（8KB），避免None导致的问题
                for chunk in remote_response.iter_content(chunk_size=8192):
                    if chunk:
                        yield chunk
            except GeneratorExit:
                # 客户端断开连接，正常退出
                print("客户端断开连接")
                remote_response.close()
            except Exception as e:
                print(f"流式响应传输错误: {e}")
                remote_response.close()
        
        # 返回响应，保持原始状态码和头信息
        excluded_headers = ['content-encoding', 'content-length', 'transfer-encoding', 'connection']
        response_headers = [
            (name, value) for name, value in remote_response.headers.items()
            if name.lower() not in excluded_headers
        ]
        
        # 禁用响应缓冲，确保流式传输
        return Response(
            generate(),
            status=remote_response.status_code,
            headers=response_headers,
            direct_passthrough=True
        )
        
    except Exception as e:
        print(f"代理请求处理出错: {str(e)}")
        return jsonify({"error": f"代理请求处理失败: {str(e)}"}), 500
