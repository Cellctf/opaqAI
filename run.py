import flask
import hanlp
import json
from flask import render_template

app = flask.Flask(__name__)
# 加载HanLP模型
print("正在加载HanLP模型...")
HanLP = hanlp.load(hanlp.pretrained.mtl.CLOSE_TOK_POS_NER_SRL_DEP_SDP_CON_ELECTRA_BASE_ZH)
print("HanLP模型加载完成！")

def desensitize(text, replacement="[Secret]", scope="basic"):
    if not text.strip():
        return "", {}
        
    try:
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
            if scope == "basic":
                if entity_type not in ["PHONE", "PERSON", "EMAIL", "INTEGER"]:
                    continue
            elif scope == "enhanced":
                if entity_type in ["TIME", "DATE", "AREA"]:
                    continue
            # scope == "full" 不过滤任何实体
            start_char = char_offsets[start_idx][0]
            end_char = char_offsets[end_idx - 1][1]
            sensitive_spans.append((start_char, end_char, entity_type, word))
        
        # 从后向前替换以避免位置变化导致的问题
        sensitive_spans.sort(reverse=True)
        
        # 创建脱敏结果和敏感信息统计
        desensitized_text = text
        stats = {}
        
        for start, end, entity_type, original_text in sensitive_spans:
            span_html = f'<span class="secret red" data-original="{original_text}">{replacement}</span>'
            print(span_html)
            desensitized_text = desensitized_text[:start] + span_html + desensitized_text[end:]
            stats[entity_type] = stats.get(entity_type, 0) + 1
        
        return desensitized_text, stats
    except Exception as e:
        print(f"脱敏处理过程出错: {str(e)}")
        return text, {"ERROR": "处理过程出错"}

def get_detailed_processing_steps(text, replacement="[Secret]", scope="basic"):
    """获取详细的处理步骤信息用于可视化"""
    if not text.strip():
        return {
            "error": "输入文本为空"
        }
    
    try:
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
            
            # 根据scope过滤 - 修复与desensitize函数保持一致的逻辑
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

@app.route("/", methods=["GET", "POST"])
def index():
    """首页路由"""
    input_text = ""
    replacement_text = ""
    desensitized_text = ""
    stats = {}
    desensitize_scope = "basic"
    
    if flask.request.method == "POST":
        input_text = flask.request.form.get("input_text", "")
        if len(input_text) > 3000:
            return flask.render_template("error.html")
        replacement_text = flask.request.form.get("replacement_text", "[Secret]")
        desensitize_scope = flask.request.form.get("desensitize_scope", "full")
        
        if replacement_text.strip() == "":
            replacement_text = "[Secret]"
        desensitized_text, stats = desensitize(input_text, replacement_text, desensitize_scope)
    
    return flask.render_template("index.html", 
                               input_text=input_text, 
                               replacement_text=replacement_text, 
                               desensitized_text=desensitized_text,
                               desensitize_scope=desensitize_scope,
                               stats=stats)

@app.route("/api/desensitize", methods=["POST"])
def api_desensitize():
    """API端点用于Ajax请求"""
    data = flask.request.get_json()
    if not data:
        return flask.jsonify({"error": "无效的请求数据"}), 400
        
    input_text = data.get("text", "")
    replacement_text = data.get("replacement", "[REDACTED]")
    desensitize_scope = data.get("scope", "basic")  # 这里要取 scope
    if replacement_text.strip() == "":
        replacement_text = "[Secret]"
        
    desensitized_text, stats = desensitize(input_text, replacement_text, desensitize_scope)
    
    return flask.jsonify({
        "desensitized_text": desensitized_text,
        "stats": stats,
    })

@app.route("/demo", methods=["GET", "POST"])
def demo():
    """演示端点，展示处理过程可视化"""
    input_text = ""
    replacement_text = "[Secret]"
    desensitize_scope = "full"
    processing_result = None
    
    if flask.request.method == "POST":
        input_text = flask.request.form.get("input_text", "")
        if len(input_text) > 100:
            return flask.render_template("error.html")
        replacement_text = flask.request.form.get("replacement_text", "[Secret]")
        desensitize_scope = flask.request.form.get("desensitize_scope", "basic")
        
        if replacement_text.strip() == "":
            replacement_text = "[Secret]"
            
        processing_result = get_detailed_processing_steps(input_text, replacement_text, desensitize_scope)
    
    return flask.render_template("demo.html", 
                               input_text=input_text, 
                               replacement_text=replacement_text,
                               desensitize_scope=desensitize_scope,
                               processing_result=processing_result)

if __name__ == "__main__":
    app.run(debug=True)