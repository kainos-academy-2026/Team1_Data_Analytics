import streamlit as st
import pandas as pd
import time
from databricks.sdk import WorkspaceClient

# --- Page Config ---
st.set_page_config(page_title="Ask the Data", layout="wide", page_icon="\U0001F916")
st.title("\U0001F916 Ask the Data")
st.caption(
    "Ask natural language questions about taxi trip data \u2014 powered by Databricks Genie"
)

# --- Constants ---
GENIE_SPACE_ID = "01f19d4c6c7c11a28ee593077cee546a"
POLL_INTERVAL = 2  # seconds between polls
POLL_TIMEOUT = 120  # max seconds to wait for a response


# --- Workspace Client ---
@st.cache_resource
def get_workspace_client():
    """Initialise the Databricks SDK client (uses app service principal auth)."""
    return WorkspaceClient()


w = get_workspace_client()


# --- Genie API Helpers ---
def poll_for_completion(space_id: str, conversation_id: str, message_id: str):
    """Poll the Genie API until the message status leaves IN_PROGRESS."""
    elapsed = 0
    while elapsed < POLL_TIMEOUT:
        msg = w.genie.get_message(space_id=space_id, conversation_id=conversation_id, message_id=message_id)
        status = msg.status if hasattr(msg, "status") else getattr(msg, "state", None)
        if status and str(status).upper() not in ("IN_PROGRESS", "EXECUTING_QUERY", "SUBMITTED"):
            return msg
        time.sleep(POLL_INTERVAL)
        elapsed += POLL_INTERVAL
    return None


def extract_response(msg):
    """Extract text, SQL, and description from a completed Genie message."""
    text_parts = []
    sql_query = None

    if hasattr(msg, "attachments") and msg.attachments:
        for att in msg.attachments:
            if hasattr(att, "text") and att.text:
                content = getattr(att.text, "content", None) or str(att.text)
                if content:
                    text_parts.append(content)
            if hasattr(att, "query") and att.query:
                sql_query = getattr(att.query, "query", None) or getattr(att.query, "content", None)

    return "\n".join(text_parts) if text_parts else None, sql_query


def get_query_result_df(space_id: str, conversation_id: str, message_id: str):
    """Retrieve the query result as a pandas DataFrame."""
    try:
        result = w.genie.get_message_query_result(
            space_id=space_id,
            conversation_id=conversation_id,
            message_id=message_id,
        )
        # Navigate the response structure
        stmt = getattr(result, "statement_response", None)
        if stmt is None:
            return None
        result_data = getattr(stmt, "result", None)
        if result_data is None:
            return None

        # Extract columns
        schema = getattr(result_data, "schema", None)
        columns = []
        if schema and hasattr(schema, "columns"):
            columns = [col.name for col in schema.columns]

        # Extract rows
        rows = getattr(result_data, "data_array", None) or []
        if not columns:
            return None
        return pd.DataFrame(rows, columns=columns)
    except Exception:
        return None


# --- Session State ---
if "genie_messages" not in st.session_state:
    st.session_state.genie_messages = []
if "genie_conversation_id" not in st.session_state:
    st.session_state.genie_conversation_id = None


# --- Sidebar ---
with st.sidebar:
    st.markdown("---")
    st.markdown("### \U0001F4A1 Example Questions")
    st.markdown(
        """
    - What was total revenue last week?
    - Which pickup zones generate the most trips?
    - How does weather affect average trip duration?
    - Show me average fare by day of week
    - What\u2019s the busiest hour of the day?
    - Compare revenue on rainy vs dry days
    """
    )
    if st.button("\U0001F504 New Conversation"):
        st.session_state.genie_messages = []
        st.session_state.genie_conversation_id = None
        st.rerun()


# --- Chat History ---
for msg in st.session_state.genie_messages:
    with st.chat_message(msg["role"]):
        if msg.get("content"):
            st.markdown(msg["content"])
        if msg.get("df") is not None and not msg["df"].empty:
            st.dataframe(msg["df"], use_container_width=True)
        if msg.get("sql"):
            with st.expander("\U0001F50D View SQL"):
                st.code(msg["sql"], language="sql")


# --- Chat Input ---
if user_input := st.chat_input("Ask about taxi trips, revenue, zones, weather impact..."):
    # Display user message
    st.session_state.genie_messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)

    # Call Genie API
    with st.chat_message("assistant"):
        with st.spinner("Querying your data..."):
            try:
                # Start or continue conversation
                if st.session_state.genie_conversation_id is None:
                    resp = w.genie.start_conversation(
                        space_id=GENIE_SPACE_ID, content=user_input
                    )
                    # Extract IDs from response
                    conversation_id = (
                        resp.conversation_id
                        if hasattr(resp, "conversation_id")
                        else resp.conversation.id
                    )
                    message_id = (
                        resp.message_id
                        if hasattr(resp, "message_id")
                        else resp.message.id
                    )
                    st.session_state.genie_conversation_id = conversation_id
                else:
                    conversation_id = st.session_state.genie_conversation_id
                    resp = w.genie.create_message(
                        space_id=GENIE_SPACE_ID,
                        conversation_id=conversation_id,
                        content=user_input,
                    )
                    message_id = resp.id if hasattr(resp, "id") else resp.message.id

                # Poll for completion
                completed_msg = poll_for_completion(
                    GENIE_SPACE_ID, conversation_id, message_id
                )

                if completed_msg is None:
                    timeout_text = (
                        "\u23F3 The query timed out. Try a simpler question."
                    )
                    st.warning(timeout_text)
                    st.session_state.genie_messages.append(
                        {"role": "assistant", "content": timeout_text}
                    )
                else:
                    status = str(
                        getattr(completed_msg, "status", "UNKNOWN")
                    ).upper()

                    if "COMPLETED" in status or "SUCCEEDED" in status:
                        # Extract text and SQL
                        response_text, sql_query = extract_response(completed_msg)

                        # Get query result DataFrame
                        result_df = get_query_result_df(
                            GENIE_SPACE_ID, conversation_id, message_id
                        )

                        # Display
                        display_text = response_text or "Here are the results:"
                        st.markdown(display_text)

                        if result_df is not None and not result_df.empty:
                            st.dataframe(result_df, use_container_width=True)

                        if sql_query:
                            with st.expander("\U0001F50D View SQL"):
                                st.code(sql_query, language="sql")

                        st.session_state.genie_messages.append(
                            {
                                "role": "assistant",
                                "content": display_text,
                                "df": result_df,
                                "sql": sql_query,
                            }
                        )
                    else:
                        # Failed or other terminal status
                        fail_text = (
                            "\u26A0\uFE0F I couldn\u2019t answer that. "
                            "Try rephrasing or ask a different question."
                        )
                        error_detail = getattr(completed_msg, "error", None)
                        if error_detail:
                            fail_text += f"\n\n*Detail: {error_detail}*"
                        st.warning(fail_text)
                        st.session_state.genie_messages.append(
                            {"role": "assistant", "content": fail_text}
                        )

            except Exception as e:
                error_text = f"\u274C An error occurred: {str(e)}"
                st.error(error_text)
                st.session_state.genie_messages.append(
                    {"role": "assistant", "content": error_text}
                )
