"""主应用入口 - Flask应用"""
import flask
from flask import render_template
from redactor import desensitize_text, get_detailed_processing_steps
from proxy import handle_proxy_request
from config import Config

app = flask.Flask(__name__)

# 在应用启动时预加载HanLP模型
print("正在初始化应用并加载HanLP模型...")
from redactor import get_hanlp_model
get_hanlp_model()
print("应用初始化完成！")


@app.route("/", methods=["GET", "POST"])
def index():
    """首页路由 - 脱敏Web界面"""
    input_text = ""
    replacement_text = ""
    desensitized_text = ""
    stats = {}
    desensitize_scope = "basic"
    
    if flask.request.method == "POST":
        input_text = flask.request.form.get("input_text", "")
        if len(input_text) > 3000:
            return flask.render_template("error.html")
        replacement_text = flask.request.form.get("replacement_text", Config.DEFAULT_REPLACEMENT)
        desensitize_scope = flask.request.form.get("desensitize_scope", Config.DEFAULT_SCOPE)
        
        if replacement_text.strip() == "":
            replacement_text = Config.DEFAULT_REPLACEMENT
        
        desensitized_text, stats = desensitize_text(
            input_text, 
            replacement_text, 
            desensitize_scope, 
            use_html=True
        )
    
    return flask.render_template("index.html", 
                               input_text=input_text, 
                               replacement_text=replacement_text, 
                               desensitized_text=desensitized_text,
                               desensitize_scope=desensitize_scope,
                               stats=stats)


@app.route("/api/desensitize", methods=["POST"])
def api_desensitize():
    """API端点 - 文本脱敏"""
    data = flask.request.get_json()
    if not data:
        return flask.jsonify({"error": "无效的请求数据"}), 400
        
    input_text = data.get("text", "")
    replacement_text = data.get("replacement", Config.DEFAULT_REPLACEMENT)
    desensitize_scope = data.get("scope", Config.DEFAULT_SCOPE)
    
    if replacement_text.strip() == "":
        replacement_text = Config.DEFAULT_REPLACEMENT
        
    desensitized_text, stats = desensitize_text(
        input_text, 
        replacement_text, 
        desensitize_scope,
        use_html=False
    )
    
    return flask.jsonify({
        "desensitized_text": desensitized_text,
        "stats": stats,
    })


@app.route("/demo", methods=["GET", "POST"])
def demo():
    """演示端点 - 展示脱敏处理过程可视化"""
    input_text = ""
    replacement_text = Config.DEFAULT_REPLACEMENT
    desensitize_scope = "full"
    processing_result = None
    
    if flask.request.method == "POST":
        input_text = flask.request.form.get("input_text", "")
        if len(input_text) > 100:
            return flask.render_template("error.html")
        replacement_text = flask.request.form.get("replacement_text", Config.DEFAULT_REPLACEMENT)
        desensitize_scope = flask.request.form.get("desensitize_scope", Config.DEFAULT_SCOPE)
        
        if replacement_text.strip() == "":
            replacement_text = Config.DEFAULT_REPLACEMENT
            
        processing_result = get_detailed_processing_steps(
            input_text, 
            replacement_text, 
            desensitize_scope
        )
    
    return flask.render_template("demo.html", 
                               input_text=input_text, 
                               replacement_text=replacement_text,
                               desensitize_scope=desensitize_scope,
                               processing_result=processing_result)


@app.route("/health", methods=["GET"])
def health():
    """健康检查端点"""
    return flask.jsonify({"status": "ok", "service": "opaqAI"})


@app.route("/<path:path>", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
def catch_all(path):
    """
    通用代理路由 - 将所有其他请求转发到远程API
    
    特定路由（/、/demo、/api/desensitize、/health）除外，
    其他所有路径都转发到 REMOTE_API_ENDPOINT + /<path>
    
    脱敏处理逻辑在proxy.py的handle_proxy_request中自动判断
    """
    # 排除特定路由
    excluded_paths = ['', 'demo', 'api/desensitize', 'health']
    
    if path in excluded_paths or path.startswith('static/'):
        return flask.jsonify({"error": "Not found"}), 404
    
    # 调用handle_proxy_request处理所有代理请求
    # 脱敏/直接转发的判断在proxy.py中完成
    return handle_proxy_request()


if __name__ == "__main__":
    app.run(debug=Config.DEBUG, port=Config.PORT, host="0.0.0.0")
