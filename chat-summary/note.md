Thứ tự đúng khi build messages gửi LLM
pythonmessages = [
    # 1. System prompt (cố định, ít thay đổi)
    SystemMessage("Bạn là trợ lý tra cứu tài liệu..."),

    # 2. Summary tin cũ (nếu có)
    SystemMessage("[Tóm tắt trước]: user hỏi về điều 5, điều 6..."),

    # 3. Recent messages (6 tin gần nhất)
    HumanMessage("Điều 7 nói gì?"),
    AIMessage("Điều 7 quy định..."),
    HumanMessage("Còn điều 8?"),
    AIMessage("Điều 8 quy định..."),

    # 4. RAG context (kết quả tìm kiếm cho câu hỏi HIỆN TẠI)
    HumanMessage("""Dựa vào tài liệu sau:
    [Trang 5]: ... nội dung chunk 1 ...
    [Trang 7]: ... nội dung chunk 2 ...
    
    Câu hỏi: Điều 9 quy định gì?"""),
]