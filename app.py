from dotenv import load_dotenv
import json
import logging
import logging.config
import os
import pandas as pd
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
    st.session_state.uploaded_documents = [
        {"name": "Tax_Return_2023.pdf", "size": "2.3 MB", "status": "completed"},
        {"name": "Receipts_Folder.zip", "size": "4.1 MB", "status": "completed"}
    ]
    st.session_state.client_details = {
        "name": "John Doe",
        "date_of_birth": "01/01/1990",
        "tfn": "123 456 789",
        "address": "42 Collins Street, Melbourne VIC 3000",
        "address_status": "needs_confirmation"
    }
    st.session_state.transaction_data = [
        {"date": "2025-03-15", "amount": 40123, "hasReceipt": False, "transactionName": "Motor vehicle expenses"},
        {"date": "2025-02-16", "amount": 3000, "hasReceipt": False, "transactionName": "Buy a laptop"},
        {"date": "2025-01-15", "amount": 45000, "hasReceipt": True, "transactionName": "Buy a car"}
    ]
    st.session_state.show_right_panel = False


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
    
    /* Sidebar styling with blue theme and increased width */
    .css-1d391kg, .css-1lcbmhc, .css-17eq0hr {
        background-color: #f1f5f9 !important;
        border-right: 2px solid #e2e8f0 !important;
        min-width: 400px !important;
        max-width: 450px !important;
        width: 400px !important;
    }
    
    /* Sidebar container adjustment */
    section[data-testid="stSidebar"] {
        width: 400px !important;
        min-width: 400px !important;
    }
    
    section[data-testid="stSidebar"] > div {
        width: 400px !important;
        min-width: 400px !important;
        max-width: 450px !important;
    }
    
    /* Main content area adjustment to accommodate larger sidebar */
    .main .block-container {
        padding-left: 2rem !important;
        max-width: calc(100vw - 420px) !important;
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
    
    /* Sidebar sections styling */
    .css-1d391kg .stSubheader {
        color: #1e40af !important;
        font-weight: 600 !important;
        margin-top: 2rem !important;
        margin-bottom: 1rem !important;
        padding-bottom: 0.5rem !important;
        border-bottom: 2px solid #e2e8f0 !important;
    }
    
    /* Sidebar card styling */
    .sidebar-card {
        background-color: #ffffff !important;
        border: 1px solid #e5e7eb !important;
        border-radius: 8px !important;
        padding: 1rem !important;
        margin-bottom: 1.5rem !important;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1) !important;
    }
    
    /* Document item styling */
    .document-item {
        background-color: #f8fdf4 !important;
        border: 1px solid #d1fae5 !important;
        border-radius: 6px !important;
        padding: 0.75rem !important;
        margin-bottom: 0.75rem !important;
    }
    
    .doc-content {
        display: flex !important;
        align-items: center !important;
        gap: 0.75rem !important;
    }
    
    .doc-icon {
        font-size: 1.25rem !important;
    }
    
    .doc-info {
        flex-grow: 1 !important;
    }
    
    .doc-name {
        font-weight: 600 !important;
        color: #1f2937 !important;
        font-size: 1rem !important;
        margin-bottom: 0.25rem !important;
        word-wrap: break-word !important;
        overflow-wrap: break-word !important;
    }
    
    .doc-size {
        color: #6b7280 !important;
        font-size: 0.9rem !important;
    }
    
    .doc-status {
        color: #059669 !important;
        font-size: 1.1rem !important;
    }
    
    /* Client details field styling */
    .client-field {
        margin-bottom: 1rem !important;
        padding-bottom: 0.75rem !important;
        border-bottom: 1px solid #f3f4f6 !important;
    }
    
    .client-field:last-child {
        border-bottom: none !important;
        margin-bottom: 0 !important;
        padding-bottom: 0 !important;
    }
    
    .field-label {
        font-weight: 600 !important;
        color: #374151 !important;
        font-size: 1rem !important;
        margin-bottom: 0.4rem !important;
    }
    
    .field-value {
        color: #1f2937 !important;
        font-size: 1rem !important;
        display: flex !important;
        align-items: center !important;
        gap: 0.5rem !important;
        line-height: 1.5 !important;
        word-wrap: break-word !important;
        overflow-wrap: break-word !important;
    }
    
    .status-check {
        color: #059669 !important;
        font-weight: 600 !important;
    }
    
    .status-warning {
        color: #f59e0b !important;
        font-weight: 600 !important;
    }
    
    .warning-message {
        background-color: #fef3c7 !important;
        color: #92400e !important;
        padding: 0.6rem !important;
        border-radius: 4px !important;
        font-size: 0.9rem !important;
        margin-top: 0.5rem !important;
        border: 1px solid #f59e0b !important;
        line-height: 1.4 !important;
        word-wrap: break-word !important;
        overflow-wrap: break-word !important;
    }
    
    /* Right panel styling */
    .right-panel-container {
        margin-top: 2rem !important;
    }
    
    .right-panel-content {
        background-color: #ffffff !important;
        border: 2px solid #e2e8f0 !important;
        border-radius: 8px !important;
        padding: 1.5rem !important;
        box-shadow: 0 4px 12px rgba(0,0,0,0.1) !important;
        position: sticky !important;
        top: 2rem !important;
    }
    
    /* MYOB header styling */
    .right-panel-content h3 {
        color: #1e40af !important;
        font-size: 1.25rem !important;
        font-weight: 700 !important;
        margin-bottom: 1rem !important;
        padding-bottom: 0.5rem !important;
        border-bottom: 2px solid #e2e8f0 !important;
        margin-top: 0 !important;
    }
    
    /* Streamlit dataframe styling for right panel */
    .right-panel-content .stDataFrame {
        margin-top: 1rem !important;
    }
    
    .right-panel-content .stDataFrame table {
        border-radius: 8px !important;
        overflow: hidden !important;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1) !important;
    }
    
    .right-panel-content .stDataFrame thead th {
        background-color: #f8fafc !important;
        color: #374151 !important;
        font-weight: 600 !important;
        border-bottom: 2px solid #e5e7eb !important;
        font-size: 0.9rem !important;
    }
    
    .right-panel-content .stDataFrame tbody td {
        padding: 0.75rem !important;
        border-bottom: 1px solid #f3f4f6 !important;
        color: #1f2937 !important;
        font-size: 0.9rem !important;
    }
    
    .right-panel-content .stDataFrame tbody tr:hover {
        background-color: #f9fafb !important;
    }
    
    /* Style specific columns */
    .right-panel-content .stDataFrame tbody td:nth-child(1) {
        color: #2563eb !important;
        font-weight: 500 !important;
    }
    
    .right-panel-content .stDataFrame tbody td:nth-child(2) {
        color: #059669 !important;
        font-weight: 600 !important;
    }
    
    /* Adjust main content when right panel is visible */
    .main-with-right-panel {
        margin-right: 470px !important;
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

# Sidebar sections
with st.sidebar:
    # Uploaded Information Section
    st.subheader("Uploaded Information")
    
    # Documents Received Container
    st.markdown('<div>', unsafe_allow_html=True)
    
    for doc in st.session_state.uploaded_documents:
        st.markdown(f'''
        <div class="document-item">
            <div class="doc-content">
                <div class="doc-icon">📄</div>
                <div class="doc-info">
                    <div class="doc-name">{doc['name']}</div>
                    <div class="doc-size">{doc['size']}</div>
                </div>
                <div class="doc-status">✅</div>
            </div>
        </div>
        ''', unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Client Details Section  
    st.subheader("Client Details")
    
    # Client Details Container
    st.markdown('<div>', unsafe_allow_html=True)
    
    # Name
    st.markdown(f'''
    <div class="client-field">
        <div class="field-label">Name</div>
        <div class="field-value">{st.session_state.client_details['name']} <span class="status-check">✓</span></div>
    </div>
    ''', unsafe_allow_html=True)
    
    # Date of Birth
    st.markdown(f'''
    <div class="client-field">
        <div class="field-label">Date of Birth</div>
        <div class="field-value">{st.session_state.client_details['date_of_birth']} <span class="status-check">✓</span></div>
    </div>
    ''', unsafe_allow_html=True)
    
    # TFN
    st.markdown(f'''
    <div class="client-field">
        <div class="field-label">TFN</div>
        <div class="field-value">{st.session_state.client_details['tfn']} <span class="status-check">✓</span></div>
    </div>
    ''', unsafe_allow_html=True)
    
    # Address
    st.markdown(f'''
    <div class="client-field">
        <div class="field-label">Address</div>
        <div class="field-value">{st.session_state.client_details['address']} <span class="status-warning">⚠️</span></div>
        <div class="warning-message">Please confirm or update this information</div>
    </div>
    ''', unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Reset Session Button
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
            
            # Check if we should show the right panel
            st.session_state.show_right_panel = "motor vehicle" in output_text.lower()
            
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

# Display right panel conditionally
if hasattr(st.session_state, 'show_right_panel') and st.session_state.show_right_panel:
    # Create a container for the right panel using Streamlit components
    with st.container():
        # Create right panel using HTML container but Streamlit components inside
        st.markdown('<div class="right-panel-container">', unsafe_allow_html=True)
        
        # Use columns to position the panel on the right
        col1, col2 = st.columns([3, 2])
        
        with col2:
            st.markdown('<div>', unsafe_allow_html=True)
            st.markdown("### MYOB Business / Silverfin")
            
            # Filter and format data
            table_data = []
            for transaction in st.session_state.transaction_data:
                table_data.append({
                    "Date": transaction["date"],
                    "Transaction Description": transaction["transactionName"],
                    "Amount ($)": f"${transaction['amount']:,}"
                })
            
            df = pd.DataFrame(table_data)
            
            # Display the table with custom styling
            st.dataframe(
                df,
                use_container_width=True,
                hide_index=True,
                column_config={
                    "Date": st.column_config.TextColumn("Date", width="small"),
                    "Transaction Description": st.column_config.TextColumn("Transaction Description", width="large"),
                    "Amount ($)": st.column_config.TextColumn("Amount ($)", width="small")
                }
            )
            
            st.markdown('</div>', unsafe_allow_html=True)
        
        st.markdown('</div>', unsafe_allow_html=True)

