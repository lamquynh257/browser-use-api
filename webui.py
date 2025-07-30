from dotenv import load_dotenv
load_dotenv()
import argparse
from src.webui.interface import theme_map, create_ui
from src.webui.api import app as fastapi_app
import gradio as gr


def main():
    parser = argparse.ArgumentParser(description="Gradio WebUI for Browser Agent")
    parser.add_argument("--ip", type=str, default="0.0.0.0", help="IP address to bind to")
    parser.add_argument("--port", type=int, default=7788, help="Port to listen on")
    parser.add_argument("--theme", type=str, default="Ocean", choices=theme_map.keys(), help="Theme to use for the UI")
    args = parser.parse_args()

    demo = create_ui(theme_name=args.theme)
    # Mount Gradio app to FastAPI
    import uvicorn
    from fastapi.middleware.cors import CORSMiddleware
    fastapi_app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app_with_gradio = gr.mount_gradio_app(fastapi_app, demo, path="/")
    uvicorn.run(app_with_gradio, host=args.ip, port=args.port)


if __name__ == '__main__':
    main()
