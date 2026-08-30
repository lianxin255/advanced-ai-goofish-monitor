import os
import sys

from dotenv import load_dotenv
from openai import AsyncOpenAI

from src.infrastructure.config.env_manager import env_manager
from src.infrastructure.config.settings import (
    AI_MAX_OUTPUT_TOKENS_DEFAULT,
    AI_MAX_OUTPUT_TOKENS_MAX,
    AI_MAX_OUTPUT_TOKENS_MIN,
    AISettings,
    AppSettings,
    NotificationSettings,
    ScraperSettings,
)

# --- AI & Notification Configuration ---
# 仍然显式 load_dotenv 一次，兼容历史上依赖"导入 src.config 即会把 .env 灌入
# os.environ"这一副作用的调用方；实际的配置解析逻辑统一委托给 settings.py 的
# Pydantic 模型（在此处每次导入都重新实例化，而不是复用其模块级单例），
# 一是避免两套独立的 os.getenv 解析逻辑产生不一致的默认值（曾经出现过
# PCURL_TO_MOBILE、STATE_FILE 在两侧默认值不一致的问题），二是保留"重新
# import/reload 本模块即可拿到最新环境变量"的原有行为。
load_dotenv(override=True)

ai_settings = AISettings()
notification_settings = NotificationSettings()
scraper_settings = ScraperSettings()
settings = AppSettings()

# --- File Paths & Directories ---
STATE_FILE = scraper_settings.state_file
IMAGE_SAVE_DIR = settings.image_save_dir
CONFIG_FILE = settings.config_file
os.makedirs(IMAGE_SAVE_DIR, exist_ok=True)

# 任务隔离的临时图片目录前缀
TASK_IMAGE_DIR_PREFIX = settings.task_image_dir_prefix

# --- API URL Patterns ---
API_URL_PATTERN = "h5api.m.goofish.com/h5/mtop.taobao.idlemtopsearch.pc.search"
DETAIL_API_URL_PATTERN = "h5api.m.goofish.com/h5/mtop.taobao.idle.pc.detail"

# --- Environment Variables ---
API_KEY = ai_settings.api_key
BASE_URL = ai_settings.base_url or None
MODEL_NAME = ai_settings.model_name or None
PROXY_URL = ai_settings.proxy_url
NTFY_TOPIC_URL = notification_settings.ntfy_topic_url
GOTIFY_URL = notification_settings.gotify_url
GOTIFY_TOKEN = notification_settings.gotify_token
BARK_URL = notification_settings.bark_url
WX_BOT_URL = notification_settings.wx_bot_url
TELEGRAM_BOT_TOKEN = notification_settings.telegram_bot_token
TELEGRAM_CHAT_ID = notification_settings.telegram_chat_id
WEBHOOK_URL = notification_settings.webhook_url
WEBHOOK_METHOD = (notification_settings.webhook_method or "POST").upper()
WEBHOOK_HEADERS = notification_settings.webhook_headers
WEBHOOK_CONTENT_TYPE = (notification_settings.webhook_content_type or "JSON").upper()
WEBHOOK_QUERY_PARAMETERS = notification_settings.webhook_query_parameters
WEBHOOK_BODY = notification_settings.webhook_body
PCURL_TO_MOBILE = notification_settings.pcurl_to_mobile
RUN_HEADLESS = scraper_settings.run_headless
LOGIN_IS_EDGE = scraper_settings.login_is_edge
RUNNING_IN_DOCKER = scraper_settings.running_in_docker
USE_SYSTEM_CHROME = scraper_settings.use_system_chrome
AI_DEBUG_MODE = ai_settings.debug_mode
SKIP_AI_ANALYSIS = ai_settings.skip_analysis
ENABLE_THINKING = ai_settings.enable_thinking
ENABLE_RESPONSE_FORMAT = ai_settings.enable_response_format

# --- Headers ---
IMAGE_DOWNLOAD_HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:139.0) Gecko/20100101 Firefox/139.0',
    'Accept': 'image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8',
    'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
    'Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': '1',
}

# --- Client Initialization ---
# 检查配置是否齐全
if not all([BASE_URL, MODEL_NAME]):
    print("警告：未在 .env 文件中完整设置 OPENAI_BASE_URL 和 OPENAI_MODEL_NAME。AI相关功能可能无法使用。")
    client = None
else:
    try:
        if PROXY_URL:
            print(f"正在为AI请求使用HTTP/S代理: {PROXY_URL}")
            # httpx 会自动从环境变量中读取代理设置
            os.environ['HTTP_PROXY'] = PROXY_URL
            os.environ['HTTPS_PROXY'] = PROXY_URL

        # openai 客户端内部的 httpx 会自动从环境变量中获取代理配置
        client = AsyncOpenAI(api_key=API_KEY, base_url=BASE_URL)
    except Exception as e:
        print(f"初始化 OpenAI 客户端时出错: {e}")
        client = None

# 检查AI客户端是否成功初始化
if not client:
    # 在 prompt_generator.py 中，如果 client 为 None，会直接报错退出
    # 在 spider_v2.py 中，AI分析会跳过
    # 为了保持一致性，这里只打印警告，具体逻辑由调用方处理
    pass

# 检查关键配置
if not all([BASE_URL, MODEL_NAME]) and 'prompt_generator.py' in sys.argv[0]:
    sys.exit("错误：请确保在 .env 文件中完整设置了 OPENAI_BASE_URL 和 OPENAI_MODEL_NAME。(OPENAI_API_KEY 对于某些服务是可选的)")

# 这些模型默认开启思考模式，且支持通过 enable_thinking=False 关闭。
THINKING_DISABLED_MODEL_MARKERS = ("minimax",)


def _model_requires_thinking_disabled(model_name):
    """识别默认需要关闭思考模式的模型（如 MiniMax）。"""
    name = (model_name or "").lower()
    return any(marker in name for marker in THINKING_DISABLED_MODEL_MARKERS)


def get_ai_max_output_tokens() -> int:
    """AI 单次回复的输出 token 上限。

    调用时经 env_manager 实时读取 .env，Web UI 保存后下一次 AI 调用即生效，
    无需重启进程；解析失败或越界时收敛到默认值。
    """
    raw = env_manager.get_value("AI_MAX_OUTPUT_TOKENS", "")
    try:
        value = int(str(raw).strip())
    except (TypeError, ValueError):
        return AI_MAX_OUTPUT_TOKENS_DEFAULT
    return max(AI_MAX_OUTPUT_TOKENS_MIN, min(AI_MAX_OUTPUT_TOKENS_MAX, value))


def get_ai_request_params(**kwargs):
    """
    构建AI请求参数，根据ENABLE_THINKING和ENABLE_RESPONSE_FORMAT环境变量决定是否添加相应参数
    """
    if ENABLE_THINKING or _model_requires_thinking_disabled(MODEL_NAME):
        kwargs["extra_body"] = {"enable_thinking": False}
    
    # 如果禁用结构化输出，则移除 text.format 配置
    if not ENABLE_RESPONSE_FORMAT and "text" in kwargs:
        text_config = kwargs.get("text")
        if isinstance(text_config, dict):
            text_config = dict(text_config)
            text_config.pop("format", None)
            if text_config:
                kwargs["text"] = text_config
            else:
                del kwargs["text"]
    
    return kwargs
