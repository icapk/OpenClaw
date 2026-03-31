#!/bin/bash
# MiniMax M2.7 API Verification Script

API_URL="https://api.minimaxi.com/anthropic/v1/messages"
API_KEY="minimax-oauth"
MODEL="MiniMax-M2.7"

RESULT_FILE="$HOME/.openclaw/workspace/agents/product/minimax-verification-results.md"

# Initialize result file
cat > "$RESULT_FILE" << 'EOF'
# MiniMax M2.7 API 能力验证报告

## 验证时间
$(date '+%Y-%m-%d %H:%M:%S %Z')

---

EOF

# Function to call the API and record result
call_api() {
    local label="$1"
    local prompt="$2"
    local expected="$3"
    
    echo "===== Testing: $label ====="
    echo ""
    
    local start_time=$(date +%s.%N)
    
    response=$(curl -s --max-time 60 \
        -X POST "$API_URL" \
        -H "Authorization: Bearer $API_KEY" \
        -H "Content-Type: application/json" \
        -H "x-api-key: $API_KEY" \
        -H "anthropic-version: 2023-06-01" \
        -d "$(jq -n --arg model "$MODEL" --arg prompt "$prompt" '{
            model: $model,
            max_tokens: 2048,
            messages: [{role: "user", content: $prompt}]
        }')" 2>&1)
    
    local end_time=$(date +%s.%N)
    local elapsed=$(echo "$end_time - $start_time" | bc)
    
    echo "[$label]" >> "$RESULT_FILE"
    echo "- 耗时: ${elapsed}s" >> "$RESULT_FILE"
    echo "- Prompt: $prompt" >> "$RESULT_FILE"
    echo "" >> "$RESULT_FILE"
    
    if echo "$response" | jq -e '.content[0].text' > /dev/null 2>&1; then
        local text=$(echo "$response" | jq -r '.content[0].text // .error.message')
        local usage=$(echo "$response" | jq -r '.usage | "input=\(.input_tokens), output=\(.output_tokens), total=\(.input_tokens + .output_tokens))"')
        local id=$(echo "$response" | jq -r '.id // empty')
        
        echo "✅ 成功" >> "$RESULT_FILE"
        echo "- Response ID: $id" >> "$RESULT_FILE"
        echo "- Token使用: $usage" >> "$RESULT_FILE"
        echo "- 输出:" >> "$RESULT_FILE"
        echo "$text" | sed 's/^/> /' >> "$RESULT_FILE"
        echo "" >> "$RESULT_FILE"
        echo "✅ $label - 成功 (${elapsed}s)"
    else
        local err=$(echo "$response" | jq -r '.error.message // .error.code // .error.type // .message // "Unknown error"')
        echo "❌ 失败: $err" >> "$RESULT_FILE"
        echo "" >> "$RESULT_FILE"
        echo "❌ $label - 失败: $err"
    fi
    
    echo "" >> "$RESULT_FILE"
    echo "---" >> "$RESULT_FILE"
    echo ""
    
    echo "$response"
}

echo "Starting MiniMax M2.7 Verification..."
echo ""

# V1: 文本生成
echo "=== V1: 文本生成 ==="
call_api "V1-文本生成" "请写一段100字的产品经理自我介绍" "返回流畅文本"

# V2: 知识推理 (独立测试，因为多轮需要session)
echo "=== V2: 知识推理 ==="
call_api "V2-知识推理" "小明有5个苹果，给了小红3个，又买了2个，一共几个？" "正确计算"

# V3: 创意发散
echo "=== V3: 创意发散 ==="
call_api "V3-创意发散" "给我10个AI产品经理的副业方向" "返回列表"

# V4: JSON结构化
echo "=== V4: JSON结构化 ==="
call_api "V4-JSON结构化" "返回一个JSON，包含：name=小明，age=25，hobby=[篮球,游泳]" "有效JSON"

# V5: 风格模仿
echo "=== V5: 风格模仿 ==="
call_api "V5-风格模仿" "用鲁迅的风格写一段关于AI的文字" "有鲁迅味"

# V6: 多语言
echo "=== V6: 多语言 ==="
call_api "V6-多语言" "把'产品经理的核心能力是判断力'翻译成英文" "准确翻译"

# V7: 代码生成
echo "=== V7: 代码生成 ==="
call_api "V7-代码生成" "写一个Python函数，计算两个数的最大公约数（欧几里得算法）" "可运行代码"

# V8: 长文本摘要
echo "=== V8: 长文本摘要 ==="
ARTICLE="人工智能（AI）技术正在深刻改变产品开发的方式。在传统的产品管理流程中，产品经理需要花费大量时间进行用户调研、数据分析和文档撰写。然而，随着大语言模型（LLM）和AI辅助工具的成熟，这些重复性工作正在被逐步自动化。具体而言，AI可以帮助产品经理快速生成用户画像、自动撰写PRD文档、智能分析用户反馈中的关键问题，以及通过对话式界面快速回答产品相关的技术问题。这不仅大大提升了产品经理的工作效率，也让他们能够将更多精力投入到真正需要人类判断力的事物上，如战略规划和跨部门协调。当然，AI工具也带来了一些挑战，包括如何确保AI生成内容的准确性、如何保护用户数据的隐私，以及如何平衡AI效率与人类创意之间的关系。产品经理需要在拥抱新技术的同时，保持批判性思维，确保AI成为提升产品价值的工具，而非风险的来源。"
call_api "V8-长文本摘要" "请总结以下文章的3个要点：$ARTICLE" "准确摘要"

# V9: 多轮对话测试
echo "=== V9: 多轮对话 ==="
call_api "V9-多轮对话-Round1" "解释什么是RAG" "上下文连贯"
echo ""
echo "(Note: 完整多轮需要session保持，这里测试单轮响应能力)"

# V10: 图像理解 - 需要一张测试图片
echo "=== V10: 图像理解 ==="
call_api "V10-图像理解" "请描述这张图片的内容：https://upload.wikimedia.org/wikipedia/commons/thumb/d/d3/Turing_machine_2.svg/400px-Turing_machine_2.svg.png" "准确描述"

echo ""
echo "========================================"
echo "Verification complete! Results saved to:"
echo "$RESULT_FILE"
echo "========================================"
