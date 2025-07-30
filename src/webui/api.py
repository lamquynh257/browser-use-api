from fastapi import FastAPI
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import asyncio
import os

from src.webui.webui_manager import WebuiManager
from src.agent.browser_use.browser_use_agent import BrowserUseAgent
from src.browser.custom_browser import CustomBrowser
from browser_use.browser.browser import BrowserConfig
from browser_use.browser.context import BrowserContextConfig
from src.controller.custom_controller import CustomController
from src.utils.llm_provider import get_llm_model

app = FastAPI()

class RunTaskRequest(BaseModel):
    task_name: str

@app.post("/api/v1/run-task")
async def run_task(request: RunTaskRequest):
    # 1. Khởi tạo WebuiManager và các thành phần cần thiết
    webui_manager = WebuiManager()
    webui_manager.init_browser_use_agent()

    # 2. Khởi tạo CustomBrowser với config mặc định (tắt headless, full màn hình)
    browser_config = BrowserConfig(
        headless=False,
        extra_browser_args=["--start-maximized"],
        new_context_config=BrowserContextConfig(
            window_width=1920,
            window_height=1080
        )
    )
    webui_manager.bu_browser = CustomBrowser(config=browser_config)

    # 3. Khởi tạo BrowserContext
    context_config = BrowserContextConfig()
    webui_manager.bu_browser_context = await webui_manager.bu_browser.new_context(config=context_config)

    # 4. Khởi tạo Controller
    webui_manager.bu_controller = CustomController()

    # 5. Khởi tạo LLM Gemini với GOOGLE_API_KEY
    google_api_key = os.getenv("GOOGLE_API_KEY")
    if not google_api_key:
        return JSONResponse(content={
            "status": "error",
            "error": "GOOGLE_API_KEY environment variable not set. Please set your Gemini API key."
        }, status_code=500)
    try:
        llm = get_llm_model(
            provider="google",
            model_name="gemini-2.5-flash",
            temperature=0.7,
            base_url=None,
            api_key=google_api_key
        )
    except Exception as e:
        return JSONResponse(content={
            "status": "error",
            "error": f"Failed to initialize Gemini LLM: {str(e)}"
        }, status_code=500)

    # 6. Khởi tạo Agent
    agent = BrowserUseAgent(
        task=request.task_name,
        llm=llm,
        browser=webui_manager.bu_browser,
        browser_context=webui_manager.bu_browser_context,
        controller=webui_manager.bu_controller,
        source="api"
    )

    # 7. Thực thi agent
    try:
        result = await agent.run()
        return JSONResponse(content={
            "status": "success",
            "task_name": request.task_name,
            "result": str(result)
        })
    except Exception as e:
        return JSONResponse(content={
            "status": "error",
            "task_name": request.task_name,
            "error": str(e)
        }, status_code=500)
    finally:
        # Đảm bảo đóng context và browser sau khi chạy xong
        try:
            if webui_manager.bu_browser_context:
                await webui_manager.bu_browser_context.close()
        except Exception:
            pass
        try:
            if webui_manager.bu_browser:
                await webui_manager.bu_browser.close()
        except Exception:
            pass 