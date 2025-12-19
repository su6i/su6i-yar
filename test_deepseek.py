import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.tools import tool
from langchain_core.messages import HumanMessage

# 1. Load Env
load_dotenv()
api_key = os.getenv("DEEPSEEK_API_KEY")

if not api_key:
    print("❌ Error: DEEPSEEK_API_KEY not found in environment!")
    exit(1)

print(f"🔑 Key found: {api_key[:5]}...{api_key[-4:]}")

# 2. Initialize Model
llm = ChatOpenAI(
    base_url="https://api.deepseek.com",
    model="deepseek-chat",
    api_key=api_key,
    temperature=0.0
)

# 3. Define a Tool (to test generic tool support)
@tool
def magic_calculator(a: int, b: int) -> int:
    """Multiplies two numbers using magic."""
    return a * b

print("\n📡 Testing Connection...")
try:
    # Test 1: Simple Chat
    response = llm.invoke("Hello, are you ready?")
    print(f"✅ Response: {response.content}")
    
    # Test 2: Tool Calling
    print("\n🛠 Testing Tool Support...")
    llm_with_tools = llm.bind_tools([magic_calculator])
    
    query = "What is 5 multiplied by 5 using magic?"
    tool_response = llm_with_tools.invoke(query)
    
    if tool_response.tool_calls:
        print(f"✅ Tool Call Detected: {tool_response.tool_calls}")
        print("🎉 DeepSeek supports Function Calling (Tools)!")
    else:
        print("⚠️ No tool call triggered. (DeepSeek V2/V3 usually supports it, might need prompt tuning)")

except Exception as e:
    print(f"❌ Error: {e}")
