import streamlit as st
import pandas as pd
import datetime
import boto3
import json
from boto3.dynamodb.types import TypeDeserializer
import pytz
import os

# Securely set AWS credentials from Streamlit secrets
os.environ['AWS_ACCESS_KEY_ID'] = st.secrets["AWS_ACCESS_KEY_ID"]
os.environ['AWS_SECRET_ACCESS_KEY'] = st.secrets["AWS_SECRET_ACCESS_KEY"]
os.environ['AWS_REGION'] = st.secrets["AWS_REGION"]

# Check authentication
if 'authenticated' not in st.session_state or not st.session_state['authenticated']:
    st.warning('You are not logged in. Please log in to access this page.')
    st.switch_page("pages/1_Login.py")

st.set_page_config(page_title="WAFR Analysis Grid", layout="wide")

def logout():
    st.session_state['authenticated'] = False
    st.session_state.pop('username', None)
    st.rerun()

if st.sidebar.button('Logout'):
    logout()

# Create AWS clients
client = boto3.client("bedrock-runtime", region_name=os.environ["AWS_REGION"])
dynamodb = boto3.client("dynamodb", region_name=os.environ["AWS_REGION"])

model_id = "anthropic.claude-3-5-sonnet-20240620-v1:0"

def load_data():
    try:
        response = dynamodb.scan(TableName=st.secrets["WAFR_ACCELERATOR_RUNS_DD_TABLE_NAME"])
        items = response['Items']
        
        while 'LastEvaluatedKey' in response:
            response = dynamodb.scan(
                TableName=st.secrets["WAFR_ACCELERATOR_RUNS_DD_TABLE_NAME"],
                ExclusiveStartKey=response['LastEvaluatedKey']
            )
            items.extend(response['Items'])

        if not items:
            st.warning("There are no existing WAFR review records")
            return pd.DataFrame(columns=['Analysis Id', 'Workload Name', 'Workload Description', 'Analysis Type', 'WAFR Lens', 'Creation Date', 'Status', 'Created By', 'Review Owner', 'Solution Summary', 'pillars', 'selected_wafr_pillars'])

        deserializer = TypeDeserializer()
        unmarshalled_items = [{k: deserializer.deserialize(v) for k, v in item.items()} for item in items]
        df = pd.DataFrame(unmarshalled_items)

        column_mapping = {
            'analysis_id': 'Analysis Id',
            'analysis_title': 'Workload Name',
            'workload_desc': 'Workload Description',
            'analysis_review_type': 'Analysis Type',
            'selected_lens': 'WAFR Lens',
            'creation_date': 'Creation Date',
            'review_status': 'Status',
            'analysis_submitter': 'Created By',
            'review_owner': 'Review Owner',
            'extracted_document': 'Document',
            'architecture_summary': 'Solution Summary'
        }

        df = df.rename(columns={k: v for k, v in column_mapping.items() if k in df.columns})

        for col in column_mapping.values():
            if col not in df.columns:
                df[col] = ''

        def parse_pillars(pillars):
            if isinstance(pillars, list):
                return [
                    {
                        'pillar_id': item.get('pillar_id', ''),
                        'pillar_name': item.get('pillar_name', ''),
                        'llm_response': item.get('llm_response', '') if isinstance(item.get('llm_response'), str) else item.get('llm_response', {})
                    }
                    for item in pillars
                ]
            return []

        if 'pillars' in df.columns:
            df['pillars'] = df['pillars'].apply(parse_pillars)
        else:
            df['pillars'] = [[] for _ in range(len(df))]

        required_columns = ['Analysis Id', 'Workload Name', 'Workload Description', 'Analysis Type', 'WAFR Lens', 'Creation Date', 'Status', 'Created By', 'Review Owner', 'Solution Summary', 'pillars', 'selected_wafr_pillars', 'Document']
        for col in required_columns:
            if col not in df.columns:
                df[col] = ''

        return df[required_columns]

    except Exception as e:
        st.error(f"An error occurred while loading data: {str(e)}")
        return pd.DataFrame(columns=['Analysis Id', 'Workload Name', 'Workload Description', 'Analysis Type', 'WAFR Lens', 'Creation Date', 'Status', 'Created By', 'Review Owner', 'Solution Summary', 'pillars', 'selected_wafr_pillars', 'Document'])

def display_summary(analysis):
    st.subheader("Summary")
    selected_wafr_pillars = ', '.join(analysis['selected_wafr_pillars']) if isinstance(analysis['selected_wafr_pillars'], list) else str(analysis['selected_wafr_pillars'])

    summary_data = {
        "Field": ["Analysis Id", "Workload Name", "Workload Description", "Analysis Type", "Status", "WAFR Lens", "Creation Date", "Created By", "Review Owner", "Selected WAFR Pillars"],
        "Value": [
            analysis['Analysis Id'],
            analysis['Workload Name'],
            analysis['Workload Description'],
            analysis['Analysis Type'],
            analysis['Status'],
            analysis['WAFR Lens'],
            analysis['Creation Date'],
            analysis['Created By'],
            analysis['Review Owner'],
            selected_wafr_pillars
        ]
    }
    st.dataframe(pd.DataFrame(summary_data), hide_index=True, use_container_width=True)

def display_design_review(analysis):
    st.subheader("Solution Summary")
    architecture_review = analysis['Solution Summary']
    st.write(architecture_review if isinstance(architecture_review, str) else "No architecture review data available.")

def display_pillar(pillar):
    st.subheader(f"Review findings & recommendations for pillar: {pillar['pillar_name']}")
    st.write(pillar.get('llm_response', "No LLM response data available."))

def parse_stream(stream):
    for event in stream:
        chunk = event.get('chunk')
        if chunk:
            message = json.loads(chunk.get("bytes").decode())
            if message['type'] == "content_block_delta":
                yield message['delta']['text'] or ""
            elif message['type'] == "message_stop":
                return "\n"

def main():
    st.title("WAFR Analysis")
    st.subheader("WAFR Analysis Runs", divider="rainbow")

    data = load_data()

    selected_columns = ['Analysis Id', 'Workload Name', 'Analysis Type', 'WAFR Lens', 'Creation Date', 'Status', 'Created By']
    st.dataframe(data[selected_columns], use_container_width=True)

    st.subheader("Analysis Details", divider="rainbow")

    analysis_names = data['Workload Name'].tolist()
    selected_analysis = st.selectbox("Select an analysis to view details:", analysis_names)

    if selected_analysis:
        selected_data = data[data['Workload Name'] == selected_analysis].iloc[0]
        wafr_container = st.container()

        with wafr_container:
            tab_names = ["Summary", "Solution Summary"] + [pillar['pillar_name'] for pillar in selected_data['pillars']]
            tabs = st.tabs(tab_names)

            with tabs[0]:
                display_summary(selected_data)
            with tabs[1]:
                display_design_review(selected_data)

            for i, pillar in enumerate(selected_data['pillars'], start=2):
                with tabs[i]:
                    display_pillar(pillar)

        st.subheader("", divider="rainbow")

        chat_container = st.container()
        with chat_container:
            st.subheader("WAFR Chat")
            chat_options = ["Summary", "Solution Summary", "Document"] + [pillar['pillar_name'] for pillar in selected_data['pillars']]
            selected_area = st.selectbox("Select an area to discuss:", chat_options)
            prompt = st.text_input("Ask a question about the selected area:")

        if prompt:
            if selected_area == "Summary":
                area_context = (
                    f"WAFR Analysis Summary:\n"
                    f"Workload Name: {selected_data['Workload Name']}\n"
                    f"Workload Description: {selected_data['Workload Description']}\n"
                    f"WAFR Lens: {selected_data['WAFR Lens']}\n"
                    f"Status: {selected_data['Status']}\n"
                    f"Created By: {selected_data['Created By']}\n"
                    f"Creation Date: {selected_data['Creation Date']}\n"
                    f"Selected WAFR Pillars: {', '.join(selected_data['selected_wafr_pillars'])}\n"
                    f"Architecture Review: {selected_data['Solution Summary']}\n"
                    f"Review Owner: {selected_data['Review Owner']}\n"
                )
            elif selected_area == "Solution Summary":
                area_context = f"WAFR Solution Summary:\n{selected_data['Solution Summary']}\n"
            elif selected_area == "Document":
                area_context = f"Document:\n{selected_data['Document']}\n"
            else:
                pillar_data = next((p for p in selected_data['pillars'] if p['pillar_name'] == selected_area), None)
                area_context = f"WAFR Analysis Context for {selected_area}:\n{pillar_data['llm_response']}" if pillar_data else "Error: Selected area not found."

            full_prompt = f"{area_context}\n\nUser Question: {prompt}\n\nPlease answer the question based on the WAFR analysis context provided above for the {selected_area}."

            body = json.dumps({
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": 1024,
                "messages": [
                    {
                        "role": "user",
                        "content": [{"type": "text", "text": full_prompt}],
                    }
                ],
            })

            guardrail_id = st.secrets.get("GUARDRAIL_ID", "Not Selected")
            if guardrail_id == "Not Selected":
                streaming_response = client.invoke_model_with_response_stream(modelId=model_id, body=body)
            else:
                streaming_response = client.invoke_model_with_response_stream(
                    modelId=model_id,
                    body=body,
                    guardrailIdentifier=guardrail_id,
                    guardrailVersion="DRAFT",
                )

            st.subheader("Response")
            stream = streaming_response.get("body")
            st.write_stream(parse_stream(stream))

if __name__ == "__main__":
    main()
