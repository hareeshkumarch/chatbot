from dataclasses import dataclass, field

from app.llm.base import Message


@dataclass
class PromptTemplate:
    task: str
    version: str
    system: str
    few_shot: list[tuple[str, str]] = field(default_factory=list)

    def render(self, **kwargs) -> list[Message]:
        messages = [Message(role="system", content=self.system.format(**kwargs) if _needs_format(self.system, kwargs) else self.system)]
        for user_text, assistant_text in self.few_shot:
            messages.append(Message(role="user", content=user_text))
            messages.append(Message(role="assistant", content=assistant_text))
        return messages


def _needs_format(template: str, kwargs: dict) -> bool:
    return any("{" + key + "}" in template for key in kwargs)


QUERY_CLASSIFICATION = PromptTemplate(
    task="query_classification",
    version="4",
    system=(
        "Break the user's question into the data source(s) needed to answer it completely, then output a plan.\n\n"
        "Available capabilities:\n"
        "small_talk - greetings, chit-chat, meta questions, or conversational follow-ups (e.g. requests to summarize, explain, translate, formatting changes, or refer back to the previous response) (never combined with others)\n"
        "document_qa - answerable from uploaded documents or general knowledge\n"
        "sql_data - the tenant's own database (counts, aggregates, records)\n"
        "connector_action - search or act on a connected tool (Slack, GitHub, Jira)\n"
        "web_search:optimized_query - open, current-events, or general-knowledge web questions\n"
        "news:optimized_query - recent news, headlines, or 'what's happening with X'. Include country or region in the query for local news.\n"
        "places:optimized_query - local businesses, venues, or things at a physical location\n"
        "trends:keyword - how interest or search volume in something has changed over time\n"
        "finance:TICKER - a stock price, quote, market cap, or other public company data. "
        "Use the correct exchange ticker: AAPL for Apple, RELIANCE.NS for Reliance (NSE India), "
        "TCS.NS for TCS, 005930.KS for Samsung (Korea), 7203.T for Toyota (Tokyo), VOW3.DE for Volkswagen (Germany).\n"
        "finance_history:TICKER:PERIOD - historical stock prices or chart data. "
        "PERIOD can be 1mo, 3mo, 6mo, 1y, 2y, 5y, or max. Use this when the user asks for a chart, graph, "
        "historical performance, or price history of a stock. Use the correct exchange ticker.\n"
        "demographics:place - population, income, or age statistics for a US state\n\n"
        "Most questions need exactly one capability: respond with just that label, or label:parameter.\n"
        "If the question genuinely needs more than one source, output every needed step "
        "separated by a semicolon, most important first, for example finance:TSLA;news:Tesla. "
        "Do not split a question into multiple steps unless it truly asks for more than one kind of information.\n"
        "Output only the plan, nothing else, no numbering, no explanation."
    ),
    few_shot=[
        ("What does our Q3 handbook say about parental leave?", "document_qa"),
        ("How many orders did we get last week?", "sql_data"),
        ("Find the deployment issue thread in Jira", "connector_action"),
        ("hey how's it going", "small_talk"),
        ("Who won the 2022 football world cup?", "web_search:2022 football world cup winner"),
        ("Find good coffee shops near Koramangala, Bangalore", "places:coffee shops Koramangala Bangalore"),
        ("What's the population and median income of Texas?", "demographics:Texas"),
        ("What's Tesla's stock price and any recent news about them?", "finance:TSLA;news:Tesla"),
        ("Generate a chart for Apple stock for last 1 year", "finance_history:AAPL:1y"),
        ("Show me the price history of MSFT over the past 6 months", "finance_history:MSFT:6mo"),
        ("Plot Reliance Industries stock performance for 2 years", "finance_history:RELIANCE.NS:2y"),
        ("Show TCS share price chart for last 1 year", "finance_history:TCS.NS:1y"),
        ("Samsung stock chart for 5 years", "finance_history:005930.KS:5y"),
        ("What's the latest news in India?", "news:India latest news"),
        ("Semiconductor industry news in Japan", "news:semiconductor industry Japan"),
        ("Latest tech news from Germany", "news:tech news Germany"),
        ("What's happening in the UK economy?", "news:UK economy latest"),
        ("Infosys stock price", "finance:INFY.NS"),
        ("What's the share price of Toyota?", "finance:7203.T"),
        ("HDFC Bank stock price", "finance:HDFCBANK.NS"),
        ("summarise them", "small_talk"),
        ("explain that", "small_talk"),
        ("summarise the headlines", "small_talk"),
        ("write a summary of the above news", "small_talk"),
        ("tell me more about the first point", "small_talk"),
        (
            "How many support tickets did we close last week, and is there any news about our main competitor?",
            "sql_data;news:main competitor",
        ),
        (
            "What does our handbook say about remote work, and how does interest in remote work compare nationally?",
            "document_qa;trends:remote work",
        ),
    ],
)

QUERY_REWRITE = PromptTemplate(
    task="query_rewrite",
    version="1",
    system=(
        "Rewrite the latest user question into a fully self-contained search query. "
        "Resolve pronouns and references using the conversation history. "
        "Output only the rewritten query, no explanation."
    ),
)

HYDE_GENERATION = PromptTemplate(
    task="hyde",
    version="1",
    system=(
        "Write a short hypothetical passage, in the style of the target document set, "
        "that would directly answer the user's question. Do not mention that it is hypothetical. "
        "Keep it under 120 words."
    ),
)

RETRIEVAL_SYNTHESIS = PromptTemplate(
    task="retrieval_synthesis",
    version="4",
    system=(
        "Answer the user's question using only the numbered context passages provided.\n"
        "Cite passage numbers in square brackets immediately after each claim, like [2]. "
        "Multiple citations may appear together, like [1][3].\n"
        "Format for readability:\n"
        "- Lead with a direct one-sentence answer.\n"
        "- Use short ### headings when the answer has distinct parts.\n"
        "- Use bullet lists for multiple parallel facts.\n"
        "- Use a markdown table only for ≤8 rows of comparable data; otherwise summarize in prose.\n"
        "If passages partially answer the question, answer what they support and state what is missing. "
        "If they do not address the question, say so in one sentence. "
        "Never invent numbers, dates, names, or quotes."
    ),
)

SQL_GENERATION = PromptTemplate(
    task="sql_generation",
    version="1",
    system=(
        "Given the database schema and the user's question, write a single read-only SQL SELECT statement "
        "that answers it. Never use INSERT, UPDATE, DELETE, DROP, ALTER, or multiple statements. "
        "Always include a LIMIT clause. Output only the SQL statement."
    ),
)

VERIFICATION = PromptTemplate(
    task="verification",
    version="3",
    system=(
        "You will be given an answer and the source passages it claims to be based on.\n"
        "Check every factual claim: names, numbers, dates, quotes, and causal statements.\n"
        "A claim is SUPPORTED only if a passage states it directly or follows from simple arithmetic on stated numbers.\n"
        "If a material claim lacks support, the answer is UNSUPPORTED.\n"
        "Respond with SUPPORTED or UNSUPPORTED, then one sentence. "
        "If UNSUPPORTED, name the specific unsupported claim."
    ),
)

CONNECTOR_SYNTHESIS = PromptTemplate(
    task="connector_synthesis",
    version="4",
    system=(
        "Answer the user's question using only the structured data below from connected tools or live sources.\n"
        "Reference specific identifiers, names, and values from the data. State numbers exactly as given.\n"
        "Format for readability:\n"
        "- Lead with a direct answer.\n"
        "- Use **bold** for the most important figures.\n"
        "- Use bullet lists when comparing multiple items.\n"
        "- Use a markdown table only for ≤8 comparable rows; the UI may render larger tables separately.\n"
        "If the data does not answer the question, say so plainly. Do not guess or round beyond what is shown.\n"
        "For stock chart data, describe the key trends: highs, lows, overall direction, and notable movements."
    ),
)

MULTI_SOURCE_SYNTHESIS = PromptTemplate(
    task="multi_source_synthesis",
    version="2",
    system=(
        "Answer the user's question by synthesizing every source in the context below — documents, database rows, "
        "market data, historical prices, trends, and live search results may all be present.\n"
        "Reason step by step internally, then write a unified answer:\n"
        "1. Identify what each source contributes.\n"
        "2. Resolve overlaps and contradictions — prefer primary data over summaries.\n"
        "3. Combine into one coherent response with citations [n] for document passages only.\n"
        "Format:\n"
        "- Open with the direct answer.\n"
        "- Use ### headings when covering distinct facets (e.g. documents vs. market data).\n"
        "- Use bullet lists and small markdown tables (≤8 rows) where they aid clarity.\n"
        "- For stock/finance data, describe trends, highs, lows, and key movements.\n"
        "Never invent facts. If a source failed or is empty, note the gap briefly."
    ),
)

GENERAL_CHAT = PromptTemplate(
    task="general_chat",
    version="1",
    system="You are a helpful enterprise assistant. Be direct, accurate, and concise.",
)

REPORT_STRUCTURING = PromptTemplate(
    task="report_structuring",
    version="1",
    system=(
        "You are structuring a research report from the gathered context provided by the user. "
        "Output ONLY valid JSON matching this exact schema, nothing else, no markdown fences, no commentary:\n"
        '{"title": string, "subtitle": string, "sections": [{"heading": string, "paragraphs": [string], '
        '"table": {"headers": [string], "rows": [[string]]} or null, '
        '"chart": {"title": string, "chart_type": "bar" or "line" or "pie", "labels": [string], '
        '"series": {"series name": [number]}} or null}]}\n\n'
        "Rules:\n"
        "- Every claim in every paragraph must come from the provided context. Never invent facts, numbers, or names.\n"
        "- Only include a table when the context has genuinely tabular data: multiple comparable records with the same fields.\n"
        "- Only include a chart when the context has numeric data across categories or time that a reader would benefit from seeing visualized. "
        "Do not fabricate numbers to fill a chart.\n"
        "- Produce 3 to 6 sections. Every section needs at least one paragraph of real prose, not bullet fragments.\n"
        "- If the context does not fully cover the topic, say so plainly in the relevant section instead of guessing."
    ),
)

PROMPTS: dict[str, PromptTemplate] = {
    p.task: p
    for p in [
        QUERY_CLASSIFICATION,
        QUERY_REWRITE,
        HYDE_GENERATION,
        RETRIEVAL_SYNTHESIS,
        SQL_GENERATION,
        VERIFICATION,
        CONNECTOR_SYNTHESIS,
        MULTI_SOURCE_SYNTHESIS,
        GENERAL_CHAT,
        REPORT_STRUCTURING,
    ]
}


def render_prompt(task: str, **kwargs) -> list[Message]:
    return PROMPTS[task].render(**kwargs)


def render_prompt_with_user_message(task: str, user_content: str, history: list[Message] | None = None, **kwargs) -> list[Message]:
    messages = render_prompt(task, **kwargs)
    if history:
        messages = [*messages, *history]
    return [*messages, Message(role="user", content=user_content)]
