#!/usr/bin/python 3.10

import os
import streamlit as st
import pandas as pd
from apply import get_chat_response
from langchain.memory import ConversationBufferWindowMemory
import random
import importlib
import role as r
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
importlib.reload(r)  

# 读取默认角色
default_roles = r.default_roles
role_manager = r.RoleManager(default_roles)

# 侧边栏
with st.sidebar:
    
    model_name = st.selectbox('请选择模型', ['DeepSeek(v3)', 'Chat_GPT(4.1-mini)', 'Chat_GPT(4-turbo)'], )
    online = st.checkbox('联网搜索（暂不可用）')
    st.divider()

    # 滑动选项卡
    tab1, tab2 = st.tabs(['API', '邀请码'])
    with tab1:
        api_key = st.text_input('请输入API：', type='password')
        if model_name == 'DeepSeek(v3)':
            st.markdown('[获取DeepSeek api密钥](https://platform.deepseek.com/usage)')
        elif model_name == 'Chat_GPT(4-turbo)' or model_name == 'Chat_GPT(4.1-mini)':
            st.markdown('[获取OpenAI api密钥](https://platform.openai.com/account/api-keys)')
    with tab2:
        code = st.text_input('请输入邀请码：', type='password')
        if code == os.getenv("CODE"):
            if model_name == 'DeepSeek(v3)':
                api_key = os.getenv("DEEPSEEK_API_KEY")
            elif model_name == 'Chat_GPT(4-turbo)' or model_name == 'Chat_GPT(4.1-mini)':
                api_key = os.getenv("OPENAI_API_KEY")

    st.divider()

    selected_role = st.selectbox('请选择角色：', ['Zuan', 'Lyra', 'Kiri', 'Neon', 'Luna', 'Zen', 'Dr. Chaos', 'B-79', '塞翁', '自定义', '混乱模式🤯'])

    if selected_role == '自定义':
        with st.expander('创造力'):
            creativity = st.slider('', value=0.5, min_value=0.0, max_value=1.0, step=0.01)
        custom_prompt = st.text_area('请输入AI角色设定：')
        custom_role = r.ChatRole(
            name="ai",
            prompt=custom_prompt,
            title="私人助手😊",
            start_msg="有什么可以帮到您？"
        )
        role_manager.add_role(custom_role)
        current_role = custom_role
        current_role.creativity = creativity
    elif selected_role == '混乱模式🤯':
        current_role = role_manager.get_random_role()
    else:
        current_role = role_manager.get_role(selected_role)

    st.divider()

    # 保存会话
    if 'memory' not in st.session_state:
        # 初始化记忆
        st.session_state.memory = ConversationBufferWindowMemory(
            return_messages=True, 
            k=20,
            memory_key="history",  # 明确指定记忆键
            input_key="input"  # 明确指定输入键
        )
        # 初始化消息
        st.session_state.messages = [AIMessage(content='有什么可以帮到您？')]


    # 清空数据
    clear = st.button('清理缓存')
    # 定义对话框
    @st.dialog("确认操作")
    def confirm_action():
        st.write("确定要执行此操作吗？")
        if st.button("确认"):
            st.session_state.confirmed = True
            # 清空所有数据缓存
            st.cache_data.clear()
            # 清空所有资源缓存（如模型、数据库连接）
            st.cache_resource.clear()
            st.session_state.messages.clear()
            st.session_state.memory.clear()
            st.rerun()  # 刷新页面
    if clear:
        confirm_action()
    # 处理确认结果
    if st.session_state.get("confirmed"):
        st.success("数据已清空！")
        del st.session_state.confirmed

# 标题
st.title(current_role.title)
f'##### {current_role.start_msg}'
st.divider()

# 打印消息
for message in st.session_state.messages:
    # 确定消息角色
    if isinstance(message, HumanMessage):
        role = "human"
    elif isinstance(message, AIMessage):
        role = "ai"
    else:
        role = "ai"  # 默认值
    st.chat_message(role).write(message.content)

# 接收输入
user_input = st.chat_input()
if user_input:
    if not api_key and not code:
        st.info('请输入api密钥或邀请码')
        st.stop()

    # 保存和打印用户输入
    st.session_state.messages.append(HumanMessage(content=user_input))
    st.chat_message('human').write(user_input)
    st.session_state.memory.chat_memory.add_message(HumanMessage(content=user_input))

    # 传入角色提示词
    st.session_state.memory.chat_memory.add_message(SystemMessage(content=current_role.prompt))


    # 调用模型
    with st.spinner('ai正在思考，请稍候...'):
        response = get_chat_response(input = user_input, 
                                     memory = st.session_state.memory, 
                                     creativity = current_role.creativity,
                                     api_key = api_key, 
                                     chat_model = model_name)
        
    # 保存和打印模型输出
    st.session_state.messages.append(AIMessage(content=response))
    st.chat_message('ai').write(response)

    # 传入回答
    st.session_state.memory.chat_memory.add_message(AIMessage(content=response))

