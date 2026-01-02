"""脱敏模块 - 封装HanLP脱敏逻辑"""
import hanlp
from config import Config

# 全局HanLP模型实例
_HanLP = None


def get_hanlp_model():
    """获取HanLP模型实例（单例模式）"""
    global _HanLP
    if _HanLP is None:
        print("正在加载HanLP模型...")
        _HanLP = hanlp.load(Config.HANLP_MODEL)
        print("HanLP模型加载完成！")
    return _HanLP


def desensitize_text(text, replacement="[SECRET]", scope="basic", use_html=False):
    """
    对文本进行脱敏处理
    
    Args:
        text: 输入文本
        replacement: 替换文本
        scope: 脱敏范围 (basic, enhanced, full)
        use_html: 是否使用HTML格式（用于web界面展示）
    
    Returns:
        (脱敏后的文本, 统计信息)
    """
    if not text or not text.strip():
        return "", {}
    
    try:
        HanLP = get_hanlp_model()
        # 执行命名实体识别
        result = HanLP(text, tasks='ner/msra')
        tokens = result['tok/fine']
        entities = result['ner/msra']
        
        # 计算每个token在原文中的字符位置
        char_offsets = []
        offset = 0
        for token in tokens:
            start = text.find(token, offset)
            if start == -1:
                continue
            end = start + len(token)
            char_offsets.append((start, end))
            offset = end
        
        # 收集所有敏感实体的字符范围
        sensitive_spans = []
        for word, entity_type, start_idx, end_idx in entities:
            # 根据scope过滤实体
            should_include = False
            if scope == "basic":
                if entity_type in ["PHONE", "PERSON", "EMAIL", "INTEGER"]:
                    should_include = True
            elif scope == "enhanced":
                if entity_type not in ["TIME", "DATE", "AREA"]:
                    should_include = True
            else:  # scope == "full"
                should_include = True
            
            if should_include:
                start_char = char_offsets[start_idx][0]
                end_char = char_offsets[end_idx - 1][1]
                sensitive_spans.append((start_char, end_char, entity_type, word))
        
        # 从后向前替换以避免位置变化导致的问题
        sensitive_spans.sort(reverse=True)
        
        # 创建脱敏结果和敏感信息统计
        desensitized_text = text
        stats = {}
        
        for start, end, entity_type, original_text in sensitive_spans:
            if use_html:
                # HTML格式，用于web界面展示
                span_html = f'<span class="secret red" data-original="{original_text}">{replacement}</span>'
                desensitized_text = desensitized_text[:start] + span_html + desensitized_text[end:]
            else:
                # 纯文本格式，用于代理
                desensitized_text = desensitized_text[:start] + replacement + desensitized_text[end:]
            
            stats[entity_type] = stats.get(entity_type, 0) + 1
        
        return desensitized_text, stats
    except Exception as e:
        print(f"脱敏处理过程出错: {str(e)}")
        return text, {"ERROR": "处理过程出错"}


def get_detailed_processing_steps(text, replacement="[SECRET]", scope="basic"):
    """
    获取详细的处理步骤信息用于可视化（用于demo页面）
    
    Args:
        text: 输入文本
        replacement: 替换文本
        scope: 脱敏范围
    
    Returns:
        包含详细处理步骤的字典
    """
    if not text or not text.strip():
        return {
            "error": "输入文本为空"
        }
    
    try:
        HanLP = get_hanlp_model()
        # 执行命名实体识别
        result = HanLP(text, tasks='ner/msra')
        tokens = result['tok/fine']
        entities = result['ner/msra']
        
        # 计算每个token在原文中的字符位置
        char_offsets = []
        offset = 0
        for token in tokens:
            start = text.find(token, offset)
            if start == -1:
                continue
            end = start + len(token)
            char_offsets.append((start, end))
            offset = end
        
        # 标记所有实体（包括按scope过滤前的所有实体）
        all_entities = []
        filtered_entities = []
        
        for word, entity_type, start_idx, end_idx in entities:
            start_char = char_offsets[start_idx][0]
            end_char = char_offsets[end_idx - 1][1]
            
            entity_info = {
                "text": word,
                "type": entity_type,
                "start": start_char,
                "end": end_char
            }
            all_entities.append(entity_info)
            
            # 根据scope过滤
            should_filter = False
            if scope == "basic":
                if entity_type not in ["PHONE", "PERSON", "EMAIL", "INTEGER"]:
                    should_filter = True
            elif scope == "enhanced":
                if entity_type in ["TIME", "DATE", "AREA"]:
                    should_filter = True
            # scope == "full" 不过滤任何实体
            
            if not should_filter:
                filtered_entities.append(entity_info)
        
        # 从后向前替换以避免位置变化导致的问题
        filtered_entities.sort(key=lambda x: x["start"], reverse=True)
        
        # 执行替换并记录每个步骤
        replacement_steps = []
        current_text = text
        
        for entity in filtered_entities:
            start = entity["start"]
            end = entity["end"]
            before_replacement = current_text
            current_text = current_text[:start] + replacement + current_text[end:]
            
            replacement_steps.append({
                "entity": entity,
                "before": before_replacement,
                "after": current_text
            })
        
        # 返回完整的处理信息
        return {
            "original_text": text,
            "tokens": tokens,
            "char_offsets": char_offsets,
            "all_entities": all_entities,
            "filtered_entities": filtered_entities,
            "replacement_steps": replacement_steps,
            "final_text": current_text
        }
    except Exception as e:
        print(f"处理步骤分析过程出错: {str(e)}")
        return {"error": str(e)}
