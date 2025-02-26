# This is a sample Python script.
import os

# Press ⌃R to execute it or replace it with your code.
# Press Double ⇧ to search everywhere for classes, files, tool windows, actions, and settings.

from dotenv import load_dotenv

# 加载 .env 文件中的环境变量
load_dotenv(override=True)
print(f"OPENAI_BASE_URL: {os.getenv('OPENAI_BASE_URL')}")
print(f"OPENAI_API_KEY: {os.getenv('OPENAI_API_KEY')}")

import gradio as gr
import openai

# 获取 PORT 环境变量，默认值为 7860（本地开发时使用）
server_port = int(os.getenv("PORT", 7860))

print(f"server_port: {server_port}")

# 可替换为其他模型，如"gpt-4"
load_model = 'deepseek-v3-241226'

def user_submit(message, files, history):
    # 将用户消息和文件添加到历史
    # user_message = {"text": message, "files": files}
    # user_message = gr.ChatMessage(role="user", content=[message, files])
    user_message = gr.ChatMessage(role="user", content=message)
    history.append(user_message)
    return history

def bot_response(history):
    # 获取用户最新消息的文本部分（暂时忽略文件）
    # last_user_message = history[-1]
    # user_text = last_user_message["text"]

    try:
        # 调用OpenAI API
        response = openai.chat.completions.create(
            # model="deepseek-r1-250120",  # 可替换为其他模型，如"gpt-4"
            # model="deepseek-v3-241226",  # 可替换为其他模型，如"gpt-4"
            model=load_model,  # 可替换为其他模型，如"gpt-4"
            messages=history

            # messages=[{"role": "user", "content": user_text}]
        )
        # bot_text = response.choices[0].message.content  # 获取生成的回复
        bot_text = response.choices[0].message  # 获取生成的回复
        msg = gr.ChatMessage(role=bot_text.role, content=bot_text.content)
        history.append(msg)
        # bot_message = [bot_text]
        # history[-1] = (last_user_message, bot_message)  # 更新对话历史
        return history, ""  # 返回更新后的历史和空错误信息
    except Exception as e:
        return history, f"API调用失败: {str(e)}"  # 返回错误信息


with gr.Blocks() as demo:
    chatbot = gr.Chatbot(type="messages")  # 显示对话历史
    text_input = gr.Textbox(placeholder="输入消息...")
    file_input = gr.File(file_count="multiple", label="上传文件")
    submit_btn = gr.Button("发送")
    error_output = gr.Textbox(label="错误信息", interactive=False)  # 错误信息显示

    # 定义事件：先处理用户输入，再生成机器人响应
    submit_btn.click(
        fn=user_submit,
        inputs=[text_input, file_input, chatbot],
        outputs=chatbot
    ).then(
        fn=bot_response,
        inputs=chatbot,
        outputs=[chatbot, error_output]
    )

print(f"OPENAI_BASE_URL: {os.getenv('OPENAI_BASE_URL')}")

loadChatDemo = gr.load_chat(base_url=os.getenv('OPENAI_BASE_URL') ,model=load_model,streaming=True)

def launch():
    # Use a breakpoint in the code line below to debug your script.
    print(f'launch ...')  # Press ⌘F8 to toggle the breakpoint.
    # 启动应用
    # demo.launch()
    loadChatDemo.launch(server_port=server_port)


# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    launch()

# See PyCharm help at https://www.jetbrains.com/help/pycharm/
