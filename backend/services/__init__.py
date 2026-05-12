"""
外部服务集成。

本模块包含各类外部服务的适配器：
- ASR（语音识别）: whisper_api、whisper_local、tencent_asr 等
- TTS（语音合成）: edge_tts、openai_tts、tencent_tts 等
- 视觉: 截图处理流水线
- 搜索: 联网搜索 Provider（tavily / serper / bing）

每类服务都有一个基类接口 + 多个 Provider 实现。
具体使用哪个 Provider 由配置决定。
"""
