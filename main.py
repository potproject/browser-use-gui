import flet as ft
import datetime
import asyncio
import os
import threading

# 仮のインポート例
from langchain_openai import ChatOpenAI
from browser_use import Agent

async def run_agent_async(task: str, model_name: str):
    agent = Agent(task=task, llm=ChatOpenAI(model=model_name))
    result = await agent.run()
    return result

def main(page: ft.Page):
    page.title = "Browser use GUI"
    page.window_width = 1100
    page.window_height = 500
    
    #--------------------------------------------------
    # テキスト操作の補助関数
    #--------------------------------------------------
    def append_log(msg: str):
        logs.value += msg
        page.update()

    def show_final_result(msg: str, is_error=False):
        if is_error:
            final_result.value += f"[ERROR] {msg}\n"
        else:
            final_result.value += f"{msg}\n"
        page.update()

    #--------------------------------------------------
    # 実行ボタンが押されたときの処理
    #--------------------------------------------------
    def on_execute(e):
        openai_api = openai_api_key.value.strip()
        anthropic_api = anthropic_api_key.value.strip()
        model = model_name.value.strip()
        task_text = text_task.value.strip()

        # 画面クリア
        logs.value = ""
        final_result.value = ""
        page.update()

        # 環境変数
        os.environ["OPENAI_API_KEY"] = openai_api
        os.environ["ANTHROPIC_API_KEY"] = anthropic_api

        append_log("[INFO] Starting Agent...\n")

        def worker():
            try:
                # 重い処理をバックグラウンドで実行
                agent_history_list = asyncio.run(run_agent_async(task_text, model))

                # ファイルに保存
                date_str = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                agent_history_list.save_to_file(f"history/{date_str}_agent_history_list.json")
                logs.value += f"[INFO] Agent history saved to history/{date_str}_agent_history_list.json\n"

                # スレッド内で直接 UI を編集
                logs.value += "[INFO] Agent finished.\n"
                final_res = agent_history_list.final_result()
                if final_res:
                    final_result.value += final_res + "\n"
                else:
                    final_result.value += "[ERROR] No final result found.\n"

            except Exception as err:
                logs.value += f"[ERROR] {str(err)}\n"
                final_result.value += f"[ERROR] {str(err)}\n"

            # 最後に更新
            page.update()

        threading.Thread(target=worker, daemon=True).start()

    #--------------------------------------------------
    # UI要素定義
    #--------------------------------------------------
    openai_api_key = ft.TextField(label="OpenAI API Key", password=True)
    anthropic_api_key = ft.TextField(label="Anthropic API Key", password=True)
    model_name = ft.TextField(label="LLM Model", value="gpt-4o-mini")
    text_task = ft.TextField(
        label="Task Input",
        multiline=True,
        min_lines=6,
        max_lines=6,
        value="Find a one-way flight from Bali to Oman on 12 January 2025 on Google Flights. Return me the cheapest option."
    )
    logs = ft.TextField(label="Logs", multiline=True, read_only=True, expand=True, min_lines=8, max_lines=8)
    final_result = ft.TextField(label="Final Result", multiline=True, read_only=True, expand=True, min_lines=8, max_lines=8)

    execute_button = ft.ElevatedButton(text="Execute", on_click=on_execute)

    # レイアウト例
    page.add(
        ft.Row([
            ft.Column([
                ft.Text("Configurations", weight=ft.FontWeight.BOLD, size=18),
                openai_api_key,
                anthropic_api_key,
                model_name,
                ft.Text("Task Input", weight=ft.FontWeight.BOLD, size=18),
                text_task,
                execute_button,
            ], width=400),
            ft.Column([
                logs,
                final_result,
            ], expand=True)
        ], expand=True)
    )

if __name__ == "__main__":
    ft.app(target=main)
