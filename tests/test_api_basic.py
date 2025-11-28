import sys
import types
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))


# Stub langchain modules to avoid dependency load during tests
class DummyLLM:
    def __init__(self, *args, **kwargs):
        pass

    def invoke(self, messages):
        return types.SimpleNamespace(content="LONG")


sys.modules.setdefault("langchain_openai", types.SimpleNamespace(ChatOpenAI=DummyLLM))
sys.modules.setdefault("langchain_anthropic", types.SimpleNamespace(ChatAnthropic=DummyLLM))
sys.modules.setdefault(
    "langchain_google_genai", types.SimpleNamespace(ChatGoogleGenerativeAI=DummyLLM)
)
# Stub langgraph modules
class DummyToolNode:
    def __init__(self, tools=None):
        self.tools = tools or []


class DummyStateGraph:
    def __init__(self, *args, **kwargs):
        pass

    def add_node(self, *args, **kwargs):
        return self

    def add_edge(self, *args, **kwargs):
        return self

    def add_conditional_edges(self, *args, **kwargs):
        return self

    def compile(self):
        return self


class DummyMessagesState(dict):
    pass


langgraph_module = types.ModuleType("langgraph")
langgraph_graph = types.ModuleType("langgraph.graph")
langgraph_graph.END = "END"
langgraph_graph.START = "START"
langgraph_graph.StateGraph = DummyStateGraph
langgraph_graph.MessagesState = DummyMessagesState
langgraph_prebuilt = types.ModuleType("langgraph.prebuilt")
langgraph_prebuilt.ToolNode = DummyToolNode
sys.modules.setdefault("langgraph", langgraph_module)
sys.modules.setdefault("langgraph.graph", langgraph_graph)
sys.modules.setdefault("langgraph.prebuilt", langgraph_prebuilt)
# Stub langchain_core.messages
lc_messages = types.ModuleType("langchain_core.messages")
class DummyMessage:
    def __init__(self, content=None, **kwargs):
        self.content = content
        self.kwargs = kwargs
        self.tool_calls = []

    def __iter__(self):
        return iter([])

class DummyRemoveMessage:
    def __init__(self, id=None):
        self.id = id

lc_messages.HumanMessage = DummyMessage
lc_messages.RemoveMessage = DummyRemoveMessage
lc_messages.AIMessage = DummyMessage
sys.modules.setdefault("langchain_core.messages", lc_messages)
# Stub langchain_core.tools
lc_tools = types.ModuleType("langchain_core.tools")
def tool(fn):
    return fn
lc_tools.tool = tool
sys.modules.setdefault("langchain_core.tools", lc_tools)
# Stub langchain_core.prompts
lc_prompts = types.ModuleType("langchain_core.prompts")
class DummyPrompt:
    def __init__(self, *args, **kwargs):
        pass
    def partial(self, **kwargs):
        return self
    def __or__(self, other):
        return self
    def bind_tools(self, tools):
        return self
    def invoke(self, messages):
        return types.SimpleNamespace(tool_calls=[], content="stub")
class DummyMessagesPlaceholder:
    def __init__(self, variable_name=None):
        self.variable_name = variable_name
lc_prompts.ChatPromptTemplate = types.SimpleNamespace(from_messages=lambda msgs: DummyPrompt())
lc_prompts.MessagesPlaceholder = DummyMessagesPlaceholder
sys.modules.setdefault("langchain_core.prompts", lc_prompts)
# Stub chromadb
class DummyChromaCollection:
    def __init__(self, *args, **kwargs):
        self._docs = []
    def add(self, **kwargs):
        self._docs.append(kwargs)
    def query(self, **kwargs):
        return {"documents": [[]], "metadatas": [[]], "distances": [[]]}
class DummyChromaClient:
    def __init__(self, *args, **kwargs):
        pass
    def create_collection(self, name=None):
        return DummyChromaCollection()
class DummyChromaSettings:
    def __init__(self, *args, **kwargs):
        pass
chromadb = types.ModuleType("chromadb")
chromadb.Client = DummyChromaClient
chromadb_config = types.ModuleType("chromadb.config")
chromadb_config.Settings = DummyChromaSettings
sys.modules.setdefault("chromadb", chromadb)
sys.modules.setdefault("chromadb.config", chromadb_config)
# Stub openai
class DummyEmbeddingData:
    def __init__(self):
        self.embedding = [0.0, 0.0]
class DummyEmbeddingResponse:
    def __init__(self):
        self.data = [DummyEmbeddingData()]
class DummyEmbeddings:
    def create(self, *args, **kwargs):
        return DummyEmbeddingResponse()
class DummyOpenAIClient:
    def __init__(self, *args, **kwargs):
        self.embeddings = DummyEmbeddings()
openai_stub = types.ModuleType("openai")
openai_stub.OpenAI = DummyOpenAIClient
sys.modules.setdefault("openai", openai_stub)

from fastapi.testclient import TestClient

from api.main import create_app


class DummyGraph:
    def __init__(self, selected_analysts=None, debug=False, config=None):
        pass

    def propagate(self, symbol, trade_date):
        return (
            {
                "investment_plan": "Bullish plan",
                "trader_investment_plan": "Trader plan",
                "final_trade_decision": "Risk judge says LONG",
            },
            "We should go LONG",
        )

    def process_signal(self, decision_text):
        return "LONG"


def dummy_graph_factory(config):
    return DummyGraph()


def test_signal_endpoint():
    app = create_app(graph_factory=dummy_graph_factory)
    client = TestClient(app)

    resp = client.post(
        "/signal",
        json={"symbol": "BTC/USDT", "trade_date": "2024-11-01", "model": "gpt-5-mini"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["decision"] == "LONG"
    assert "Final Decision" in data["summary"]
