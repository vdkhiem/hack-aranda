from dotenv import load_dotenv
import json
import logging
import logging.config
import os
import re
from UI import bedrock_agent_runtime
import streamlit as st
import uuid
import yaml

load_dotenv()

# Configure logging using YAML
if os.path.exists("logging.yaml"):
    with open("logging.yaml", "r") as file:
        config = yaml.safe_load(file)
        logging.config.dictConfig(config)
else:
    log_level = logging.getLevelNamesMapping()[(os.environ.get("LOG_LEVEL", "INFO"))]
    logging.basicConfig(level=log_level)

logger = logging.getLogger(__name__)

# Get config from environment variables
agent_id = os.environ.get("BEDROCK_AGENT_ID")
agent_alias_id = os.environ.get("BEDROCK_AGENT_ALIAS_ID", "TSTALIASID")  # TSTALIASID is the default test alias ID
ui_title = os.environ.get("BEDROCK_AGENT_TEST_UI_TITLE", "Welcome to Accura Agent")
ui_icon = os.environ.get("BEDROCK_AGENT_TEST_UI_ICON")


def init_session_state():
    st.session_state.session_id = str(uuid.uuid4())
    st.session_state.messages = []
    st.session_state.citations = []
    st.session_state.trace = {}


# General page configuration and initialization
st.set_page_config(page_title=ui_title, page_icon=ui_icon, layout="wide")

# Custom CSS for Accura Analysis theme
st.markdown("""
<style>
    /* Main content area styling with Accura colors */
    .main .block-container {
        font-family: "Source Sans Pro", sans-serif;
        font-size: 16px;
        line-height: 1.6;
        background-color: #f8f9fa;
    }
    
    /* Page header styling */
    h1 {
        color: #2563eb !important;
        font-family: "Source Sans Pro", sans-serif !important;
        font-weight: 700 !important;
        font-size: 2.5rem !important;
        margin-bottom: 1rem !important;
    }
    
    /* Chat messages styling with blue theme */
    .stChatMessage {
        font-family: "Source Sans Pro", sans-serif !important;
        font-size: 16px !important;
        line-height: 1.6 !important;
        border-radius: 8px !important;
        margin-bottom: 1rem !important;
    }
    
    /* User message styling */
    .stChatMessage[data-testid="user"] {
        background-color: #dbeafe !important;
        border-left: 4px solid #2563eb !important;
    }
    
    /* Assistant message styling */
    .stChatMessage[data-testid="assistant"] {
        background-color: #ffffff !important;
        border-left: 4px solid #f97316 !important;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1) !important;
    }
    
    /* Chat message content normalization */
    .stChatMessage .stMarkdown,
    .stChatMessage [data-testid="stMarkdownContainer"] {
        font-family: "Source Sans Pro", sans-serif !important;
        font-size: 16px !important;
        font-weight: 400 !important;
    }
    
    .stChatMessage .stMarkdown *,
    .stChatMessage [data-testid="stMarkdownContainer"] * {
        font-family: "Source Sans Pro", sans-serif !important;
        font-weight: 400 !important;
    }
    
    .stChatMessage .stMarkdown strong,
    .stChatMessage .stMarkdown b,
    .stChatMessage [data-testid="stMarkdownContainer"] strong,
    .stChatMessage [data-testid="stMarkdownContainer"] b {
        font-weight: 600 !important;
        color: #1e40af !important;
    }
    
    /* Additional chat message styling */
    .stChatMessage p, .stChatMessage div, .stChatMessage span {
        font-family: "Source Sans Pro", sans-serif !important;
        font-size: 16px !important;
        line-height: 1.6 !important;
    }
    
    /* Ensure all text elements use consistent font */
    .stMarkdown, .stText, p, div, span {
        font-family: "Source Sans Pro", sans-serif !important;
        font-weight: 400 !important;
    }
    
    /* Headers consistent styling with blue theme */
    h2, h3, h4, h5, h6 {
        font-family: "Source Sans Pro", sans-serif !important;
        font-weight: 600 !important;
        color: #1e40af !important;
    }
    
    /* Chat input styling with blue accent */
    .stChatInput > div > div > textarea {
        font-family: "Source Sans Pro", sans-serif !important;
        font-size: 16px !important;
        border: 2px solid #e5e7eb !important;
        border-radius: 8px !important;
    }
    
    .stChatInput > div > div > textarea:focus {
        border-color: #2563eb !important;
        box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.1) !important;
    }
    
    /* Sidebar styling with blue theme */
    .css-1d391kg, .css-1lcbmhc, .css-17eq0hr {
        background-color: #f1f5f9 !important;
        border-right: 2px solid #e2e8f0 !important;
    }
    
    /* Sidebar headers */
    .css-1d391kg h1, .css-1d391kg h2, .css-1d391kg h3 {
        color: #1e40af !important;
        font-family: "Source Sans Pro", sans-serif !important;
    }
    
    /* Code blocks styling */
    .stCode {
        font-family: "Fira Code", "Consolas", monospace !important;
        background-color: #f8fafc !important;
        border: 1px solid #e2e8f0 !important;
        border-radius: 6px !important;
    }
    
    /* Button styling with blue theme */
    .stButton > button {
        font-family: "Source Sans Pro", sans-serif !important;
        font-weight: 600 !important;
        background-color: #2563eb !important;
        color: white !important;
        border: none !important;
        border-radius: 6px !important;
        padding: 0.5rem 1rem !important;
        transition: all 0.2s ease !important;
    }
    
    .stButton > button:hover {
        background-color: #1d4ed8 !important;
        transform: translateY(-1px) !important;
        box-shadow: 0 4px 12px rgba(37, 99, 235, 0.3) !important;
    }
    
    /* Expander styling with blue theme */
    .streamlit-expanderHeader {
        font-family: "Source Sans Pro", sans-serif !important;
        font-weight: 600 !important;
        background-color: #f1f5f9 !important;
        border: 1px solid #e2e8f0 !important;
        border-radius: 6px !important;
        color: #1e40af !important;
    }
    
    .streamlit-expanderContent {
        border: 1px solid #e2e8f0 !important;
        border-top: none !important;
        border-radius: 0 0 6px 6px !important;
        background-color: #ffffff !important;
    }
    
    /* Override any bold/italic inconsistencies in markdown */
    .stMarkdown strong, .stMarkdown b {
        font-weight: 600 !important;
        font-family: "Source Sans Pro", sans-serif !important;
        color: #1e40af !important;
    }
    
    .stMarkdown em, .stMarkdown i {
        font-style: italic !important;
        font-weight: 400 !important;
        font-family: "Source Sans Pro", sans-serif !important;
    }
    
    /* Fix inline text formatting inconsistencies */
    .stMarkdown * {
        font-family: "Source Sans Pro", sans-serif !important;
    }
    
    /* Normalize all text content */
    [data-testid="stMarkdownContainer"] * {
        font-family: "Source Sans Pro", sans-serif !important;
        font-weight: 400 !important;
    }
    
    [data-testid="stMarkdownContainer"] strong,
    [data-testid="stMarkdownContainer"] b {
        font-weight: 600 !important;
        color: #1e40af !important;
    }
    
    /* List styling with orange accents */
    .stMarkdown ul, .stMarkdown ol {
        font-family: "Source Sans Pro", sans-serif !important;
        font-size: 16px !important;
        line-height: 1.6 !important;
    }
    
    .stMarkdown li {
        font-family: "Source Sans Pro", sans-serif !important;
        font-size: 16px !important;
        font-weight: 400 !important;
        margin-bottom: 8px !important;
        position: relative !important;
    }
    
    .stMarkdown ul li::marker {
        color: #f97316 !important;
    }
    
    /* Spinner styling */
    .stSpinner > div {
        border-color: #2563eb !important;
    }
    
    /* Citation links styling */
    sup {
        color: #f97316 !important;
        font-weight: 600 !important;
    }
    
    /* Citation references styling */
    br + a {
        color: #f97316 !important;
        text-decoration: none !important;
    }
    
    br + a:hover {
        text-decoration: underline !important;
        color: #ea580c !important;
    }
    
    /* Warning/alert boxes (if any) */
    .stAlert {
        border-radius: 8px !important;
    }
    
    .stAlert[data-baseweb="notification"] {
        background-color: #fef3c7 !important;
        border-left: 4px solid #f59e0b !important;
    }
    
    /* Success messages */
    .stSuccess {
        background-color: #dcfce7 !important;
        border-left: 4px solid #22c55e !important;
        border-radius: 8px !important;
    }
    
    /* Info messages */
    .stInfo {
        background-color: #dbeafe !important;
        border-left: 4px solid #2563eb !important;
        border-radius: 8px !important;
    }
</style>
""", unsafe_allow_html=True)

st.title(ui_title)
if len(st.session_state.items()) == 0:
    init_session_state()

# Sidebar button to reset session state
with st.sidebar:
    if st.button("Reset Session"):
        init_session_state()

# Messages in the conversation
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"], unsafe_allow_html=True)

# Chat input that invokes the agent
if prompt := st.chat_input():
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.write(prompt)

    with st.chat_message("assistant"):
        with st.empty():
            with st.spinner():
                response = bedrock_agent_runtime.invoke_agent(
                    agent_id,
                    agent_alias_id,
                    st.session_state.session_id,
                    prompt
                )
            output_text = response["output_text"]

            # Check if the output is a JSON object with the instruction and result fields
            try:
                # When parsing the JSON, strict mode must be disabled to handle badly escaped newlines
                # TODO: This is still broken in some cases - AWS needs to double sescape the field contents
                output_json = json.loads(output_text, strict=False)
                if "instruction" in output_json and "result" in output_json:
                    output_text = output_json["result"]
            except json.JSONDecodeError as e:
                pass

            # Add citations
            if len(response["citations"]) > 0:
                citation_num = 1
                output_text = re.sub(r"%\[(\d+)\]%", r"<sup>[\1]</sup>", output_text)
                num_citation_chars = 0
                citation_locs = ""
                for citation in response["citations"]:
                    for retrieved_ref in citation["retrievedReferences"]:
                        citation_marker = f"[{citation_num}]"
                        citation_locs += f"\n<br>{citation_marker} {retrieved_ref['location']['s3Location']['uri']}"
                        citation_num += 1
                output_text += f"\n{citation_locs}"

            st.session_state.messages.append({"role": "assistant", "content": output_text})
            st.session_state.citations = response["citations"]
            st.session_state.trace = response["trace"]
            
            # Display with consistent styling - clean text processing
            st.markdown(output_text, unsafe_allow_html=True)

trace_types_map = {
    "Pre-Processing": ["preGuardrailTrace", "preProcessingTrace"],
    "Orchestration": ["orchestrationTrace"],
    "Post-Processing": ["postProcessingTrace", "postGuardrailTrace"]
}

trace_info_types_map = {
    "preProcessingTrace": ["modelInvocationInput", "modelInvocationOutput"],
    "orchestrationTrace": ["invocationInput", "modelInvocationInput", "modelInvocationOutput", "observation", "rationale"],
    "postProcessingTrace": ["modelInvocationInput", "modelInvocationOutput", "observation"]
}

# Sidebar section for trace
with st.sidebar:
    st.title("Trace")

    # Show each trace type in separate sections
    step_num = 1
    for trace_type_header in trace_types_map:
        st.subheader(trace_type_header)

        # Organize traces by step similar to how it is shown in the Bedrock console
        has_trace = False
        for trace_type in trace_types_map[trace_type_header]:
            if trace_type in st.session_state.trace:
                has_trace = True
                trace_steps = {}

                for trace in st.session_state.trace[trace_type]:
                    # Each trace type and step may have different information for the end-to-end flow
                    if trace_type in trace_info_types_map:
                        trace_info_types = trace_info_types_map[trace_type]
                        for trace_info_type in trace_info_types:
                            if trace_info_type in trace:
                                trace_id = trace[trace_info_type]["traceId"]
                                if trace_id not in trace_steps:
                                    trace_steps[trace_id] = [trace]
                                else:
                                    trace_steps[trace_id].append(trace)
                                break
                    else:
                        trace_id = trace["traceId"]
                        trace_steps[trace_id] = [
                            {
                                trace_type: trace
                            }
                        ]

                # Show trace steps in JSON similar to the Bedrock console
                for trace_id in trace_steps.keys():
                    with st.expander(f"Trace Step {str(step_num)}", expanded=False):
                        for trace in trace_steps[trace_id]:
                            trace_str = json.dumps(trace, indent=2)
                            st.code(trace_str, language="json", line_numbers=True, wrap_lines=True)
                    step_num += 1
        if not has_trace:
            st.text("None")

    st.subheader("Citations")
    if len(st.session_state.citations) > 0:
        citation_num = 1
        for citation in st.session_state.citations:
            for retrieved_ref_num, retrieved_ref in enumerate(citation["retrievedReferences"]):
                with st.expander(f"Citation [{str(citation_num)}]", expanded=False):
                    citation_str = json.dumps(
                        {
                            "generatedResponsePart": citation["generatedResponsePart"],
                            "retrievedReference": citation["retrievedReferences"][retrieved_ref_num]
                        },
                        indent=2
                    )
                    st.code(citation_str, language="json", line_numbers=True, wrap_lines=True)
                citation_num = citation_num + 1
    else:
        st.text("None")
