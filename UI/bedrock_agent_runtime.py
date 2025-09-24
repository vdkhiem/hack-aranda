import boto3
from botocore.exceptions import ClientError
import logging
import os

logger = logging.getLogger(__name__)


def invoke_agent(agent_id, agent_alias_id, session_id, prompt):
    try:
        # Create client with explicit region configuration
        session = boto3.Session()
        client = session.client(
            service_name="bedrock-agent-runtime",
            region_name=os.environ.get("AWS_DEFAULT_REGION", "ap-southeast-2")
        )
        
        # Use environment variables or fallback to hardcoded values
        actual_agent_id = agent_id or os.environ.get("BEDROCK_AGENT_ID", "F95VFQLKN0")
        actual_agent_alias_id = agent_alias_id or os.environ.get("BEDROCK_AGENT_ALIAS_ID", "S5KM0MEAKF")
        
        logger.info(f"Invoking agent {actual_agent_id} with alias {actual_agent_alias_id}")
        
        # See https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/bedrock-agent-runtime/client/invoke_agent.html
        response = client.invoke_agent(
            agentId=actual_agent_id,
            agentAliasId=actual_agent_alias_id,
            enableTrace=True,
            sessionId=session_id,
            inputText=prompt
        )

        output_text = ""
        citations = []
        trace = {}

        has_guardrail_trace = False
        for event in response.get("completion"):
            # Combine the chunks to get the output text
            if "chunk" in event:
                chunk = event["chunk"]
                output_text += chunk["bytes"].decode()
                if "attribution" in chunk:
                    citations += chunk["attribution"]["citations"]

            # Extract trace information from all events
            if "trace" in event:
                for trace_type in ["guardrailTrace", "preProcessingTrace", "orchestrationTrace", "postProcessingTrace"]:
                    if trace_type in event["trace"]["trace"]:
                        mapped_trace_type = trace_type
                        if trace_type == "guardrailTrace":
                            if not has_guardrail_trace:
                                has_guardrail_trace = True
                                mapped_trace_type = "preGuardrailTrace"
                            else:
                                mapped_trace_type = "postGuardrailTrace"
                        if trace_type not in trace:
                            trace[mapped_trace_type] = []
                        trace[mapped_trace_type].append(event["trace"]["trace"][trace_type])

    except ClientError as e:
        raise

    return {
        "output_text": output_text,
        "citations": citations,
        "trace": trace
    }
